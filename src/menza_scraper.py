from time import sleep
import requests   
from bs4 import *
import xmlrpc.client

class Scraper:
    URL = "https://www.scpu.hr/hr/prehrana/"
    DAYS = set(("monday","tuesday","wednesday","thursday","friday","saturday","sunday"))
    MENUES = ("I","II","Vege","Po izboru")

    def __init__(self) -> None:
        self.api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')
        self.currentDay = ""
        self.daily_menu = {"lunch":[],"dinner":[]}
        self.parsed_menues = {"lunch":{},"dinner":{}}

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
        menues = {"lunch":{},"dinner":{}}
        for timeOfDay in menues:
            last = 0
            for men in Scraper.MENUES:
                if not men in self.daily_menu[timeOfDay]:
                    continue
                temp = []
                for s in self.daily_menu[timeOfDay][last:self.daily_menu[timeOfDay].index(men)]:

                    if s.find("sadr") == -1:
                        temp.append(s)

                menues[timeOfDay][men] = temp       
                last = self.daily_menu[timeOfDay].index(men)+1
        
        self.parsed_menues = menues
    
    def update(self) -> bool:
        return self.api.write_menza(self.parsed_menues)

def main():
    scraper = Scraper()
    scraper.scrap()
    scraper.parse()
    while scraper.update():
        sleep(60*30)
        scraper.scrap()
        scraper.parse()

if __name__ == "__main__": 
    main()