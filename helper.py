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

def get_sheet(sheet, make_local = False):
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
        # print(spreadsheet.title)
    if make_local:
        with open('details.json', 'w') as f:
            json.dump(details, f)
    
    return details

def gsheet_load(array, sheet, tab, clear=False):
    scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
    ]
    file_name = 'client_key.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(file_name,scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet)
    try:
        worksheet = spreadsheet.add_worksheet(title=tab, rows="20", cols="20")
    except:
        worksheet = spreadsheet.worksheet(tab)
    if clear:
        worksheet.clear()
    append_rows(worksheet,array)
    print("MODIFIED")

def conv_float(obi_wan_kenobi):
    for key, values in obi_wan_kenobi.items():
        for i, value in enumerate(values):
            for j,v in enumerate(value):
                try:
                    obi_wan_kenobi[key][i][j] = float(v)
                except:
                    pass
    return obi_wan_kenobi

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
            for br in td.find_all("br"):
                br.replace_with("\n")
            row.append(td.text.strip())
        matrix.append(row)
    for index in range(len(matrix)):
        while not len(matrix[index]) == len(matrix[1]):
            matrix[index].append("")

    if "Der Mittelwert bezieht sich" in matrix:
        return matrix[:-1]
    else:
        return matrix

def get_table_cust(url, cookies):
    soup = getSoup(url, cookies)
    matrix = []
    table_body = soup.find('table', {'id': 'tableAusgabe'})
    for tr in table_body.find_all('tr'):
        row = []
        for td in tr.find_all('td'):
            td_str = str(td).replace("<br>", "\n").replace("<b>", "").replace(" colspan=\"10\"", "").replace("left b", "left").replace(" colspan=\"9\"", "")
            try:
                value = re.findall(r"td class=\"left\"*>(.*?)<", td_str)[0]
            except:
                value = ""
            row.append(value)
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
    gsheet_load(master_mat, sheet, tab, True)

def format_daily_details(date, matrix, obi_wan_kenobi):
    # print(date)
    # print(matrix[1])
    try:
        pos_1 = matrix[1].index("")
    except:
        pos_1 = len(matrix[1])
        pos_1 = len(matrix[1])
    try:
        pos_2 = matrix[1].index("", pos_1+1)
    except:
        pos_2 = len(matrix[1])

    obsts = []
    gemuses = []
    potatoes = []

    for i in range(1,len(matrix)):
        obsts.append(matrix[i][:pos_1])
        if not pos_1 == len(matrix[1]):
            gemuses.append(matrix[i][pos_1+1:pos_2])
        if not pos_2 == len(matrix[1]):
            potatoes.append(matrix[i][pos_2+1:])

    date = datetime.strptime(date, '%m-%d').strftime('%d%b') 
    
    if date in obi_wan_kenobi["Obst"][0]:
        date_index = obi_wan_kenobi["Obst"][0].index(date)
    else:
        date_index = len(obi_wan_kenobi["Obst"][0])
        obi_wan_kenobi["Obst"][0].append(date)
        obi_wan_kenobi["Gemuse"][0].append(date)
        obi_wan_kenobi["Potatoes"][0].append(date)
        for i in range(1,len(obi_wan_kenobi["Obst"])):
            obi_wan_kenobi["Obst"][i].append('')
        for i in range(1,len(obi_wan_kenobi["Gemuse"])):
            obi_wan_kenobi["Gemuse"][i].append('')
        for i in range(1,len(obi_wan_kenobi["Potatoes"])):
            obi_wan_kenobi["Potatoes"][i].append('')
    product = ""
    for obst in obsts:
        if len(list(filter(None, obst))) == 1:
            product = obst[0]
            continue
        heading = "Obst"+ product + ''.join(list(filter(None, obst[0:4])))
        mittel = obst[-1].replace("\n", "")
        mittel = mittel.replace(",",".")[:-1]
        if mittel.count('.') > 1:
            mittel = mittel.replace(".", "", 1)
        try:
            mittel = float(mittel)
        except:
            pass
        for obi in obi_wan_kenobi["Obst"]:
            if obi[0].replace(" ","").lower() == heading.replace(" ","").lower():
                obi[date_index] = mittel
    product = ""
    for gemuse in gemuses:
        if len(list(filter(None, gemuse))) == 1:
            product = gemuse[0] 
            continue
        heading = "Gemuse"+product + ''.join(list(filter(None, gemuse[0:4])))
        mittel = gemuse[-1].replace("\n", "")
        mittel = mittel.replace(",",".")[:-1]
        if mittel.count('.') > 1:
            mittel = mittel.replace(".", "", 1)
        try:
            mittel = float(mittel)
        except:
            pass
        for obi in obi_wan_kenobi["Gemuse"]:
            if obi[0].replace(" ","").lower() == heading.replace(" ","").lower():
                obi[date_index] = mittel
    product = ""
    for potato in potatoes:
        if len(list(filter(None, potato))) == 1:
            product = potato[0] 
            continue
        heading = product+product + ''.join(list(filter(None, potato[0:4])))
        # heading_k = "Kartoffeln"+product + ''.join(list(filter(None, potato[0:4])))
        mittel = potato[-1].replace("\n", "")
        mittel = mittel.replace(",",".")
        if mittel.count('.') > 1:
            mittel = mittel.replace(".", "", 1)
        try:
            mittel = float(mittel)
        except:
            pass
        for obi in obi_wan_kenobi["Potatoes"]:
            if obi[0].replace(" ","").lower() == heading.replace(" ","").lower():
                obi[date_index] = mittel

    return obi_wan_kenobi

