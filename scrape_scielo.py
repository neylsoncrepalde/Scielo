#!/usr/bin/env python3
from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv
import time
import re


class ScrapeScielo:
    def __init__(self, revistas):
        self.revistas = revistas
        self.edicoes = "edicoes.csv"

    def scrape_editions(self):
        begin = time.time()

        arquivo = open(self.revistas)
        revistas = arquivo.readlines()

        saida = open("edicoes.csv", "w")
        export = csv.writer(saida)
        self.edicoes = "edicoes.csv"

        print("Scraping Jounals' editions....")

        for revista in revistas:
            pagina = urlopen(revista)
            pagina = BeautifulSoup(pagina, "lxml")
            for tag in pagina.findAll("font", {"color": "#000080"}):
                try:
                    link_edicao = tag.findNext("a").get("href")
                    if "http" not in link_edicao:
                        continue
                    else:
                        export.writerow([link_edicao])
                except AttributeError:
                    continue
        saida.close()
        end = time.time()

        print("Done")
        print("Scraping editions took {} seconds.".format(round(end-begin, 3)))

    def scrape_articles(self):
        print("Scraping articles links...")
        begin = time.time()

        saida = open("artigos.csv", "w")
        export = csv.writer(saida)

        arquivo = open(self.edicoes)
        edicoes = arquivo.readlines()
        newline = re.compile("\n")
        edicoes = [newline.sub("", i) for i in edicoes]

        for edicao in edicoes:
            pagina = urlopen(edicao)
            pagina = BeautifulSoup(pagina, "lxml")
            links = [i.findNext("a").get("href") for i in pagina.findAll("div", {"align": 'left'})]
            for link in links:
                if "arttext" in link:
                    export.writerow([link])

        end = time.time()
        saida.close()
        print("Done")
        print("Scraping of the articles took {} seconds.".format(round(end-begin, 3)))

    def scrape_xml(self):
        print("Scraping xml links for the articles...")
        begin = time.time()

        saida = open("links_xml.csv", "w")
        export = csv.writer(saida)
        
        arquivo = open('artigos.csv')
        artigos = arquivo.readlines()
        newline = re.compile("\n")
        artigos = [newline.sub("", i) for i in artigos]
        
        for url in artigos:
            pagina = urlopen(url)
            pagina = BeautifulSoup(pagina, "lxml")
            
            for i in pagina.findAll("a", {"target":"xml"}):
                pagina_xml = i.get('href')
                export.writerow([pagina_xml])
        
        end = time.time()
        saida.close()
        print("Done")
        print("Scraping of the xml links took {} seconds.".format(round(end-begin, 3)))
        
    def scrape_content(self):
        pass
        
