from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from system.database.enties import UserHomeworkController,UserProgressController 
from datetime import datetime
import logging

router = Router()

class HomeworkStates(StatesGroup):
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
    return f"Внимание, на выполнение задания по предмету '{task.subject}'\
                            осталось примерно {task.deadline_time // 60} минут.\
                           \n Не упусти шанс сделать!"

@router.message(Command("add_homework"))
async def add_hometask(message: types.Message, state: FSMContext):
    if message.from_user is None:
        logging.error("UserError: user params is empty")
        return
    await message.answer("Укажите, по какому предмету вы хотите записать задание:")
    await state.set_state(HomeworkStates.choosing_lesson)

@router.message(HomeworkStates.choosing_lesson)
async def choose_lesson(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(lesson = message.text)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(HomeworkStates.enter_homework_text)

@router.message(HomeworkStates.enter_homework_text)
async def enter_homework_text(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(task_text=message.text)
    await message.answer("Введите дату, к которой нужно завершить задание в формате ГГГГ.ММ.ДД.ЧЧ или /cancel.\n")
    await state.set_state(HomeworkStates.enter_deadline_date)

@router.message(HomeworkStates.enter_deadline_date)
async def enter_deadline_date(message: types.Message, state: FSMContext):
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
        subject_id=state_data.get("lesson"),
        task_text=state_data.get("task_text"),
        deadline_ts = int(deadline_date.timestamp())
    )
    
    await message.answer("Задание зарегистрировано.\n")
    await state.clear()

#TODO:добавить клавиатуру с выбором уроков в choose_lesson()
async def get_lessons_keyboard():
    pass

@router.message(Command("homework"))
async def homework(message: types.Message):
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
async def done(message: types.Message, state: FSMContext):
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(HomeworkStates.enter_text)

@router.message(HomeworkStates.enter_subject)
async def enter_subject(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("Повторите ввод")
        return
    await state.update_data(subject = message.text)
    await message.answer("Введите текст задания или /cancel.\n")
    await state.set_state(HomeworkStates.enter_text)

@router.message(HomeworkStates.enter_text)
async def enter_text(message: types.Message, state: FSMContext):   
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
    except:
        await message.answer("Задание отсутствует")
    finally:
        await message.answer("Готово")
        await state.clear()