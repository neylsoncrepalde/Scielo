#!/usr/bin/env python3
from urllib.request import urlopen, HTTPError
from urllib.error import URLError
from bs4 import BeautifulSoup
import pandas as pd
import csv
import time
import re
import os


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


    def scrape_content(self):
        #Abrindo os arquivos
        saida = open('articles_content.csv','w')
        export = csv.writer(saida)
        export.writerow(['title','year','journal', 'authors', 'affs',
                         'keywords'])

        #regex = re.compile("\xa0")
        #rent = re.compile("[\n|\t]")
        #relink = re.compile("\[ Link\] ")

        begin = time.time()

        arquivo = open('artigos.csv')
        links_artigos = arquivo.readlines()
        newline = re.compile("\n")
        links_artigos = [newline.sub("", i) for i in links_artigos]
        links_artigos = list(set(links_artigos))

        url_broken = []
        contador = 1
        for url in links_artigos:
            if contador % 10 == 0:
                print("Scraping {} of {} articles...".format(contador, len(links_artigos)))

            try:
                page = urlopen(url)
                page = BeautifulSoup(page, "lxml")
            except URLError:
                contador += 1
                url_broken.append(url)
                continue

            journal = page.find("meta", {"name": "citation_journal_title"}).get("content")
            title = page.find("meta", {"name": "citation_title"}).get("content")
            year = page.find("meta", {"name": "citation_date"}).get("content")[-4:]
            autores = [i.get("content") for i in page.findAll("meta", {"name": "citation_author"})]
            autores = list(set(autores))
            affs = [i.get("content") for i in page.findAll("meta", {"name": "citation_author_institution"})]
            affs = list(set(affs))

            abstract = page.find("meta", {"name": "citation_abstract_html_url"}).get("content")

            try:
                pageabs = urlopen(abstract)
                pageabs = BeautifulSoup(pageabs, "lxml")
                keys = [i.get_text() for i in pageabs.find("div", {"class": "index,pt"}).findAll("p")[4]]
            except HTTPError:
                keys = [""]

            # Escrevendo os dados
            export.writerow([title, year, journal, autores, affs, keys])

            contador += 1

        saida.close()

        end = time.time()

        print('Done')
        print("Total of {} broken URLs".format(len(url_broken)))
        print("Scraping of the article content took {} seconds.".format(round(end-begin, 3)))

    def clean_data(self):
        print("Cleaning data and exporting datasets.....")
        bd = pd.read_csv("articles_content.csv")
        autores = bd.authors
        rebegin = re.compile("\[")
        reend = re.compile("\]")
        regex = re.compile("', '")
        reaspas = re.compile("'")
        autores = [rebegin.sub("", i) for i in autores]
        autores = [reend.sub("", i) for i in autores]
        autoresnew = [regex.split(i) for i in autores]

        for i in range(len(autoresnew)):
            for j in range(len(autoresnew[i])):
                autoresnew[i][j] = reaspas.sub("", autoresnew[i][j])

        # Verificando o tamanho máximo no banco
        max_autores = max([len(i) for i in autoresnew])

        # Cria max_autores novas variáveis no banco
        for i in range(max_autores):
            bd['autor' + str(i)] = ""

        # Coloca os dados no lugar certo
        for i in range(len(autoresnew)):
            tamanho = len(autoresnew[i])
            for j in range(tamanho):
                bd.iloc[i, j+6] = autoresnew[i][j]
        bd_autores = bd.drop(['authors', 'keywords'], axis=1)

        # Faz a mesma limpeza para afiliaçoes
        afiliacoes = bd.affs
        afiliacoes = [rebegin.sub("", i) for i in afiliacoes]
        afiliacoes = [reend.sub("", i) for i in afiliacoes]
        afiliacoesnew = [regex.split(i) for i in afiliacoes]
        for i in range(len(afiliacoesnew)):
            for j in range(len(afiliacoesnew[i])):
                afiliacoesnew[i][j] = reaspas.sub("", afiliacoesnew[i][j])

        # Verificando o tamanho máximo no banco
        max_afiliacoes = max([len(i) for i in afiliacoesnew])

        # Cria max_autores novas variáveis no banco
        for i in range(max_afiliacoes):
            bd['inst' + str(i)] = ""

        # Coloca os dados no lugar certo
        for i in range(len(afiliacoesnew)):
            tamanho = len(afiliacoesnew[i])
            for j in range(tamanho):
                bd.iloc[i, j+6] = afiliacoesnew[i][j]
        bd_afiliacoes = bd.drop(['affs', 'keywords'], axis=1)

        # Exportando os bancos
        bd_autores.to_csv("scielo_autores.csv", index=False)
        bd_afiliacoes.to_csv("scielo_afiliacoes.csv", index=False)

        print('Removing junk data...')
        os.remove(['edicoes.csv', 'artigos.csv', 'articles_content.csv'])

        print('Done!!!')

    def get_all_articles(self):
        self.scrape_editions()
        self.scrape_articles()
        self.scrape_content()
        self.clean_data()
