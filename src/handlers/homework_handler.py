from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from system.bd_worker import UserHomeworkController,UserProgressController 
from datetime import datetime
import logging

router = Router()

class homework_states(StatesGroup):
    choosing_lesson = State()
    enter_homework_text = State()
    enter_deadline_date = State()
    enter_deadline_time = State()

def init_homework(user_id):
    global user_homework,user_progress 
    user_homework = UserHomeworkController(user_id)
    user_progress = UserProgressController(user_id)
    pass

def delete_right_tasks(tasks_id: list[int],user_id):
    init_homework(user_id)
    for i in tasks_id:
        user_homework.set_status_complete(i)
        user_homework.delete_task(i)
    user_progress.right_tasks_plus(len(tasks_id))
    user_progress.user_exp_count_plus(0.1*len(tasks_id))

async def deadline_notify(bot,user_id,task_id):
    id,user,lesson,task,dead_time = user_homework.conn.execute("""SELECT * FROM UserHomeworkController WHERE id = ?""",(task_id))
    await bot.send_message(user_id,f"Внимание, на выполнение задания по предмету '{lesson}' осталось {dead_time // 3600} ч.\
                           \n Не упусти шанс сделать!")

@router.message(Command("add_homework"))
async def add_hometask(message: types.Message, state: FSMContext):
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    user_homework = UserHomeworkController(message.from_user.id)
    await message.answer("Укажите, по какому предмету вы хотите записать задание:")
    await state.set_state(homework_states.choosing_lesson)

@router.message(homework_states.choosing_lesson)
async def choose_lesson(message: types.Message, state: FSMContext):
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    lesson = message.text
    await state.update_data(lesson = lesson)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(homework_states.enter_homework_text)

@router.message(homework_states.enter_homework_text)
async def enter_homework_text(message: types.Message, state: FSMContext):
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    task_text = message.text
    await state.update_data(task_text = task_text)
    await message.answer("Введите дату, к которой нужно завершить задание в формате ГГГГ.ММ.ДД.ЧЧ или /cancel.\n")
    await state.set_state(homework_states.enter_deadline_date)

@router.message(homework_states.enter_deadline_date)
async def enter_deadline_date(message: types.Message, state: FSMContext):
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    deadline_date_text = message.text
    elems = deadline_date_text.strip().split('.')
    if len(elems) != 4:
        await message.answer("Дата должна быть записана в формате ГГГГ.ММ.ДД.ЧЧ.")
        return
    deadline_date = datetime(int(elems[0]), int(elems[1]), int(elems[2]), int(elems[3]))
    user_homework = UserHomeworkController(message.from_user.id)
    state_data = await state.get_data()
    user_homework.add_task(
        str(state_data.get("lesson")),
        str(state_data.get("task_text")),
        int((deadline_date - datetime.now()).total_seconds())
    )
    await message.answer("Задание зарегистрировано.\n")
    await state.clear()

async def get_lessons_keyboard():
    pass

@router.message(Command("homework"))
async def homework(message: types.Message):
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    user_homework = UserHomeworkController(message.from_user.id)
    a = user_homework.get_active_tasks()
    await message.answer("\n".join(a))

@router.message(Command("done"))
async def done(message: types.Message, command: CommandObject):
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    user_homework = UserHomeworkController(message.from_user.id)
    if not command.args:
        return await message.answer("Ошибка! Введите название предмета и текст задания")
    args = command.args.split(" ")
    if len(args) < 2:
        return await message.answer("Ошибка! Введите название предмета и текст задания")
    subject,*task_text = args
    try:
        id = user_homework.get_task_id(subject," ".join(task_text))
        user_homework.set_status_complete(id)
    except:
        await message.answer("Задание отсутствует")
    finally:
        await message.answer("Готово")