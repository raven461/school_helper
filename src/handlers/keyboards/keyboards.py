from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime

def get_user_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
            text="Ученик", 
            callback_data="type_pupil"
        ))
    builder.add(InlineKeyboardButton(
            text="Учитель", 
            callback_data="type_teacher"
        ))
    builder.adjust(1,1) 
    return builder.as_markup()

def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
            text="Получить файл логов", 
            callback_data="logs"
        ))
    builder.add(InlineKeyboardButton(
            text="Получить состояние сервера", 
            callback_data="server_info"
        ))
    builder.add(InlineKeyboardButton(
            text="Отправить файл логов на почту", 
            callback_data="send_logs"
        ))
    builder.add(InlineKeyboardButton(
            text="Очистить базу данных", 
            callback_data="drop_db"
        ))
    
    builder.adjust(2, 1, 1) 
    return builder.as_markup()


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