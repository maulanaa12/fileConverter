from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import os
import time

from fastapi.testclient import TestClient
from PIL import Image

from app import app
from core.rate_limiter import limiter


def queued_conversion_probe(**kwargs):
    from core.image_converter import convert_images_to_pdf
    marker = Path(kwargs['output_path']).parent / 'started'
    marker.write_text(str(os.getpid()))
    time.sleep(.5)
    result = convert_images_to_pdf(**kwargs)
    result['worker_pid'] = os.getpid()
    result['started'] = marker.stat().st_mtime
    result['finished'] = time.time()
    return result


def test_separate_pdfs_saved_without_zip_in_selected_folder(tmp_path: Path):
    images = []
    for number in (1, 2):
        image_path = tmp_path / f"page_{number}.png"
        Image.new("RGB", (10, 10), "white").save(image_path)
        images.append(str(image_path))

    destination = tmp_path / "results"
    limiter.reset()
    with TestClient(app) as client:
        response = client.post(
            "/api/image-to-pdf",
            json={
                "images": images,
                "mode": "individual",
                "group_size": 1,
                "custom_output_dir": str(destination),
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["saved_to_folder"] == str(destination.resolve())
        assert sorted(path.name for path in destination.iterdir()) == ["page_1.pdf", "page_2.pdf"]
        assert client.get(result["download_url"]).status_code == 200


def test_conversions_are_serial_and_health_remains_available(tmp_path, monkeypatch):
    import app as app_module
    monkeypatch.setattr(app_module, 'convert_images_to_pdf', queued_conversion_probe)
    monkeypatch.setattr(app_module, 'get_task_dirs',
                        lambda task_id: (tmp_path, make_output(tmp_path, task_id)))
    image = tmp_path / 'source.png'
    with Image.new('RGB', (50, 60), 'red') as img:
        img.save(image)
    limiter.reset()
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as callers:
        first = callers.submit(client.post, '/api/image-to-pdf', json={'images': [str(image)]})
        deadline = time.monotonic() + 15
        while not list(tmp_path.glob('*/started')):
            assert time.monotonic() < deadline
            time.sleep(.02)
        second = callers.submit(client.post, '/api/image-to-pdf', json={'images': [str(image)]})
        assert client.get('/api/health').status_code == 200
        assert not first.done()
        a, b = first.result(timeout=20).json(), second.result(timeout=20).json()
        assert a['success'] and b['success']
        assert a['worker_pid'] == b['worker_pid'] != os.getpid()
        assert a['finished'] <= b['started']


def make_output(root, task_id):
    path = root / task_id
    path.mkdir()
    return path


def test_folder_failure_keeps_download_available(tmp_path):
    image = tmp_path / 'source.png'
    with Image.new('RGB', (50, 60), 'red') as img:
        img.save(image)
    blocked = tmp_path / 'blocked'
    blocked.write_text('this is a file, not a folder')
    limiter.reset()
    with TestClient(app) as client:
        response = client.post('/api/image-to-pdf', json={
            'images': [str(image)], 'custom_output_dir': str(blocked),
        })
        result = response.json()
        assert result['success'] and result['saved_to_folder'] is None
        assert result['warning']
        assert client.get(result['download_url']).status_code == 200
