from aiogram import Router, F
from aiogram.types import Message,CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from system.database.entities import UserHomeworkController,UserProgressController
from keyboards.keyboards import get_lessons_keyboard
from datetime import datetime
import logging

router = Router()

class AddingStates(StatesGroup):
    choosing_lesson = State()
    enter_homework_text = State()
    enter_deadline_date = State()
    enter_deadline_time = State()

class SetDoneStates(StatesGroup):
    enter_subject = State()
    enter_text = State()

class DeletingStates(StatesGroup):
    enter_subject = State()
    enter_text = State()

def validate_lessons(lesson:str,user_id:int):
    with open("../../lessons.txt","x") as lessons_file:
        lessons = str(lessons_file.readlines()).lower().split(" ")
        if lesson.lower() not in lessons:
            if lessons_file.writable():
                lessons_file.write(" "+lesson)
            else:
                logging.error(f"Can't write lesson to lessons.txt from user with id={user_id}")
                return

async def deadline_notify(user_id):
    user_homework = await UserHomeworkController.create(user_id)
    tasks = await user_homework.get_all_pending_reminders()
    message = ""
    for record in tasks:
        message += f"Внимание, на выполнение задания по предмету <i>{record.subject}</i>\
                            осталось <i>{record.deadline_time // 60} минут</i>.\
                           \n Не упусти шанс сделать!\n\n"
    return message

@router.message(Command("deadlines"))
async def deadlines(message: Message):
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    report = await deadline_notify(message.from_user.id)
    await message.answer(report, parse_mode = "HTML")

@router.message(Command("add_homework"))
async def add_hometask(message: Message, state: FSMContext):
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    await message.answer("Укажите, по какому предмету вы хотите записать задание, или выберите с клавиатуры",
                         reply_markup=get_lessons_keyboard())
    await state.set_state(AddingStates.choosing_lesson)

@router.callback_query(F.data.startswith("lesson_"))
async def choose_lesson_by_keyboard(callback: CallbackQuery, state: FSMContext):
    lesson = callback.data.split("_")[1]
    await state.update_data(lesson = lesson)
    await callback.message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(AddingStates.enter_homework_text)

@router.message(AddingStates.choosing_lesson)
async def choose_lesson(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    lesson = message.text
    validate_lessons(lesson,message.from_user.id)
    await state.update_data(lesson = lesson)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(AddingStates.enter_homework_text)

@router.message(AddingStates.enter_homework_text)
async def enter_homework_text(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(task_text=message.text)
    await message.answer("Введите дату, к которой нужно завершить задание в формате ГГГГ.ММ.ДД.ЧЧ или /cancel.\n")
    await state.set_state(AddingStates.enter_deadline_date)

@router.message(AddingStates.enter_deadline_date)
async def enter_deadline_date(message: Message, state: FSMContext):
    try:
        elems = message.text.strip().split(".")
        if len(elems) != 4:
            await message.answer("Дата должна быть записана в формате ГГГГ.ММ.ДД.ЧЧ.")
            return
    
        year, month, day, hour = map(int, elems)
        deadline_date = datetime(year, month, day, hour)
    
        if deadline_date <= datetime.now():
            await message.answer("Дата должна быть в будущем!")
            return
        
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ГГГГ.ММ.ДД.ЧЧ (например: 2024.12.25.18)")
        return
    
    state_data = await state.get_data()
    user_homework = await UserHomeworkController.create(message.from_user.id)
    
    await user_homework.add_task(
        subject_id=str(state_data.get("lesson")),
        task_text=str(state_data.get("task_text")),
        deadline_ts = int(deadline_date.timestamp())
    )
    
    await message.answer("Задание зарегистрировано.\n")
    await state.clear()

@router.message(Command("homework"))
async def homework(message: Message):
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    user_homework = await UserHomeworkController.create(message.from_user.id)
    tasks = await user_homework.get_active_tasks()
    if not tasks:
        await message.answer("У вас нет активных заданий")
        return
    formatted_tasks = []
    for task in tasks:
        deadline = datetime.fromtimestamp(float(task.deadline_time))
        formatted_tasks.append(f"📌 {task.subject}: {task.text}\n⏰ До: {deadline.strftime('%d.%m.%Y %H:00')}")
    await message.answer("📚 <b>Ваши задания:</b>\n\n" + "\n\n".join(formatted_tasks), parse_mode="HTML")

@router.message(Command("done"))
async def done(message: Message, state: FSMContext):
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(SetDoneStates.enter_subject)

@router.message(SetDoneStates.enter_subject)
async def enter_subject(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    lesson = message.text
    validate_lessons(lesson,message.from_user.id)
    await state.update_data(subject = lesson)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(SetDoneStates.enter_text)

@router.message(SetDoneStates.enter_text)
async def enter_text(message: Message, state: FSMContext):   
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    user_homework = await UserHomeworkController.create(message.from_user.id)
    user_progress = await UserProgressController.create(message.from_user.id)
    state_data = await state.get_data()
    try:
        id = await user_homework.get_task_id(str(state_data.get("subject")), message.text)
        await user_homework.set_status_complete(id)
        await user_progress.append_right_tasks_quantity(1)
        await user_progress.append_user_exp(0.9)
        await message.answer("Готово")
    except:
        await message.answer("Задание отсутствует")
    finally:
        await state.clear()

@router.message(Command("delete"))
async def delete(message: Message, state: FSMContext):
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(DeletingStates.enter_subject)

@router.message(DeletingStates.enter_subject)
async def enter_del_subject(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(subject = message.text)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(SetDoneStates.enter_text)

@router.message(DeletingStates.enter_text)
async def enter_del_text(message: Message, state: FSMContext):   
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    user_homework = await UserHomeworkController.create(message.from_user.id)
    state_data = await state.get_data()
    try:
        id = await user_homework.get_task_id(str(state_data.get("subject")), message.text)
        await user_homework.delete_task(id)
        await message.answer("Готово")
    except:
        await message.answer("Задание отсутствует")
    finally:
        await state.clear()