def format_weekly_details(date, matrix, obi_wan_kenobi):
    # print(date)
    # print(matrix[1])
    try:
        pos_1 = matrix[1].index("")
    except:
        pos_1 = len(matrix[1])
        pos_1 = len(matrix[1])
    try:
        pos_2 = matrix[1].index("", pos_1+1)
    except:
        pos_2 = len(matrix[1])

    obsts = []
    gemuses = []
    potatoes = []

    for i in range(1,len(matrix)):
        obsts.append(matrix[i][:pos_1])
        if not pos_1 == len(matrix[1]):
            gemuses.append(matrix[i][pos_1+1:pos_2])
        if not pos_2 == len(matrix[1]):
            potatoes.append(matrix[i][pos_2+1:])

    date = obsts[0][7]
    if date in obi_wan_kenobi["Obst"][0]:
        date_index = obi_wan_kenobi["Obst"][0].index(date)
    else:
        date_index = len(obi_wan_kenobi["Obst"][0])
        obi_wan_kenobi["Obst"][0].append(date)
        obi_wan_kenobi["Gemuse"][0].append(date)
        obi_wan_kenobi["Potatoes"][0].append(date)
        for i in range(1,len(obi_wan_kenobi["Obst"])):
            obi_wan_kenobi["Obst"][i].append('')
        for i in range(1,len(obi_wan_kenobi["Gemuse"])):
            obi_wan_kenobi["Gemuse"][i].append('')
        for i in range(1,len(obi_wan_kenobi["Potatoes"])):
            obi_wan_kenobi["Potatoes"][i].append('')

    product = ""
    for obst in obsts:
        if len(list(filter(None, obst))) == 1:
            product = obst[0]
            continue
        heading = "Obst"+ product + ''.join(list(filter(None, obst[0:4])))
        mittel = obst[-2].replace("\n", "")
        mittel = mittel.replace(",",".")
        if mittel.count('.') > 1:
            mittel = mittel.replace(".", "", 1)
        try:
            mittel = float(mittel)
        except:
            pass
        for obi in obi_wan_kenobi["Obst"]:
            if obi[0].replace(" ","").lower() == heading.replace(" ","").lower():
                obi[date_index] = mittel
    product = ""
    for gemuse in gemuses:
        if len(list(filter(None, gemuse))) == 1:
            product = gemuse[0] 
            continue
        heading = "Gemuse"+product + ''.join(list(filter(None, gemuse[0:4])))
        mittel = gemuse[-2].replace("\n", "")
        mittel = mittel.replace(",",".")
        if mittel.count('.') > 1:
            mittel = mittel.replace(".", "", 1)
        try:
            mittel = float(mittel)
        except:
            pass
        for obi in obi_wan_kenobi["Gemuse"]:
            if obi[0].replace(" ","").lower() == heading.replace(" ","").lower():
                obi[date_index] = mittel
    product = ""
    for potato in potatoes:
        if len(list(filter(None, potato))) == 1:
            product = potato[0] 
            continue
        heading_f = "FrühkartoffelnFrühkartoffeln"+product + ''.join(list(filter(None, potato[0:4])))
        heading_k = "KartoffelnKartoffeln"+product + ''.join(list(filter(None, potato[0:4])))
        mittel = potato[-2].replace("\n", "")
        mittel = mittel.replace(",",".")
        if mittel.count('.') > 1:
            mittel = mittel.replace(".", "", 1)
        try:
            mittel = float(mittel)
        except:
            pass
        for obi in obi_wan_kenobi["Potatoes"]:
            if obi[0].replace(" ","").lower() == heading_f.replace(" ","").lower() or obi[0].replace(" ","").lower() == heading_k.replace(" ","").lower():
                obi[date_index] = mittel

    return obi_wan_kenobi

