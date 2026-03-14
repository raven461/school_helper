from system.database.enties import UserProgressController, UserHomeworkController
import json
import ast

class Achievements:
    def __init__(self):
        with open("achievements.json","r", encoding="utf-8") as achievements:
            self.available_achievements = json.load(achievements)
        self.ach_map = {ach["id"]: ach for ach in self.available_achievements}

    def get_achievement_name(self, ach_id):
        return self.ach_map.get(ach_id, {}).get("name", "Неизвестное достижение")

    def get_achievement_desc(self, ach_id):
        return self.ach_map.get(ach_id, {}).get("desc", "Описание отсутствует")

    async def update(self, user_id):
        prog = await UserProgressController().create(user_id)
        hw = await UserHomeworkController().create(user_id)
        
        current_ids = prog.achievments
        new_unlocked = []

        for ach in self.available_achievements:
            if ach["id"] not in current_ids:
                if ast.parse(ach["check"],mode = "eval")(prog, hw):
                    new_unlocked.append(ach)
                    reward = ach.get("reward_exp", 0)
                    if reward > 0:
                        await prog.append_user_exp(reward)

        if new_unlocked:
            updated_ids = current_ids + [ach["id"] for ach in new_unlocked]
            await prog.set_achievements(updated_ids)
            
        return new_unlocked