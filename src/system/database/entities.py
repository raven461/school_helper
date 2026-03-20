from .connect import get_db_connection
from .models import SchoolTableRecord, UserTableRecord, HomeworkTableRecord, ProgressTableRecord,AchievementTableRecord
import json
import time
import logging
import ast

class UserController:
    def __init__(self, user_id):
        self.user_id = user_id

    @classmethod
    async def create(cls,user_id):
        obj = cls(user_id)
        await obj.update_user_information()
        return obj

    async def update_user_information(self):
        async with get_db_connection() as conn:
            async with conn.execute(
                "SELECT * FROM Users WHERE user_id = ?",
                (self.user_id,)
            ) as cursor:
                res = await cursor.fetchone()
                if res:
                    self.user_record = UserTableRecord(
                        id=int(res[0]),
                        name=str(res[1]),
                        school_name=str(res[2]),
                        grade=str(res[3]),
                        type=str(res[4])
                    )
                else:
                    logging.error("RecordFoundError: user record not found")

    def is_register(self) -> bool:
        return hasattr(self, 'user_record') and self.user_record is not None

    @property
    def grade_number(self) -> int | None:
        return int((self.user_record.grade)[0]) if self.is_register() else None

    @staticmethod
    async def register_user(user_id:int, nickname:str, school:str, grade:str, user_type:str):
        async with get_db_connection() as conn:
            await conn.execute(
                "INSERT OR REPLACE INTO Users (user_id, full_name, school, grade, type) VALUES (?,?,?,?,?)",
                (user_id, nickname, school, grade,user_type)
            )
            if user_type == "pupil":
                await conn.execute(
                    "INSERT OR IGNORE INTO UsersProgress (user_id) VALUES (?)",
                    (user_id,)
                )
            await conn.commit()
class UserHomeworkController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.homework_records: list[HomeworkTableRecord] = []

    @classmethod
    async def create(cls,user_id):
        obj = cls(user_id)
        await obj.update_user_information()
        return obj

    async def update_user_information(self):
        async with get_db_connection() as conn:
            async with conn.execute(
                "SELECT * FROM UsersHomeWork WHERE user_id = ?",
                (self.user_id,)
            ) as cursor:
                self.homework_records.clear()
                for raw in await cursor.fetchall():
                    record = HomeworkTableRecord(
                        id=int(raw[0]),
                        user_id=int(self.user_id),
                        subject=str(raw[2]),
                        text=str(raw[3]),
                        deadline_time=int(raw[4]),
                        reminder_time=int(raw[5]),
                        is_done=bool(raw[6])
                    )
                    self.homework_records.append(record)

    async def get_task_id(self, subject_id: str, task_text: str) -> int | None:
        async with get_db_connection() as conn:
            async with conn.execute(
                "SELECT id FROM UsersHomeWork WHERE user_id = ? AND subject_id = ? AND task_text = ?",
                (self.user_id, subject_id, task_text)
            ) as cursor:
                res = await cursor.fetchone()
                return res[0] if res else None

    async def add_task(self, subject_id: str, task_text: str, deadline_ts: int, reminder_delta_minutes: int = 60):
        reminder_time = deadline_ts - (reminder_delta_minutes * 60)
        async with get_db_connection() as conn:
            await conn.execute(
                "INSERT INTO UsersHomeWork (user_id, subject_id, task_text, deadline, reminder_time, status) "
                "VALUES (?, ?, ?, ?, ?, 0)",
                (self.user_id, subject_id, task_text, deadline_ts, reminder_time)
            )
            await conn.commit()
        await self.update_user_information()

    async def set_status_complete(self, task_id: int):
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE UsersHomeWork SET status = 1 WHERE id = ? AND user_id = ?",
                (task_id, self.user_id)
            )
            await conn.commit()
        await self.update_user_information()

    async def get_active_tasks(self) -> list[HomeworkTableRecord]:
        await self.update_user_information()
        active_tasks = []
        for task in self.homework_records:
            if task.is_done == False:
                active_tasks.append(task)
        return active_tasks

    async def delete_task(self, task_id: int):
        async with get_db_connection() as conn:
            await conn.execute(
                "DELETE FROM UsersHomeWork WHERE id = ? AND user_id = ?",
                (task_id, self.user_id)
            )
            await conn.commit()
        await self.update_user_information()

    async def get_all_pending_reminders(self):
        current_ts = int(time.time())
        await self.update_user_information()
        result = []
        for record in self.homework_records:
            if (not record.is_done) and (record.reminder_time > 0) and (record.reminder_time < current_ts) :
                result.append(record)
        return result
    
    async def clear_reminder(self, task_id: int):
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE UsersHomeWork SET reminder_time = 0 WHERE id = ?",
                (task_id,)
            )
            await conn.commit()

