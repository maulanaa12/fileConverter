from pathlib import Path
import io

from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from app import app
from core.rate_limiter import limiter
from core.splitter import organize_pdf_pages


def make_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=500)
    with path.open("wb") as output:
        writer.write(output)


def test_organize_can_insert_repeat_rotate_and_preview(tmp_path: Path):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    make_pdf(first, [200, 300])
    make_pdf(second, [400])
    limiter.reset()

    with TestClient(app) as client:
        with first.open("rb") as first_file, second.open("rb") as second_file:
            upload = client.post(
                "/api/upload",
                files=[
                    ("files", ("first.pdf", first_file, "application/pdf")),
                    ("files", ("second.pdf", second_file, "application/pdf")),
                ],
            )
        assert upload.status_code == 200
        uploaded = upload.json()["files"]
        base_path, added_path = [item["temp_path"] for item in uploaded]

        preview = client.get("/api/pdf-page-preview", params={"path": added_path, "page": 1})
        assert preview.status_code == 200
        assert preview.headers["content-type"] == "image/png"
        assert preview.content.startswith(b"\x89PNG")
        assert client.get("/api/pdf-page-preview", params={"path": added_path, "page": 2}).status_code == 400
        assert client.get("/api/pdf-page-preview", params={"path": str(first), "page": 1}).status_code == 403
        forbidden = client.post(
            "/api/organize",
            json={"pdf_path": base_path, "operations": [{"source_path": str(second), "page": 1}]},
        )
        assert forbidden.status_code == 403

        response = client.post(
            "/api/organize",
            json={
                "pdf_path": base_path,
                "operations": [
                    {"source_path": added_path, "page": 1},
                    {"source_path": base_path, "page": 2},
                    {"source_path": base_path, "page": 2, "rotation": 90},
                    {"source_path": base_path, "page": 1, "delete": True},
                ],
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["total_pages"] == 3
        pdf = PdfReader(result["output_path"])
        assert [int(page.mediabox.width) for page in pdf.pages] == [400, 300, 300]
        assert [page.get("/Rotate", 0) for page in pdf.pages] == [0, 0, 90]
        download = client.get(result["download_url"])
        assert download.status_code == 200
        assert len(PdfReader(io.BytesIO(download.content)).pages) == 3


def test_repeated_pages_keep_independent_rotations(tmp_path: Path):
    source = tmp_path / "source.pdf"
    make_pdf(source, [200])
    result = organize_pdf_pages(source, tmp_path / "result.PDF", [
        {"page": 1, "rotation": 90},
        {"page": 1, "rotation": 180},
        {"page": 1},
    ])
    assert result["filename"] == "result.PDF"
    assert [page.get("/Rotate", 0) for page in PdfReader(result["output_path"]).pages] == [90, 180, 0]
    assert PdfReader(source).pages[0].get("/Rotate", 0) == 0


def test_same_named_uploads_and_custom_save(tmp_path: Path):
    first, second = tmp_path / "first.pdf", tmp_path / "second.pdf"
    make_pdf(first, [200, 300])
    make_pdf(second, [400])
    limiter.reset()
    with TestClient(app) as client:
        upload = client.post("/api/upload", files=[
            ("files", ("same.pdf", first.read_bytes(), "application/pdf")),
            ("files", ("same.pdf", second.read_bytes(), "application/pdf")),
        ]).json()["files"]
        assert upload[0]["temp_path"] != upload[1]["temp_path"]
        assert [len(PdfReader(item["temp_path"]).pages) for item in upload] == [2, 1]
        response = client.post("/api/organize", json={
            "pdf_path": upload[0]["temp_path"],
            "output_filename": "Gabungan #1.PDF",
            "custom_output_dir": str(tmp_path / "saved"),
            "operations": [
                {"source_path": upload[1]["temp_path"], "page": 1, "rotation": 270},
                {"page": 2},
            ],
        })
        assert response.status_code == 200
        result = response.json()
        assert Path(result["saved_to_folder"]).read_bytes() == Path(result["output_path"]).read_bytes()
        download = client.get(result["download_url"])
        assert download.status_code == 200
        pages = PdfReader(io.BytesIO(download.content)).pages
        assert [int(page.mediabox.width) for page in pages] == [400, 300]
        assert [page.get("/Rotate", 0) for page in pages] == [270, 0]
        for operations in ([{"page": 3}], [{"page": 1, "delete": True}], [{"page": 1, "rotation": 45}]):
            rejected = client.post("/api/organize", json={"pdf_path": upload[0]["temp_path"], "operations": operations})
            assert rejected.status_code == 400
            assert rejected.json()["success"] is False


def test_custom_save_failure_keeps_download(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.pdf"
    make_pdf(source, [200])
    monkeypatch.setattr("app.handle_custom_save", lambda *args: None)
    limiter.reset()
    with TestClient(app) as client:
        uploaded = client.post("/api/upload", files={"files": ("source.pdf", source.read_bytes(), "application/pdf")}).json()["files"][0]
        response = client.post("/api/organize", json={
            "pdf_path": uploaded["temp_path"], "operations": [{"page": 1}],
            "custom_output_dir": str(tmp_path / "saved"),
        })
        result = response.json()
        assert result["success"] is True
        assert result["saved_to_folder"] is None
        assert result["save_warning"]
        assert client.get(result["download_url"]).status_code == 200
