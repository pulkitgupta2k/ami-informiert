import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import itertools
from creds import username, password

def getSoup(link, cookies):
    req = requests.get(link, cookies = cookies)
    html = req.content
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def append_rows(self, values, value_input_option='RAW'):
    params = {
            'valueInputOption': value_input_option
    }
    body = {
            'majorDimension': 'ROWS',
            'values': values
    }
    return self.spreadsheet.values_append(self.title, params, body)

def get_sheet(sheet):
    scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
    file_name = 'client_key.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
    client = gspread.authorize(creds)
    spreadsheets = client.open(sheet)
    details = {}
    for spreadsheet in spreadsheets:
        details[spreadsheet.title] = spreadsheet.get_all_values()
        # print(spreadsheet.get_all_values())
        print(spreadsheet.title)
    with open('details.json', 'w') as f:
        json.dump(details, f)
    
    return details

def gsheet_load(array, sheet, tab):
    scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
    file_name = 'client_key.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet)
    worksheet = spreadsheet.add_worksheet(title=tab, rows="20", cols="20")
    append_rows(worksheet,array)
    print("MODIFIED")


def login():
    session = requests.Session()
    login_link = "https://www.ami-informiert.de/login-erforderlich"
    payload = { 'user': username,
            'pass': password,
            'login.x': '71',
            'login.y': '9',
            'logintype': 'login',
            'pid': '141',
            'redirect_url': '/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte'
            }
    headers = {
    'Connection': 'close',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'DNT': '1'
    }
    session.post(login_link, headers=headers, data = payload)
    cookies = session.cookies.get_dict()
    return cookies

def join_mat(mat_1, mat_2):
    matrix = []
    for i in range(len(mat_1)):
        row = mat_1[i]
        row.extend(mat_2[i])
        matrix.append(row)
    return matrix


def get_table(url, cookies):
    soup = getSoup(url, cookies)
    matrix = []
    table_body = soup.find('table', {'id': 'tableAusgabe'})
    for tr in table_body.find_all('tr'):
        row = []
        for td in tr.find_all('td'):
            row.append(td.text.strip())
        matrix.append(row)
    for index in range(len(matrix)):
        while not len(matrix[index]) == len(matrix[1]):
            matrix[index].append("")
    return matrix

def get_table_cust(url, cookies):
    soup = getSoup(url, cookies)
    matrix = []
    table_body = soup.find('table', {'id': 'tableAusgabe'})
    for tr in table_body.find_all('tr'):
        row = []
        for td in tr.find_all('td'):
            td_str = str(td).replace("<br>", "").replace("<b>", "").replace(" colspan=\"10\"", "").replace("left b", "left")
            try:
                value = re.findall(r"td class=\"left\"*>(.*?)<", td_str)[0]
            except:
                value = ""
            row.append(value)
        # print(row)
        matrix.append(row)

    for index in range(len(matrix)):
        while not len(matrix[index]) == len(matrix[1]):
            matrix[index].append("")
    return matrix

def make_snap(mat_1, mat_2, mat_3, sheet, tab):
    master_mat = []
    max_length = max(len(mat_1), len(mat_2))
    max_length = max(max_length, len(mat_3))

    while not len(mat_1) == max_length:
        row = [""] * len(mat_1[1])
        mat_1.append(row)
    while not len(mat_2) == max_length:
        row = [""] * len(mat_2[1])
        mat_2.append(row)
    while not len(mat_3) == max_length:
        row = [""] * len(mat_3[1])
        mat_3.append(row)

    for i in range(max_length):
        row = []
        row.extend(mat_1[i])
        row.append("")
        row.extend(mat_2[i])
        row.append("")
        row.extend(mat_3[i])
        master_mat.append(row)
    # pprint(master_mat)
    gsheet_load(master_mat, sheet, tab)

def format_daily_details(date, matrix, obi_wan_kenobi):
    pos_1 = matrix[1].index("")
    pos_2 = matrix[1].index("", pos_1+1)

    obsts = []
    gemuses = []
    potatoes = []

    for i in range(1,len(matrix)):
        for j in range(0, pos_1):
            row = []
            row.append(matrix[i][j])
            obsts.append(row)
        for j in range(pos_1+1, pos_2):
            row = []
            row.append(matrix[i][j])
            gemuses.append(row)
        for j in range(pos_2+1,len(matrix[i])):
            row = []
            row.append(matrix[i][j])
            potatoes.append(row)

    date = datetime.strptime(date, '%m-%d').strftime('%d%b') 
    
    if date in obi_wan_kenobi["obst"][0]:
        date_index = obi_wan_kenobi["obst"].index(date)
    else:
        obi_wan_kenobi["obst"][0].append(date)
        for i in range(1,obi_wan_kenobi["obst"]):
            obi_wan_kenobi["obst"][i].append('')
    product = ""
    for obst in obsts:
        if len(list(filter(None, obst))):
            product = obst[0] 
            continue
        heading = product + ''.join(list(filter(None, obst[0:4])))
        mittel = obst[-1].split()[0]
        for obi in obi_wan_kenobi["obst"]:
            if obi[0] == heading:
                obi[date_index] = mittel
    product = ""
    for gemuse in gemuses:
        if len(list(filter(None, gemuse))):
            product = gemuse[0] 
            continue
        heading = product + ''.join(list(filter(None, gemuse[0:4])))
        mittel = gemuse[-1].split()[0]
        for obi in obi_wan_kenobi["gemuse"]:
            if obi[0] == heading:
                obi[date_index] = mittel
    product = ""
    for potato in potatoes:
        if len(list(filter(None, potato))):
            product = potato[0] 
            continue
        heading = product + ''.join(list(filter(None, potato[0:4])))
        mittel = potato[-1].split()[0]
        for obi in obi_wan_kenobi[["potatoes"]]:
            if obi[0] == heading:
                obi[date_index] = mittel

    return obi_wan_kenobi
    
