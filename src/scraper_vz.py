from time import sleep
import grpc
import requests   
from bs4 import *

import menza_pb2_grpc
import menza_pb2

class Scraper:
    URL = "https://www.scvz.unizg.hr/jelovnik-varazdin/"
    TRANSLATOR = {"Ručak":"lunch","Večera":"dinner"}

    def __init__(self) -> None:
        self.api = grpc.insecure_channel('localhost:50051')
        self.menu = None#{"restaurant":{"name":"Varazdin"},"lunch":[],"dinner":[]}

    def scrap(self) -> None:
        html = requests.get(Scraper.URL).text

        # get the data  
        soup = BeautifulSoup(html, 'html.parser')
        main_div = soup.find("div",{"class":"jelovnik-content active"})
        if main_div == None:
            return
        self.menu = {"restaurant":{"name":"Varazdin"},"lunch":[],"dinner":[]}
        for tag in main_div:
            if len(tag) > 1:
                tp = Scraper.TRANSLATOR[tag.find("h3").text]
                for menu in tag.find("div",{"class":"row"}):
                    if len(menu) > 1:
                        data = menu.find("p").text.split("\r\n")
                        self.menu[tp].append({"menu":{"name":data[0],"meal":tp.upper()},"dishes":[dict([["name",name]]) for name in data[1:]]})
                    
    def update(self):
        stub = menza_pb2_grpc.MediatorStub(self.api)
        return stub.WriteMenza(menza_pb2.Menza(**self.menu))

def main():
    scraper = Scraper()
    while True:
        scraper.scrap()
        try:
            print(scraper.update())
        except grpc.RpcError as e:
            error_code = e.code()
            if error_code == grpc.StatusCode.UNAVAILABLE:
                print("mediator service is offline")
            else:
                print("unknown error occured: ",e)
        except TypeError as e:
            print("no data to scrap")
        sleep(60*30)


if __name__ == "__main__":
    main()
