from aiogram import Router,F
from aiogram.types import Message,CallbackQuery
from aiogram.filters import Command
from datetime import datetime
from .keyboards.keyboards import get_dynamic_days_keyboard
from system.database.enties import UserController
from system.shedule_parser import ScheduleParser
from system.exam_parser import ExamsParser
import logging
import asyncio
import time
import re

router = Router()

async def update_data_task():
    parser = await ScheduleParser.create("ГБОУ Лицей №419 Санкт-Петербурга имени К.М. Калманова")
    """Фоновая задача для обновления данных по расписанию каждую минуту"""
    while True:
        try:
            await parser.update_schedule()
            await parser.update_delta_schedule()
            logging.info("Расписание успешно обновлено")
        except Exception as e:
            logging.error(f"Ошибка обновления: {e}")
        await asyncio.sleep(60)

def format_schedule_view(day_name, user_class:str, schedule_dict, delta_list):
    lessons = schedule_dict.get(day_name, [])
    day_deltas = [d for d in delta_list if d['day'] == day_name]

    header = f"🗓 <b>{day_name} | КЛАСС {user_class.upper()}</b>\n"
    line = "⎯" * 15 + "\n"
    
    body = ""
    if not lessons and not day_deltas:
        body = "<i>Уроков не найдено или выходной</i>\n"
    else:
        none_lessons = []
        for i, subject in enumerate(lessons, 1):
            change = next((d for d in day_deltas if str(d['lesson']) == str(i)), None)
            if change:
                if ("Нет" in change["comment"]) and ("урок" in change["comment"]):
                    none_lessons.append([int(x) for x in re.findall(r"\d+", change["comment"])])
                body += f"❌ <s>{i}. {subject}</s>\n"
                if change["room"] is None or change["comment"] is None or i in none_lessons:
                    body += "✅ <b>Нет урока</b>\n"
                body += f"✅ <b>{i}. {change.get('subject', 'Замена')}</b> | каб. {change['room']}\n"
            else:
                body += f"○ {i}. {subject}\n"

    return header + line + body

@router.callback_query(F.data.startswith("day_"))
async def handle_day(callback: CallbackQuery):
    parser = await ScheduleParser.create("ГБОУ Лицей №419 Санкт-Петербурга имени К.М. Калманова")
    timestamp = time.time()
    if callback.data is None or callback.message is None:
        logging.error("Empty callback data")
        return
    selected_day = callback.data.split("_")[1]
    user = UserController(callback.from_user.id)
    grade = str(user.user_record.grade)
    
    if not grade:
        await callback.answer("Сначала пройдите регистрацию командой /reg", show_alert=True)
        return

    full_schedule = await parser.get_schedule(grade)
    
    if isinstance(full_schedule, str):
        await callback.answer(f"⚠️ {full_schedule}", show_alert=True)
        return
        
    all_deltas = parser.get_delta(grade)
    text = format_schedule_view(selected_day, grade, full_schedule, all_deltas)
    logging.info("Schedule request time:"+str(time.time() - timestamp))
    await callback.answer()
    try:
        await callback.message.edit_text(
            text, 
            parse_mode="HTML", 
            reply_markup=get_dynamic_days_keyboard() 
        )
    except Exception:
        pass
    
@router.message(Command("schedule"))
async def schedule(message: Message):
    await message.answer("Выберите день:", reply_markup=get_dynamic_days_keyboard())

@router.message(Command("today"))
async def today(message: Message):
    if message.from_user == None:
        logging.error("BotUserError: user params is empty")
        return
    user = await UserController.create(message.from_user.id)
    parser = await ScheduleParser.create("ГБОУ Лицей №419 Санкт-Петербурга имени К.М. Калманова")
    today = datetime.now().weekday() 
    days_db = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
    grade = user.user_record.grade
    await message.answer(
        format_schedule_view(
            days_db[today],
            str(grade),
            await parser.get_schedule(str(grade)),
            parser.get_delta(str(grade))),
        parse_mode = "HTML"  
    )
@router.message(Command("exams"))
async def exams(message: Message):
    if message.from_user == None:
        logging.error("BotUserError: user params is empty")
        return
    user = await UserController.create(message.from_user.id)
    parser = await ExamsParser.create("ГБОУ Лицей №419 Санкт-Петербурга имени К.М. Калманова")
    await message.answer_document(parser.returnFilename(user.grade_number))