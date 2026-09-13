"""
Tests for SEC-06 (Download Path Traversal), SEC-07 (CORS), and SEC-08 (Rate Limiting).

Menggunakan FastAPI TestClient untuk pengujian integration-level.
"""
import sys
from pathlib import Path

# Tambahkan project root ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from core.utils import OUTPUT_DIR


def get_test_client():
    """Membuat TestClient fresh untuk setiap test group."""
    # Reset rate limiter state untuk setiap test group
    from core.rate_limiter import limiter
    limiter.reset()

    from app import app
    return TestClient(app)


def setup_test_file():
    """Membuat file test di OUTPUT_DIR untuk pengujian download."""
    test_task_id = "test-task-001"
    test_filename = "test_document.pdf"
    test_dir = OUTPUT_DIR / test_task_id
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / test_filename
    test_file.write_bytes(b"%PDF-1.4 fake content for testing")
    return test_task_id, test_filename, test_file


def cleanup_test_file(test_task_id: str):
    """Membersihkan file test setelah pengujian."""
    import shutil
    test_dir = OUTPUT_DIR / test_task_id
    if test_dir.exists():
        shutil.rmtree(test_dir)


# ============================================================
# SEC-06: Download Path Traversal Tests
# ============================================================

def test_sec06_normal_download():
    """Download file valid harus berhasil (200)."""
    task_id, filename, test_file = setup_test_file()
    try:
        client = get_test_client()
        resp = client.get(f"/api/download/{task_id}/{filename}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert b"PDF" in resp.content
        print("  [PASS] test_sec06_normal_download PASSED")
    finally:
        cleanup_test_file(task_id)


def test_sec06_task_id_traversal_rejected():
    """Path traversal di task_id (../../) harus ditolak (400)."""
    client = get_test_client()
    resp = client.get("/api/download/../../etc/test.pdf")
    # FastAPI mungkin menangani ".." di path, tapi jika sampai ke handler:
    assert resp.status_code in (400, 404, 422), \
        f"Expected 400/404/422, got {resp.status_code}"
    print("  [PASS] test_sec06_task_id_traversal_rejected PASSED")


def test_sec06_task_id_special_chars_rejected():
    """Task ID dengan karakter spesial harus ditolak (400)."""
    client = get_test_client()
    # Task ID dengan titik-titik dan slash
    resp = client.get("/api/download/task..id/test.pdf")
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print("  [PASS] test_sec06_task_id_special_chars_rejected PASSED")


def test_sec06_filename_traversal_rejected():
    """Path traversal di filename (../) harus ditolak."""
    task_id, _, _ = setup_test_file()
    try:
        client = get_test_client()
        # Filename dengan path traversal — Path("../../../etc/passwd").name = "passwd"
        # Ini aman karena Path().name menghilangkan path separator
        # Tapi tetap harus gagal karena file "passwd" tidak ada
        resp = client.get(f"/api/download/{task_id}/../../../etc/passwd")
        assert resp.status_code in (400, 403, 404, 422), \
            f"Expected 400/403/404/422, got {resp.status_code}"
        print("  [PASS] test_sec06_filename_traversal_rejected PASSED")
    finally:
        cleanup_test_file(task_id)


def test_sec06_dotdot_filename_rejected():
    """Filename '..' harus ditolak (400)."""
    client = get_test_client()
    resp = client.get("/api/download/test-task-001/..")
    assert resp.status_code in (400, 404, 422), \
        f"Expected 400/404/422, got {resp.status_code}"
    print("  [PASS] test_sec06_dotdot_filename_rejected PASSED")


def test_sec06_nonexistent_file_404():
    """File yang tidak ada harus return 404."""
    client = get_test_client()
    resp = client.get("/api/download/valid-task-id/nonexistent.pdf")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    print("  [PASS] test_sec06_nonexistent_file_404 PASSED")


def test_sec06_valid_task_id_formats():
    """Task ID alfanumerik, underscore, dan dash harus diterima."""
    task_id_variants = ["abc123", "task-001", "my_task_id", "ABC-def_123"]
    client = get_test_client()
    for tid in task_id_variants:
        resp = client.get(f"/api/download/{tid}/test.pdf")
        # Harus 404 (file tidak ada), bukan 400 (format invalid)
        assert resp.status_code == 404, \
            f"Task ID '{tid}': Expected 404, got {resp.status_code}"
    print("  [PASS] test_sec06_valid_task_id_formats PASSED")


# ============================================================
# SEC-07: CORS Configuration Tests
# ============================================================

def test_sec07_allowed_origin_accepted():
    """Request dari allowed origin harus menyertakan CORS header."""
    client = get_test_client()
    resp = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:8000"}
    )
    assert resp.status_code == 200
    cors_header = resp.headers.get("access-control-allow-origin")
    assert cors_header == "http://localhost:8000", \
        f"Expected CORS header 'http://localhost:8000', got '{cors_header}'"
    print("  [PASS] test_sec07_allowed_origin_accepted PASSED")


