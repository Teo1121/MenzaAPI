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

from menza_error_codes import RPCCodes

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
class Email:
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __send_message(self, message : MIMEText) -> RPCCodes:
      try:
        body = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')}
        message = (self.service.users().messages().send(userId='me', body=body)
                   .execute())
        return RPCCodes.SUCCESS
      except HttpError as error:
        print('An error occurred: %s' % error)
        return RPCCodes.SERVER_ERROR

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

    def send_all(self, emails : list[str], data : dict) -> RPCCodes:
        
        message = MIMEText("data: "+str(data))
        message['from'] = "me"
        message['subject'] = "New menu"

        for m in emails:
            message['to'] = m
            if self.__send_message(message) == RPCCodes.SERVER_ERROR:
                return RPCCodes.SERVER_ERROR
        return RPCCodes.SUCCESS
    
    def send_verification(self, email : str, id : str) -> RPCCodes:

        link = "http://127.0.0.1:8081/verify/"+id
        message = MIMEText("link :"+link)
        message['to'] = email
        message['from'] = "me"
        message['subject'] = "Verify subscription"

        return self.__send_message(message)
    
    def send_confirmation(self, email : str) -> RPCCodes:

        message = MIMEText("Thank you for subscribing!")
        message['to'] = email
        message['from'] = "me"
        message['subject'] = "Thank you!"

        return self.__send_message(message)
            
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