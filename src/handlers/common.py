from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from system.database.enties import UserController
import logging

router = Router()
         
class registration(StatesGroup):
    choosing_class = State()
    choosing_school = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user == None:
        logging.error("UserNameError: user name is empty")
        return
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        "Я — твой персональный дневник-ассистент.\n\n"
        "📅 Расписание\n"
        "📝 Домашние задания\n"
        "⏰ Напоминания\n"
        "И многое другое!\n\n"
        "Для полной настройки бота введи команду /reg\n"
        "Введи /help, чтобы узнать все команды."
    )
@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "📚 <b>Справка по командам</b>\n\n"
        "📅 <b>Расписание</b>\n"
        "/schedule — посмотреть расписание на неделю\n"
        "/today – получить расписание с изменениям на сегодня\n"
        "/exams – получить файл с расписанием контрольных работ и экзаменов\n"
        "📝 <b>Домашние задания</b>\n"
        "/add_homework — добавить новое задание\n"
        "/homework — список всех заданий\n"
        "/done — отметить задание выполненным\n\n"
        "🏆 <b>Мотивация</b>\n"
        "/achievements — мои достижения\n"
        "/profile — мой профиль\n\n"
        "❓ <b>Другое</b>\n"
        "/help — эта справка\n" \
        "/ask – спросить нейросеть для помощи в учёбе, если есть сложности с пониманием.\n" \
        "Нейросеть подскажет и натолкнёт на решение наводящими вопросами."
        ,parse_mode="HTML"
    )

@router.message(Command("reg"))
async def start_reg(message: types.Message, state: FSMContext):
    if message.from_user == None:
        logging.error("UserNameError: user name is empty")
        return
    user_info = UserController(message.from_user.id)
    if user_info.is_register():
        await message.answer(f"Вы уже в базе. Класс: {user_info.user_record.grade}\n\
                             Для смены введите класс заново или /cancel")
    await message.answer("Укажите класс (например: 9а или 11б) или /cancel :")
    await state.set_state(registration.choosing_class)

@router.message(registration.choosing_class)
async def process_class(message: types.Message, state: FSMContext):
    if message.text == None:
        logging.warning("MessageTextWaring: message is empty")
        return
    user_class = message.text.lower().strip().replace(" ", "")
    if not any(char.isdigit() for char in user_class):
        await message.answer("Используйте формат "цифра+буква" (8в).")
        return
    await state.update_data(user_class = user_class)
    await message.answer("Введите название школы или /cancel.\n"\
                        "Поддерживаемые сейчас школы вы можете узнать командой /read_schools")
    await state.set_state(registration.choosing_school)

@router.message(registration.choosing_school)
async def process_school(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    if message.from_user == None:
        logging.error("UserNameError: user name is empty")
        return
    UserController.register_user(
        user_id=message.from_user.id,
        nickname=message.from_user.full_name,
        school=message.text,
        grade= state_data.get("user_class")
    )
    await message.answer(f"Готово")
    await state.clear()    

@router.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.")