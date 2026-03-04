from connect import conn,init_db
from bd_dataclasses import SchoolTableRecord
import json
import time
init_db()

class UserController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.update_user_information()

    def update_user_information(self):
        cur = conn.cursor()
        res = cur.execute("SELECT * FROM Users WHERE user_id = ?", (self.user_id,))
        self.id,self.name,self.school,self.class_ = res.fetchone()        
    
    def is_user_register(self) -> bool:
        return self.school is not None

    def get_user_name(self): return self.name if self.is_user_register() else None
    def get_user_school(self): return self.school if self.is_user_register() else None
    def get_user_class(self) -> str|None : return self.class_ if self.is_user_register() else None
    def get_user_grade(self) -> int|None : return int((self.class_)[0]) if self.is_user_register() else None

    @staticmethod
    def register_user(user_id, nickname, school, class_):
        with conn:
            conn.execute("INSERT OR REPLACE INTO Users (user_id, full_name, school, grade) VALUES (?,?,?,?)",
                         (user_id, nickname, school, class_))
            conn.execute("INSERT OR IGNORE INTO UsersProgress (user_id) VALUES (?)", (user_id,))

class UserProgressController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.update_user_information()

    def update_user_information(self):
        cur = conn.cursor()
        res = cur.execute("SELECT * FROM UsersProgress WHERE user_id = ?", (self.user_id,))
        self.all_user_information = res.fetchone()
        if not self.all_user_information:
            with conn:
                conn.execute("INSERT OR IGNORE INTO UsersProgress (user_id) VALUES (?)", (self.user_id,))
            self.update_user_information()

    def set_achievements(self, new_achievements: list):
        ach = json.dumps(new_achievements, ensure_ascii=False)
        with conn:
            conn.execute("UPDATE UsersProgress SET achievements = ? WHERE user_id = ?", (ach, self.user_id))
        self.update_user_information()

    def set_exp(self, new_exp: float):
        with conn:
            conn.execute("UPDATE UsersProgress SET exp_count = ? WHERE user_id = ?", (new_exp, self.user_id))
        self.update_user_information()

    def set_right_tasks(self, new_count: int):
        with conn:
            conn.execute("UPDATE UsersProgress SET count_tasks = ? WHERE user_id = ?", (new_count, self.user_id))
        self.update_user_information()

    def get_user_achievements(self) -> list:
        try: return json.loads(self.all_user_information[1])
        except: return []

    def get_user_exp_count(self) -> float: return float(self.all_user_information[2])
    def get_user_sucesfull_tasks(self) -> int: return int(self.all_user_information[3])

    def append_user_exp(self, count: float):
        self.set_exp(self.get_user_exp_count() + count)

    def append_right_tasks_quantity(self, count: int):
        self.set_right_tasks(self.get_user_sucesfull_tasks() + count)

class UserHomeworkController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.conn = conn
        self.update_user_information()

    def update_user_information(self):
        cur = self.conn.cursor()
        res = cur.execute(
            "SELECT * FROM UsersHomeWork WHERE user_id = ?", 
            (self.user_id,)
        )
        self.all_homework = res.fetchall()
    def get_task_id(self,subject_id: str, task_text: str):
        cur = self.conn.cursor()
        res = cur.execute(
            "SELECT * FROM UsersHomeWork WHERE user_id = ? AND subject_id = ? AND task_text = ?", 
            (self.user_id,subject_id,task_text)
        )
        return res.fetchall()[0]
    def add_task(self, subject_id: str, task_text: str, deadline_ts: int, reminder_delta_minutes: int = 60):
        reminder_time = deadline_ts - (reminder_delta_minutes * 60)
        with self.conn:
            self.conn.execute("""
                INSERT INTO UsersHomeWork (user_id, subject_id, task_text, deadline, reminder_time, status)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (self.user_id, subject_id, task_text, deadline_ts, reminder_time))
        self.update_user_information()

    def set_status_complete(self, task_id: int):
        with self.conn:
            self.conn.execute(
                "UPDATE UsersHomeWork SET status = 1 WHERE id = ? AND user_id = ?", 
                (task_id, self.user_id)
            )
        self.update_user_information()

    def get_active_tasks(self):
        cur = self.conn.cursor()
        res = cur.execute(
            "SELECT * FROM UsersHomeWork WHERE user_id = ? AND status = 0 ORDER BY deadline ASC", 
            (self.user_id,)
        )
        return res.fetchall()

    def delete_task(self, task_id: int):
        with self.conn:
            self.conn.execute(
                "DELETE FROM UsersHomeWork WHERE id = ? AND user_id = ?", 
                (task_id, self.user_id)
            )
        self.update_user_information()
        
    @staticmethod
    def get_all_pending_reminders(connection):
        current_ts = int(time.time())
        cur = connection.cursor()
        res = cur.execute("""
            SELECT user_id, subject_id, task_text, id 
            FROM UsersHomeWork 
            WHERE status = 0 AND reminder_time <= ? AND reminder_time > 0
        """, (current_ts,))
        return res.fetchall()

    def clear_reminder(self, task_id: int):
        with self.conn:
            self.conn.execute(
                "UPDATE UsersHomeWork SET reminder_time = 0 WHERE id = ?", 
                (task_id,)
            )
#TODO:реализовать методы удаления школ
class SchoolController:
    def __init__(self):
        self.conn = conn
    def add_school(self, school_name: str,base_url:str,delta_url:str):
        with self.conn:
            self.conn.execute("""
                INSERT INTO Schools (school_name, base_url, delta_url) VALUES (?, ?, ?)
            """, (school_name, base_url, delta_url,))

    def get_all_schools(self) -> list[SchoolTableRecord]:
        with self.conn:
            raw_schools = self.conn.execute("""
                SELECT * FROM Schools
            """).fetchall()
        schools = []
        for record in raw_schools:
            schools.append(
                SchoolTableRecord(id = record[0],
                                  name = record[1],
                                  base_schedule_url = record[2],
                                  delta_schedule_url = record[3]))
        return schools
    
    def get_school(self,name:str) -> SchoolTableRecord:
        #Возвращается первый элемент списка, поскольку предполагается, что FDIUT (First Data Is Undoubted True)
        school = list(filter(lambda elem: elem.name == name, self.get_all_schools()))[0]
        return school