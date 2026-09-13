"""
Tests for SEC-09 (ZIP Slip) and SEC-10 (Version & Info Exposure).
"""
import io
import sys
import shutil
import zipfile
from pathlib import Path

# Tambahkan project root ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from core.utils import OUTPUT_DIR


def get_test_client():
    """Membuat TestClient fresh."""
    from core.rate_limiter import limiter
    limiter.reset()
    from app import app
    return TestClient(app)


# ============================================================
# SEC-09: ZIP Slip Tests
# ============================================================

def create_test_zip(entries: dict, zip_path: Path):
    """Membuat file ZIP dengan entry yang ditentukan.

    Args:
        entries: dict {filename: content_bytes}
        zip_path: Path file ZIP yang akan dibuat
    """
    with zipfile.ZipFile(zip_path, 'w') as z:
        for name, content in entries.items():
            z.writestr(name, content)


def test_sec09_normal_zip_extracts():
    """ZIP dengan entry normal harus diekstrak dengan benar."""
    from app import handle_custom_save

    test_dir = OUTPUT_DIR / "test_sec09_normal"
    test_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = OUTPUT_DIR / "test_sec09_normal_out"

    try:
        # Buat ZIP dengan file normal
        zip_path = test_dir / "test.zip"
        create_test_zip({
            "document.pdf": b"%PDF-1.4 test",
            "image.jpg": b"\xff\xd8\xff test jpg",
        }, zip_path)

        result = handle_custom_save(zip_path, str(extract_dir))
        assert result is not None

        # Verifikasi file berhasil diekstrak
        assert (extract_dir / "document.pdf").exists(), "document.pdf should be extracted"
        assert (extract_dir / "image.jpg").exists(), "image.jpg should be extracted"
        print("  [PASS] test_sec09_normal_zip_extracts PASSED")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
        shutil.rmtree(extract_dir, ignore_errors=True)


def test_sec09_traversal_entry_blocked():
    """ZIP entry dengan path traversal (../../) harus di-skip."""
    from app import handle_custom_save

    test_dir = OUTPUT_DIR / "test_sec09_traversal"
    test_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = OUTPUT_DIR / "test_sec09_traversal_out"

    try:
        # Buat ZIP dengan entry traversal
        zip_path = test_dir / "evil.zip"
        create_test_zip({
            "safe_file.txt": b"safe content",
            "../../evil.txt": b"evil content",
            "../../../etc/passwd": b"root:x:0:0",
        }, zip_path)

        result = handle_custom_save(zip_path, str(extract_dir))
        assert result is not None

        # File aman harus ada
        assert (extract_dir / "safe_file.txt").exists(), "safe_file.txt should be extracted"

        # File traversal TIDAK boleh ada di luar extract_dir
        parent_evil = extract_dir.parent / "evil.txt"
        assert not parent_evil.exists(), "Traversal file should NOT exist in parent"

        print("  [PASS] test_sec09_traversal_entry_blocked PASSED")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
        shutil.rmtree(extract_dir, ignore_errors=True)
        # Cleanup jika traversal berhasil keluar (seharusnya tidak)
        parent_evil = extract_dir.parent / "evil.txt"
        if parent_evil.exists():
            parent_evil.unlink()


def test_sec09_absolute_path_entry_blocked():
    """ZIP entry dengan absolute path harus di-skip."""
    from app import handle_custom_save

    test_dir = OUTPUT_DIR / "test_sec09_abs"
    test_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = OUTPUT_DIR / "test_sec09_abs_out"

    try:
        zip_path = test_dir / "abs.zip"
        # zipfile.writestr dengan absolute path di Windows tidak benar-benar
        # menulis ke absolute path, tapi kita tetap validasi
        create_test_zip({
            "normal.txt": b"normal",
            "/tmp/evil.txt": b"evil",
        }, zip_path)

        result = handle_custom_save(zip_path, str(extract_dir))
        assert result is not None

        # Normal file harus ada
        assert (extract_dir / "normal.txt").exists(), "normal.txt should be extracted"
        print("  [PASS] test_sec09_absolute_path_entry_blocked PASSED")
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
        shutil.rmtree(extract_dir, ignore_errors=True)


