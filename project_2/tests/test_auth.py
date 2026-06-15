import pytest

from storage import db


@pytest.fixture
async def tmp_db(tmp_path):
    db.configure(str(tmp_path / "auth.db"))
    await db.init_db()


async def test_unknown_user_not_authorized(tmp_db):
    assert await db.is_authorized(999) is False


async def test_authorize_then_check(tmp_db):
    await db.authorize(42)
    assert await db.is_authorized(42) is True


async def test_authorize_is_idempotent(tmp_db):
    await db.authorize(42)
    await db.authorize(42)
    s = await db.stats()
    assert s["total"] == 1


async def test_revoke(tmp_db):
    await db.authorize(42)
    assert await db.revoke(42) is True
    assert await db.is_authorized(42) is False
    # revoking again is a no-op
    assert await db.revoke(42) is False
