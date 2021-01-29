import PySimpleGUI as sg
import ccchecker as cc
import os
import configparser
import re

# Chiki Chiki Checker GUI

STR_TO_BOOL = {'False': False, 'True': True}

# Widget 暫定ルール
# key を '(Widget Name) (Part Name)'として、空白で区切る
# 将来的にはkeyを動的に変更してメッセージをやりとりできるかも？
# →できない、keyを変更すると外部から操作できない(window[key].update()など)

GUI_MESSAGE_SPLIT_CHARACTER = '-'

PROGRESS_BAR_SIZE = (50, 20)



def remove_emptyline(text):
    ret = re.sub(r'^\n+', r'', text)
    filelist_string = re.sub(r'^\s+', r'', text)
    filelist_string = re.sub(r'\n[\n\s]*', r'\n', text)
    return ret

class Widget():
    STR_TO_BOOL = {'False': False, 'True': True}
    CONDITION_RANGE_SELECT = ['のみ', 'から', '以上', '以下']
    GUI_MESSAGE_SPLIT_CHARACTER = '-'

    def __init__(self, name, messenger=None, message_split_character=GUI_MESSAGE_SPLIT_CHARACTER):
        self.name = name
        self.handler = {}
        self.messenger = messenger
        self.GUI_MESSAGE_SPLIT_CHARACTER = message_split_character

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

    def create(self):
        lyt = []
        return lyt

    def key(self, part_name, name=None):
        if name is None:
            name = self.name
        return name + self.GUI_MESSAGE_SPLIT_CHARACTER + part_name

    def split_key(self, key):
        key_split = key.split(self.GUI_MESSAGE_SPLIT_CHARACTER)
        return key_split[0], key_split[1]

    #the message come from Messenger
    #part_nameでいろいろできるかも？
    def receive_message(self, message):
        #print(message)
        name, part_name = self.split_key(message['key']) #自分宛て
        if name == self.name: #通常のメッセージ
            self.handler[part_name](message)
        elif name == 'Messenger': #メッセンジャーからの特別なメッセージ
            self.handler[part_name](message)




#あくまでも暫定
class ProgressBar:
    PROGRESS_MAX = 1000000
    PROGRESS_LOG_LOAD_MAX = 500000
    PROGRESS_FILTER_LOG_MAX = 450000
    ##PROGRESS_FINAL_STEP = PROGRESS_MAX - (PROGRESS_LOG_LOAD_MAX + PROGRESS_FILTER_LOG_MAX)
    progress_count = 0
    progress_step = 0
    progress_max = 0

    window = None
    key = ''

    def __init__(self, window, key):
        self.window = window
        self.key = key

    def step_progress_bar(self):
        self.progress_count += self.progress_step
        self.window[self.key].update(self.progress_count)
        #print(str(self.progress_count) + '/' + str(self.progress_step))

    def change_step_value_progress_bar(self, step_max, progress_part_max):
        self.progress_step = progress_part_max // step_max
        #print(str(self.progress_count) + '/' + str(self.progress_step))

    def change_final_step(self):
        self.progress_step = self.progress_max - self.progress_count

    def initialize_progress_bar(self, length_data=None, progress_part_max=None):
        self.progress_count = 0
        self.progress_max = self.PROGRESS_MAX
        if length_data and progress_part_max:
            self.change_step_value_progress_bar(length_data, progress_part_max)
        self.window[self.key].update(self.progress_count, self.progress_max)
        #print(str(self.progress_count) + '/' + str(self.progress_step))







