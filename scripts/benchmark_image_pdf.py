"""Windows scan benchmark: external memory cap, isolated outputs, verified page order.

Run: python scripts/benchmark_image_pdf.py SOURCE --counts 100 500 1000
Reports contain metrics only; all generated PDFs are removed after verification.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'peak_rss', 'rss', 'peak_paged', 'paged', 'peak_nonpaged', 'nonpaged',
            'commit', 'peak_commit', 'private')]


def memory_reader(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x410, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())

    def read():
        counters = MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.rss, counters.private
    return read, lambda: kernel.CloseHandle(handle)


def child(args):
    import pymupdf as fitz
    from PIL import Image
    from core.image_converter import convert_images_to_pdf, create_image_groups
    from core import image_pdf_writer
    from core.utils import natural_sort_key

    if args.batch_mib is not None:
        image_pdf_writer.CHECKPOINT_BYTES = args.batch_mib * 1024**2
    if args.batch_pages is not None:
        image_pdf_writer.CHECKPOINT_PAGES = args.batch_pages

    sources = sorted(args.source.glob('IMG-*.jpeg'), key=lambda p: natural_sort_key(p.name))
    if not sources:
        raise ValueError('No IMG-*.jpeg sources')
    items = [sources[i % len(sources)] for i in range(args.count)]
    options = {'mode': 'combine'}
    if args.scenario != 'combine':
        options = {'mode': 'individual', 'group_size': 1 if args.scenario == 'individual' else 2}
        if args.scenario == 'custom':
            options['custom_groups_str'] = f'3-{args.count - 2}'
    groups = [list(range(args.count))] if args.scenario == 'combine' else create_image_groups(
        args.count, options['group_size'], options.get('custom_groups_str'))
    directory = args.work
    start = time.perf_counter()
    result = convert_images_to_pdf(items, directory / 'result.pdf', **options)
    converted = time.perf_counter()
    (directory / 'converted').touch()
    hashes = {p: hashlib.sha256(p.read_bytes()).digest() for p in set(items)}
    dimensions = set()
    for path in set(items):
        with Image.open(path) as img:
            dimensions.add(img.size)

    def verify(path, indices):
        with fitz.open(path) as doc:
            assert doc.page_count == len(indices)
        # Reopen during validation too, so loading image streams cannot distort the benchmark.
        for offset in range(0, len(indices), 16):
            with fitz.open(path) as doc:
                for local in range(offset, min(offset + 16, len(indices))):
                    xref = doc[local].get_images()[0][0]
                    assert hashlib.sha256(doc.xref_stream_raw(xref)).digest() == hashes[items[indices[local]]]
        with fitz.open(path) as doc:
            for page_no in sorted({0, len(indices) // 2, len(indices) - 1}):
                pix = doc[page_no].get_pixmap(matrix=fitz.Matrix(.05, .05))
                assert pix.width > 0 and pix.height > 0
        fitz.TOOLS.store_shrink(100)

    if args.scenario == 'combine':
        verify(result['output_path'], groups[0])
    else:
        with zipfile.ZipFile(result['output_path']) as archive:
            names = archive.namelist()
            assert len(names) == len(groups)
            for name, group in zip(names, groups):
                extracted = Path(archive.extract(name, directory / 'verify'))
                verify(extracted, group)
                extracted.unlink()
    report = {'count': args.count, 'scenario': args.scenario, 'unique_sources': len(set(items)),
              'batch_mib': image_pdf_writer.CHECKPOINT_BYTES // 1024**2,
              'batch_pages': image_pdf_writer.CHECKPOINT_PAGES,
              'repeated_sources': args.count - len(set(items)), 'dimensions': sorted(dimensions),
              'conversion_seconds': round(converted - start, 2),
              'verification_seconds': round(time.perf_counter() - converted, 2),
              'output_bytes': result['file_size'], 'pdf_files': result['total_files'],
              'verified_pages': args.count}
    (directory / 'result.json').write_text(json.dumps(report), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--counts', type=int, nargs='+', default=[100, 500, 1000])
    parser.add_argument('--scenarios', nargs='+', default=['combine', 'individual', 'pairs', 'custom'])
    parser.add_argument('--report', type=Path, default=ROOT / 'tmp/image-pdf-benchmark.json')
    parser.add_argument('--batch-mib', type=int)
    parser.add_argument('--batch-pages', type=int)
    parser.add_argument('--child', action='store_true')
    parser.add_argument('--count', type=int)
    parser.add_argument('--scenario')
    parser.add_argument('--work', type=Path)
    args = parser.parse_args()
    if args.child:
        child(args)
        return
    if os.name != 'nt':
        raise RuntimeError('External memory sampler currently requires Windows')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    status_file = args.report.with_suffix('.status.json')
    reports = []
    for count in args.counts:
        for scenario in args.scenarios:
            with TemporaryDirectory(prefix='image-bench-', dir=args.report.parent) as work:
                work = Path(work)
                # Bypass Windows venv's redirector so the measured PID owns the conversion memory.
                bootstrap = (f'import runpy,sys; sys.path[:]={sys.path!r}; '
                             'sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0], run_name="__main__")')
                cmd = [sys._base_executable, '-c', bootstrap, str(Path(__file__).resolve()), str(args.source), '--child',
                       '--count', str(count), '--scenario', scenario, '--work', str(work)]
                if args.batch_mib is not None:
                    cmd += ['--batch-mib', str(args.batch_mib)]
                if args.batch_pages is not None:
                    cmd += ['--batch-pages', str(args.batch_pages)]
                with (work / 'child.log').open('w', encoding='utf-8') as log:
                    process = subprocess.Popen(cmd, stdout=log, stderr=log,
                                               creationflags=subprocess.CREATE_NO_WINDOW)
                    read = close = None
                    try:
                        read, close = memory_reader(process.pid)
                        peak_rss = peak_private = conversion_private = 0
                        started = last_status = time.monotonic()
                        status_file.write_text(json.dumps({'state': 'running', 'count': count,
                                                          'scenario': scenario, 'pid': process.pid}), encoding='utf-8')
                        while process.poll() is None:
                            try:
                                rss, private = read()
                            except OSError:
                                if process.poll() is not None:
                                    break
                                raise
                            peak_rss, peak_private = max(peak_rss, rss), max(peak_private, private)
                            if not (work / 'converted').exists():
                                conversion_private = max(conversion_private, private)
                            if private > 2 * 1024**3:
                                raise RuntimeError(f'{count}/{scenario} exceeded 2 GiB private memory')
                            if time.monotonic() - last_status >= 5:
                                status_file.write_text(json.dumps({
                                    'state': 'verifying' if (work / 'converted').exists() else 'converting',
                                    'count': count, 'scenario': scenario, 'pid': process.pid,
                                    'elapsed_seconds': round(time.monotonic() - started, 1),
                                    'peak_private_mib': round(peak_private / 1024**2, 1),
                                }), encoding='utf-8')
                                last_status = time.monotonic()
                            time.sleep(.1)
                        if process.returncode:
                            raise RuntimeError((work / 'child.log').read_text(encoding='utf-8'))
                    except BaseException as error:
                        status_file.write_text(json.dumps({'state': 'failed', 'count': count,
                                                          'scenario': scenario, 'error': str(error)}), encoding='utf-8')
                        raise
                    finally:
                        if process.poll() is None:
                            process.kill()
                        process.wait()
                        if close:
                            close()
                report = json.loads((work / 'result.json').read_text(encoding='utf-8'))
                report.update(peak_rss_mib=round(peak_rss / 1024**2, 1),
                              peak_private_mib=round(peak_private / 1024**2, 1),
                              conversion_peak_private_mib=round(conversion_private / 1024**2, 1))
                reports.append(report)
                args.report.write_text(json.dumps(reports, indent=2), encoding='utf-8')
                print(json.dumps({key: value for key, value in report.items() if key != 'dimensions'}), flush=True)
                if conversion_private >= 1024**3:
                    raise RuntimeError('Conversion exceeded 1 GiB acceptance target; stop before scaling up')
    status_file.write_text(json.dumps({'state': 'complete', 'cases': len(reports)}), encoding='utf-8')


if __name__ == '__main__':
    main()
