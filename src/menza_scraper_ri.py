from time import sleep
import requests   
from bs4 import *
import xmlrpc.client
import re
import json

class Scraper:
    URL = "https://app.scri.hr/dnevnimeni/41"

    def __init__(self) -> None:
        self.api = xmlrpc.client.ServerProxy('http://127.0.0.1:8000')
        self.currentDay = ""
        self.parsed_menues = {"RUČAK":{},"VEČERA":{}}

    def scrap(self) -> None:
        html = requests.get(Scraper.URL).text

        # get the data  
        soup = BeautifulSoup(html, 'html.parser')
        
        daily_menu = {"RUČAK":{},"VEČERA":{}}

        for tag in soup.find_all("strong"):
            table = tag.parent.parent.parent.parent.find("tbody")

            for row in table.find_all("tr"):
                daily_menu[tag.text][row.text.split('\n')[1]] =  list(filter(None,re.sub(r'<.+?>',',', row.text.split('\n')[2].replace('</span>','')).split(',')))
                
        self.parsed_menues = daily_menu

    def update(self) -> bool:
        with open("menza.json",'w',encoding='utf-8') as file:
            file.write(json.dumps(self.parsed_menues,ensure_ascii=False))
        print("wrote")
        return True#self.api.write_menza(self.parsed_menues)

def main():
    scraper = Scraper()
    scraper.scrap()
    while scraper.update():
        sleep(60*30)
        scraper.scrap()

if __name__ == "__main__": 
    main()