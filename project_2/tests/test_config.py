"""Settings parsing tests (required fields come from conftest env)."""
from config import Settings


def test_admin_ids_comma_separated():
    assert Settings(admin_ids="1,2,3").admin_ids == [1, 2, 3]


def test_admin_ids_space_separated():
    assert Settings(admin_ids="4 5").admin_ids == [4, 5]


def test_admin_ids_json_list():
    assert Settings(admin_ids="[6, 7]").admin_ids == [6, 7]


def test_admin_ids_empty():
    assert Settings(admin_ids="").admin_ids == []


def test_max_image_bytes_derived():
    assert Settings(max_image_mb=10).max_image_bytes == 10 * 1024 * 1024