def format_verbraunch_details(date, matrix, obi_wan_kenobi):
    # print(date)
    try:
        pos_1 = matrix[1].index("")
    except:
        pos_1 = len(matrix[1])
        pos_1 = len(matrix[1])
    try:
        pos_2 = matrix[1].index("", pos_1+1)
    except:
        pos_2 = len(matrix[1])

    obsts = []
    gemuses = []
    potatoes = []

    for i in range(1,len(matrix)):
        obsts.append(matrix[i][:pos_1])
        if not pos_1 == len(matrix[1]):
            gemuses.append(matrix[i][pos_1+1:pos_2])
        if not pos_2 == len(matrix[1]):
            potatoes.append(matrix[i][pos_2+1:])

    date = obsts[0][4].split('.')[0].replace("\n","").replace("  ", "W")
    last_year_date = obsts[0][2].split('.')[0].replace("\n","").replace("  ", "W")
    

    if date in obi_wan_kenobi["VPreise"][0]:
        date_index = obi_wan_kenobi["VPreise"][0].index(date)
    else:
        date_index = len(obi_wan_kenobi["VPreise"][0])
        obi_wan_kenobi["VPreise"][0].append(date)
        for i in range(1,len(obi_wan_kenobi["VPreise"])):
            obi_wan_kenobi["VPreise"][i].append('')
    
    if last_year_date in obi_wan_kenobi["VPreise"][0]:
        last_year_date_index = obi_wan_kenobi["VPreise"][0].index(last_year_date)
    else:
        last_year_date_index = len(obi_wan_kenobi["VPreise"][0])
        obi_wan_kenobi["VPreise"][0].append(last_year_date)
        for i in range(1,len(obi_wan_kenobi["VPreise"])):
            obi_wan_kenobi["VPreise"][i].append('')

    
    for obst in obsts[1:]:
        if not obst[0] == '' and not obst[1] == '':
            heading = ['Obst']
            heading.extend(obst[0:2])
            mittel = obst[4]
            last_yaer_mittel = obst[2]
            try:
                mittel = float(mittel)
            except:
                pass
            found = 0
            for obi in obi_wan_kenobi["VPreise"]:
                if obi[0:3] == heading:
                    obi[date_index] = mittel
                    obi[last_year_date_index] = last_yaer_mittel
                    found = 1
                    break
            if found == 0:
                row = [''] * len(obi_wan_kenobi["VPreise"][0])
                row[0:3] = heading
                row[date_index] = mittel
                row[last_year_date_index] = last_yaer_mittel
                obi_wan_kenobi["VPreise"].append(row)

    for gemuse in gemuses[1:]:
        if not gemuse[0] == '' and not gemuse[1] == '':
            heading = ['Gemuse']
            heading.extend(gemuse[0:2])
            mittel = gemuse[4]
            last_yaer_mittel = gemuse[2]
            try:
                mittel = float(mittel)
            except:
                pass
            found = 0
            for obi in obi_wan_kenobi["VPreise"]:
                if obi[0:3] == heading:
                    obi[date_index] = mittel
                    obi[last_year_date_index] = last_yaer_mittel
                    found = 1
                    break
            if found == 0:
                row = [''] * len(obi_wan_kenobi["VPreise"][0])
                row[0:3] = heading
                row[date_index] = mittel
                row[last_year_date_index] = last_yaer_mittel
                obi_wan_kenobi["VPreise"].append(row)
    
    for potato in potatoes[1:]:
        if not potato[0] == '' and not potato[1] == '':
            heading = ['Kartoffeln']
            heading.extend(potato[0:2])
            mittel = potato[4]
            last_year_mittel = potato[2]
            try:
                mittel = float(mittel)
                last_year_mittel = float(last_year_mittel)
            except:
                pass
            found = 0
            for obi in obi_wan_kenobi["VPreise"]:
                # print(heading + " : " + obi[0:3])
                if obi[0:3] == heading:
                    obi[date_index] = mittel
                    obi[last_year_date_index] = last_year_mittel
                    found = 1
                    break
            if found == 0:
                row = [''] * len(obi_wan_kenobi["VPreise"][0])
                row[0:3] = heading
                row[date_index] = mittel
                row[last_year_date_index] = last_year_mittel
                obi_wan_kenobi["VPreise"].append(row)

    return obi_wan_kenobi

def add_daily():
    with open("details.json") as f:
        details = json.load(f)
    obi_wan_kenobi = get_sheet("AMIPG_Daily")
    for key_detail, value_detail in details.items():
        if re.match(r'\d\d-\d\d',key_detail) and 'shota' not in key_detail:
            obi_wan_kenobi = format_daily_details(key_detail, value_detail, obi_wan_kenobi)
    obi_wan_kenobi = conv_float(obi_wan_kenobi)
    for key, value in obi_wan_kenobi.items():
        gsheet_load(value, "AMIPG_Daily", key, True)

