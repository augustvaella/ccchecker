from bs4 import BeautifulSoup
import zipfile
import glob
import os
import re
import csv
import pickle
import datetime 

# Chiki Chiki Checker

#曜日変換
WEEKDAY_JA_TO_EN = {
    '月': 'Mon',
    '火': 'Tue',
    '水': 'Wed',
    '木': 'Thu',
    '金': 'Fri',
    '土': 'Sat',
    '日': 'Sun'
}

WEEKDAY_EN_TO_JA = {
    'Mon': '月',
    'Tue': '火',
    'Wed': '水',
    'Thu': '木',
    'Fri': '金',
    'Sat': '土',
    'Sun': '日'
}


#ふたばスレッド futaba_thread……list
#ふたばレス futaba_res……dict

#ふたばレス futaba_res

FUTABA_RESPONSE_COLOMN = {
    r'url': r'URL',
    r'thread_number': r'スレッド番号',
    r'thread_title': r'スレッドタイトル',
    r'number': r'レス番号',
    r'munen': r'無念',
    r'name': r'名前',
    r'date': r'年月日',
    r'weekday': r'曜日',
    r'time': r'時刻',
    r'ip': r'IP',
    r'domain': r'ドメイン',
    r'res_id': r'レスID',
    r'soudane': r'そうだね',
    r'res': r'レス'
}

FUTABA_RESPONSE_TEMPLATE = {
    'url': '',
    'thread_number': 0,
    'thread_title': '',
    'number': 0,
    'munen': '無念',
    'name': 'としあき',
    'date': '00/01/01',
    'weekday': '月',
    'time': '00:00:00',
    'ip': '000.000.*',
    'domain': 'xxx.com',
    'res_id': 0,
    'soudane': 0,
    'res': ''
}

# コピー
# dest = list(map(lambda d: d.copy(), target))

CONDITION_METHOD = {
    'none': 0,
    'freeword': 1,
    'range': 2
}

re_datetime = re.compile(r'\d\d/\d\d/\d\d\([日月火水木金土]\)\d\d:\d\d:\d\d')
re_datetime_search = re.compile(r'(\d\d)/(\d\d)/(\d\d)%s*(\d\d):(\d\d):(\d\d)')
re_date = re.compile(r'(\d\d)/(\d\d)/(\d\d)')
re_time = re.compile(r'(\d\d):(\d\d):(\d\d)')
re_weekday = re.compile(r'[日月火水木金土]')

re_ip = re.compile(r'IP:([0-9a-fA-F]+[\.:])+\*?')
re_domain = re.compile(r'\([0-9a-zA-Z\-\.]+\)')

re_brace = re.compile(r'[\(\)]')
re_ip_letters = re.compile(r'IP:')
re_numbers = re.compile(r'\d+')
re_link = re.compile(r'\[\nlink\n\]')
re_res_ip = re.compile(r'([0-9a-fA-F]+[\.:]?)+')
re_res_ip_reform = re.compile(r'\[\n(([0-9a-fA-F]+[\.:]?)+)\n]')



def split_time_ip_domain(data):
    #21/01/24(日)20:47:21 IP:101.141.*(eonet.ne.jp)
    #21/01/24(日)20:47:07 IP:240f:45.*(ipv6)
    time = re_datetime.search(data)
    ip = re_ip.search(data)
    domain = re_domain.search(data)

    if domain:
        ret_domain = re_brace.sub('', domain.group(0))
    else:
        ret_domain = None
    
    if time:
        ret_time = time.group(0)
    else:
        ret_time = None
    
    if ip:
        ret_ip = re_ip_letters.sub('', ip.group(0))
    else:
        ret_ip = None
    
    return ret_time, ret_ip, ret_domain



def split_date_weekday_time(data):
    #21/01/24(日)20:47:07
    date = re_date.search(data)
    weekday = re_weekday.search(data)
    time = re_time.search(data)

    if date:
        ret_date = date.group(0)
    else:
        ret_date = None
    
    if weekday:
        ret_weekday = weekday.group(0)
    else:
        ret_weekday = None
    
    if time:
        ret_time = time.group(0)
    else:
        ret_time = None
    
    return ret_date, ret_weekday, ret_time




def convert_soudane(data):
    ret = 0
    chk = re_numbers.search(data)
    if chk:
        ret = int(chk.group(0))
    return ret



def convert_res_id(data):
    ret = 0
    chk = re_numbers.search(data)
    if chk:
        ret = int(chk.group(0))
    return ret



def check_res_ip(soup):
    data = soup.select('blockquote font[color="#ff0000"]')
    if not data :
        return None
    
    data = data[0].get_text()
    chk = re_res_ip.search(data)
    
    if chk:
        return chk.group(0)
    else:
        return None
    return



def convert_res(data):
    ret = data
    ret = re_link.sub('', ret)
    ret = re_res_ip_reform.sub(r'[\1]', ret)
    return ret
    


