"""
Tests for SEC-04 (open-folder hardening) and SEC-05 (ReDoS protection).
"""
import re
import sys
import time
from pathlib import Path

# Tambahkan project root ke sys.path agar bisa import core modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.path_security import AllowedDirRegistry
from core.renamer import safe_compile_regex, safe_regex_sub, calculate_new_names


# ============================================================
# SEC-04: AllowedDirRegistry validation tests
# ============================================================

def test_sec04_allowed_path_accepted():
    """Path dalam registry harus diizinkan."""
    reg = AllowedDirRegistry()
    test_dir = Path(__file__).resolve().parent
    reg.register(test_dir)
    assert reg.is_allowed(test_dir), "Registered dir should be allowed"
    print("  ✅ test_sec04_allowed_path_accepted PASSED")


def test_sec04_subdirectory_allowed():
    """Subdirektori dari path terdaftar juga diizinkan."""
    reg = AllowedDirRegistry()
    test_dir = Path(__file__).resolve().parent.parent
    reg.register(test_dir)
    subdir = test_dir / "core"
    assert reg.is_allowed(subdir), "Subdirectory should be allowed"
    print("  ✅ test_sec04_subdirectory_allowed PASSED")


def test_sec04_arbitrary_path_rejected():
    """Path arbitrary yang belum di-register harus ditolak."""
    reg = AllowedDirRegistry()
    reg.register(Path(__file__).resolve().parent)
    # C:\Windows\System32 seharusnya ditolak
    assert not reg.is_allowed(r"C:\Windows\System32"), \
        "Arbitrary path should be rejected"
    print("  ✅ test_sec04_arbitrary_path_rejected PASSED")


def test_sec04_parent_traversal_rejected():
    """Path traversal ke parent dari registered dir harus ditolak."""
    reg = AllowedDirRegistry()
    test_dir = Path(__file__).resolve().parent
    reg.register(test_dir)
    parent = test_dir.parent
    # Parent seharusnya tidak allowed (kecuali kalau parent juga diregister)
    if parent not in reg.registered_dirs:
        assert not reg.is_allowed(parent), \
            "Parent traversal should be rejected"
    print("  ✅ test_sec04_parent_traversal_rejected PASSED")


# ============================================================
# SEC-05: ReDoS protection tests
# ============================================================

def test_sec05_valid_regex_works():
    """Regex valid dan sederhana harus berfungsi normal."""
    compiled = safe_compile_regex(r"\d+")
    result = safe_regex_sub(compiled, "NUM", "file123test")
    assert result == "fileNUMtest", f"Expected 'fileNUMtest', got '{result}'"
    print("  ✅ test_sec05_valid_regex_works PASSED")


def test_sec05_invalid_regex_raises():
    """Regex dengan syntax error harus raise ValueError."""
    try:
        safe_compile_regex(r"[invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "tidak valid" in str(e)
    print("  ✅ test_sec05_invalid_regex_raises PASSED")


def test_sec05_too_long_pattern_rejected():
    """Pattern > 200 karakter harus ditolak."""
    long_pattern = "a" * 201
    try:
        safe_compile_regex(long_pattern)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "terlalu panjang" in str(e)
    print("  ✅ test_sec05_too_long_pattern_rejected PASSED")


def test_sec05_redos_pattern_timeout():
    """ReDoS pattern harus timeout, bukan hang."""
    # Pattern klasik ReDoS: (a+)+$ pada string "aaa...!" yang panjang
    compiled = safe_compile_regex(r"(a+)+$")
    evil_string = "a" * 30 + "!"  # Cukup untuk trigger exponential backtracking

    start = time.time()
    result = safe_regex_sub(compiled, "X", evil_string, timeout=2.0)
    elapsed = time.time() - start

    # Harus selesai dalam ~2 detik (timeout), bukan hang
    assert elapsed < 5.0, f"Should have timed out, took {elapsed:.1f}s"
    # Harus mengembalikan string asli saat timeout
    assert result == evil_string, "Should return original string on timeout"
    print(f"  ✅ test_sec05_redos_pattern_timeout PASSED (elapsed: {elapsed:.1f}s)")


def test_sec05_calculate_new_names_with_regex():
    """calculate_new_names dengan regex valid harus berfungsi."""
    files = ["scan001.pdf", "scan002.pdf", "scan003.pdf"]
    results = calculate_new_names(
        files,
        rule_type="replace",
        find_text=r"scan(\d+)",
        replace_text=r"document_\1",
        is_regex=True
    )
    assert results[0]["new_name"] == "document_001.pdf", \
        f"Expected 'document_001.pdf', got '{results[0]['new_name']}'"
    assert results[0]["changed"] is True
    print("  ✅ test_sec05_calculate_new_names_with_regex PASSED")


def test_sec05_calculate_new_names_invalid_regex():
    """calculate_new_names dengan regex invalid harus return nama asli."""
    files = ["test.pdf"]
    results = calculate_new_names(
        files,
        rule_type="replace",
        find_text=r"[invalid",
        replace_text="x",
        is_regex=True
    )
    assert results[0]["new_name"] == "test.pdf", \
        "Invalid regex should return original filename"
    assert results[0]["changed"] is False
    print("  ✅ test_sec05_calculate_new_names_invalid_regex PASSED")


if __name__ == "__main__":
    print("\n🔒 SEC-04: Open-Folder Path Validation Tests")
    print("=" * 50)
    test_sec04_allowed_path_accepted()
    test_sec04_subdirectory_allowed()
    test_sec04_arbitrary_path_rejected()
    test_sec04_parent_traversal_rejected()

    print("\n🔒 SEC-05: ReDoS Protection Tests")
    print("=" * 50)
    test_sec05_valid_regex_works()
    test_sec05_invalid_regex_raises()
    test_sec05_too_long_pattern_rejected()
    test_sec05_redos_pattern_timeout()
    test_sec05_calculate_new_names_with_regex()
    test_sec05_calculate_new_names_invalid_regex()

    print("\n✅ All tests passed!")
