from bs4 import BeautifulSoup
import zipfile
import glob
import os
import re
import csv
import pickle
import datetime 
import requests

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
    

#ふたばログそのまんま。
#Shift_JIS, HTMLの書き換えなし
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
###-----------

###--------------
#いっそクラス化しちゃえ
class Scraper():
    def __init__(self):
        self.re_date = re.compile(r'(\d\d)/(\d\d)/(\d\d)')
        self.re_time = re.compile(r'(\d\d):(\d\d):(\d\d)')
        self.re_weekday = re.compile(r'[日月火水木金土]')
        self.re_ip = re.compile(r'IP:([0-9a-fA-F]+[\.:])+\*?')
        self.re_domain = re.compile(r'\([0-9a-zA-Z\-\.]+\)')
        self.re_ip_letters = re.compile(r'IP:')
        self.re_brace = re.compile(r'[\(\)]')
        self.re_numbers = re.compile(r'\d+')
        self.re_link = re.compile(r'\[\nlink\n\]')
        self.re_res_ip = re.compile(r'([0-9a-fA-F]+[\.:]?)+')
        self.re_res_ip_reform = re.compile(r'\[\n(([0-9a-fA-F]+[\.:]?)+)\n]')

        self.FUTABA_RESPONSE_TEMPLATE = {
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

        #魚拓サイトごとのパーサーを用意しとくよ！
        self.scrapParser = {
            'archive.today': ArchiveTodayParser(),
            'FTBucket': FtbucketParser()
        }

    #サイトもこっちで判別しようか
    def scrap_thread(self, thread, url, to_write):
        soup = BeautifulSoup(thread, 'html.parser') #ギュッと珍獣あきの汚ねースープを出すよ！
        site = self.check_site(soup) #スープで判別できるといいなあ

        thread_title = self.scrapParser[site].get_thread_title(soup)
        thread_number = self.scrapParser[site].get_thread_number(soup)

        #スレ主のデータ
        munen, name, timestamp, res_id, soudane, res, res_ip = self.scrapParser[site].get_thread_dominus(soup)

        #パックして詰める        
        self.pack_futaba_res_dict(to_write, url, thread_number, thread_title, '0', munen, name, timestamp, res_id, soudane, res, res_ip)

        #子レスリストをゲット
        children  = []
        self.scrapParser[site].get_thread_child_list(soup, children)

        #ぶんまわす
        for child in children:
            number, munen, name, timestamp, res_id, soudane, res, res_ip = self.scrapParser[site].get_thread_child(child)
            #パックして詰める        
            self.pack_futaba_res_dict(to_write, url, thread_number, thread_title, number, munen, name, timestamp, res_id, soudane, res, res_ip)
        
        #おしまい


    #ソースから抜いてきたやつを辞書にまとめてリストイン
    def pack_futaba_res_dict(
        self,
        to_write,
        url,
        thread_number,
        thread_title,
        number,
        munen,
        name,
        timestamp,
        res_id,
        soudane,
        res,
        res_ip
        ):

        #タイムスタンプ分解
        date, weekday, time, ip, domain = self.split_timestamp(timestamp)

        #レス内IPが存在してタイムスタンプのIPと重なってたらIP書き換え
        #ねんのために小文字化しとく(in はケースセンシティブ)
        #文末ピリオド(ipv6はコロン)、アスタリスクに注意
        if res_ip:
            if ip.replace('.*', '').lower() in res_ip.lower():
                ip = res_ip

        #dictにパックして詰める
        to_write.append(self.get_futaba_res_dict(
            url,
            thread_number,
            thread_title,
            number,
            munen,
            name,
            date,
            weekday,
            time,
            ip,
            domain,
            self.get_res_id(res_id),
            self.get_soudane(soudane),
            self.reform_res(res)
        ))


    #scrapParser のキーを返してね
    #megalodonはフレームになってるのでhttps://megalodon/... を https://megalodon/ref/... にしてください
    def check_site(self, soup):
        
        chk = soup.select('head meta[property="og:site_name"]')
        if chk:
            if 'archive.' in chk[0]['content']:
                return 'archive.today' #ヘッダーのメタに'archive.*'が含まれてたらとりあえずarchive.today

        #よくわかんないので汎用のftbucket返しとく
        return 'FTBucket'


    #そうだね数
    def get_soudane(self, text):
        ret = self.re_numbers.search(text)
        if ret:
            return ret.group(0)
        else:
            return '0'

    #No.xxxxxx.. のやつ
    def get_res_id(self, text):
        ret = self.re_numbers.search(text)
        if ret:
            return ret.group(0)
        else:
            return ''

    #レスのテキスト整形
    def reform_res(self, text):
        ret = text
        ret = re_link.sub('', ret) #[link]を消す
        ret = re_res_ip_reform.sub(r'[\1]', ret) #ip部分の表示を整形
        return ret


    #タイムスタンプ分割
    def split_timestamp(self, text):
        ret_date = self.re_date.search(text)
        ret_time = self.re_time.search(text)
        ret_weekday = self.re_weekday.search(text)
        ret_ip = self.re_ip.search(text)
        ret_domain = self.re_domain.search(text)

        if ret_date:
            date = ret_date.group(0)
        else:
            date = ''
        
        if ret_time:
            time = ret_time.group(0)
        else:
            time = ''

        if ret_weekday:
            weekday = ret_weekday.group(0)
        else:
            weekday = ''

        if ret_ip:
            ip = re_ip_letters.sub('', ret_ip.group(0))
        else:
            ip = ''

        if ret_domain:
            domain = re_brace.sub('', ret_domain.group(0))
        else:
            domain = ''
        return date, weekday, time, ip, domain


    #ふたばレス辞書にまとめる
    def get_futaba_res_dict(self,
        url='',
        thread_number='0',
        thread_title='',
        number='0',
        munen='無念',
        name='としあき',
        date='00/01/01',
        weekday='月',
        time='00:00:00',
        ip='000.000.*',
        domain='xxx.com',
        res_id='0',
        soudane='0',
        res=''
        ):
            
        ret = self.FUTABA_RESPONSE_TEMPLATE.copy()
        ret['url'] = url
        ret['thread_number'] = thread_number
        ret['thread_title'] = thread_title
        ret['number'] = number
        ret['munen'] = munen
        ret['name'] = name
        ret['date'] = date
        ret['weekday'] = weekday
        ret['time'] = time
        ret['ip'] = ip
        ret['domain'] = domain
        ret['res_id'] = res_id
        ret['soudane'] = soudane
        ret['res'] = res
        return ret



#生のソースから情報抜くところは別にクラス化
class ScrapParser():
    def __init__(self):
        self.re_res_ip = re.compile(r'([0-9a-fA-F]+[\.:]?)+')

        pass

    def get_thread_title(self, soup):
        pass

    def get_thread_number(self, soup):
        pass

    #return  munen, name, timestamp, res_id(=thread number), soudane, res, res_ip
    def get_thread_dominus(self, soup):
        pass
    
    #return number, munen, name, timestamp, res_id, soudane, res, res_ip
    def get_thread_child(self, soup):
        pass

    #return child list
    #reses.append()してね
    def get_thread_child_list(self, soup, children):
        pass

    #ここはレス部分のスープを渡す
    def get_res_ip(self, soup):
        pass


class FtbucketParser(ScrapParser):
    def __init__(self):
        super().__init__()
    
    def get_thread_title(self, soup):
        return soup.select('title')[0].get_text()
    
    def get_thread_number(self, soup):
        return soup.select('.thre')[0]['data-res']
    
    def get_thread_dominus(self, soup):
        munen = soup.select('span.csb')[0].get_text()
        name = soup.select('span.cnm')[0].get_text()
        timestamp = soup.select('span.cnw')[0].get_text()
        res_id = soup.select('span.cno')[0].get_text()
        soudane = soup.select('a.sod')[0].get_text()
        res = soup.select('blockquote')[0].get_text('\n')

        #レス部分のIPもチェック
        res_ip = self.get_res_ip(soup.select('blockquote')[0])

        return munen, name, timestamp, res_id, soudane, res, res_ip
    
    def get_thread_child(self, soup):
        number = soup.select('span.rsc')[0].get_text()
        munen = soup.select('span.csb')[0].get_text()
        name = soup.select('span.cnm')[0].get_text()
        timestamp = soup.select('span.cnw')[0].get_text()
        res_id = soup.select('span.cno')[0].get_text()
        soudane = soup.select('a.sod')[0].get_text()
        res = soup.select('blockquote')[0].get_text('\n')

        #レス部分のIPもチェック
        res_ip = self.get_res_ip(soup.select('blockquote')[0])

        return number, munen, name, timestamp, res_id, soudane, res, res_ip
    
    def get_thread_child_list(self, soup, children):
        for child in soup.select('td.rtd'):
            children.append(child)

    def get_res_ip(self, soup):
        chk = soup.select('font[color="#ff0000"]')
        if not chk:
            return None
    
        ret = self.re_res_ip.search(chk[0].get_text())

        if ret:
            return ret.group(0)
        else:
            return None

    

# archive.today用
# スレ番号がない？(spna.thre の data-res 属性)
# 方法1: スレ主のレス番号をスレ番号にする
# #    ret = re.search(r'\d+', soup.select('span[old-class^="cno"]')[0].get_text())
# 方法2: 空欄にしちゃう
# 方法3:div[old-class="thre"] span[id="delcheckxxxxxxxx"](1番目)を使う

class ArchiveTodayParser(ScrapParser):
    def __init__(self):
        super().__init__()



    def get_thread_title(self, soup):
        thread_title = soup.select('title')[0].get_text()
        return thread_title



    def get_thread_number(self, soup):
        thread_number = soup.select('div[old-class="thre"] span')[0]['id']
        return thread_number.replace('delcheck', '')



    def get_thread_dominus(self, soup):
        munen = soup.select('div[old-class="thre"] span[old-class="csb"]')[0].get_text()
        name = soup.select('div[old-class="thre"] span[old-class="cnm"]')[0].get_text()
        timestamp = soup.select('div[old-class="thre"] span[old-class="cnw"]')[0].get_text()
        res_id = soup.select('div[old-class="thre"] span[old-class="cno"] a')[0].get_text()
        soudane = soup.select('div[old-class="thre"] a[old-class="sod"]')[0].get_text()
        res = soup.select('div[old-class="thre"] blockquote')[0].get_text('\n')
        res_ip = self.get_res_ip(soup.select('div[old-class="thre"] blockquote')[0])
        return munen, name, timestamp, res_id, soudane, res, res_ip



    def get_thread_child(self, soup):
        number = soup.select('span[old-class="rsc"]')[0].get_text()
        munen = soup.select('span[old-class="csb"]')[0].get_text()
        name = soup.select('span[old-class="cnm"]')[0].get_text()
        timestamp = soup.select('span[old-class="cnw"]')[0].get_text()
        res_id = soup.select('span[old-class="cno"] a')[0].get_text()
        soudane = soup.select('a[old-class="sod"]')[0].get_text()
        res = soup.select('blockquote')[0].get_text('\n')
        res_ip = self.get_res_ip(soup.select('blockquote')[0])
        return number, munen, name, timestamp, res_id, soudane, res, res_ip




    def get_thread_child_list(self, soup, children):
        for child in soup.select('div[old-class="thre"] table td[old-class="rtd"]'):
            children.append(child)



    def get_res_ip(self, soup):
        chk = soup.select('font[color="#ff0000"]')
        
        if not chk:
            return
        
        chk = self.re_res_ip.search(chk[0].get_text())

        if chk:
            return chk.group(0)
        else:
            return None


###------------

#Scraper用のスレッドデータを取り出します
class Fetcher():
    def __init__(self):
        self.fetch = {
            'URL': self.url,
            'megalodon': self.megalodon,
            'localfile': self.localfile,
            'FTBucket Zip': self.ftbucket_zip
        }

    def fetch_thread(self, address, is_url=False, is_ftbucket_zip=False):
        if is_url == True:
            if '//megalodon.jp/' in address:
                return self.fetch['megalodon'](address)
            else:
                return self.fetch['URL'](address)
        else:
            if is_ftbucket_zip == True:
                return self.fetch['FTBucket Zip'](address)
            return self.fetch['localfile'](address)                


    def url(self, url):
        res = requests.get(url)
        res.encoding = res.apparent_encoding #これいれないと文字化けします！！！
        return res.text



    def megalodon(self, url):
        res = requests.get(url.replace('//megalodon.jp/', '//megalodon.jp/ref/'))
        res.encoding = res.apparent_encoding #これいれないと文字化けします！！！
        return res.text



    def localfile(self, filename):
        with open(filename, 'r') as f:
            ret = f.read()
        return ret
        


    def ftbucket_zip(self, filename):
        with zipfile.ZipFile(filename) as log:
            log_list = log.namelist()
            log_index = [s for s in log_list if(r'index.htm' in s and r'gz' not in s)][0]
            with log.open(log_index) as log_content:
                ret = log_content.read()
        return ret
    


#--------------
# 検索用

class Searcher():
    def __init__(self, box=None):
        self.searchbox = {
            'default': SimpleSearch()
        }

        self.settings = {
            'isIgnoreCharacter' : False,
            'ignoreCharacter': '/ .'
        }

        self.search_type = {
            'free word': self.filter_free_word,
            'range': self.filter_range,
            'reg word': self.filter_reg_word
        }

        if box:
            self.box = box
        else:
            self.box = 'default'



    def filter_range(self, text, filt):
        return self.searchbox[self.box](text, filt[1], filt[2])



    #filt_dict = {
    # res_key: (search_type, filter_fore, filter_apre)}
    #
    #filt = (search_type, filter_fore, filter_apre)
    #
    def filter(self, resitem, filt_dict):
        for key, value in filt_dict.items():
            if self.search_type[value[0]](resitem[key], value) == False:
                return False
        return True



    def filter_free_word(self, text, filt):
        for word in filt[1].split():
            if self.searchbox[self.box].is_contains_word(text, word) == False:
                return False
        return True

    

    def filter_reg_word(self, text, filt):
        return self.searchbox[self.box].is_re_search(text, filt[1])



class SearchBox():
    def __init__(self):
        pass

    def is_in_range(self, res, fore=None, apre=None):
        pass

    def is_re_search(self, text, reg_text):
        pass

    def is_contains_word(self, text, word):
        pass



class SimpleSearch(SearchBox):
    def __init__(self):
        super().__init__()



    def is_in_range(self, res, fore=None, apre=None):
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



    def is_re_search(self, text, reg_text):
        ret = re.search(reg_text, text)
        if ret:
            return True
        else:
            return False



    def is_contains_word(self, text, word):
        return word.lower() in text.lower()



class QueryParser():
    def __init__(self):
        pass


#-------------
class Writer():
    def __init__(self):
        pass

    def write_to_pickle(self, filename, to_write):
        with open(filename, 'wb') as f:
            pickle.dump(to_write, f)
        return
    


    def write_to_csv(self, filename, to_write):
        with open(filename, 'w', errors='xmlcharrefreplace') as f:
            csv.writer(f, lineterminator='\n').writerows([x.values() for x in to_write])


class Loader():
    def __init__(self):
        pass

    def load_pickle(self, filename, to_load):
        with open(filename, 'rb') as f:
            ret = pickle.load(f)
            if isinstance(ret, list):
                for x in ret:
                    to_load.append(x)
            else:
                pass #エラー処理
    
    def load_csv(self, filename, to_load):
        pass


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


def get_url_data(url):
    #data = requests.get(url)
    data = requests.post(url)
    return data
