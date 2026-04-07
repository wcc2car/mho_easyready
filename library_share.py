import os
import datetime

try:
    import winreg  # Windows only
except ImportError:
    winreg = None

'''
######################################################################################################
# 訊息表, 有中英雙語言, 自動判斷系統語言, 輸出對應語言訊息. // 執行檔參數: 0=英文, >0=中文 // 函式參數: 訊息代號
class LibraryMsgOutput:

    def __init__(self, force_lang=None):

        self.messages = {
            0: (
                "!! 指定的訊息字串異常 !!",
                "!! Specified message string error !!"
            ),

            1: (
                "!!! 無效的日期時間格式索引",
                "!!! Invalid datetime format index"
            ),

            2: (
                "%s 格式錯誤. 行 %s, 列 %s: %s",
                "%s format error. Line %s, Col %s: %s"
            ),

            3: (
                "!!! %s 檔案讀取錯誤",
                "!!! %s: File read error"
            ),

            4: ("", ""),
            5: ("", ""),
            6: ("", ""),
            7: ("", ""),
            8: ("", ""),
            9: ("", ""),
            10: ("", ""),
        }
        self.lang_mode = self._detect_language(force_lang)

    @staticmethod
    def _detect_language(force_lang):                     # 偵測語言

        if len(sys.argv) > 1:                             # - 外掛參數控制語言
            try:
                arg = int(sys.argv[1])
                if arg == 0:
                    return "en"
                elif arg > 0:
                    return "zh"
            except ValueError:
                pass

        if force_lang is not None:                        # - 外部函式強制指定
            if force_lang == 0:
                return "en"
            else:
                return "zh"

        if platform.system() == "Windows" and winreg:     # - Windows 系統語言偵測
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Control Panel\International"
                )
                locale_name, _ = winreg.QueryValueEx(key, "LocaleName")
                winreg.CloseKey(key)

                if "zh-TW" in locale_name or "zh_Hant" in locale_name:
                    return "zh"

            except OSError:
                pass

        return "en"

    def output(self, msg_id):                                         # 輸出訊息

        lang_index = 0 if self.lang_mode == "zh" else 1
        lib_msg = self.messages.get(msg_id)

        if not lib_msg:
            error_msg = self.messages[0]
            return "%s (%s)" % (error_msg[lang_index], msg_id)

        return lib_msg[lang_index]


###########################################################################################
# 建立 LibraryMsgOutput() 物件 libmsg
libmsg = LibraryMsgOutput()
'''

# ^^^^^^^^^^^^ 以上是類別 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

###########################################################################################
# 輸出時間字串, 依指定格式 // 參數如下表, 由 0~7 .
def datetime_string(index: int = 0) -> str:

    _FORMATS = (
        "%Y-%m-%d %H:%M:%S",   # 0. 日期 時間
        "%Y-%m-%d",            # 1. 日期
        "%H:%M:%S",            # 2. 時:分:秒
        "%H:%M:%S.%f",         # 3. 時:分:秒.微秒
        "%Y-%m-%d_%H-%M-%S",   # 4. 年-月-日_時-分-秒, 當檔名使用
        "%Y-%m-%d_%H%M",       # 5. 年-月-日_時分, 當檔名使用
        "%m-%d_%H%M",          # 6. 月-日_時分, 當檔名使用
        "%m%d_%H%M%S",         # 7. 月日_時分秒, 當檔名使用
    )

    try:
        fmt = _FORMATS[index]
    except IndexError:
        raise ValueError(f"無效的日期時間格式索引: {index}")

    return datetime.datetime.now().strftime(fmt)


###############################################################################################
# 判斷檔案是否存在. // 參數: "檔名"  // 回傳值: 不存在=False , 存在=True
def check_file_exists(filename):
    if os.path.isfile(filename):
        return True                   # 檔案存在
    else:
        return False                  # 檔案不存在


###############################################################################################
# 清除螢幕
def clear_screen():
    in_pycharm = os.environ.get("PYCHARM_HOSTED") == "1"     # 偵測是否在 PyCharm console

    if in_pycharm:
        print("\n" * 24)                                     # PyCharm console 不支援 cls / clear，使用多行換行模擬 cls
    else:
        os.system('cls' if os.name == 'nt' else 'clear')     # 系統終端機


###############################################################################################
# 輸入一個字元, 限指定的按鍵. // 參數= message: 提示訊息, allowed_keys: 限用字元, 例如 "AaBb123+"
def input_one_letter(message: str, allowed_keys: str) -> str:
    allowed = set(allowed_keys)

    while True:
        buff = input(message).strip()

        if len(buff) == 1 and buff in allowed:
            return buff

'''
#################################################################################################
# 檢查 json 檔內容是否有誤 // 參數: 目標檔名  // 回傳: 成功 = True, ""; 異常=False, "異常訊息"
def check_json_file(filename: str):

    try:
        with open(filename, "r", encoding="utf-8") as f:
            json.load(f)

        return True, ""

    except json.JSONDecodeError as e:
        return False, libmsg.output(2) % (filename, e.lineno, e.colno, e.msg)

    except (FileNotFoundError, OSError):
        return False, libmsg.output(3) % filename
'''

#################################################################################################
# 將檔案更名備份 // 參數: 目標檔名  // 回傳: 成功 =True, 異常=False
def rename_with_timestamp(filename: str) -> int:
    try:
        directory, name = os.path.split(filename)
        base, ext = os.path.splitext(name)
        new_name = f"{base}.{datetime_string(7)}{ext}"
        new_filename = os.path.join(directory, new_name)
        os.replace(filename, new_filename)
        return True
    except OSError:
        return False
