from aiogram import Bot as AiogramBot
from .models import *
from os import path
from . import DIR


class FileManager:

    def __init__(self, source: str):
        self.source = source

    async def download_file(self, bot: AiogramBot, ubot_id: int, file_id: str):
        file = await bot.get_file(file_id)
        filename = f"{ubot_id}_{path.basename(file.file_path)}"
        await bot.download_file(file.file_path, path.join(DIR, self.source, "media", filename))
        return filename

    def get_file(self, filename):
        if filename is None:
            return None
        file = open(path.join(DIR, self.source, "media", filename), "rb")
        return file
