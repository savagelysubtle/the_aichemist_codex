from pathlib import Path

import aiofiles


class AsyncFileReader:
    @staticmethod
    async def read(file_path: Path) -> str:
        async with aiofiles.open(file_path, "r") as f:
            return await f.read()

    @staticmethod
    async def read_binary(file_path: Path) -> bytes:
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
