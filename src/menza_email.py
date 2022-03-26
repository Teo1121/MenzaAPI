from matplotlib.style import context
import xmlrpc.client  
from bs4 import *
import smtplib
import ssl

class Email:
    PORT = 465
    EMAIL = "racunalni.praktikum.smtp@gmail.com"
    PASSWORD = "9Nq5BkS4dWDz7faU"

    def __init__(self) -> None:

        context = ssl.create_default_context()
        self.server = smtplib.SMTP_SSL("smtp.gmail.com", Email.PORT, context=context)
        self.server.login(Email.EMAIL, Email.PASSWORD) 

        self.api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')

    def send(self):
        emails = self.api.read_email()
        data = self.api.read_menza()

        message = """\
Subject: New menu

Data: """+data

        for m in emails:
            self.server.sendmail(Email.EMAIL, m, message)
            


