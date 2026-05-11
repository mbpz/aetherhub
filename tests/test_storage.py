import pytest
import tempfile
import os


@pytest.mark.asyncio
async def test_local_storage_upload():
    from web.backend.services.storage import LocalStorage
    with tempfile.TemporaryDirectory() as td:
        storage = LocalStorage(td)
        local_file = os.path.join(td, "test.txt")
        with open(local_file, "w") as f:
            f.write("hello")
        result = await storage.upload_file(local_file, "skills/1/test.txt")
        assert os.path.exists(result)
        assert storage.get_url("skills/1/test.txt") == result


@pytest.mark.asyncio
async def test_local_storage_download():
    from web.backend.services.storage import LocalStorage
    with tempfile.TemporaryDirectory() as td:
        storage = LocalStorage(td)
        local_file = os.path.join(td, "src.txt")
        with open(local_file, "w") as f:
            f.write("world")
        dest = os.path.join(td, "dst.txt")
        await storage.upload_file(local_file, "test.txt")
        await storage.download_file("test.txt", dest)
        with open(dest) as f:
            assert f.read() == "world"