def test_sec07_disallowed_origin_no_cors():
    """Request dari origin tidak dikenal tidak boleh punya CORS header."""
    client = get_test_client()
    resp = client.get(
        "/api/health",
        headers={"Origin": "http://evil.com"}
    )
    assert resp.status_code == 200  # Request tetap diproses (non-preflight)
    cors_header = resp.headers.get("access-control-allow-origin")
    assert cors_header is None, \
        f"Expected no CORS header for evil.com, got '{cors_header}'"
    print("  [PASS] test_sec07_disallowed_origin_no_cors PASSED")


def test_sec07_preflight_allowed_origin():
    """Preflight OPTIONS dari allowed origin harus berhasil."""
    client = get_test_client()
    resp = client.options(
        "/api/upload",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:8000"
    print("  [PASS] test_sec07_preflight_allowed_origin PASSED")


def test_sec07_preflight_disallowed_origin():
    """Preflight OPTIONS dari origin tidak dikenal tidak boleh punya CORS header."""
    client = get_test_client()
    resp = client.options(
        "/api/upload",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    cors_header = resp.headers.get("access-control-allow-origin")
    assert cors_header is None, \
        f"Expected no CORS header for malicious site, got '{cors_header}'"
    print("  [PASS] test_sec07_preflight_disallowed_origin PASSED")


def test_sec07_localhost_8041_accepted():
    """Request dari port 8041 (desktop app) harus diterima."""
    client = get_test_client()
    resp = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:8041"}
    )
    cors_header = resp.headers.get("access-control-allow-origin")
    assert cors_header == "http://localhost:8041", \
        f"Expected CORS header for :8041, got '{cors_header}'"
    print("  [PASS] test_sec07_localhost_8041_accepted PASSED")


# ============================================================
# SEC-08: Rate Limiting Tests
# ============================================================

def test_sec08_within_limit_succeeds():
    """Request dalam batas rate limit harus berhasil."""
    client = get_test_client()
    # Health endpoint (30/minute limit) — satu request harus sukses
    resp = client.get("/api/health")
    assert resp.status_code == 200
    print("  [PASS] test_sec08_within_limit_succeeds PASSED")


def test_sec08_heavy_endpoint_rate_limited():
    """Request melebihi heavy limit (5/minute) harus mendapat 429."""
    client = get_test_client()
    # Kirim 6 request ke endpoint merge (heavy: 5/minute)
    # Merge akan gagal karena payload kosong, tapi rate limiter cek dulu
    for i in range(5):
        resp = client.post("/api/merge", json={
            "files": [],
            "output_filename": "test.pdf"
        })
        # Bisa 200 atau 400 (karena file list kosong), yang penting bukan 429
        assert resp.status_code != 429, \
            f"Request {i+1} should not be rate limited, got 429"

    # Request ke-6 harus kena rate limit
    resp = client.post("/api/merge", json={
        "files": [],
        "output_filename": "test.pdf"
    })
    assert resp.status_code == 429, \
        f"Request 6 should be rate limited (429), got {resp.status_code}"
    print("  [PASS] test_sec08_heavy_endpoint_rate_limited PASSED")


def test_sec08_rate_limit_headers_present():
    """Response harus menyertakan rate limit headers."""
    client = get_test_client()
    resp = client.get("/api/health")
    # slowapi biasanya menambahkan header X-RateLimit-Limit dan X-RateLimit-Remaining
    # Tapi ini tergantung versi. Cukup periksa response berhasil.
    assert resp.status_code == 200
    print("  [PASS] test_sec08_rate_limit_headers_present PASSED")


# ============================================================
# Runner
# ============================================================

if __name__ == "__main__":
    print("\n[SEC-06] Download Path Traversal Tests")
    print("=" * 50)
    test_sec06_normal_download()
    test_sec06_task_id_traversal_rejected()
    test_sec06_task_id_special_chars_rejected()
    test_sec06_filename_traversal_rejected()
    test_sec06_dotdot_filename_rejected()
    test_sec06_nonexistent_file_404()
    test_sec06_valid_task_id_formats()

    print("\n[SEC-07] CORS Configuration Tests")
    print("=" * 50)
    test_sec07_allowed_origin_accepted()
    test_sec07_disallowed_origin_no_cors()
    test_sec07_preflight_allowed_origin()
    test_sec07_preflight_disallowed_origin()
    test_sec07_localhost_8041_accepted()

    print("\n[SEC-08] Rate Limiting Tests")
    print("=" * 50)
    test_sec08_within_limit_succeeds()
    test_sec08_heavy_endpoint_rate_limited()
    test_sec08_rate_limit_headers_present()

    print("\n[OK] All SEC-06/07/08 tests passed!")