class UserProgressController:
    def __init__(self, user_id):
        self.user_id = user_id
        
    @classmethod
    async def create(cls,user_id):
        obj = cls(user_id)
        await obj.update_user_information()
        return obj

    async def update_user_information(self):
        async with get_db_connection() as conn:
            async with conn.execute(
                "SELECT * FROM UsersProgress WHERE user_id = ?",
                (self.user_id,)
            ) as cursor:
                res = await cursor.fetchone()
                if res:
                    self.progress_record = ProgressTableRecord(
                        id=int(res[0]),
                        achievments=json.loads(res[1]),
                        exp=res[2],
                        done_tasks=res[3]
                    )
                    if self.progress_record.id is None:
                        await conn.execute(
                            "INSERT OR IGNORE INTO UsersProgress (user_id) VALUES (?)",
                            (self.user_id,)
                        )
                        await conn.commit()
                        await self.update_user_information()

    async def set_achievements(self, new_achievements: list):
        ach = json.dumps(new_achievements, ensure_ascii=False)
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE UsersProgress SET achievements = ? WHERE user_id = ?",
                (ach, self.user_id)
            )
            await conn.commit()
        await self.update_user_information()

    async def set_exp(self, new_exp: float):
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE UsersProgress SET exp_count = ? WHERE user_id = ?",
                (new_exp, self.user_id)
            )
            await conn.commit()
        await self.update_user_information()

    async def set_right_tasks(self, new_count: int):
        async with get_db_connection() as conn:
            await conn.execute(
                "UPDATE UsersProgress SET count_tasks = ? WHERE user_id = ?",
                (new_count, self.user_id)
            )
            await conn.commit()
        await self.update_user_information()

    @property
    def achievements(self) -> list:
            return self.progress_record.achievments or []

    @property
    def exp(self) -> float:
        return self.progress_record.exp

    @property
    def sucesfull_tasks(self) -> int:
        return self.progress_record.done_tasks

    async def append_user_exp(self, count: float):
        await self.set_exp(self.exp + count)

    async def append_right_tasks_quantity(self, count: int):
        await self.set_right_tasks(self.sucesfull_tasks + count)

class SchoolController:
    def __init__(self):
        pass

    async def add_school(self, school_name: str,domain:str ,base_url: str, delta_url: str, exams_urls: list[str]):
        async with get_db_connection() as conn:
            await conn.execute(
                """INSERT INTO Schools (
                    name,
                    domain_url,
                    base_schedule_url,
                    delta_schedule_url,
                    exams_urls) VALUES (?, ?, ?, ?, ?)""",
                (school_name, domain, base_url, delta_url,json.dumps(exams_urls, ensure_ascii=False))
            )
            await conn.commit()

    async def delete_school(self, id: int):
        async with get_db_connection() as conn:
            await conn.execute(
                "DELETE FROM Schools WHERE id = ?",
                (id,)
            )
            await conn.commit()

    async def get_all_schools(self) -> list[SchoolTableRecord]:
        async with get_db_connection() as conn:
            async with conn.execute("SELECT * FROM Schools") as cursor:
                school_records = await cursor.fetchall()
        schools = []
        for record in school_records:
            schools.append(
                SchoolTableRecord(
                    id=int(record[0]),
                    name=str(record[1]),
                    domain_url=str(record[2]),
                    base_schedule_url=str(record[3]),
                    delta_schedule_url=str(record[4]),
                    exams_urls=json.loads(record[5])
                )
            )
        return schools

    async def get_school(self, name: str) -> SchoolTableRecord | None:
        all_schools = await self.get_all_schools()
        matching_schools = [school for school in all_schools if school.name == name]
        return matching_schools[0] if matching_schools else None

class AchievementsController:
    def __init__(self):
        pass
    
    async def get_all_ach(self) -> list[AchievementTableRecord]:
        async with get_db_connection("achievements.db") as conn:
            async with conn.execute("SELECT * FROM Achievements") as cursor:
                row_ach = await cursor.fetchall()
        ach = []
        for record in row_ach:
            ach.append(
                AchievementTableRecord(
                    id=int(record[0]),
                    name=str(record[1]),
                    desc=str(record[2]),
                    exp=float(record[3]),
                    check_function=str(record[4])
                )
            )
        return ach

    async def get_ach_by_name(self,name: str) -> AchievementTableRecord | None:
        all_ach = await self.get_all_ach()
        matching_schools = [ach for ach in all_ach if ach.name == name]
        return matching_schools[0] if matching_schools else None
    
    async def get_ach_by_id(self,id: int) -> AchievementTableRecord | None:
        all_ach = await self.get_all_ach()
        matching_schools = [ach for ach in all_ach if ach.id == id]
        return matching_schools[0] if matching_schools else None
    
    async def add_ach(self,name:str,desc:str,exp:float,check_function:str):
        async with get_db_connection("achievements.db") as conn:
            await conn.execute(
                "INSERT INTO Achievements (name,desc,exp,check_function) VALUES (?, ?, ?, ?)",
                (name, desc, exp, check_function)
            )
            await conn.commit()

    async def delete_ach(self,id:int):
        async with get_db_connection("achievements.db") as conn:
            await conn.execute(
                "DELETE FROM Achievements WHERE id = ?",
                (id,)
            )
            await conn.commit()

    async def check_all_ach(self,user_id:int) -> list[AchievementTableRecord]:
        prog = await UserProgressController.create(user_id)
        hw = await UserHomeworkController.create(user_id)
        current_ids = prog.achievements
        new_unlocked = []
        reward = 0
        all_ach = await self.get_all_ach()
        for ach in all_ach:
            if str(ach.id) not in current_ids:
                if eval(compile(ast.parse(ach.check_function, mode="eval"), "<string>", "eval"))(prog, hw):
                    new_unlocked.append(ach)
                    reward += ach.exp
        if reward > 0:
            await prog.append_user_exp(reward)
        return new_unlocked
