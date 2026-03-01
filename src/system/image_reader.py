from aiogram.types import PhotoSize
from PIL import Image
import pytesseract

#TODO:доделать получение фотографий
async def text_from_tg_photo(photo: PhotoSize, lang: str = 'rus+eng') -> str:
    image = Image.open(photo)
    return pytesseract.image_to_string(image, lang=lang)