from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app import app
from core.rate_limiter import limiter


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
