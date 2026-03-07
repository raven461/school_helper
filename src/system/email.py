from config import config
import smtplib
class EmailController:
  def __init__(self, login=config.email_login.get_secret_value()):
    self.login = login
    self.smtpObj = smtplib.SMTP("smtp.gmail.com", 587)
    self.smtpObj.starttls()
    password = config.email_password.get_secret_value()
    self.smtpObj.login(login,password)
    
  def send_email(self, receiver, text):
    self.smtpObj.sendmail(self.login, receiver, text)
  def exit(self):
    self.smtpObj.quit()