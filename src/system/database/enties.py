from connect import conn,init_db
from bd_dataclasses import SchoolTableRecord,UserTableRecord,HomeworkTableRecord,ProgressTableRecord
import json
import time
init_db()

class UserController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = None
        self.update_user_information()

    def update_user_information(self):
        cur = conn.cursor()
        res = cur.execute("SELECT * FROM Users WHERE user_id = ?", (self.user_id,)).fetchone()
        self.user_record = UserTableRecord(id = res[0],
                                           name = res[1],
                                           school_name = res[2],
                                           grade = res[3])        
    
    def is_register(self) -> bool:
        return self.user_record is not None
    
    @property
    def grade_number(self) -> int|None : return int((self.user_record.grade)[0]) if self.is_register() else None

    @staticmethod
    def register_user(user_id, nickname, school, grade):
        with conn:
            conn.execute("INSERT OR REPLACE INTO Users (user_id, full_name, school, grade) VALUES (?,?,?,?)",
                         (user_id, nickname, school, grade))
            conn.execute("INSERT OR IGNORE INTO UsersProgress (user_id) VALUES (?)", (user_id,))

class UserProgressController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.update_user_information()

    def update_user_information(self):
        cur = conn.cursor()
        res = cur.execute("SELECT * FROM UsersProgress WHERE user_id = ?", (self.user_id,)).fetchone()
        self.progress_record = ProgressTableRecord(id = res[0],
                                                   achievments = res[1],
                                                   exp = res[2],
                                                   done_tasks = res[3])
        if not self.progress_record.id == None:
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
        try: return json.loads(str(self.progress_record.achievments))
        except: return []

    @property
    def exp(self) -> float: return self.progress_record.exp
    @property
    def sucesfull_tasks(self) -> int: return self.progress_record.done_tasks

    def append_user_exp(self, count: float):
        self.set_exp(self.exp + count)

    def append_right_tasks_quantity(self, count: int):
        self.set_right_tasks(self.sucesfull_tasks + count)

class UserHomeworkController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.homework_records:list[HomeworkTableRecord] = []
        self.conn = conn
        self.update_user_information()

    def update_user_information(self):
        cur = self.conn.cursor()
        res = cur.execute(
            "SELECT * FROM UsersHomeWork WHERE user_id = ?", 
            (self.user_id,)
        )
        for raw_record in res.fetchall():
            record = HomeworkTableRecord(id = raw_record[0],
                                         user_id = self.user_id,
                                         subject = raw_record[2],
                                         task_text = raw_record[3],
                                         deadline_time = raw_record[4],
                                         reminder_time = raw_record[5],
                                         is_done = raw_record[6])
            self.homework_records.append(record)
    
    def get_task_id(self,subject_id: str, task_text: str):
        cur = self.conn.cursor()
        res = cur.execute(
            "SELECT * FROM UsersHomeWork WHERE user_id = ? AND subject_id = ? AND task_text = ?", 
            (self.user_id,subject_id,task_text)
        )
        return res.fetchone()[0]

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
    def get_all_pending_reminders():
        current_ts = int(time.time())
        cur = conn.cursor()
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

class SchoolController:
    def __init__(self):
        self.conn = conn
    def add_school(self, school_name: str,base_url:str,delta_url:str):
        with self.conn:
            self.conn.execute("INSERT INTO Schools (school_name, base_url, delta_url) VALUES (?, ?, ?)", 
                              (school_name, base_url, delta_url,))
    def delete_shcool(self, id: int):
        with self.conn:
            self.conn.execute("DELETE FROM Schools WHERE id = ?", (id,))
    def get_all_schools(self) -> list[SchoolTableRecord]:
        with self.conn:
            school_records = self.conn.execute("SELECT * FROM Schools").fetchall()
        schools = []
        for record in school_records:
            schools.append(
                SchoolTableRecord(id = record[0],
                                  name = record[1],
                                  domain_url = record[2],
                                  base_schedule_url = record[3],
                                  delta_schedule_url = record[4],
                                  exams_url = record[5]))
        return schools
    
    def get_school(self,name:str) -> SchoolTableRecord:
        #Возвращается первый элемент списка, поскольку предполагается, что FDIUT (First Data Is Undoubted True)
        return list(filter(lambda elem: elem.name == name, self.get_all_schools()))[0]