from system.database.enties import UserProgressController, UserHomeworkController
import json
import ast

#TODO:доделать обработку данных из json
class Achievements:
    def __init__(self):
        with open("achievements.json","r", encoding="utf-8") as achievements:
            self.available_achievements = json.load(achievements)
        self.ach_map = {ach["id"]: ach for ach in self.available_achievements}

    def get_achievement_name(self, ach_id):
        return self.ach_map.get(ach_id, {}).get("name", "Неизвестное достижение")

    def get_achievement_desc(self, ach_id):
        return self.ach_map.get(ach_id, {}).get("desc", "Описание отсутствует")

    def update(self, user_id):
        prog = UserProgressController(user_id)
        hw = UserHomeworkController(user_id)
        
        current_ids = prog.get_user_achievements()
        new_unlocked = []

        for ach in self.available_achievements:
            if ach["id"] not in current_ids:
                if ast.parse(ach["check"],mode = "eval")(prog, hw):
                    new_unlocked.append(ach)
                    reward = ach.get("reward_exp", 0)
                    if reward > 0:
                        prog.user_exp_count_plus(reward)

        if new_unlocked:
            updated_ids = current_ids + [ach["id"] for ach in new_unlocked]
            prog.set_achievements(updated_ids)
            
        return new_unlocked