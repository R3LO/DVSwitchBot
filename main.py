from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import configparser
import requests
import json
import asyncio
import time


config = configparser.ConfigParser()
config.read('config.ini')
url = config.get('Settings', 'url')
channel_id = config.get('Settings', 'channel_id')
token = config.get('Settings', 'token')
fn = config.get('Settings', 'file_json')
wait = int(config.get('Settings', 'wait_minutes'))

async def reg_send(msg, channel_id, token):
    '''    sent to telegrann    '''
    url = 'https://api.telegram.org/bot'
    url += token
    method = url + '/sendMessage'
    r = requests.post(method, data={
        'chat_id': channel_id,
        'text': msg,
        'parse_mode': 'MarkdownV2'
    })
    if r.status_code != 200:
        print('Telegramm error')

def check_json(date, call, group) -> bool:
    """    Check data from LSON    """
    with open(fn, "r") as f_json:
        t_dict = json.load(f_json)
    now = datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S") # type str
    # date = date + timedelta(hours=3) # Windows time
    if call in t_dict and group in t_dict[call]:
        spot_date = datetime.strptime(t_dict[call][group], '%Y-%m-%d %H:%M:%S')
        now_date = datetime.strptime(now, '%Y-%m-%d %H:%M:%S')
        if spot_date + timedelta(minutes=wait) < date:
            t_dict[call] = {group : now}
            with open(fn, "w") as f_json:
                json.dump(t_dict, f_json)
            return True
        else:
            return False
    else:
        now_date = datetime.strptime(now, '%Y-%m-%d %H:%M:%S')
        if now_date < date + timedelta(minutes=wait):
            t_dict[call] = {group : now}
            with open(fn, "w") as f_json:
                json.dump(t_dict, f_json)
            return True
    return False

def get_spots(url: str) -> list:
    """ get spots from dashboard   """
    row = [] # temp list
    all_spots = [] # return list
    try:
        r = requests.get(url, verify=False)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)

    if r.status_code == 200:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            tables = soup.find('fieldset').findAll('table')[4]
            alltrs = tables.findAll('tr')[1:]
            for data in alltrs:
                tds = data.find_all('td')
                for td in tds:
                    if len(tds) == 6 or len(tds) == 0:
                        break
                    elif len(tds) == 8:
                        date = tds[0].text.strip() + ' ' + str(datetime.now().year)
                        date = datetime.strptime(date, '%H:%M:%S %b %d %Y')
                        mode = tds[1].text.strip()
                        callsign = tds[2].text.strip()
                        target = tds[3].text.strip()[3:]
                        src = tds[4].text.strip()
                        dur = tds[5].text.strip()
                        loss = tds[6].text.strip()
                        ber = tds[7].text.strip()
                        row = [date, mode, callsign, target, src, dur, loss, ber]
                if row:
                    all_spots.append(row)
            return all_spots
        except:
            print('Parsing error')

def add_sign(parm: str) -> str:
    try:
        if parm == '--':
            return ''
        elif float(parm[:-1]) != 0.0:
            return '⚠️'
    except:
        pass
    return  ''


def main() -> None:
    while (True):
        all_spots = get_spots(url)
        for i in range(len(all_spots)):
            date = all_spots[i][0]
            call = all_spots[i][2].strip()
            group = all_spots[i][3].strip()
            dur = all_spots[i][5].strip()
            loss = all_spots[i][6].strip()
            loss_sign = add_sign(loss)
            ber = all_spots[i][7].strip()
            ber_sign = add_sign(ber)
            for x, y in (".", "\\."), ("-", "\\-"):
                dur = dur.replace(x, y)
                loss = loss.replace(x, y)
                ber = ber.replace(x, y)
            status = check_json(date, call, group)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if status and group == '250667':
                telegram_mess = ('*🔔 В эфире:*\n'\
                                 'TG' + group + ': ' + '*' + call + '*' + ' ⏱ ' + dur + ' sec\n' \
                                  + loss_sign + '*Loss*\\=' + loss + ' ' + ber_sign +'*BER*\\=' + ber)
                print(telegram_mess)
                asyncio.run(reg_send(telegram_mess, channel_id, token))
        print(now)
        time.sleep(5)




if __name__ == "__main__":
    main()