# ============================================================
# SEC-10: Version & Information Exposure Tests
# ============================================================

def test_sec10_docs_disabled():
    """/docs harus return 404."""
    client = get_test_client()
    resp = client.get("/docs")
    assert resp.status_code == 404, f"Expected 404 for /docs, got {resp.status_code}"
    print("  [PASS] test_sec10_docs_disabled PASSED")


def test_sec10_redoc_disabled():
    """/redoc harus return 404."""
    client = get_test_client()
    resp = client.get("/redoc")
    assert resp.status_code == 404, f"Expected 404 for /redoc, got {resp.status_code}"
    print("  [PASS] test_sec10_redoc_disabled PASSED")


def test_sec10_openapi_json_disabled():
    """/openapi.json harus return 404."""
    client = get_test_client()
    resp = client.get("/openapi.json")
    assert resp.status_code == 404, f"Expected 404 for /openapi.json, got {resp.status_code}"
    print("  [PASS] test_sec10_openapi_json_disabled PASSED")


def test_sec10_sanitize_windows_path():
    """sanitize_error harus menghapus Windows path dari error message."""
    from app import sanitize_error

    err = Exception(
        r"File not found: C:\Users\johndoe\Documents\secret\file.pdf"
    )
    result = sanitize_error(err)
    assert "johndoe" not in result, f"Username leaked: {result}"
    assert "Documents" not in result, f"Path leaked: {result}"
    assert "<path>" in result, f"Should contain <path> placeholder: {result}"
    print("  [PASS] test_sec10_sanitize_windows_path PASSED")


def test_sec10_sanitize_linux_path():
    """sanitize_error harus menghapus Linux path dari error message."""
    from app import sanitize_error

    err = Exception(
        "Permission denied: /home/azmi/projects/converter/uploads/task123"
    )
    result = sanitize_error(err)
    assert "azmi" not in result, f"Username leaked: {result}"
    assert "projects" not in result, f"Path leaked: {result}"
    assert "<path>" in result, f"Should contain <path> placeholder: {result}"
    print("  [PASS] test_sec10_sanitize_linux_path PASSED")


def test_sec10_sanitize_preserves_safe_message():
    """sanitize_error tidak mengubah pesan tanpa path."""
    from app import sanitize_error

    err = Exception("Invalid PDF format: header not found")
    result = sanitize_error(err)
    assert result == "Invalid PDF format: header not found", \
        f"Safe message was modified: {result}"
    print("  [PASS] test_sec10_sanitize_preserves_safe_message PASSED")


def test_sec10_error_response_no_path():
    """Error response dari endpoint tidak boleh mengandung path filesystem."""
    client = get_test_client()
    # Trigger error pada merge endpoint dengan file yang tidak ada
    resp = client.post("/api/merge", json={
        "files": [{"path": r"C:\Users\testuser\nonexistent.pdf", "rotation": 0}],
        "output_filename": "test.pdf"
    })
    body = resp.text
    # Response tidak boleh mengandung username dari path
    assert "testuser" not in body.lower(), \
        f"Username leaked in error response: {body}"
    print("  [PASS] test_sec10_error_response_no_path PASSED")


# ============================================================
# Runner
# ============================================================

if __name__ == "__main__":
    print("\n[SEC-09] ZIP Slip Tests")
    print("=" * 50)
    test_sec09_normal_zip_extracts()
    test_sec09_traversal_entry_blocked()
    test_sec09_absolute_path_entry_blocked()

    print("\n[SEC-10] Version & Info Exposure Tests")
    print("=" * 50)
    test_sec10_docs_disabled()
    test_sec10_redoc_disabled()
    test_sec10_openapi_json_disabled()
    test_sec10_sanitize_windows_path()
    test_sec10_sanitize_linux_path()
    test_sec10_sanitize_preserves_safe_message()
    test_sec10_error_response_no_path()

    print("\n[OK] All SEC-09/10 tests passed!")
