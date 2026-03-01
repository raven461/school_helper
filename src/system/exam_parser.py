import httpx
import datetime
from dateutil.relativedelta import relativedelta
t = datetime.date.today()
halfyear = (2,1)[t.month > 9]
year = (t + relativedelta(months=-6)).year
class Parser419Exams:
    def __init__(self):
        self.main_url = "https://419.spb.ru/f/grafik_ocenochnyh_procedur_"
        self.exams = [f"{halfyear}_polugodie_na_{year}-{year+1}_uchebnyj_god_srednij_uroven",
                      f"{halfyear}_polugodie_na_{year}-{year+1}_uchebnyj_god_osnovnaya_shkola",
                      f"{halfyear}_polugodie_na_{year}-{year+1}_uchebnyj_god_nachalnaya_shkola"]
    def returnFilename(self,user_class):
        if user_class < 5:
            name = self.main_url + self.exams[2]
        elif user_class < 9:
            name = self.main_url + self.exams[1]
        else:
            name = self.main_url + self.exams[0]
        with httpx.Client(timeout=10.0) as client:
            try:
                client.get(name + ".pdf")
                return name + ".pdf"
            except:
                client.get(name + "_otredaktirovannyj.pdf")
                return name + "_otredaktirovannyj.pdf"