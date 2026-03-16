import aiosqlite

def get_db_connection(adress = "user_information.db"):
    return aiosqlite.connect(adress)

async def init_db():
    async with get_db_connection() as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            school TEXT,
            grade TEXT,
            type TEXT CHECK (type IN ("teacher","pupil","parent"))
        );""")
        
        await conn.execute("""CREATE TABLE IF NOT EXISTS UsersProgress (
            user_id INTEGER PRIMARY KEY,
            achievements TEXT DEFAULT '[]',
            exp_count REAL DEFAULT 0.0,
            count_tasks INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        );""")

        await conn.execute("""CREATE TABLE IF NOT EXISTS UsersHomeWork(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id TEXT,
            task_text TEXT,
            deadline INTEGER,      
            reminder_time INTEGER, 
            status BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES Users(user_id)
        );""")

        await conn.execute("""CREATE TABLE IF NOT EXISTS Schools(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            domain_url TEXT,               
            base_schedule_url TEXT,
            delta_schedule_url TEXT,
            exams_urls TEXT DEFAULT '[]'
        );""")
        await conn.commit()
    async with get_db_connection("achievements.db") as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS Achievements(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT 'Неизвестное достижение',
            desc TEXT 'Описание отсутствует',               
            exp REAL DEFAULT 0.0,
            check_function TEXT
        );""")
        await conn.commit()


async def del_db():
    async with get_db_connection() as conn:
        await conn.execute("DROP TABLE IF EXISTS Users;")
        await conn.execute("DROP TABLE IF EXISTS UsersProgress;")
        await conn.execute("DROP TABLE IF EXISTS UsersHomeWork;")
        await conn.commit()