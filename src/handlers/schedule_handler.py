from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from system.bd_worker import User
from system.shedule_parser import Parser419School
from system.exam_parser import Parser419Exams
import logging
import asyncio
import time
import re

router = Router()
parser = Parser419School()

async def update_data_task():
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
    #TODO:обработка комментариев "нет ... урока"
    lessons = schedule_dict.get(day_name, [])
    day_deltas = [d for d in delta_list if d['day'] == day_name]

    header = f"🗓 <b>{day_name} | КЛАСС {user_class.upper()}</b>\n"
    line = "⎯" * 15 + "\n"
    
    body = ""
    if not lessons and not day_deltas:
        body = "<i>Уроков не найдено или выходной</i>\n"
    else:
        for i, subject in enumerate(lessons, 1):
            change = next((d for d in day_deltas if str(d['lesson']) == str(i)), None)
            if change:
                if ("Нет" in change["comment"]) and ("урока" in change["comment"]):
                    classes = re.findall(r"\d+",change["comment"])
                    if i in classes:
                        body += "✅ <b>{i}. Нет урока<b>\n"
                body += f"❌ <s>{i}. {subject}</s>\n"
                if change["room"] == None or change["comment"] == None:
                    body += "✅ <b>Нет урока<b>\n"
                body += f"✅ <b>{i}. {change.get('subject', 'Замена')}</b> | каб. {change['room']}\n"
            else:
                body += f"○ {i}. {subject}\n"

    return header + line + body

def get_dynamic_days_keyboard():
    builder = InlineKeyboardBuilder()
    today_idx = datetime.now().weekday() 
    
    days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    days_db = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
    if today_idx < 6:
        builder.add(InlineKeyboardButton(
            text=f"Сегодня ({days_names[today_idx]})", 
            callback_data=f"day_{days_db[today_idx]}"
        ))
    tomorrow_idx = (today_idx + 1) % 7
    if tomorrow_idx < 6:
        builder.add(InlineKeyboardButton(
            text=f"Завтра ({days_names[tomorrow_idx]})", 
            callback_data=f"day_{days_db[tomorrow_idx]}"
        ))
    for i in range(6):
        if i != today_idx and i != tomorrow_idx:
            builder.add(InlineKeyboardButton(
                text=days_names[i], 
                callback_data=f"day_{days_db[i]}"
            ))
            
    builder.adjust(1, 1, 2) 
    return builder.as_markup()

@router.callback_query(F.data.startswith("day_"))
async def handle_day(callback: types.CallbackQuery):
    _ = time.time()
    if callback.data == None or callback.message == None:
        logging.error("Empty callback data")
        return
    selected_day = callback.data.split("_")[1]
    user = User(callback.from_user.id)
    grade = str(user.get_user_class())
    
    if not grade:
        await callback.answer("Сначала пройдите регистрацию командой /reg", show_alert=True)
        return

    full_schedule = await parser.get_schedule(grade)
    
    if isinstance(full_schedule, str):
        await callback.answer(f"⚠️ {full_schedule}", show_alert=True)
        return
        
    all_deltas = parser.get_delta(grade)
    text = format_schedule_view(selected_day, grade, full_schedule, all_deltas)
    logging.info("Schedule request time:"+str(time.time()-_))
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
async def schedule(message: types.Message):
    await message.answer("Выберите день:", reply_markup=get_dynamic_days_keyboard())

@router.message(Command("today"))
async def today(message :types.Message):
    if message.from_user == None:
        logging.error("BotUserError: user params is empty")
        return
    user = User(message.from_user.id)
    today = datetime.now().weekday() 
    days_db = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
    class_ = user.get_user_class()
    await message.answer(
        format_schedule_view(
            days_db[today],
            class_,
            await parser.get_schedule(str(class_)),
            parser.get_delta(str(class_))),
        parse_mode = "HTML"  
    )
@router.message(Command("exams"))
async def exams(message:types.Message):
    if message.from_user == None:
        logging.error("BotUserError: user params is empty")
        return
    user = User(message.from_user.id)
    parser = Parser419Exams()
    await message.answer_document(parser.returnFilename(user.get_user_grade()))