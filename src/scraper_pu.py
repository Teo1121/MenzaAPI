from time import sleep
import grpc
import requests   
from bs4 import *

import menza_pb2_grpc
import menza_pb2

class Scraper:
    URL = "https://www.scpu.hr/hr/prehrana/"
    DAYS = set(("monday","tuesday","wednesday","thursday","friday","saturday","sunday"))
    MENUES = ("I","II","Vege","Po izboru")

    def __init__(self) -> None:
        self.api = grpc.insecure_channel('localhost:50051')
        self.currentDay = ""
        self.daily_menu = {"lunch":[],"dinner":[]}
        self.parsed_menu = {"restaurant":{"name":"Studentski restoran Pula"},"lunch":[],"dinner":[]}

    def scrap(self) -> None:
        html = requests.get(Scraper.URL).text

        # get the data  
        soup = BeautifulSoup(html, 'html.parser')

        self.currentDay = str(list(Scraper.DAYS.intersection(soup.find("div",{"class":"active"}).attrs["class"]))[0])


        daily_menu = {"lunch":[],"dinner":[]}

        for tag in soup.find_all("div",{"class":self.currentDay}):
            daily_menu[tag.parent.attrs["class"][0]] = list(filter(''.__ne__,[i.strip() for i in tag.text.split('\n')]))

        self.daily_menu = daily_menu

    def parse(self) -> None:
        result = {"restaurant":{"name":"Studentski restoran Pula"},"lunch":[],"dinner":[]}
        for time_of_day in ("lunch","dinner"):
            last = 0
            for menu in Scraper.MENUES:
                if not menu in self.daily_menu[time_of_day]:
                    continue
                result[time_of_day].append({"menu":{"name":menu,"meal":time_of_day.upper()}, "dishes":[]})
                for s in self.daily_menu[time_of_day][last:self.daily_menu[time_of_day].index(menu)]:
                    if s.find("sadr") == -1:
                        result[time_of_day][-1]["dishes"].append({"name":s}) 
                last = self.daily_menu[time_of_day].index(menu)+1
        
        self.parsed_menu = result
    
    def update(self):
        stub = menza_pb2_grpc.MediatorStub(self.api)
        return stub.WriteMenza(menza_pb2.Menza(**self.parsed_menu))

def main():
    scraper = Scraper()
    while True:
        scraper.scrap()
        scraper.parse()   
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