import httpx
from lxml import html
from io import BytesIO
from database.enties import SchoolController
import pandas as pd
import asyncio
import logging

#TODO: добавить функции для поддержки парсинга сайтов других школ
class ScheduleParser:
    def __init__(self, school_name: str):
        self.school_name = school_name
        self.basic_url,self.delta_url,self.domain,self.exams  = ""

    @classmethod
    async def create(cls, school_name: str):
        obj = cls(school_name)
        """Запрос к базе данных.
        Не проводится в __init__, т.к. для работы с базой данных используется библиотека aiosqlite, а
        Python не поддерживает асинхронные конструкторы классов"""
        school = await SchoolController().get_school(school_name)
        if school is None:
            logging.error(f"ValueError: School {school_name} not found at Schools")
            raise ValueError(f"School {school_name} not found at Schools")
        obj.basic_url = school.base_schedule_url
        obj.delta_url = school.delta_schedule_url
        obj.domain = school.domain_url
        obj.exams = school.exams_urls
        return obj

    async def update_schedule(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(self.basic_url)
                tree = html.fromstring(resp.content)
                links = tree.xpath("//a[contains(@href, 'deti') and contains(@href, '.xls')]/@href")
                if not links: return False
                file_resp = await client.get(self.domain + links[0])
                self.data = file_resp.content
                return True
            except Exception: return False

    def process_excel(self, target_class: str):
        try:
            df = pd.read_excel(BytesIO(self.data))
            df.iloc[:, 0] = df.iloc[:, 0].ffill()
            target_clean = target_class.lower().replace(" ", "").replace("-", "")
            
            col_idx = None
            for j in range(len(df.columns)):
                if df.iloc[:, j].astype(str).str.lower().str.replace(" ", "").str.contains(target_clean).any():
                    col_idx = j
                    break
            if col_idx is None: return "Класс не найден"

            schedule = {}
            days = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА"]
            curr_day = None
            for _, row in df.iterrows():
                val = str(row.iloc[0]).strip().upper()
                if val in days:
                    curr_day = val
                    schedule[curr_day] = []
                if curr_day and str(row.iloc[col_idx]).strip().lower() not in ['nan', target_clean]:
                    schedule[curr_day].append(str(row.iloc[col_idx]).strip())
            return schedule
        except Exception as e: return f"Ошибка: {e}"

    async def get_schedule(self, target_class: str):
        if not self.data: return "Данные не загружены"
        return await asyncio.to_thread(self.process_excel, target_class)

    async def update_delta_schedule(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(self.delta_url)
                tree = html.fromstring(resp.content)
                self.table_delta = {}
                days = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА"]
                for table in tree.xpath('//table'):
                    txt = table.text_content().upper()
                    day = next((d for d in days if d in txt), None)
                    if day:
                        for row in table.xpath('.//tr')[1:]:
                            cells = [c.text_content().strip() for c in row.xpath('.//td')]
                            if len(cells) >= 6 and any(i.isdigit() for i in cells[0]):
                                self.table_delta.setdefault(day, []).append({
                                    "class": cells[0].lower(), "num": cells[1],
                                    "subject": cells[2], "room": cells[3], "comment": cells[5]
                                })
            except Exception: pass

    def get_delta(self, target_class: str) -> list:
        res = []
        target = target_class.lower().replace(" ", "")
        for day, deltas in self.table_delta.items():
            for d in deltas:
                if target in d["class"].replace(" ", ""):
                    res.append({"day": day, "lesson": d["num"], "subject": d["subject"], "room": d["room"], "comment": d["comment"]})
        return res