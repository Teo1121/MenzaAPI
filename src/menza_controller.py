from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from threading import Thread
from menza_email import Email
from menza_scraper import Scraper
from time import sleep

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class Controller:
    def __init__(self) -> None:
        #self.email_service = Email()
        self.scraper_service = Scraper()
        Thread(target=self.__loop,daemon=True).start()

    def __loop(self):
        while True:
            self.scraper_service.scrap()
            self.scraper_service.parse()

            if self.scraper_service.parsed_menues != self.scraper_service.api.read_menza():
                if self.scraper_service.update():
                    print("Sent emails!")
                    #self.email_service.send()
            print("No emails sent.")
            sleep(30)

    def request_sub(self,email):
        print("sub has been requested")

    def email_verified(self,email):
        print("email has been verified")

if __name__ == "__main__": 
    with SimpleXMLRPCServer(('127.0.0.1', 8080),
                            requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        server.register_instance(Controller())

        # Run the server's main loop
        server.serve_forever()