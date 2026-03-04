from pydantic import BaseModel

class UserTableRecord(BaseModel):
    id:int
    name:str
    school_name:str
    grade:str

class ProgressTableRecord(BaseModel):
    id:int
    achievments:list[str]
    exp:float
    done_tasks:int

class HomeworkTableRecord(BaseModel):
    id:int
    user_id:int
    subject:str
    task_text:str
    deadline_time:int
    reminder_time:int
    is_done:bool

class SchoolTableRecord(BaseModel):
    id:int
    name:str
    base_schedule_url:str
    delta_schedule_url:str