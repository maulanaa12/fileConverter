import zipfile
from pathlib import Path

import pymupdf as fitz
import pytest
from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat
from pypdf import PdfReader

from core.image_converter import convert_images_to_pdf
from core import image_pdf_writer


def picture(path, orientation=1, mode='RGB'):
    with Image.new(mode, (120, 80), 'white') as img:
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 0, 59, 39), fill='red')
        draw.rectangle((60, 40, 119, 79), fill='blue')
        exif = Image.Exif()
        exif[274] = orientation
        img.save(path, exif=exif)
    return path


@pytest.mark.parametrize('exif', range(1, 9))
@pytest.mark.parametrize('rotation', [0, 90, 180, 270, 33])
def test_orientation_matches_pillow(tmp_path, exif, rotation):
    source = picture(tmp_path / 'image.jpg', exif)
    output = tmp_path / 'out.pdf'
    convert_images_to_pdf([{'path': str(source), 'rotation': rotation}], output)
    with Image.open(source) as raw, ImageOps.exif_transpose(raw) as transposed:
        with transposed.convert('RGB') as rgb, rgb.rotate(-rotation, expand=True) as expected:
            with fitz.open(output) as doc:
                page = doc[0]
                assert page.rect.width == pytest.approx(expected.width * .72, abs=.01)
                assert page.rect.height == pytest.approx(expected.height * .72, abs=.01)
                pix = page.get_pixmap(dpi=100)
                with Image.frombytes('RGB', (pix.width, pix.height), pix.samples) as actual:
                    with actual.resize(expected.size) as resized:
                        assert max(ImageStat.Stat(ImageChops.difference(resized, expected)).mean) < 8
                if exif in (1, 3, 6, 8) and rotation % 90 == 0:
                    xref = page.get_images()[0][0]
                    assert doc.xref_stream_raw(xref) == source.read_bytes()


@pytest.mark.parametrize('paper,orientation,size', [
    ('a4', 'portrait', (595, 842)), ('a4', 'auto', (842, 595)),
    ('letter', 'landscape', (792, 612)), ('legal', 'portrait', (612, 1008)),
    ('fit', 'auto', (126.4, 97.6)),
])
def test_page_geometry_and_source_resolution(tmp_path, paper, orientation, size):
    source = picture(tmp_path / 'image.jpg')
    output = tmp_path / 'out.pdf'
    convert_images_to_pdf([source], output, paper_size=paper, orientation=orientation, margin_size='small')
    with fitz.open(output) as doc:
        page = doc[0]
        assert (page.rect.width, page.rect.height) == pytest.approx(size)
        info = page.get_image_info()[0]
        assert (info['width'], info['height']) == (120, 80)
        bbox = fitz.Rect(info['bbox'])
        assert bbox.x0 >= 19.99 and bbox.y0 >= 19.99
        assert bbox.x1 <= size[0] - 19.99 and bbox.y1 <= size[1] - 19.99


@pytest.mark.parametrize('mode', ['RGBA', 'LA', 'P'])
def test_transparency_is_white(tmp_path, mode):
    source = tmp_path / 'transparent.png'
    with Image.new('RGBA', (40, 40), (255, 0, 0, 0)) as rgba:
        with rgba.convert(mode) as img:
            img.save(source)
    output = tmp_path / 'out.pdf'
    convert_images_to_pdf([source], output)
    with fitz.open(output) as doc:
        pix = doc[0].get_pixmap()
        assert pix.pixel(10, 10) == (255, 255, 255)


@pytest.mark.parametrize('mode,group_size,custom,lengths', [
    ('combine', 1, None, [35]), ('individual', 1, None, [1] * 35),
    ('separated', 2, None, [2] * 17 + [1]),
    ('individual', 2, '3-30', [2, 28, 2, 2, 1]),
])
def test_grouping_order_and_incremental_output(tmp_path, monkeypatch, mode, group_size, custom, lengths):
    monkeypatch.setattr(image_pdf_writer, 'CHECKPOINT_PAGES', 16)
    sources = []
    for number in range(35):
        path = tmp_path / f'{number}.png'
        with Image.new('RGB', (30, 20), (number * 7, 0, 0)) as img:
            img.save(path)
        sources.append(path)
    result = convert_images_to_pdf(sources, tmp_path / 'out.pdf', mode=mode,
                                   group_size=group_size, custom_groups_str=custom,
                                   naming_mode='sequence', start_num=10, step=2,
                                   padding=3, prefix='scan_', suffix='_done')
    assert result['total_files'] == len(lengths)
    if mode == 'combine':
        paths = [Path(result['output_path'])]
    else:
        with zipfile.ZipFile(result['output_path']) as archive:
            assert archive.testzip() is None
            assert archive.namelist() == [f'scan_{10+i*2:03d}_done.pdf' for i in range(len(lengths))]
            archive.extractall(tmp_path / 'extracted')
            paths = [tmp_path / 'extracted' / name for name in archive.namelist()]
    index = 0
    for path, count in zip(paths, lengths):
        assert len(PdfReader(path).pages) == count
        with fitz.open(path) as doc:
            for page in doc:
                assert page.get_pixmap().pixel(5, 5) == (index * 7, 0, 0)
                index += 1
    assert not list(tmp_path.glob('.image-pdf-*'))


