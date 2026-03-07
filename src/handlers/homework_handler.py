from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from system.database.enties import UserHomeworkController,UserProgressController 
from datetime import datetime
import logging

router = Router()

class homework_states(StatesGroup):
    #Adding homework
    choosing_lesson = State()
    enter_homework_text = State()
    enter_deadline_date = State()
    enter_deadline_time = State()
    #Set homework done
    enter_subject = State()
    enter_text = State()

async def deadline_notify(user_id,task_id):
    user_homework = UserHomeworkController(user_id)
    task = list(filter(lambda elem: elem.id == task_id, user_homework.homework_records))[0]
    return f"Внимание, на выполнение задания по предмету "{task.subject}"\
                            осталось примерно {task.deadline_time // 60} минут.\
                           \n Не упусти шанс сделать!"

@router.message(Command("add_homework"))
async def add_hometask(message: types.Message, state: FSMContext):
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    await message.answer("Укажите, по какому предмету вы хотите записать задание:")
    await state.set_state(homework_states.choosing_lesson)

@router.message(homework_states.choosing_lesson)
async def choose_lesson(message: types.Message, state: FSMContext):
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(lesson = message.text)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(homework_states.enter_homework_text)

@router.message(homework_states.enter_homework_text)
async def enter_homework_text(message: types.Message, state: FSMContext):
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(task_text = message.text)
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
    elems = message.text.strip().split(".")
    if len(elems) != 4:
        await message.answer("Дата должна быть записана в формате ГГГГ.ММ.ДД.ЧЧ.")
        return
    deadline_date = datetime(int(elems[0]), int(elems[1]), int(elems[2]), int(elems[3]))
    user_homework = UserHomeworkController(message.from_user.id)
    state_data = await state.get_data()
    user_homework.add_task(
        str(state_data.get("lesson")),
        str(state_data.get("task_text")),
        int(deadline_date.timestamp())
    )
    await message.answer("Задание зарегистрировано.\n")
    await state.clear()

#TODO:добавить клавиатуру с выбором уроков в choose_lesson()
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
async def done(message: types.Message, state: FSMContext):
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(homework_states.enter_text)

@router.message(homework_states.enter_subject)
async def enter_subject(message: types.Message, state: FSMContext):
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(subject = message.text)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(homework_states.enter_text)

@router.message(homework_states.enter_text)
async def enter_text(message: types.Message, state: FSMContext):   
    if message.from_user == None:
        logging.error("UserError: user params is empty")
        return
    if message.text == None:
        await message.answer("Повторите ввод")
        return
    user_homework = UserHomeworkController(message.from_user.id)
    user_progress = UserProgressController(message.from_user.id)
    state_data = await state.get_data()
    try:
        id = user_homework.get_task_id(str(state_data.get("subject")),message.text)
        user_homework.set_status_complete(id)
        user_progress.append_right_tasks_quantity(1)
        user_progress.append_user_exp(0.9)
    except:
        await message.answer("Задание отсутствует")
    finally:
        await message.answer("Готово")
    await state.clear()