def add_weekly():
    with open("details.json") as f:
        details = json.load(f)
    obi_wan_kenobi = get_sheet("AMIPG_Weekly")
    for key_detail, value_detail in details.items():
        if re.match(r'W_\d\d',key_detail) and 'shota' not in key_detail:
            obi_wan_kenobi = format_weekly_details(key_detail, value_detail, obi_wan_kenobi)
    obi_wan_kenobi = conv_float(obi_wan_kenobi)
    for key, value in obi_wan_kenobi.items():
        gsheet_load(value, "AMIPG_Weekly", key, True)

def add_verbraunch():
    with open("details.json") as f:
        details = json.load(f)
    obi_wan_kenobi = get_sheet("AMIPG_Weekly")
    with open("obi_wan_kenobi.json", "w") as f:
        json.dump(obi_wan_kenobi, f)
    for key_detail, value_detail in details.items():
        if re.match(r'V_\d\d',key_detail) and not 'V_21' == key_detail:
            obi_wan_kenobi = format_verbraunch_details(key_detail, value_detail, obi_wan_kenobi)
    
    obi_wan_kenobi = conv_float(obi_wan_kenobi)
    gsheet_load(obi_wan_kenobi["VPreise"], "AMIPG_Weekly", "VPreise", True)

def daily_driver():
    cookies = login()
    table_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?purg=1%2C2%2C6%2C20%2C25%2C30%2C35%2C36%2C37%2C50%2C51%2C70%2C71%2C75%2C76%2C78%2C90%2C91%2C92%2C93%2C99%2C"
    table_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?moart=2&purg=200%2C201%2C207%2C209%2C211%2C212%2C214%2C230%2C231%2C232%2C240%2C241%2C242%2C244%2C245%2C260%2C261%2C262%2C270%2C271%2C272%2C273%2C277%2C278%2C279%2C280%2C281%2C284%2C285%2C286%2C287%2C300%2C301%2C302%2C303%2C304%2C340%2C341%2C342%2C343%2C290%2C291%2C292%2C"
    table_5 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-kartoffeln/preisenotierungen/grossmaerkte?prozessnr=1"
    mat_1 = get_table(table_1, cookies)
    mat_2 = get_table(table_2, cookies)
    mat_5 = get_table_cust(table_5, cookies)
    today = datetime.today().strftime("%m-%d")
    make_snap(mat_1, mat_2, mat_5, 'AMIPG_Snaps', today)

def weekly_driver():
    cookies = login()
    table_3 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?moart=1&purg=1%2C2%2C6%2C20%2C25%2C30%2C35%2C36%2C37%2C50%2C51%2C70%2C71%2C75%2C76%2C78%2C90%2C91%2C92%2C93%2C99%2C&prozessnr=3"
    table_4 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/grossmaerkte?moart=2&prozessnr=3&purg=200%2C201%2C207%2C209%2C211%2C212%2C214%2C230%2C231%2C232%2C240%2C241%2C242%2C244%2C245%2C260%2C261%2C262%2C270%2C271%2C272%2C273%2C277%2C278%2C279%2C280%2C281%2C284%2C285%2C286%2C287%2C300%2C301%2C302%2C303%2C304%2C340%2C341%2C342%2C343%2C290%2C291%2C292%2C"
    table_6 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-kartoffeln/preisenotierungen/grossmaerkte?prozessnr=3"

    mat_3 = get_table(table_3, cookies)
    mat_4 = get_table(table_4, cookies)
    mat_6 = get_table_cust(table_6, cookies)


    week = mat_3[1][-2].split("/")[-1]
    week = "W_"+week
    make_snap(mat_3, mat_4, mat_6, 'AMIPG_Snaps', week)

def driver_verbrauch():
    cookies = login()
    table_v_1_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-obst"
    table_v_1_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-obst?selectedtype=2"
    table_v_2_1 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-gemuese"
    table_v_2_2 = "https://www.ami-informiert.de/ami-onlinedienste/markt-aktuell-obst-und-gemuese/preise/verbraucherpreise-gemuese?selectedtype=2"
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
    week = 'V_'+week
    make_snap(mat_1, mat_2, mat_3, 'AMIPG_Snaps', week)

def driver():
    daily_driver()
    weekly_driver()
    driver_verbrauch()
    print("######## Snaps made ###########")
    get_sheet('AMIPG_Snaps', make_local=True)
    add_daily()
    print("######## Daily results added ###########")
    add_weekly()
    add_verbraunch()
    print("######## COMPLETE #############")

add_weekly()