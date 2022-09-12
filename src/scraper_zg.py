from time import sleep
import grpc
import requests   
from bs4 import *
import re

import menza_pb2_grpc
import menza_pb2

class Scraper:
    URL = "https://odeon.hr/dnevni-meni-studentska-menza/"

    def __init__(self) -> None:
        self.api = grpc.insecure_channel('localhost:50051')
        self.menu = {"restaurant":{"name":"Odeon Zagreb"},"lunch":[],"dinner":[]}

    def scrap(self) -> None:
        html = requests.get(Scraper.URL).text

        # get the data  
        soup = BeautifulSoup(html, 'lxml')

        for tag in soup.find("div",{"class":"entry-content clearfix"}).find_all("div"):
            menu_name = tag.find(text=re.compile("Menu"))
            if menu_name == None:
                menu_name = tag.find(text=re.compile("Jela"))
            tag = menu_name.parent
            self.menu['lunch'].append({"menu":{"name":str(menu_name),"meal":"LUNCH"},"dishes":[dict([["name",name]]) for name in tag.get_text(separator=',').split(",")[1:]]})
    
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
                print("service offline: ", e.details())
            else:
                print("unknown error occured: ",e)
           
        sleep(60*30)


if __name__ == "__main__":
    main()