def convert_to_futaba_res_dict(
    url='',
    thread_number='0',
    thread_title='',
    number='0',
    munen='無念',
    name='としあき',
    timestamp='00/01/01(月) IP:000.000.*(xxx.com)',
    res_id='0',
    soudane='+',
    res=''):
    
    ret = FUTABA_RESPONSE_TEMPLATE.copy()
    ret['url'] = url
    ret['thread_number'] = int(thread_number)
    ret['thread_title'] = thread_title
    ret['number'] = int(number)
    ret['munen'] = munen
    ret['name'] = name

    dtm, ip, domain = split_time_ip_domain(timestamp)
    date, weekday, time = split_date_weekday_time(dtm)

    ret['date'] = date
    ret['weekday'] = weekday
    ret['time'] = time
    ret['ip'] = ip
    ret['domain'] = domain
    
    ret['res_id'] = convert_res_id(res_id)
    ret['soudane'] = convert_soudane(soudane)
    ret['res'] = convert_res(res)
    return ret



def split_thread_meta(soup):
    thread_title = soup.select('title')[0].get_text()
    thread_number = soup.select('span.thre')[0]['data-res']
    return thread_title, thread_number



def split_thread_dominus(soup):
    dom_munen = soup.select('span.csb')[0].get_text()
    dom_name = soup.select('span.cnm')[0].get_text()
    dom_time = soup.select('span.cnw')[0].get_text()
    dom_number = soup.select('span.cno')[0].get_text()
    dom_sod = soup.select('a.sod')[0].get_text()
    dom_content = soup.select('blockquote')[0].get_text('\n')
    return dom_munen, dom_name, dom_time, dom_number, dom_sod, dom_content



def split_thread_res(res):
    res_count = res.select('span.rsc')[0].get_text()
    res_munen = res.select('span.csb')[0].get_text()
    res_name = res.select('span.cnm')[0].get_text()
    res_time = res.select('span.cnw')[0].get_text()
    res_number = res.select('span.cno')[0].get_text()
    res_sod = res.select('a.sod')[0].get_text()
    res_content = res.select('blockquote')[0].get_text('\n')
    return res_count, res_munen, res_name, res_time, res_number, res_sod, res_content



def is_contains_word(res, word):
    return word.lower() in res.lower()

def is_res_in_range(res, fore=None, apre=None):
    if fore == apre:
        if res == fore:
            return True
        else:
            return False
    elif fore and apre:
        if res >= fore and res <= apre:
            return True
        else:
            return False
    elif not fore and apre:
        if res <= apre:
            return True
        else:
            return False
    elif fore and not apre:
        if res >= fore:
            return True
        else:
            return False
    else:
        return True



def is_res_matched_re(res, word):
    ret = re.search(word, res)
    if ret:
        return True
    else:
        return False




#filt=(mode, fore, apre)
def filter_range(res, filt):
    return is_res_in_range(res, filt[1], filt[2])


#連言
def filter_res(res, filt):
    for key, value in filt.items():
        if condition_handler[CONDITION_METHOD[value[0]]](res[key], value) == False:
            return False
    
    return True



#filt=(mode, words, isReg)
def filter_free_word(res, filt):
    if filt[2] == True:
        return is_res_matched_re(res, filt[1])
    else:
        #print(str(filt[0]) + str(filt[1]) + str(filt[2]))
        for x in filt[1].split():
            if is_contains_word(res, x) == False:
                return False
        return True




condition_handler = [
    None,
    filter_free_word,
    filter_range
]






def load_thread_dict(filename):
    with open(filename, 'rb') as f:
        ret = pickle.load(f)
    return ret
    


def set_list_to_write(thread, url, to_write):
    soup = BeautifulSoup(thread, 'html.parser')
    thread_title, thread_number = split_thread_meta(soup)

    dom_munen, dom_name, dom_time, dom_number, dom_sod, dom_content = split_thread_dominus(soup)

    dom = convert_to_futaba_res_dict(
        url,
        thread_number,
        thread_title,
        '0',
        dom_munen,
        dom_name,
        dom_time,
        dom_number,
        dom_sod,
        dom_content
        )
    chk = check_res_ip(soup)
    if chk:
        dom['ip'] = chk
   
    to_write.append(dom)

    reses = [s for s in soup.select('td.rtd')]
    for res in reses:
        res_count, res_munen, res_name, res_time, res_number, res_sod, res_content = split_thread_res(res)

        res_dict = convert_to_futaba_res_dict(
            url,
            thread_number,
            thread_title,
            res_count,
            res_munen,
            res_name,
            res_time,
            res_number,
            res_sod,
            res_content
            )
        chk = check_res_ip(res)
        if chk:
            res_dict['ip'] = chk
        
        to_write.append(res_dict)
    
    return



def write_thread_dict(filename, to_write):
    with open(filename, 'wb') as f:
        pickle.dump(to_write, f)
    return



def write_csv(result_filename, to_write):
    with open(result_filename, 'w', errors='xmlcharrefreplace') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerows([x.values() for x in to_write])



def extract_ftbucket_zip(filename):
    with zipfile.ZipFile(filename) as log:
        log_list = log.namelist()
        log_index = [s for s in log_list if(r'index.htm' in s and r'gz' not in s)][0]
        with log.open(log_index) as log_content:
            ret = log_content.read()
    return ret



def fetch_html_file(filename):
    with open(filename, 'r') as f:
        ret = f.read()
    return ret
