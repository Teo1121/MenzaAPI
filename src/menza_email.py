import xmlrpc.client  
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

import os.path
from email.mime.text import MIMEText
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
class Email:
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __send_message(self, message):
      try:
        body = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')}
        message = (self.service.users().messages().send(userId='me', body=body)
                   .execute())
        print('Message Id: %s' % message['id'])
        return message
      except HttpError as error:
        print('An error occurred: %s' % error)

    def __init__(self) -> None:
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', Email.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', Email.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        try:
        # Call the Gmail API
            self.service = build('gmail', 'v1', credentials=creds)
        except HttpError as error:
            print(f'An error occurred: {error}')

        self.api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')

    def send_all(self) -> bool:
        emails = self.api.read_email()
        data = self.api.read_menza()

        message = MIMEText("data: "+data)
        message['from'] = "me"
        message['subject'] = "New menu"

        for m in emails:
            message['to'] = m
            self.__send_message(message)
        return True
    
    def send_verification(self,email : str) -> bool:

        link = "test"
        message = MIMEText("link :"+link)
        message['to'] = email
        message['from'] = "me"
        message['subject'] = "Verify subscription"

        self.__send_message(message)
        return True
    
    def send_confirmation(self, email : str) -> bool:

        message = MIMEText("Thank you!")
        message['to'] = email
        message['from'] = "me"
        message['subject'] = "Thank you!"

        self.__send_message(message)
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