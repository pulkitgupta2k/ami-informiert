import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import itertools
from creds import username, password, cookie

def getHTML(link):
    req = requests.get(link)
    html = req.content
    return html

def login():
    login_link = "https://www.ami-informiert.de/login-erforderlich"
    payload = { 'user': 'nikhil.choraria%40gmail.com',
            'pass': 'upwork',
            'login.x': '71',
            'login.y': '9',
            'logintype': 'login',
            'pid': '141',
            'redirect_url': '%2Fami-onlinedienste%2Fmarkt-aktuell-obst-und-gemuese%2Fpreise%2Fgrossmaerkte%3Fpurg%3D1%252C2%252C6%252C20%252C25%252C30%252C35%252C36%252C37%252C50%252C51%252C70%252C71%252C75%252C76%252C78%252C90%252C91%252C92%252C93%252C99%252C%26cHash%3D69258fafc8d1d6e1fb2b2c6acbb4615a',
            'referer': 'https%3A%2F%2Fwww.ami-informiert.de%2Fami-onlinedienste%2Fmarkt-aktuell-obst-und-gemuese%2Fpreise%2Fgrossmaerkte%3Fpurg%3D1%252C2%252C6%252C20%252C25%252C30%252C35%252C36%252C37%252C50%252C51%252C70%252C71%252C75%252C76%252C78%252C90%252C91%252C92%252C93%252C99%252C%26cHash%3D69258fafc8d1d6e1fb2b2c6acbb4615a'
            }
    headers = {
    'Connection': 'close',
    'Cookie': cookie,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'DNT': '1'
    }
    requests.post(login_link, headers=headers, data = payload)
    url = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?purg=1%2C2%2C6%2C20%2C25%2C30%2C35%2C36%2C37%2C50%2C51%2C70%2C71%2C75%2C76%2C78%2C90%2C91%2C92%2C93%2C99%2C&cHash=69258fafc8d1d6e1fb2b2c6acbb4615a"
    headers = {'Cookie': cookie}
    requests.get(url, headers=headers)



def driver():
    login()

