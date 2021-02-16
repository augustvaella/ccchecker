import PySimpleGUI as sg
import ccchecker as cc
import os
import configparser
import re

# Chiki Chiki Checker GUI


# Widget 暫定ルール
# key を '(Widget Name) (Part Name)'として、空白で区切る
# 将来的にはkeyを動的に変更してメッセージをやりとりできるかも？
# →できない、keyを変更すると外部から操作できない(window[key].update()など)

STR_TO_BOOL = {'False': False, 'True': True, 'None': None}
GUI_MESSAGE_SPLIT_CHARACTER = '-'
CONDITION_RANGE_SELECT = ['のみ', 'から', '以上', '以下']

CONFIG_INI_PATH = 'config.ini'
is_config_ini_initialized = False


PROGRESS_BAR_SIZE = (50, 20)



def remove_emptyline(text):
    ret = re.sub(r'^\n+', r'', text)
    filelist_string = re.sub(r'^\s+', r'', text)
    filelist_string = re.sub(r'\n[\n\s]*', r'\n', text)
    return ret

class Key():
    def __init__(self, name):
        self.name = name

    def key(self, part_name, name=None):
        if name is None:
            name = self.name
        return name + GUI_MESSAGE_SPLIT_CHARACTER + part_name

    def split_key(self, key):
        key_split = key.split(GUI_MESSAGE_SPLIT_CHARACTER)
        return key_split[0], key_split[1]




class Widget():
    def __init__(self, name, messenger=None):
        self.name = name
        self.handler = {}
        self.messenger = messenger
        self.__key = Key(self.name)
        self.handler = {
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close,
            'initializeConfig': self.on_initialize_config
        }

    def activate(self):
        pass
    def deactivate(self):
        pass

    def load_config(self, config, section, option):
        if config.has_section(section) and config.has_option(section, option):
            return config.get(section, option)
        else:
            return None

    def save_config(self, config, section, option, value):
        if not config.has_section(section):
            config.add_section(section)

        config.set(section, option, value)
    
    def check_config(self, config, section, lst):
        for x in lst:
            if self.load_config(config, section, self.key(x)) is None:
                self.initialize_config(config)
                return

    def initialize_config(self, config):
        pass

    def create(self):
        lyt = []
        return lyt

    def key(self, part_name, name=None):
        return self.__key.key(part_name, name)

    def split_key(self, key):
        return self.__key.split_key(key)

    #the message come from Messenger
    #part_nameでいろいろできるかも？
    def receive_message(self, message):
        #print(message)
        name, part_name = self.split_key(message['key']) #自分宛て
        if name == self.name: #通常のメッセージ
            self.handler[part_name](message)
        elif name == 'Messenger': #メッセンジャーからの特別なメッセージ
            self.handler[part_name](message)

    def on_window_close(self, message):
        pass

    def on_window_finalized(self, message):
        pass

    def on_initialize_config(self, message):
        pass

    def dummy(self, message):
        pass



