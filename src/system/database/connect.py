import sqlite3
conn = sqlite3.connect('users_information.db', check_same_thread=False)

def init_db():
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            school TEXT,
            grade TEXT
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
            name TEXT,
            domain_url TEXT,
            schedule_url TEXT,
            delta_schedule_url TEXT,
            exams_url TEXT
        );""")
def del_db():
    with conn:
        conn.execute("""DROP TABLE IF EXISTS Users;
            DROP TABLE IF EXISTS UsersProgress;
            DROP TABLE IF EXISTS UsersHomeWork;
            DROP TABLE IF EXISTS Schools;""")