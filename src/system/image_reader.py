from aiogram import Bot
from aiogram.types import PhotoSize
from PIL import Image
import pytesseract
import logging

async def text_from_tg_photo(bot: Bot,photo: PhotoSize, lang: str = "rus+eng") -> str:
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    if file_path is not None:
        logging.error(f"GetPhotoError: photo with id: {photo.file_id} has None path")
        return ""
    downloaded_file = await bot.download_file(file_path)
    image = Image.open(downloaded_file)
    return pytesseract.image_to_string(image, lang=lang)