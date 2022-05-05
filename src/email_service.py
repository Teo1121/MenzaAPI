import os.path
from email.mime.text import MIMEText
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from concurrent import futures
import grpc
import menza_pb2
import menza_pb2_grpc

class Email(menza_pb2_grpc.EmailServiceServicer):
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    def __send_message(self, message : MIMEText):
      try:
        body = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')}
        message = (self.service.users().messages().send(userId='me', body=body)
                   .execute())
        return grpc.StatusCode.OK
      except HttpError as error:
        print('An error occurred: %s' % error)
        return grpc.StatusCode.UNKNOWN

    def __init__(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', Email.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request()) # https://support.google.com/cloud/answer/10311615#zippy=%2Ctesting
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
    
    def SendEmail(self, request, context):
        
        message = MIMEText("data: "+str(request.data))
        message['from'] = "me"
        message['subject'] = "New menu in "+request.data.restaurant.name
        message['to'] = request.email.address

        context.set_code(self.__send_message(message))
        return menza_pb2.Response(msg="Mail sent")

    def SendVerification(self, request, context):

        link = "http://127.0.0.1:8081/verify/"+request.uuid
        message = MIMEText("Your uuid is: uuid\nLink to verify user email :"+link)
        message['to'] = request.address
        message['from'] = "me"
        message['subject'] = "Verify Email"

        context.set_code(self.__send_message(message))
        return menza_pb2.Response(msg="Verification mail sent")

    
    def SendConfirmation(self, request, context):

        message = MIMEText("Thank you for subscribing!" if request.has_subscribed else "Thank you for unsubscribing!")
        message['to'] = request.email.address
        message['from'] = "me"
        message['subject'] = "Thank you!"

        context.set_code(self.__send_message(message))
        return menza_pb2.Response(msg="Confirmation mail sent")

            
def main():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    menza_pb2_grpc.add_EmailServiceServicer_to_server(Email(),server)
    server.add_insecure_port('[::]:50053')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__": 
    main()