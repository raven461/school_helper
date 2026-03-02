from config import config, email_login
import smtplib
class Email:
  def __init__(self, login=email_login):
    self.login = login
    self.smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    self.smtpObj.starttls()
    password =config.email.get_secret_value()
    self.smtpObj.login(login,password)
    
  def send_email(self, receiver, text):
    self.smtpObj.sendmail(self.login, receiver, text)
  def exit(self):
    self.smtpObj.quit()
    
    
