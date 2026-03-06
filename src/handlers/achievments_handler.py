from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from system.database.enties import UserProgressController
from achievements.achievements import Achievements
import logging

router = Router()

async def update_achivments():
    achievements = Achievements()
         
@router.message(Command("achievements"))
async def get_achievements(message: Message):
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    user_progress = UserProgressController(message.from_user.id)
    try:
        await message.answer("\n".join(user_progress.get_user_achievements()))
    except:
        await message.answer("Пока нет ни одного достижения, но это скоро изменится! :)")
    finally:
        await message.answer("Готово")

@router.message(Command("profile"))
async def profile(message: Message):
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    user_progress = UserProgressController(message.from_user.id)
    await message.answer("Name: " + message.from_user.first_name)
    await message.answer("Exp: "+ str(user_progress.exp))
    await message.answer("Готово")