import sqlite3
import json
import time
conn = sqlite3.connect('users_information.db', check_same_thread=False)

def init_db():
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            school TEXT,
            grade TEXT,
            reg_date DATETIME DEFAULT CURRENT_TIMESTAMP
        );""")
        
        conn.execute("""CREATE TABLE IF NOT EXISTS UsersProgress (
            user_id INTEGER PRIMARY KEY,
            achievements TEXT DEFAULT '[]',
            exp_count REAL DEFAULT 0.0,
            count_tasks INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        );""")

        conn.execute("""CREATE TABLE IF NOT EXISTS UsersHomeWork(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id TEXT,
            task_text TEXT,
            deadline INTEGER,      
            reminder_time INTEGER, 
            status BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        );""")

        conn.execute("""CREATE TABLE IF NOT EXISTS Schools(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
            schedule_url TEXT
            delta_schedule_url TEXT
        );""")
def del_db():
    with conn:
        conn.execute("""DROP TABLE IF EXISTS Users;
            DROP TABLE IF EXISTS UsersProgress;
            DROP TABLE IF EXISTS UsersHomeWork;
            DROP TABLE IF EXISTS Schools;""")
init_db()

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.update_user_information()

    def update_user_information(self):
        cur = conn.cursor()
        res = cur.execute("SELECT * FROM Users WHERE user_id = ?", (self.user_id,))
        self.all_user_information = res.fetchone()        
    
    def is_user_register(self) -> bool:
        return self.all_user_information is not None

    def get_user_name(self): return self.all_user_information[1] if self.is_user_register() else None
    def get_user_school(self): return self.all_user_information[2] if self.is_user_register() else None
    def get_user_class(self) -> str : return self.all_user_information[3] if self.is_user_register() else ""
    def get_user_grade(self) -> int: return int((self.all_user_information[3])[0]) if self.is_user_register() else 0

    @staticmethod
    def register_user(user_id, nickname, school, class_):
        with conn:
            conn.execute("INSERT OR REPLACE INTO Users (user_id, full_name, school, grade) VALUES (?,?,?,?)",
                         (user_id, nickname, school, class_))
            conn.execute("INSERT OR IGNORE INTO UsersProgress (user_id) VALUES (?)", (user_id,))

class UserProgress:
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
        val = json.dumps(new_achievements, ensure_ascii=False)
        with conn:
            conn.execute("UPDATE UsersProgress SET achievements=? WHERE user_id = ?", (val, self.user_id))
        self.update_user_information()

    def set_exp(self, new_exp: float):
        with conn:
            conn.execute("UPDATE UsersProgress SET exp_count=? WHERE user_id = ?", (new_exp, self.user_id))
        self.update_user_information()

    def set_right_tasks(self, new_count: int):
        with conn:
            conn.execute("UPDATE UsersProgress SET count_tasks=? WHERE user_id = ?", (new_count, self.user_id))
        self.update_user_information()

    def get_user_achievements(self) -> list:
        try: return json.loads(self.all_user_information[1])
        except: return []

    def get_user_exp_count(self) -> float: return float(self.all_user_information[2])
    def get_user_sucesfull_tasks(self) -> int: return int(self.all_user_information[3])

    def user_exp_count_plus(self, count: float):
        self.set_exp(self.get_user_exp_count() + count)

    def right_tasks_plus(self, count: int):
        self.set_right_tasks(self.get_user_sucesfull_tasks() + count)

class UserHomeWork:
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

#TODO:работа с базой данных с таблицей школ
class School:
    def __init__(self,school_name:str):
        self.name = school_name
        self.conn = conn
    
    def update_user_information(self):
        cur = self.conn.cursor()
        self.schedule_url,self. = cur.execute(
            "SELECT * FROM Schools WHERE name = ?", 
            (self.name,)
        ).fetchall()