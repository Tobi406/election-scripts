import requests
import re
from bs4 import BeautifulSoup
import os
import time

URL = "https://www.bundeswahlleiter.de/bundestagswahlen/2021/ergebnisse/opendata/daten/"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

results = soup.find_all("a")

matchingResults = []
for link in results:
  href = link.get('href')
  if (href.startswith('erg')):
    matchingResults.append(href)

os.chdir(r'D:\\wahlscripts\\de\\bt') # change working dir

for part in matchingResults:
  link = "https://www.bundeswahlleiter.de/bundestagswahlen/2021/ergebnisse/opendata/daten/" + part
  requestContent = requests.get(link)
  xml = BeautifulSoup(requestContent.content, "xml")
  f = open('data/' + part, "w", encoding="utf-8")
  f.write(str(xml))
  f.close()
  time.sleep(0.3)

