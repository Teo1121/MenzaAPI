from time import sleep
import grpc
import requests   
from bs4 import *
import re
from difflib import SequenceMatcher

import menza_pb2_grpc
import menza_pb2

import pickle
from datetime import datetime

def similar(a, b):
    """Used to check for differences in words caused by grammatical mistakes, plurals and similar letter mismatches"""
    return SequenceMatcher(None, a, b).ratio()

class Scraper:
    URL = "https://app.scri.hr/dnevnimeni/"
    MENZE = {'41':"RESTORAN INDEX",
             '42':"RESTORAN KAMPUS",
             '43':"RESTORAN MINI",
             '45':"BISTRO PRAVRI",
             '46':"BISTRO RITEH",
             '47':"BISTRO POMORAC"}
    RI_MAP = {"RUČAK":"lunch","VEČERA":"dinner"}

    def __init__(self,index : int) -> None:
        self.index = str(index)
        self.api = grpc.insecure_channel('localhost:50051')
        self.currentDay = ""
        self.daily_menu = {"RUČAK":{},"VEČERA":{}}
        self.parsed_menu = {"restaurant":{"name":Scraper.MENZE[self.index]},"lunch":[],"dinner":[]}

    def scrap(self) -> None:
        html = requests.get(Scraper.URL+self.index).text

        # get the data  
        soup = BeautifulSoup(html, 'html.parser')
        
        daily_menu = {"RUČAK":{},"VEČERA":{}}
        
        for tag in soup.find_all("strong"):
            table = tag.parent.parent.parent.parent.find("tbody")
            if table is not None:
                for row in table.find_all("tr"):
                    food_list = list(filter(None,re.sub(r'<.+?>','|', row.text.split('\n')[2].replace('</span>','').replace('\ufeff','')).split('|')))
                    daily_menu[tag.text][row.text.split('\n')[1]] = self.__parse_text(food_list)              
            else:
                daily_menu[tag.text] = {}

        self.daily_menu = daily_menu

    def parse(self):
        result = {"restaurant":{"name":Scraper.MENZE[self.index]},"lunch":[],"dinner":[]}
        stub = menza_pb2_grpc.MediatorStub(self.api)
        try:
            dishes = set([model.dish.name for model in stub.ListDishes(menza_pb2.MenzaQuery()).data])
        except grpc.RpcError as e:
            dishes = set()
        for key in self.daily_menu:
            for menu in self.daily_menu[key]:
                result[Scraper.RI_MAP[key]].append({'menu':{'name':menu,"meal":Scraper.RI_MAP[key].upper()},"dishes":[]})
                for meal in self.daily_menu[key][menu]:
                    for dish in dishes:
                        if similar(dish,meal) >= 0.8275862068965517:
                            meal = dish
                            break
                    dishes.add(meal)
                    result[Scraper.RI_MAP[key]][-1]['dishes'].append({'name':meal})

        self.parsed_menu = result

    def __parse_text(self,food_list):
        skip_next = False
        result = []
        for jelo in food_list:
            if skip_next:
                skip_next = False
                continue
            jelo = jelo.replace('&nbsp;','')
            index = jelo.find('-')
            if index != -1:
                if len(jelo[index:]) < 3:   
                    skip_next = True
                jelo = jelo[:(index-1 if jelo[index-1] == ' ' else index)]
            if 'KRUH' in jelo:
                jelo = 'KRUH'
            elif jelo.find('SALATA') > 1:
                jelo = ' '.join(jelo.split(' ')[::-1])
            dot_index = jelo.find('.')
            if dot_index != -1:
                if jelo[dot_index-1] == ' ':
                    jelo = jelo[:dot_index-1]+jelo[dot_index:]
                    dot_index -=1
                if jelo[dot_index+1] != ' ':
                    jelo = jelo[:dot_index+1]+' '+jelo[dot_index+1:]

            result.append(jelo)
            
        return result


    def update(self):
        stub = menza_pb2_grpc.MediatorStub(self.api)
        return stub.WriteMenza(menza_pb2.Menza(**self.parsed_menu))

    def save_to_file(self,file : str):
        ts = datetime.now().replace(microsecond=0,second=0).isoformat()
        new = []
        try:
            r_file = open(file,'rb')
            new = pickle.load(r_file)
            r_file.close()
        except FileNotFoundError:
            pass
        self.parsed_menu["date"] = ts
        new.append(self.parsed_menu)
        w_file = open(file,'wb')
        pickle.dump(new,w_file)
        w_file.close()

def main():
    scraper = Scraper(41)
    while True:
        scraper.scrap()
        scraper.parse()
        #scraper.save_to_file("rika.dat") 
        try:
            print(scraper.update())
        except grpc.RpcError as e:
            error_code = e.code()
            if error_code == grpc.StatusCode.UNAVAILABLE:
                print("service offline: ", e.details())
            else:
                print("unknown error occured:",e)

        sleep(60*30)

if __name__ == "__main__":
    main()
