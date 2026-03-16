from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from system.database.entities import UserProgressController,AchievementsController
import logging

router = Router()
         
@router.message(Command("achievements"))
async def get_achievements(message: Message):
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    user_progress = await UserProgressController.create(message.from_user.id)
    report = ""
    try:
        ach_controller = AchievementsController()
        for i in await ach_controller.get_all_ach():
            if i.id in user_progress.achievements:
                report += "<i>Название:</i> " + i.name + "\n"
                report += "<i>Описание:</i> " + i.desc + "\n"
                report += "\n"
        if report != "":
            await message.answer(report, parse_mode = "HTML")
        else:
            await message.answer("Пока нет ни одного достижения, но это скоро изменится! :)")
    except:
        await message.answer("Пока нет ни одного достижения, но это скоро изменится! :)")
    finally:
        await message.answer("Готово")

@router.message(Command("profile"))
async def profile(message: Message):
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    user_progress = await UserProgressController.create(message.from_user.id)
    await message.answer("Name: " + message.from_user.first_name)
    await message.answer("Exp: " + str(user_progress.exp))
    await message.answer("Готово")