def test_duplicate_original_names(tmp_path):
    first = picture(tmp_path / 'same.jpg')
    result = convert_images_to_pdf([first, first], tmp_path / 'out.pdf', mode='individual')
    with zipfile.ZipFile(result['output_path']) as archive:
        assert archive.namelist() == ['same.pdf', 'same_1.pdf']


@pytest.mark.parametrize('suffix,mode', [('.bmp', 'RGB'), ('.webp', 'RGB'),
                                        ('.tiff', 'RGB'), ('.jpg', 'L'), ('.jpg', 'CMYK')])
def test_supported_formats_and_color_modes(tmp_path, suffix, mode):
    source = picture(tmp_path / f'source{suffix}', mode=mode)
    output = tmp_path / 'out.pdf'
    convert_images_to_pdf([source], output)
    with Image.open(source) as raw, raw.convert('RGB') as expected, fitz.open(output) as doc:
        pix = doc[0].get_pixmap(dpi=100)
        with Image.frombytes('RGB', (pix.width, pix.height), pix.samples) as rendered:
            with rendered.resize(expected.size) as actual:
                assert max(ImageStat.Stat(ImageChops.difference(actual, expected)).mean) < 8


def test_failed_publish_preserves_previous_result(tmp_path, monkeypatch):
    import core.image_converter as converter
    source = picture(tmp_path / 'source.jpg')
    output = tmp_path / 'out.pdf'
    output.write_bytes(b'previous result')
    def deny_replace(*args):
        raise PermissionError('output is locked')
    monkeypatch.setattr(converter.os, 'replace', deny_replace)
    with pytest.raises(PermissionError):
        convert_images_to_pdf([source], output)
    assert output.read_bytes() == b'previous result'
    assert not list(tmp_path.glob('.image-pdf-*'))


@pytest.mark.parametrize('failure', ['corrupt', 'missing', 'write', 'incremental'])
@pytest.mark.parametrize('mode', ['combine', 'individual'])
def test_failure_preserves_previous_output_and_cleans_scratch(tmp_path, monkeypatch, failure, mode):
    source = picture(tmp_path / 'good.jpg')
    bad = tmp_path / 'bad.jpg'
    bad.write_bytes(b'not an image')
    output = tmp_path / ('out.pdf' if mode == 'combine' else 'out.zip')
    output.write_bytes(b'previous result')
    images = [source, bad]
    if failure == 'missing':
        bad.unlink()
    elif failure == 'write':
        def fail(*args, **kwargs):
            raise OSError('disk full')
        monkeypatch.setattr(fitz.Document, 'save', fail)
    elif failure == 'incremental':
        monkeypatch.setattr(image_pdf_writer, 'CHECKPOINT_PAGES', 1)
        monkeypatch.setattr(fitz.Document, 'can_save_incrementally', lambda self: False)
        images = [source, source]
    with pytest.raises(Exception):
        convert_images_to_pdf(images, output, mode=mode, group_size=2)
    assert output.read_bytes() == b'previous result'
    assert source.exists()
    assert not list(tmp_path.glob('.image-pdf-*'))


def test_byte_budget_flushes_before_page_limit(tmp_path, monkeypatch):
    source = picture(tmp_path / 'source.jpg')
    monkeypatch.setattr(image_pdf_writer, 'CHECKPOINT_BYTES', 1)
    output = tmp_path / 'out.pdf'
    convert_images_to_pdf([source] * 4, output)
    with fitz.open(output) as doc:
        assert doc.page_count == 4
        assert doc.version_count == 4
