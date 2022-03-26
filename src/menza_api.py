from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client
import json

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class API:
    __instance = None

    def __init__(self) -> None:
        self.__email_file = "./resources/email.txt"
        self.__menza_file = "./resources/menza.json"
        self.__menza_backup = "./resources/yesterday.json"

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance
    
    def read_email(self) -> list[str]:
        with open(self.__email_file,'r', encoding='utf-8') as file:
            return list(set([email[:-1] for email in file.readlines()]))
    
    def __dupicate(self, email : str) -> int:
        return email in self.read_email()

    def write_email(self, email : str) -> bool:
        if self.__dupicate(email):
            return False
        with open(self.__email_file,'a', encoding='utf-8') as file:
            file.write(email+'\n')
        return True
    
    def delete_email(self, email : str) -> bool:
        emails = self.read_email()
        try:
            emails.remove(email)
        except ValueError:
            return False
        with open(self.__email_file,'w', encoding='utf-8') as file:
            for e in emails:
                file.write(e+'\n')
        return True
    
    def read_menza(self) -> dict:
        with open(self.__menza_file,'r', encoding='utf8') as file:
            return json.loads(file.readline())

    def __backup(self) -> dict:
        with open(self.__menza_backup,'r', encoding='utf-8') as file:
            return json.loads(file.readline())

    def write_menza(self, meal : dict) -> bool:
        try:
            with open(self.__menza_backup,'w', encoding='utf-8') as file:
                file.write(json.dumps(self.read_menza(),ensure_ascii=False))
            with open(self.__menza_file,'w', encoding='utf-8') as file:
                file.write(json.dumps(meal,ensure_ascii=False))
        except Exception as e:
            print(e)
            return False
        if self.__check_change():
            with xmlrpc.client.ServerProxy('http://127.0.0.1:8080') as email:
                email.send_all()

        return True

    def __check_change(self):
        return not self.__backup() == self.read_menza()
    
    def verify_email(self, email : str) -> bool:
        if self.__dupicate(email):
            return False
        with xmlrpc.client.ServerProxy('http://127.0.0.1:8080') as email:
                return email.send_verification(email)
def main():
    # Create server
    with SimpleXMLRPCServer(('127.0.0.1', 8000),
                            requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        server.register_instance(API())

        # Run the server's main loop
        server.serve_forever()

if __name__ == "__main__": 
    main()