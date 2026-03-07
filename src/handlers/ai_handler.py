from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from aiogram.enums.parse_mode import ParseMode
from system.image_reader import text_from_tg_photo
from system.ai_message import AI
import logging

router = Router()
ai = AI()

class Text(StatesGroup):
    read_task = State()
@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
@router.message(Command("ask"))
async def start_solve(message: types.Message, state: FSMContext):
    await message.answer("Введите задачу или /cancel")
    await state.set_state(Text.read_task)

#TODO:сделать обработку изображений в запросах   
@router.message(Text.read_task)
async def process_ask_ai(message: types.Message, state: FSMContext):
    if message.bot == None:
        logging.error("BotError: the bot is not unknown.")
        return
    async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
        try:
            answer = await ai.get_request_to_ai(await text_from_tg_photo(message.bot,message.photo[-1]) +
                                                str(message.text))
        except:
            answer = str(await ai.get_request_to_ai(str(message.text)))
        finally:
            await message.answer(answer,parse_mode=ParseMode.MARKDOWN)
    await state.clear()