class FileListWidget(Widget):
    def __init__(self, name,
     messenger = None,
     tab_text='',
     file_types=(('全てのファイル', '*.*'),),
     is_local_file=True,
     file_types_list=(('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))
     ):
        super().__init__(name, messenger=messenger)
        self.tab_text = tab_text

        self.handler['clear'] = self.clear_list
        self.handler['add'] = self.add_to_list
        self.handler['addlistfile'] = self.add_list_to_list
        self.handler['output'] = self.output_list
        self.handler['list'] = self.touch_list

        self.file_types = file_types
        self.is_local_file = is_local_file
        self.file_types_list = file_types_list
        self.listfile_path = self.name + 'list'
    
    def create(self):
        lyt = sg.Tab(
            self.tab_text,
            [
                [sg.Multiline(
                    key=self.key('list'),
                    enable_events=True,
                    auto_refresh=True
                    )
                ],
                [sg.Column([[sg.Button('クリア', key=self.key('clear'))]]),
                sg.Column([[sg.Button('追加', key=self.key('add'), enable_events=True)]]),
                sg.Column([[sg.Button('追加(リストファイル)', key=self.key('addlistfile'), enable_events=True)]]),
                sg.Column([[sg.Button('リストをファイルに書き出す', key=self.key('output'), enable_events=True)]])
                ]
            ]
        )

        return lyt

    def touch_list(self, message):
        pass
    
    def clear_list(self, message):
        window = message['window']
        if sg.popup_yes_no('リストをクリアしますか？') == 'Yes':
            window[self.key('list')].update('')
        pass

    #self.is_local_file == Trueならローカルファイル、さもなくばURL
    #暫定措置、ほかのモードが欲しければ拡張
    def add_to_list(self, message):
        key = self.key('list')
        window = message['window']
        values = message['values']

        if self.is_local_file == True:
            ret = sg.popup_get_file('追加するファイルの選択:', multiple_files=True, modal=True, file_types=self.file_types)

            if not ret:
                return
            
            lst = ret.split(sg.BROWSE_FILES_DELIMITER)
            if values[key] == '\n' or values[key] == '':
                window[key].update(re.sub(r'^\n', '', '\n'.join(lst)))
            else:
                window[key].update(values[key] + '\n'.join(lst))

        else:
            ret = sg.popup_get_text('追加するURLの入力:', modal=True)

            if not ret:
                return
            
            if values[key] == '\n' or values[key] == '':
                window[key].update(re.sub(r'^\n', '', ret))
            else:
                window[key].update(values[key] + ret)



    def add_list_to_list(self, message):
        key = self.key('list')
        window = message['window']
        values = message['values']

        ret = sg.popup_get_file('リストファイルの選択:', multiple_files=False, modal=True, file_types=self.file_types_list)
        if not ret:
            return
        if os.path.isfile(ret) == False:
            return
        
        #エンコード問題はなんとかしないと
        try:
            with open(ret, 'r', encoding='utf-8') as f:
                lst = f.read()
        except UnicodeDecodeError as e:
            sg.popup_error('ファイルを開けません。選択したファイルがUTF-8でエンコードされているか確認してください。', e)
        else:
            if values[key] == '\n' or values[key] == '':
                window[key].update(re.sub(r'^\n', '', lst))
            else:
                window[key].update(values[key] + lst)
        

    def initialize_list(self):
        pass

    def expand_list_widget(self, message):
        key = self.key('list')
        window = message['window']

        window[key].expand(True, True)




    def output_list(self, message):
        key = self.key('list')
        window = message['window']
        values = message['values']

        ret = sg.popup_get_file('書き出すリストファイルの選択:', save_as=True, multiple_files=False, modal=True, file_types=self.file_types_list)
        if not ret:
            return
        
        try:
            with open(ret, 'w', encoding='utf-8') as f:
                f.write(values[key])
        except PermissionError as e:
            sg.popup_error('ファイルを書き込めません。パーミッションエラーです:', e)
        else:
            sg.popup('ファイルを書き出しました')



    def get_listfile_to_initialize(self):
        pass

    def on_window_finalized(self, message):
        window = message['window']
        values = message['values']

        default_list = ''
        if os.path.isfile(self.listfile_path) == False:
            try:
                with open(self.listfile_path, 'w', encoding='utf-8') as f:
                    f.write('\n')
            except PermissionError as e:
                sg.popup_error('保存用の設定ファイルを書き込めません。パーミッションエラーです。', e)
        else:
            try:
                with open(self.listfile_path, 'r', encoding='utf-8') as f:
                    default_list = f.read()
            except PermissionError as e:
                sg.popup_error('保存用の設定ファイルを読み込めません。パーミッションエラーです。', e)
        
        window[self.key('list')].update(default_list)
        self.expand_list_widget(message)
    
    def on_window_close(self, message):
        window = message['window']
        values = message['values']

        try:
            with open(self.listfile_path, 'w', encoding='utf-8') as f:
                f.write(values[self.key('list')])
        except PermissionError as e:
            sg.popup_error('保存用の設定ファイルを書き込めません。パーミッションエラーです。', e)
    
    def on_initialize_config(self, config):
        pass



class InputStringWidget(Widget):
    def __init__(self, name, messenger = None):
        super().__init__(name, messenger=messenger)
        self.handler['isActive'] = self.on_is_active
        self.handler['input'] = self.on_input
        self.handler['reg'] = self.on_reg


    def create(self):
        lyt = [
            sg.Checkbox(
                '',
                key=self.key('isActive'),
                enable_events=True
                ),
            sg.InputText(
                '',
                key=self.key('input'),
                size=CONDITION_INPUT_SINGLE,
                enable_events=True,
                tooltip=TOOLTIP_COND[0],
                disabled=True
                ),
            sg.Checkbox(
                '正規表現',
                key=self.key('reg'),
                disabled=True
                )]

        return lyt



    def on_is_active(self, message):
        key = self.key('isActive')
        window = message['window']
        values = message['values']

        if values[key] == True:
            self.activate_input(message)
        else:
            self.deactivate_input(message)



    def activate_input(self, message):
        window = message['window']
        values = message['values']

        window[self.key('input')].update(disabled=False)
        window[self.key('reg')].update(disabled=False)



    def deactivate_input(self, message):
        window = message['window']
        values = message['values']

        window[self.key('input')].update(disabled=True)
        window[self.key('reg')].update(disabled=True)



    def on_input(self, message):
        pass

    def on_reg(self, message):
        pass

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.check_config(config, 'Widget', ['isActive', 'input', 'reg'])

        ret = STR_TO_BOOL[self.load_config(config, 'Widget', self.key('isActive'))]
        window[self.key('isActive')].update(ret)
        if ret:
            self.activate_input(message)

        window[self.key('input')].update(self.load_config(config, 'Widget', self.key('input')))
        window[self.key('reg')].update(STR_TO_BOOL[self.load_config(config, 'Widget', self.key('reg'))])

    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.save_config(config, 'Widget', self.key('isActive'), str(values[self.key('isActive')]))
        self.save_config(config, 'Widget', self.key('input'), str(values[self.key('input')]))
        self.save_config(config, 'Widget', self.key('reg'), str(values[self.key('reg')]))

    def on_initialize_config(self, message):
        self.initialize_config(message['config'])
    
    def initialize_config(self, config):
        self.save_config(config, 'Widget', self.key('isActive'), 'False')
        self.save_config(config, 'Widget', self.key('input'), '')
        self.save_config(config, 'Widget', self.key('reg'), 'False')
        


class InputNumberWidget(Widget):
    def __init__(self, name, messenger=None, input_type='number'):
        super().__init__(name, messenger=messenger)
        self.handler['isActive'] = self.on_is_active
        self.handler['input_fore'] = self.on_input_fore
        self.handler['input_apre'] = self.on_input_apre
        self.handler['button_fore'] = self.on_button_fore
        self.handler['button_apre'] = self.on_button_apre
        self.handler['range'] = self.on_range

        self.input_handler = {
            'number': self.input_number,
            'date': self.input_date,
            'time': self.input_time
        }

        self.input_type = input_type
        self.re_date = re.compile(r'(\d\d)/(\d\d)/(\d\d)')
        self.re_time = re.compile(r'(\d\d):(\d\d):(\d\d)')



    def create(self):
        lyt = [
            sg.Checkbox(
                '',
                key=self.key('isActive'),
                enable_events=True
                ),
            sg.InputText(
                '',
                key=self.key('input_fore'),
                size=(15, 1),
                enable_events=True,
                #tooltip=TOOLTIP_COND[0],
                disabled=True
                ),
            sg.Button(
                '変更',
                key=self.key('button_fore'),
                enable_events=True,
                disabled=True
                ),
            sg.Combo(
                CONDITION_RANGE_SELECT,
                CONDITION_RANGE_SELECT[0],
                size=(4,1),
                enable_events=True,
                key=self.key('range'),
                readonly=True
                ),
            sg.InputText(
                '',
                key=self.key('input_apre'),
                size=(15, 1),
                enable_events=True,
                #tooltip=TOOLTIP_COND[0],
                disabled=True
                ),
            sg.Button(
                '変更',
                key=self.key('button_apre'),
                enable_events=True,
                disabled=True
                )
            ]

        return lyt



    def on_is_active(self, message):
        key = self.key('isActive')
        window = message['window']
        values = message['values']

        if values[key] == True:
            self.activate_input(message)
        else:
            self.deactivate_input(message)



    def activate_input(self, message):
        window = message['window']
        values = message['values']

        window[self.key('button_fore')].update(disabled=False)
        window[self.key('button_apre')].update(disabled=False)



    def deactivate_input(self, message):
        window = message['window']
        values = message['values']

        window[self.key('button_fore')].update(disabled=True)
        window[self.key('button_apre')].update(disabled=True)

    def input_number(self, message, input_part_name):
        window = message['window']
        values = message['values']

        while True:
            ret = sg.popup_get_text('数字を入力してください:', default_text=values[input_part_name])
            if ret is None:
                break
            elif not ret:
                window[input_part_name].update('')
                break
            elif ret.isdecimal() == True:
                window[input_part_name].update(ret)
                break

    def input_date(self, message, input_part_name):
        window = message['window']
        values = message['values']

        if values[input_part_name]:
            year, month, day = self.get_date_split(values[input_part_name])
            if month:
                ret = sg.popup_get_date(month, day, year)
            else:
                ret = sg.popup_get_date()
        else:
            ret = sg.popup_get_date()
        if ret:
            window[input_part_name].update(self.get_reformed_date(ret[2], ret[0], ret[1]))



    def input_time(self, message, input_part_name):
        window = message['window']
        values = message['values']

        while True:
            ret = sg.popup_get_text('hh:mm:ssの形式で時刻を入力してください:', default_text=values[input_part_name])
            if ret is None:
                break
            elif self.get_time(ret):
                window[input_part_name].update(ret)
                break

    def get_reformed_date(self, year, month, day, split_character='/'):
        return str(year).zfill(2)[-2:] + split_character + str(month).zfill(2) + split_character + str(day).zfill(2)

    def is_date(self, year, month, day):
        return (year >= 0 and year <= 99 and month >= 1 and month <= 12 and day >= 1 and day <= 31)

    def is_time(self, hour, minute, second):
        return (hour >= 0 and hour <= 23 and minute >= 0 and minute <= 59 and second >= 0 and second <= 59)

    def get_date(self, text):
        dt = self.re_date.search(text)
        if dt:
            if self.is_date(int(dt.group(1)), int(dt.group(2)), int(dt.group(3))):
                return dt.group(0)
            else:
                return None
        else:
            return None

    def get_date_split(self, text):
        dt = self.re_date.search(text)
        if dt:
            if self.is_date(int(dt.group(1)), int(dt.group(2)), int(dt.group(3))):
                return int(dt.group(1)), int(dt.group(2)), int(dt.group(3))
            else:
                return None
        else:
            return None

    def get_time(self, text):
        dt = self.re_time.search(text)
        if dt:
            if self.is_time(int(dt.group(1)), int(dt.group(2)), int(dt.group(3))):
                return dt.group(0)
            else:
                return None
        else:
            return None

    def get_time_split(self, text):
        dt = self.re_time.search(text)
        if dt:
            if self.is_time(int(dt.group(1)), int(dt.group(2)), int(dt.group(3))):
                return int(dt.group(1)), int(dt.group(2)), int(dt.group(3))
            else:
                return None
        else:
            return None



    def on_input_fore(self, message):
        pass

    def on_input_apre(self, message):
        pass

    def on_button_fore(self, message):
        self.input_handler[self.input_type](message, self.key('input_fore'))

    def on_button_apre(self, message):
        self.input_handler[self.input_type](message, self.key('input_apre'))
         

    def on_range(self, message):
        pass

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.check_config(config, 'Widget', ['isActive', 'input_fore', 'input_apre', 'range'])
        ret = STR_TO_BOOL[self.load_config(config, 'Widget', self.key('isActive'))]
        window[self.key('isActive')].update(ret)
        if ret:
            self.activate_input(message)

        window[self.key('input_fore')].update(self.load_config(config, 'Widget', self.key('input_fore')))
        window[self.key('input_apre')].update(self.load_config(config, 'Widget', self.key('input_apre')))
        window[self.key('range')].update(self.load_config(config, 'Widget', self.key('range')))

    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.save_config(config, 'Widget', self.key('isActive'),  str(values[self.key('isActive')]))
        self.save_config(config, 'Widget', self.key('input_fore'), values[self.key('input_fore')])
        self.save_config(config, 'Widget', self.key('input_apre'), values[self.key('input_apre')])
        self.save_config(config, 'Widget', self.key('range'), values[self.key('range')])

    def on_initialize_config(self, message):
        self.initialize_config(message['config'])
    
    def initialize_config(self, config):
        self.save_config(config, 'Widget', self.key('isActive'),  'False')
        self.save_config(config, 'Widget', self.key('input_fore'), '')
        self.save_config(config, 'Widget', self.key('input_apre'), '')
        self.save_config(config, 'Widget', self.key('range'), CONDITION_RANGE_SELECT[0])



class OutputFilenameWidget(Widget):
    def __init__(
        self,
        name,
        messenger=None,
        file_types=(('CSVファイル', '*.csv'), ('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))
        ):
        super().__init__(name, messenger=messenger)
        self.file_types = file_types
        self.handler['browse'] = self.on_browse
        self.handler['filename'] = self.on_filename

    def on_filename(self, message):
        pass

    def on_browse(self, message):
        pass

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.check_config(config, 'Widget', ['filename'])

        window[self.key('filename')].update(self.load_config(config, 'Widget', self.key('filename')))



    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.save_config(config, 'Widget', self.key('filename'), values[self.key('filename')])


    def on_initialize_config(self, message):
        self.initialize_config(message['config'])

    def initialize_config(self, config):
        self.save_config(config, 'Widget', self.key('filename'), '')


    def create(self):
        lyt = [
            sg.Text('保存用CSVファイル名'), 
            sg.Input('', enable_events=True, key=self.key('filename')),
            sg.FileSaveAs('参照', key=self.key('browse'), file_types=self.file_types)
            ]

        return lyt



class OKAndExitWidget(Widget):
    def __init__(self, name, messenger=None):
        super().__init__(name, messenger=messenger)

        self.scraper = cc.Scraper()
        self.fetcher = cc.Fetcher()
        self.searcher = cc.Searcher()
        self.writer = cc.Writer()

        self.packConditionDict = PackConditionDict()

        self.handler['ok'] = self.on_ok
        self.handler['exit'] = self.on_exit

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']


    def on_ok(self, message):
        window = message['window']
        values = message['values']

        filelist_string = self.remove_emptyline(values[self.key('list', name='fileList')])
        ziplist_string = self.remove_emptyline(values[self.key('list', name='zipList')])

        filelist_raw = filelist_string.split('\n')
        ziplist_raw = ziplist_string.split('\n')

        csv_filename = values[self.key('filename', name='outputFilename')]

        if sg.popup_yes_no('CSVファイルに書き出しますか？', modal=True) == 'No':
            return
        
        if not csv_filename:
            sg.popup_error('書き出すCSVファイルの名前を入力してください')
            return
        
        filelist = []
        ziplist = []

        self.append_filename_to_list(filelist_raw, filelist)
        self.append_filename_to_list(ziplist_raw, ziplist)

        length_list = len(filelist) + len(ziplist)

        if length_list < 1:
            sg.popup_error('処理すべきファイルまたはURLがありません')
            return
        
        #実作業開始
        to_write = []
        progress_bar_widget.initialize(message, max=(len(filelist) + len(ziplist)) )

        for filename in filelist:
            self.get_content_from_file(self.fetcher.localfile, filename, to_write)
            progress_bar_widget.do_step(message)
        
        for filename in ziplist:
            self.get_content_from_file(self.fetcher.ftbucket_zip, filename, to_write)
            progress_bar_widget.do_step(message)

        if len(to_write) < 1:
            sg.popup('ログは抽出されませんでした')
            return
        
        flt = {}
        self.packConditionDict.pack(message, flt)
        filtered = []
        progress_bar_widget.initialize(message, max=len(to_write))

        self.searcher.settings['isIgnoreCharacter'] = values[self.key('isIgnoreCharacter', 'settings')]
        self.searcher.settings['ignoreCharacter'] = values[self.key('ignoreCharacter', 'settings')]

        for x in to_write:
            if self.searcher.filter(x, flt) == True:
                filtered.append(x)
            progress_bar_widget.do_step(message)
        
        if len(filtered) < 1:
            sg.popup('検索条件に適合するレスは抽出されませんでした')
            return

        try:
            self.writer.write_to_csv(csv_filename, filtered)
        except PermissionError as e:
            sg.popup_error('CSVファイルに書き込めません。パーミッションエラーです。\n', e)
            return
        else:
            sg.popup('CSVファイルに書き出しました')
        finally:
            pass




    def on_exit(self, message):
        pass



    def remove_emptyline(self, text):
        ret = text
        ret = re.sub(r'^[\n\s]+$', r'', ret)
        return ret



    def append_filename_to_list(self, filelist_raw, filelist):
        for filename in filelist_raw:
            if not filename:
                continue

            if os.path.isfile(filename) == False:
                sg.popup_error('ファイルが存在しません:' + filename)
                continue
        
            filelist.append(filename)

    

    def get_content_from_file(self, get_function, filename, to_write):
        try:
            thread = get_function(filename)
        except UnicodeDecodeError as e:
            sg.popup_error('ファイルを開けません:' + filename, e)
        else:
            cc.set_list_to_write(thread, r'', to_write)
        finally:
            pass



    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

    def create(self):
        lyt = [
            sg.Button('書き出し', key=self.key('ok')),
            sg.Button('終了', key=self.key('exit'))
            ]
        return lyt

    def on_initialize_config(self, message):
        config = message['config']
        



class ProgressBarWidget(Widget):
    DEFAULT_MAX = 1000000
    DEFAULT_STEP = 1
    DEFAULT_COUNT = 0

    def __init__(
        self,
        name,
        messenger=None,
        max=DEFAULT_MAX,
        count=DEFAULT_COUNT,
        step=DEFAULT_STEP
        ):

        super().__init__(name, messenger=messenger)
        self.max = max
        self.count = count
        self.step = step

    def do_step(self, message):
        window = message['window']
        values = message['values']

        self.count += self.step
        window[self.key('bar')].update(self.count)        


    def change_step(self, message, step):
        self.step = step

    def final_step(self, message):
        self.step = self.max - self.count

    def initialize(
        self,
        message,
        max=DEFAULT_MAX,
        count=DEFAULT_COUNT,
        step=DEFAULT_STEP
        ):

        window = message['window']
        values = message['values']

        self.max = max
        self.step = step
        self.count = count

        window[self.key('bar')].update(self.count, self.max)

       

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']


    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']


    def create(self):
        lyt = [
            sg.ProgressBar(
                0,
                size=(50, 20),
                orientation='horizontal',
                key=self.key('bar'))
        ]

        return lyt    

    def on_initialize_config(self, message):
        pass



class SettingsWidget(Widget):
    def __init__(self, name, messenger=None):
        super().__init__(name, messenger=messenger)
        self.handler['isIgnoreCharacter'] = self.dummy
        self.handler['ignoreCharacter'] = self.dummy
    
    def create(self):
        lyt = sg.Tab(
            '設定',
            [
                [sg.Checkbox(
                        'レス内容の通常検索で特定の文字を無視する',
                        key=self.key('isIgnoreCharacter'),
                        enable_events=True
                    ),
                    sg.InputText(
                        '',
                        key=self.key('ignoreCharacter'),
                        #size=20,
                        enable_events=True,
                        tooltip='無視する文字を並べて記入'
                    )
                ]
            ]
        )

        return lyt

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.check_config(config, 'Settings', ['isIgnoreCharacter', 'ignoreCharacter'])
        window[self.key('isIgnoreCharacter')].update(STR_TO_BOOL[self.load_config(config, 'Settings', self.key('isIgnoreCharacter'))])
        window[self.key('ignoreCharacter')].update(self.load_config(config, 'Settings', self.key('ignoreCharacter')))
    
    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.save_config(config, 'Settings', self.key('isIgnoreCharacter'), str(values[self.key('isIgnoreCharacter')]))
        self.save_config(config, 'Settings', self.key('ignoreCharacter'), str(values[self.key('ignoreCharacter')]))

    def initialize_config(self, config):
        self.save_config(config, 'Settings', self.key('isIgnoreCharacter'), 'False')
        self.save_config(config, 'Settings', self.key('ignoreCharacter'), '')




class Messenger():
    address_book = {}

    def __init__(self, name, config=None):
        self.name = name
        self.__key = ''
        self.__values = {} #とりあえずget_message()でゲットしたやつは持っとく
        self.__config = config
        self.__window = None
        self.__key_class = Key(name)


    #メッセージ(self.key and self.key) は隠しとく(外から書き換え不可)
    @property
    def key(self):
        return self.__key
    
    @property
    def values(self):
        return self.__values

    @property
    def config(self):
        return self.__config

    @property
    def window(self):
        return self.__window
    
    #message_raw: window.read()
    #PySimpleGUI.window.read() でメッセージを受けとるよ！
    def get_message(self, window, message_raw):
        key, values = message_raw
        self.__key = key
        self.__values = values
        self.__window = window
    
    def dispatch_message(self, key=None, config=None, values=None, window=None, ps=None, by=None):
        #メッセージを配りなさい
        message = self.pack_message(key=key, config=config, values=values, window=window, ps=ps, by=by)
        for name in self.address_book.keys():
            self.address_book[name](message)
        

    def pack_message(self, key=None, config=None, values=None, window=None, ps=None, by=None):
        if not key:
            key = self.key
        if not config:
            config = self.config
        if not values:
            values_copy = self.values.copy()
        else:
            values_copy = self.values.copy()
        if not window:
            window = self.window
        if not ps:
            ps_copy = {}
        else:
            ps_copy = ps.copy()

        return {
            'key': key,
            'config': config,
            'values': values_copy,
            'window': window,
            'ps': ps_copy,
            'by': by
        }
   

    def register_destination(self, name, receiver):
        self.address_book[name] = receiver

    def generate_key(self, part_name, name=None):
        return self.__key_class.key(part_name, name)
    
    def split_key(self, key):
        return self.__key_class.split_key(key)
    
    #window.finalize() が出たときに全登録ガジェットに配られる特別なメッセージ
    def send_window_finalized_message(self, window):
        self.dispatch_message(key=self.generate_key('windowFinalized'), window=window)

    #window.close()が呼ばれそうなときに全登録ガジェットに配られる特別なメッセージ
    def send_window_close_message(self, window):
        self.dispatch_message(key=self.generate_key('windowClose'), window=window)
    
    def send_initialize_config_message(self, window):
        self.dispatch_message(key=self.generate_key('initializeConfig'), window=window)


class PackConditionDict():
    def __init__(self):
        super().__init__()
        self.name = 'PackConditionDict'
        self.__key = Key(self.name)
        self.range_handler = {
            CONDITION_RANGE_SELECT[0]: lambda fore, apre: (fore, fore),
            CONDITION_RANGE_SELECT[1]: lambda fore, apre: (fore, apre),
            CONDITION_RANGE_SELECT[2]: lambda fore, apre: (fore, None),
            CONDITION_RANGE_SELECT[3]: lambda fore, apre: (None, apre)
        }



    def key(self, part_name, name):
        return self.__key.key(part_name, name)



    def pack_string(self, message, ret, attr, name):
        values = message['values']
        if values[self.key('isActive', name)]:
            if values[self.key('reg', name)]:
                ret[attr] = ('reg word', values[self.key('input', name)], None)
            else:
                ret[attr] = ('free word', values[self.key('input', name)], None)



    def pack_number(self, message, ret, attr, name):
        values = message['values']
        if values[self.key('isActive', name)]:
            chk = self.range_handler[values[self.key('range', name)]](values[self.key('input_fore', name)], values[self.key('input_apre', name)])
            ret[attr] = ('range', chk[0], chk[1])


    def pack_date(self, message, ret, attr, name):
        self.pack_number(message, ret, attr, name)

    def pack_time(self, message, ret, attr, name):
        self.pack_number(message, ret, attr, name)

    def pack(self, message, ret):
        #ret = {}

        self.pack_string(message, ret, 'url', 'url')
        self.pack_string(message, ret, 'thread_title', 'threadTitle')
        self.pack_string(message, ret, 'munen', 'munen')
        self.pack_string(message, ret, 'name', 'name')
        self.pack_string(message, ret, 'weekday', 'weekday')
        self.pack_string(message, ret, 'ip', 'ip')
        self.pack_string(message, ret, 'domain', 'domain')
        self.pack_string(message, ret, 'res', 'res')

        self.pack_number(message, ret, 'thread_number', 'threadNumber')
        self.pack_number(message, ret, 'number', 'number')
        self.pack_number(message, ret, 'res_id', 'resId')
        self.pack_number(message, ret, 'soudane', 'soudane')

        self.pack_date(message, ret, 'date', 'date')
        self.pack_time(message, ret, 'time', 'time')

        






#RESPONSE_CONDITION[6].append(pat)
to_write = []
file_types_write = (('CSVファイル', '*.csv'), ('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))
file_types_log = (('HTMLファイル', '*.htm;*.html'), ('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))
file_types_ziplog = (('ZIPファイル', '*.zip'), ('全てのファイル', '*.*'))
file_types_list = (('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))

TOOLTIP_COND = [
    '文字列を入力',
    '半角数字を入力',
    '文字列を入力',
    '半角数字を入力',
    '文字列を入力',
    '文字列を入力',
    '日付(yy/mm/dd形式)、時刻(hh:mm:ss)、または日付時刻(yy/mm/dd hh:mm:ss)を入力',
    '文字列を入力',
    '文字列を入力',
    '数字を入力',
    '数字を入力',
    '文字列を入力'
]

CONDITION_TEXT_PAD = (2, 5)
CONDITION_INPUT_SINGLE = (50, 1)
CONDITION_INPUT_DOUBLE = (15, 1)
CONDITION_INPUT_DATETIME = (20, 1)

CONDITION_DATETIME_SELECT = ['日付', '時刻', '日付時刻']

CONDITION_RANGE_SELECT = ['のみ', 'から', '以上', '以下']

condition_range_handler = {
    CONDITION_RANGE_SELECT[0]: lambda fore, apre: (fore, fore),
    CONDITION_RANGE_SELECT[1]: lambda fore, apre: (fore, apre),
    CONDITION_RANGE_SELECT[2]: lambda fore, apre: (fore, None),
    CONDITION_RANGE_SELECT[3]: lambda fore, apre: (None, apre)
}

#sg.theme('Light Brown 12')


config = configparser.ConfigParser()

if os.path.isfile(CONFIG_INI_PATH) == False:
    with open(CONFIG_INI_PATH, 'w', encoding='utf-8') as f:
        f.write('\n')
    is_config_ini_initialized = True

with open(CONFIG_INI_PATH, 'r', encoding='utf-8') as f:
    config.read_file(f)


messenger = Messenger('Messenger', config)



layout_condition_text = sg.Column([
    [sg.Text('URL', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('スレッド番号', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('スレッドタイトル', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('レス番号', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('無念', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('名前', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('年月日', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('曜日', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('時刻', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('IP', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('ドメイン', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('レスID', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('そうだね', pad=CONDITION_TEXT_PAD)], 
    [sg.Text('レス', pad=CONDITION_TEXT_PAD)]
    ], element_justification='right')

url_input_widget = InputStringWidget('url', messenger=messenger)
thread_number_input_widget = InputNumberWidget('threadNumber', messenger=messenger)
thread_title_input_widget = InputStringWidget('threadTitle', messenger=messenger)
number_input_widget = InputNumberWidget('number', messenger=messenger)
munen_input_widget = InputStringWidget('munen', messenger=messenger)
name_input_widget = InputStringWidget('name', messenger=messenger)
date_input_widget = InputNumberWidget('date', messenger=messenger, input_type='date')
weekday_input_widget = InputStringWidget('weekday', messenger=messenger)
time_input_widget = InputNumberWidget('time', messenger=messenger, input_type='time')
ip_input_widget = InputStringWidget('ip', messenger=messenger)
domain_input_widget = InputStringWidget('domain', messenger=messenger)
res_id_input_widget = InputNumberWidget('resId', messenger=messenger)
soudane_input_widget = InputStringWidget('soudane', messenger=messenger)
res_input_widget = InputStringWidget('res', messenger=messenger)

layout_condition_input = sg.Column([
    url_input_widget.create(),
    thread_number_input_widget.create(),
    thread_title_input_widget.create(),
    number_input_widget.create(),    
    munen_input_widget.create(),
    name_input_widget.create(),
    date_input_widget.create(),
    weekday_input_widget.create(),
    time_input_widget.create(),
    ip_input_widget.create(),
    domain_input_widget.create(),
    res_id_input_widget.create(),
    soudane_input_widget.create(),
    res_input_widget.create()
    ])

layout_tab_condition = sg.Tab('検索条件',[
    [layout_condition_text, layout_condition_input]
    ])

    #↓-FILEPATH-ではなく-FILELISTPATH-イベントが発生する。FileBrowse系は必ず同列ではなく別々に
    #[sg.FilesBrowse('参照', key="-FILEPATH-", change_submits=True), sg.FileBrowse('リストファイル読み込み', key='-FILELISTPATH-', change_submits=True)]

fileListWidget = FileListWidget('fileList', messenger=messenger, tab_text='ファイル', file_types=file_types_log)
zipListWidget = FileListWidget('zipList', messenger=messenger, tab_text='ftbucketDLログZip', file_types=file_types_ziplog)
urlListWidget = FileListWidget('urlList', messenger=messenger, tab_text='URL', is_local_file=False)

settings_widget = SettingsWidget('settings', messenger=messenger)

output_filename_widget = OutputFilenameWidget('outputFilename', messenger=messenger)
ok_and_exit_widget = OKAndExitWidget('okAndExit', messenger=messenger)
progress_bar_widget = ProgressBarWidget('progressBar', messenger=messenger)

layout = [
    [sg.TabGroup([[layout_tab_condition, urlListWidget.create(), fileListWidget.create(), zipListWidget.create(), settings_widget.create()]], enable_events=True, key='-TABGROUP-')],
    output_filename_widget.create(),
    ok_and_exit_widget.create(),
    progress_bar_widget.create()
]


messenger.register_destination('fileList', fileListWidget.receive_message)
messenger.register_destination('zipList', zipListWidget.receive_message)
messenger.register_destination('urlList', urlListWidget.receive_message)
messenger.register_destination('urlInput', url_input_widget.receive_message)
messenger.register_destination('threadNumber', thread_number_input_widget.receive_message)
messenger.register_destination('threadTitle', thread_title_input_widget.receive_message)
messenger.register_destination('number', number_input_widget.receive_message)
messenger.register_destination('munen', munen_input_widget.receive_message)
messenger.register_destination('name', name_input_widget.receive_message)
messenger.register_destination('date', date_input_widget.receive_message)
messenger.register_destination('weekday', weekday_input_widget.receive_message)
messenger.register_destination('time', time_input_widget.receive_message)
messenger.register_destination('ip', ip_input_widget.receive_message)
messenger.register_destination('domain', domain_input_widget.receive_message)
messenger.register_destination('resId', res_id_input_widget.receive_message)
messenger.register_destination('soudane', soudane_input_widget.receive_message)
messenger.register_destination('res', res_input_widget.receive_message)
messenger.register_destination('outputFilename', ok_and_exit_widget.receive_message)
messenger.register_destination('okAndExit', output_filename_widget.receive_message)
messenger.register_destination('progressBar', progress_bar_widget.receive_message)
messenger.register_destination('settings', settings_widget.receive_message)

window = sg.Window('Chiki Chiki Checker', layout, enable_close_attempted_event=True)

window.finalize()
messenger.send_window_finalized_message(window)



while True:
    message_raw = window.read()
    messenger.get_message(window, message_raw)
    key, values = message_raw

    if key == sg.WIN_CLOSED or key == ok_and_exit_widget.key('exit') or key == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        if sg.PopupYesNo('終了しますか？', modal=True) == 'Yes':
            messenger.send_window_close_message(window)
            
            with open(CONFIG_INI_PATH, 'w', encoding='utf-8') as f:
                config.write(f)

            break
    

    messenger.dispatch_message()
    
        

window.close()

