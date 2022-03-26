from matplotlib.style import context
import xmlrpc.client  
from bs4 import *
import smtplib
import ssl

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
class Email:
    PORT = 465
    EMAIL = "racunalni.praktikum.smtp@gmail.com"
    PASSWORD = "9Nq5BkS4dWDz7faU"

    def __init__(self) -> None:
        context = ssl.create_default_context()
        self.server = smtplib.SMTP_SSL("smtp.gmail.com", Email.PORT, context=context)
        self.server.login(Email.EMAIL, Email.PASSWORD) 

        self.api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')

    def send_all(self) -> bool:
        emails = self.api.read_email()
        data = self.api.read_menza()

        message = """\
Subject: New menu

Data: """+data

        for m in emails:
            self.server.sendmail(Email.EMAIL, m, message)
        return True
    
    def send_verification(self,email : str) -> bool:

        link = "test"
        message = """\
Subject: verify email

link to confirm: """+link

        self.server.sendmail(Email.EMAIL, email, message)
        return True
    
    def send_confirmation(self, email : str) -> bool:
        message = """\
Subject: Thank you

Thank you"""

        self.server.sendmail(Email.EMAIL, email, message)
        return True

            
def main():
    # Create server
    with SimpleXMLRPCServer(('127.0.0.1', 8080),
                            requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        server.register_instance(Email())

        # Run the server's main loop
        server.serve_forever()

if __name__ == "__main__": 
    main()