def add_daily():
    with open("details.json") as f:
        details = json.load(f)
    obi_wan_kenobi = {}
    obi_wan_kenobi["obst"] = []
    obi_wan_kenobi["gemuse"] = []
    obi_wan_kenobi["potatoes"] = []
    for key_detail, value_detail in details.items():
        if re.match(r'\d\d-\d\d',key_detail):
            obi_wan_kenobi = format_daily_details(key_detail, value_detail, obi_wan_kenobi)



def daily_driver():
    cookies = login()
    table_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?purg=1%2C2%2C6%2C20%2C25%2C30%2C35%2C36%2C37%2C50%2C51%2C70%2C71%2C75%2C76%2C78%2C90%2C91%2C92%2C93%2C99%2"
    table_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?moart=2&purg=200%2C201%2C207%2C209%2C211%2C212%2C214%2C230%2C231%2C232%2C240%2C241%2C242%2C244%2C245%2C260%2C261%2C262%2C270%2C271%2C272%2C273%2C277%2C278%2C279%2C280%2C281%2C284%2C285%2C286%2C287%2C300%2C301%2C302%2C303%2C304%2C340%2C341%2C342%2C343%2C290%2C291%2C292%2C"
    table_5 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-kartoffeln/preisenotierungen/grossmaerkte?prozessnr=1"
    mat_1 = get_table(table_1, cookies)
    mat_2 = get_table(table_2, cookies)
    mat_5 = get_table_cust(table_5, cookies)
    today = datetime.today().strftime("%d-%m")
    make_snap(mat_1, mat_2, mat_5, 'AMI_Snaps', today)

def weekly_driver():
    cookies = login()
    table_3 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?moart=1&purg=1%2C2%2C6%2C20%2C25%2C30%2C35%2C36%2C37%2C50%2C51%2C70%2C71%2C75%2C76%2C78%2C90%2C91%2C92%2C93%2C99%2C&prozessnr=3"
    table_4 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?moart=2&prozessnr=3&purg=200%2C201%2C207%2C209%2C211%2C212%2C214%2C230%2C231%2C232%2C240%2C241%2C242%2C244%2C245%2C260%2C261%2C262%2C270%2C271%2C272%2C273%2C277%2C278%2C279%2C280%2C281%2C284%2C285%2C286%2C287%2C300%2C301%2C302%2C303%2C304%2C340%2C341%2C342%2C343%2C290%2C291%2C292%2C"
    table_6 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-kartoffeln/preisenotierungen/grossmaerkte?prozessnr="

    mat_3 = get_table(table_3, cookies)
    mat_4 = get_table(table_4, cookies)
    mat_6 = get_table_cust(table_6, cookies)

    week = mat_3[1][-2].split("/")[-1]
    week = "W"+week+"_test"
    make_snap(mat_3, mat_4, mat_6, 'AMI_Snaps', week)

def driver_verbrauch():
    cookies = login()
    table_v_1_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-gemuese"
    table_v_1_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-gemuese?selectedtype=2"
    table_v_2_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-obst"
    table_v_2_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-obst?selectedtype=2"
    table_v_3_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-kartoffeln/preisenotierungen/verbraucherpreise?selectedtype=1"
    table_v_3_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-kartoffeln/preisenotierungen/verbraucherpreise?selectedtype=2"

    mat_1_1 = get_table(table_v_1_1, cookies)
    mat_1_2 = get_table(table_v_1_2, cookies)
    mat_2_1 = get_table(table_v_2_1, cookies)
    mat_2_2 = get_table(table_v_2_2, cookies)
    mat_3_1 = get_table(table_v_3_1, cookies)
    mat_3_2 = get_table(table_v_3_2, cookies)

    mat_1 = join_mat(mat_1_1, mat_1_2)
    mat_2 = join_mat(mat_2_1, mat_2_2)
    mat_3 = join_mat(mat_3_1, mat_3_2)

    week = mat_1_1[1][4].split()[-1].split('.')[0]
    week = 'V_W'+week
    make_snap(mat_1, mat_2, mat_3, 'AMI_Snaps', week)

def driver():
    # weekly_driver()
    # driver_verbrauch()
    get_sheet('AMI_Snaps_PG')

    
