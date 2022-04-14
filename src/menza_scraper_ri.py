from time import sleep
import requests   
from bs4 import *
import xmlrpc.client
import re

from menza_error_codes import RPCCodes

class Scraper:
    URL = "https://app.scri.hr/dnevnimeni/"
    MENZE = {'41':"RESTORAN INDEX",
             '42':"RESTORAN KAMPUS",
             '43':"RESTORAN MINI",
             '45':"BISTRO PRAVRI",
             '46':"BISTRO RITEH",
             '47':"BISTRO POMORAC"}


    def __init__(self,index : int) -> None:
        self.index = str(index)
        self.api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')
        self.currentDay = ""
        self.parsed_menues = {"RUČAK":{},"VEČERA":{}}

    def scrap(self) -> None:
        html = requests.get(Scraper.URL+self.index).text

        # get the data  
        soup = BeautifulSoup(html, 'html.parser')
        
        daily_menu = {"RUČAK":{},"VEČERA":{}}

        for tag in soup.find_all("strong"):
            table = tag.parent.parent.parent.parent.find("tbody")

            for row in table.find_all("tr"):
                daily_menu[tag.text][row.text.split('\n')[1]] =  list(filter(None,re.sub(r'<.+?>',',', row.text.split('\n')[2].replace('</span>','')).split(',')))
                
        self.parsed_menues = daily_menu

    def update(self) -> RPCCodes:
        return self.api.write_menza(self.parsed_menues,Scraper.MENZE[self.index])
        
def main():
    scraper = Scraper(41)
    scraper.scrap()
    while True:
        try:
            if scraper.update() != RPCCodes.SUCCESS:
                print("failed to save new data")
        except ConnectionRefusedError:
            print("mediator service is offline")
        sleep(60*30)
        scraper.scrap()

if __name__ == "__main__": 
    main()