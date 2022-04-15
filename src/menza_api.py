from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client
import json
import uuid

from menza_error_codes import RPCCodes 

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

    def log_message(self, format, *args):

        with open("log.txt",'a') as file:
            file.write("%s - - [%s] %s\n" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      format%args))

        super().log_message(format,*args)

class API:
    __instance = None

    def __init__(self) -> None:
        self.__email_file = "./resources/email.csv"
        self.__menza_file = "./resources/menza.json"
        self.__menza_backup = "./resources/yesterday.json"

        self.email_service = xmlrpc.client.ServerProxy('http://127.0.0.1:8080')

        self.emails2verify = {}

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance
    
    def read_email(self) -> dict:
        with open(self.__email_file,'r', encoding='utf-8') as file:
            header = file.readline()
            result = []
            for email in file.readlines():
                email_list = email[:-1].split(', ')
                result.append([
                    email_list[0],[
                        email_list[1],
                        email_list[2].split('|')
                    ]
                ])
            return dict(result)
    
    def __dupicate(self, email : str) -> bool:
        for values in self.read_email().values():
            if email in values:
                return True
        return False

    def verify_email(self, email : str, subs : list[str]) -> RPCCodes:
        if self.__dupicate(email):
            return RPCCodes.DUPLICATE
        uid = str(uuid.uuid1())
        self.emails2verify[uid] = email 
        try:
            return self.email_service.send_verification(email,uid,subs)
        except ConnectionRefusedError:
            print("email service is offline")
            return RPCCodes.SERVER_ERROR

    def write_email(self, uid : str, subs : str) -> RPCCodes:
        if not uid in self.emails2verify:
            if uid in self.read_email():
                return RPCCodes.DUPLICATE
            else:
                return RPCCodes.NOT_FOUND
        with open(self.__email_file,'a', encoding='utf-8') as file:
            file.write(uid+', '+self.emails2verify[uid]+', '+subs+'\n')
        try:
            temp = self.email_service.send_confirmation(self.emails2verify[uid])
        except ConnectionRefusedError:
            print("email service is offline")
            temp = RPCCodes.SUCCESS
        self.emails2verify.pop(uid)
        return temp
    
    def delete_email(self, uid : str) -> RPCCodes:
        emails = self.read_email()
        try:
            emails.pop(uid)
        except KeyError:
            return RPCCodes.NOT_FOUND
        with open(self.__email_file,'w', encoding='utf-8') as file:
            file.write('uuid, email\n')
            for id in emails:
                file.write(id+', '+emails[id][0]+', '+'|'.join(emails[id][1])+'\n')
        return RPCCodes.SUCCESS
    


    def read_menza(self) -> dict:
        with open(self.__menza_file,'r', encoding='utf-8') as file:
            return json.loads(file.readline())

    def __backup(self) -> dict:
        with open(self.__menza_backup,'r', encoding='utf-8') as file:
            return json.loads(file.readline())

    def write_menza(self, meal : dict, menza : str) -> RPCCodes:
        temp = self.read_menza()
        try:
            with open(self.__menza_backup,'w', encoding='utf-8') as file:
                file.write(json.dumps(temp,ensure_ascii=False))
            temp[menza] = meal
            with open(self.__menza_file,'w', encoding='utf-8') as file:
                file.write(json.dumps(temp,ensure_ascii=False))
        except Exception as e:
            print(e)
            return RPCCodes.SERVER_ERROR
        if self.__check_change(menza):
            try:
                for email in self.read_email().values():
                    if menza in email[1]:
                        self.email_service.send(email[0],meal,menza)
            except ConnectionRefusedError:
                print("email service is offline")
        return RPCCodes.SUCCESS

    def __check_change(self, menza : str) -> bool:
        try:
            return not self.__backup()[menza] == self.read_menza()[menza]
        except KeyError:
            return True
    
def main():
    # Create server
    with SimpleXMLRPCServer(('0.0.0.0', 8000),
                            requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        server.register_instance(API())

        # Run the server's main loop
        server.serve_forever()

if __name__ == "__main__": 
    main()