class FileListWidget(Widget):
    def __init__(self, name,
     tab_text='',
     file_types=(('全てのファイル', '*.*'),),
     is_local_file=True,
     file_types_list=(('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))
     ):
        super().__init__(name)
        self.tab_text = tab_text
        self.handler = {
            'clear': self.clear_list,
            'add': self.add_to_list,
            'addlistfile': self.add_list_to_list,
            'output': self.output_list,
            'list': self.touch_list,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }
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



class InputStringWidget(Widget):
    def __init__(self, name):
        super().__init__(name)
        self.handler = {
            'isActive': self.on_is_active,
            'input': self.on_input,
            'reg': self.on_reg,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }


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


        ret = self.STR_TO_BOOL[self.load_config(config, 'Widget', self.key('isActive'))]
        window[self.key('isActive')].update(ret)
        if ret:
            self.activate_input(message)

        window[self.key('input')].update(self.load_config(config, 'Widget', self.key('input')))
        window[self.key('reg')].update(self.STR_TO_BOOL[self.load_config(config, 'Widget', self.key('reg'))])

    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.save_config(config, 'Widget', self.key('isActive'), str(values[self.key('isActive')]))
        self.save_config(config, 'Widget', self.key('input'), str(values[self.key('input')]))
        self.save_config(config, 'Widget', self.key('reg'), str(values[self.key('reg')]))



class InputNumberWidget(Widget):
    def __init__(self, name, input_type='number'):
        super().__init__(name)
        self.handler = {
            'isActive': self.on_is_active,
            'input_fore': self.on_input_fore,
            'input_apre': self.on_input_apre,
            'button_fore': self.on_button_fore,
            'button_apre': self.on_button_apre,
            'range': self.on_range,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }
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
                self.CONDITION_RANGE_SELECT,
                self.CONDITION_RANGE_SELECT[0],
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
            if is_time(int(dt.group(1)), int(dt.group(2)), int(dt.group(3))):
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

        ret = self.STR_TO_BOOL[self.load_config(config, 'Widget', self.key('isActive'))]
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



class OutputFilenameWidget(Widget):
    def __init__(self, name,
     file_types=(('CSVファイル', '*.csv'), ('テキストファイル', '*.txt'), ('全てのファイル', '*.*'))
     ):
        super().__init__(name)
        self.file_types = file_types
        self.handler = {
            'browse': self.on_browse,
            'filename': self.on_filename,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }

    def on_filename(self, message):
        pass

    def on_browse(self, message):
        pass

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        window[self.key('filename')].update(self.load_config(config, 'Widget', self.key('filename')))



    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        self.save_config(config, 'Widget', self.key('filename'), values[self.key('filename')])



    def create(self):
        lyt = [
            sg.Text('保存用CSVファイル名'), 
            sg.Input('', enable_events=True, key=self.key('filename')),
            sg.FileSaveAs('参照', key=self.key('browse'), file_types=self.file_types)
            ]

        return lyt



class OKAndExitWidget(Widget):
    def __init__(self, name, event_ok=None, event_exit=None):
        super().__init__(name)
        if not event_ok:
            event_ok = self.on_ok
        if not event_exit:
            event_exit = self.on_exit
        self.handler = {
            'ok': event_ok,
            'exit': event_exit,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']


    def on_ok(self, message):
        pass

    def on_exit(self, message):
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



class ProgressBarWidget(Widget):
    def __init__(self, name, max=1000000, count=0, step=1):
        super().__init__(name)
        self.handler = {
            'step': self.on_step,
            'changeStep': self.on_change_step,
            'finalStep': self.on_final_step,
            'initialize': self.on_initialize,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }
        self.max = max
        self.count = count
        self.step = step

    def on_step(self, message):
        window = message['window']
        values = message['values']

        self.count += self.step
        window[self.key('bar')].update(self.count)        


    def on_change_step(self, message):
        pass
    def on_final_step(self, message):
        self.step = self.max - self.count

    def on_initialize(self, message):
        window = message('window')
        values = message('values')

        max=1000000
        count=0
        step=1
        self.max = max
        self.step = step
        self.count = count

        window[self.key('bar')].update(self.count, self.max)

       

    def on_window_finalized(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        #window[self.key('input_fore')].update(self.load_config(config, 'Widget', self.key('input_fore')))

    def on_window_close(self, message):
        config = message['config']
        window = message['window']
        values = message['values']

        #self.save_config(config, 'Widget', self.key('isActive'),  str(values[self.key('isActive')]))

    def create(self):
        lyt = [
            sg.ProgressBar(
                0,
                size=(50, 20),
                orientation='horizontal',
                key=self.key('bar'))
        ]

        return lyt    



class Messenger():
    address_book = {}

    def __init__(self, name, config=None, message_split_character=GUI_MESSAGE_SPLIT_CHARACTER):
        self.name = name
        self.__key = ''
        self.__values = {} #とりあえずget_message()でゲットしたやつは持っとく
        self.__config = config
        self.__window = None
        self.GUI_MESSAGE_SPLIT_CHARACTER = message_split_character


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
        if name is None:
            name = self.name
        return name + self.GUI_MESSAGE_SPLIT_CHARACTER + part_name
    
    #window.finalize() が出たときに全登録ガジェットに配られる特別なメッセージ
    def send_window_finalized_message(self, window):
        self.dispatch_message(key=self.generate_key('windowFinalized'), window=window)

    #window.close()が呼ばれそうなときに全登録ガジェットに配られる特別なメッセージ
    def send_window_close_message(self, window):
        self.dispatch_message(key=self.generate_key('windowClose'), window=window)



class PackConditionDict(Widget):
    def __init__(self, name):
        super().__init__(name)
        self.handler={
            'pack': self.pack,
            'windowFinalized': self.on_window_finalized,
            'windowClose': self.on_window_close
        }
        self.range_handler = {
            self.CONDITION_RANGE_SELECT[0]: lambda fore, apre: (fore, fore),
            self.CONDITION_RANGE_SELECT[1]: lambda fore, apre: (fore, apre),
            self.CONDITION_RANGE_SELECT[2]: lambda fore, apre: (fore, None),
            self.CONDITION_RANGE_SELECT[3]: lambda fore, apre: (None, apre)
        }
        pass

    def on_window_finalized(self, message):
        pass

    def on_window_close(self, message):
        pass

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

    def pack(self, message):
        ret = {}

        self.pack_string(ret, message, 'url', 'url')
        self.pack_string(ret, message, 'thread_title', 'threadTitle')
        self.pack_string(ret, message, 'munen', 'munen')
        self.pack_string(ret, message, 'name', 'name')
        self.pack_string(ret, message, 'weekday', 'weekday')
        self.pack_string(ret, message, 'ip', 'ip')
        self.pack_string(ret, message, 'domain', 'domain')
        self.pack_string(ret, message, 'res', 'res')

        self.pack_number(ret, message, 'thread_number', 'threadNumber')
        self.pack_number(ret, message, 'number', 'number')
        self.pack_number(ret, message, 'res_id', 'resId')
        self.pack_number(ret, message, 'soudane', 'soudane')

        self.pack_date(ret, message, 'date', 'date')
        self.pack_time(ret, message, 'time', 'time')

        pass



CONFIG_INI_PATH = 'config.ini'
is_config_ini_initialized = False

config = configparser.ConfigParser()
if os.path.isfile(CONFIG_INI_PATH) == False:
    #with open(CONFIG_INI_PATH, 'w', encoding='utf-8') as f:
    #    f.write('\n')
    is_config_ini_initialized = True
else:
    with open(CONFIG_INI_PATH, 'r', encoding='utf-8') as f:
        config.read_file(f)



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

store_cond6a = '00/01/01 00:00:00'
store_cond6z = '00/01/01 00:00:00'

#sg.theme('Light Brown 12')

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

url_input_widget = InputStringWidget('urlInput')
thread_number_input_widget = InputNumberWidget('threadNumber')
thread_title_input_widget = InputStringWidget('threadTitle')
number_input_widget = InputNumberWidget('number')
munen_input_widget = InputStringWidget('munen')
name_input_widget = InputStringWidget('name')
date_input_widget = InputNumberWidget('date', input_type='date')
weekday_input_widget = InputStringWidget('weekday')
time_input_widget = InputNumberWidget('time', input_type='time')
ip_input_widget = InputStringWidget('ip')
domain_input_widget = InputStringWidget('domain')
res_id_input_widget = InputNumberWidget('resId')
soudane_input_widget = InputStringWidget('soudane')
res_input_widget = InputStringWidget('res')

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

fileListWidget = FileListWidget('fileList', tab_text='ファイル', file_types=file_types_log)
zipListWidget = FileListWidget('zipList', tab_text='ftbucketDLログZip', file_types=file_types_ziplog)
urlListWidget = FileListWidget('urlList', tab_text='URL', is_local_file=False)

layout_tab_setting = sg.Tab('設定', [])

output_filename_widget = OutputFilenameWidget('outputFilename')
ok_and_exit_widget = OKAndExitWidget('okAndExit')
progress_bar_widget = ProgressBarWidget('progressBar')

layout = [
    [sg.TabGroup([[layout_tab_condition, urlListWidget.create(), fileListWidget.create(), zipListWidget.create(), layout_tab_setting]], enable_events=True, key='-TABGROUP-')],
    output_filename_widget.create(),
    ok_and_exit_widget.create(),
    progress_bar_widget.create()
]



#('words', (bool)is_Reg)
#('number', 'number')
#('time', 'time')
def pack_search_input_string(ret, attr, name):
    if values[widgets[name]['key']['iscond']]:
        ret[attr] = ('freeword', values[widgets[name]['key']['cond']], values[widgets[name]['key']['reg']])
""" 
    if values[widgets[name]['key']['iscond']]:
        if values[widgets[name]['key']['reg'] == True:
            ret[attr] = ('reg word', values[widgets[name]['key']['cond']], None])
"""

def pack_search_input_number(ret, attr, name):
    if values[widgets[name]['key']['iscond']]:
        chk = condition_range_handler[values[widgets[name]['key']['range']]](values[widgets[name]['key']['from']], values[widgets[name]['key']['to']])
        ret[attr] = ('range', chk[0], chk[1])
        """
        if values[widgets[name]['key']['range']] == CONDITION_DATETIME_SELECT[0]:
            ret[attr] = ('range', values[widgets[name]['key']['from']], values[widgets[name]['key']['to']])
        else:
            ret[attr] = ('range', values[widgets[name]['key']['from']], None)
        """



def pack_search_input_time(ret, attr, name):
    pack_search_input_number(ret, attr, name)



def pack_search_input_date(ret, attr, name):
    pack_search_input_number(ret, attr, name)



def pack_search_words():
    ret = {}

    #pack_search_input_string(ret, 'url', 'url')
    pack_search_input_string(ret, 'thread_title', 'thread title')
    pack_search_input_string(ret, 'munen', 'munen')
    pack_search_input_string(ret, 'name', 'name')
    pack_search_input_string(ret, 'ip', 'ip')
    pack_search_input_string(ret, 'domain', 'domain')
    pack_search_input_string(ret, 'res', 'res')
    pack_search_input_string(ret, 'weekday', 'weekday')

    pack_search_input_number(ret, 'thread_number', 'thread number')
    pack_search_input_number(ret, 'number', 'number')
    pack_search_input_number(ret, 'res_id', 'res id')
    pack_search_input_number(ret, 'soudane', 'soudane')

    pack_search_input_date(ret, 'date', 'date')
    pack_search_input_time(ret, 'time', 'time')

    return ret


"""
def event_ok():
    # ファイルリスト等取得
    filelist_string = remove_emptyline(messenger.values['fileList list'])# キーの取得はきちんと書き換え必要！
    ziplist_string = remove_emptyline(messenger.values['zipList list'])
    #print('======' + filelist_string + '\n----\n' + ziplist_string + '\n=========\n')
    filelist_raw = filelist_string.split('\n')
    ziplist_raw = ziplist_string.split('\n')
    #csv_filename = values['-CSVFILENAME-']
    csv_filename = ''

    # 作業開始確認    
    if sg.popup_yes_no('CSVファイルに書き出しますか？', modal=True) == 'No':
        return

    # ファイルエラー処理

    if not csv_filename:
        sg.popup_error('書き出すCSVファイルの名前を入力してください')
        return

    # 存在しないファイルだとエラー？
    
    #if os.access(csv_filename, os.W_OK) == False:
    #    sg.popup_error('指定されたCSVファイルへの書き込めません。')
    #    return

    filelist = []
    ziplist = []

    for filename in filelist_raw:
        if not filename:
            continue
        if os.path.isfile(filename) == False:
            sg.popup_error('ファイルが存在しません("' + filename + '")')
            continue
        filelist.append(filename)

    for filename in ziplist_raw:
        if not filename:
            continue
        if os.path.isfile(filename) == False:
            sg.popup_error('ファイルが存在しません("' + filename + '")')
            continue
        ziplist.append(filename)

    length_list = len(filelist) + len(ziplist)

    if length_list < 1:
        sg.popup_error('処理すべきファイルがありません。')
        return

    # 実作業

    # ログ取得
    progress_bar.initialize_progress_bar(length_list, progress_bar.PROGRESS_LOG_LOAD_MAX)

    to_write = []
    for filename in filelist:
        try:
            thread = cc.fetch_html_file(filename)
        except UnicodeDecodeError as e:
            sg.popup_error('ファイルを開けません(' + filename + '):\n', e)
        else:
            cc.set_list_to_write(thread, r'', to_write)
        finally:
            progress_bar.step_progress_bar()

    for zipname in ziplist:
        try:
            thread = cc.extract_ftbucket_zip(zipname)
        except UnicodeDecodeError as e:
            sg.popup_error('ファイルを開けません(' + filename + '):\n', e)
        else:
            cc.set_list_to_write(thread, r'', to_write)
        finally:
            progress_bar.step_progress_bar()

    if len(to_write) < 1:
        sg.popup('ログは抽出されませんでした')
        return

    #to_write = (cc.set_list_to_write(thread, r''))
    # 辞書リスト
    # to_write.append(...)ではだめ
    # 解決点
    # set_list_to_write に直接渡してやる

    # 検索条件でフィルタリング
    progress_bar.change_step_value_progress_bar(len(to_write), progress_bar.PROGRESS_FILTER_LOG_MAX)

    flt = pack_search_words()
    filtered = []
    for x in to_write:
        if cc.filter_res(x, flt) == True:
            filtered.append(x)
        progress_bar.step_progress_bar()

    progress_bar.change_final_step()

    if len(filtered) < 1:
        sg.popup('検索条件に適合するレスは抽出されませんでした。')
        progress_bar.step_progress_bar()
        return


    #ファイル書き込み

    try:
        cc.write_csv(csv_filename, filtered)
    except PermissionError as e:
        sg.popup_error('CSVファイルに書き込めません。パーミッションエラーです。\n', e)
        return
    else:
        progress_bar.step_progress_bar()
        sg.popup('CSVファイルの書き出しが終了しました。')
    finally:
        pass

    return
"""

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
messenger.register_destination('outputFilename', output_filename_widget.receive_message)
messenger.register_destination('okAndExit', output_filename_widget.receive_message)
messenger.register_destination('progressBar', progress_bar_widget.receive_message)

window = sg.Window('Chiki Chiki Checker', layout, enable_close_attempted_event=True)
window.finalize()

messenger.send_window_finalized_message(window)



while True:
    message_raw = window.read()
    messenger.get_message(window, message_raw)
    key, values = message_raw

    if key == sg.WIN_CLOSED or key == '-EXIT-' or key == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        if sg.PopupYesNo('終了しますか？', modal=True) == 'Yes':
            messenger.send_window_close_message(window)
            
            break
    

    messenger.dispatch_message()
    
        

window.close()

