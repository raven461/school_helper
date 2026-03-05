from aiogram import Router,F
from aiogram.types import Message,InlineKeyboardButton,CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import config
from conf.logging.file_opening import LOG_FILE_PATH
from system.database.connect import del_db

router = Router()
class dev_states(StatesGroup):
    get_bot_logs = State()
    get_server_info = State()
    drop_db = State()
    send_logs_archives = State()
    read_email = State()

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

@router.message(Command("admin_mode"))
async def admin_pannel(message: Message):
    await message.answer("Команда подтверждена. для выхода нажмите /cancel", reply_markup=get_admin_keyboard())

@router.callback_query(F.data.startswith("logs"))
async def logs(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Введите ключ доступа")
    await state.set_state(dev_states.get_bot_logs)

#TODO:доделать выгрузку логов файлом
@router.message(dev_states.get_bot_logs)
async def get_bot_logs(message: Message, state: FSMContext):
    dev_key = message.text
    if dev_key == config.dev_key.get_secret_value():
        with open(LOG_FILE_PATH,"r") as log:
            await message.answer_document(LOG_FILE_PATH)
        await message.answer("Готово")
        return
    await message.answer("Неверный ключ доступа. Попробуйте ещё раз или /cancel")
    await state.set_state(dev_states.get_bot_logs)

#TODO:доделать получение состояния сервера
@router.callback_query(F.data.startswith("server_info"))
async def server_info(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Введите ключ доступа")
    await state.set_state(dev_states.get_bot_logs)

@router.message(dev_states.get_server_info)
async def get_server_info(message: Message, state: FSMContext):
    dev_key = message.text
    if dev_key == config.dev_key.get_secret_value():
        await message.answer("Готово")
        return
    await message.answer("Неверный ключ доступа. Попробуйте ещё раз или /cancel")
    await state.set_state(dev_states.get_server_info)

@router.callback_query(F.data.startswith("drop_db"))
async def delete_db(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Введите ключ доступа")
    await state.set_state(dev_states.drop_db)

@router.message(dev_states.drop_db)
async def drop_db(message: Message, state: FSMContext):
    dev_key = message.text
    if dev_key == config.dev_key.get_secret_value():
        del_db()
        await message.answer("Готово")
        return
    await message.answer("Неверный ключ доступа. Попробуйте ещё раз или /cancel")
    await state.set_state(dev_states.drop_db)

#TODO:доделать отправку логов на почту
@router.callback_query(F.data.startswith("send_logs"))
async def send_logs(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Введите ключ доступа")
    await state.set_state(dev_states.send_logs_archives)

@router.message(dev_states.send_logs_archives)
async def send_logs_archives(message: Message, state: FSMContext):
    dev_key = message.text
    if dev_key == config.dev_key.get_secret_value():
        await message.answer("Введите email-адрес, по которому должен быть прислан лог-файл")
        await state.set_state(dev_states.read_email)
        return
    await message.answer("Неверный ключ доступа. Попробуйте ещё раз или /cancel")
    await state.set_state(dev_states.send_logs_archives)

@router.message(dev_states.read_email)
async def send_log_email(message: Message, state: FSMContext):
    email = message.text
    await message.answer("Готово")