import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import os
import sys
import webbrowser
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import EasyReady_ui as easyReadyUI

######################################################
# i18n , 顯示不同語言的字串訊息
class I18N:
    def __init__(self, translations, default="zh_tw"):
        self.translations = translations
        self.lang = default

    def set_lang(self, lang):
        if lang in self.translations:
            self.lang = lang

    def tr(self, key):
        return self.translations.get(self.lang, {}).get(key, key)


####################################################################################
#  i18n 語言切換
class LanguageController:
    def __init__(self, ui, i18n, combobox, lang_codes):
        self.ui = ui
        self.i18n = i18n
        self.cbox = combobox
        self.lang_codes = lang_codes
        self._setup()

    def _setup(self):
        tr = self.i18n.tr
        values = [tr("MENU_ZH_TW"), tr("MENU_EN_US")]
        self.cbox.configure(values=values)

        idx = self.lang_codes.index(self.i18n.lang)
        self.cbox.current(idx)
        self.cbox.bind("<<ComboboxSelected>>", self._changed)

    def _changed(self, _event=None):
        idx = self.cbox.current()
        new_lang = self.lang_codes[idx]

        if new_lang != self.i18n.lang:
            self.i18n.set_lang(new_lang)
            self.retranslate_ui()

    def retranslate_ui(self):
        tr = self.i18n.tr
        ui = self.ui

        ui.frame_lu.configure(text=tr("TITLE_MENU"))
        ui.frame_ld.configure(text=tr("TITLE_STEP"))
        ui.frame_r.configure(text=tr("TITLE_NOTE"))
        ui.radio_bt1.configure(text=tr("RB_ONLINE"))
        ui.radio_bt2.configure(text=tr("RB_OFFLINE"))
        ui.radio_bt3.configure(text=tr("RB_LAN_SERVER"))
        ui.lab_txt_a1.configure(text=tr("LAB_A1"))
        ui.lab_txt_a2.configure(text=tr("LAB_A2"))
        ui.lab_txt_a3.configure(text=tr("LAB_A3"))
        ui.button_1.configure(text=tr("BTN_GO"))

        if hasattr(ui, "step_manager"):
            ui.step_manager.retranslate(tr)

        if hasattr(ui, "logger"):
            if hasattr(ui.logger, "rerender"):
                ui.logger.rerender()

        if hasattr(ui, "check_mode"):
            ui.check_mode()


######################################################
# i18n 字串表
TRANSLATIONS = {
    "zh_tw": {
        "MSG_ONLINE": ">連線至網際網路的伺服器進行多人遊戲, 類似當年 Gazillion 官方遊戲 (舊帳號已不存在). 只需取得遊戲軟體, 挑個伺服器申請帳號就能玩.\n",
        "MSG_OFFLINE": ">在電腦上進行單機版遊戲, 不需連線網際網路也能玩. 自己就是 GM, 掌握各種修改權力. 需要取得遊戲軟體, 並安裝 MHServerEmu.\n",
        "MSG_LAN_SERVER": ">安裝遊戲伺服器, 供區域網路的電腦連線多人遊玩. 區域網路包括: 家庭網路, 學校宿網, 公司內網... 需要一台電腦安裝單機版, 其它電腦比照網路版設定.\n",
        "TITLE_MENU": "[ 選單 ]",
        "TITLE_NOTE": "[ 狀態/訊息 ]",
        "TITLE_STEP": "[ 進程 ]",
        "RB_ONLINE": "設置網路版遊戲",
        "RB_OFFLINE": "設置單機版遊戲",
        "RB_LAN_SERVER": "設置區網伺服器",
        "MENU_ZH_TW": "繁體中文",
        "MENU_EN_US": "English",
        "BTN_GO": "開始",
        "BTN_NEXT": "下一步",
        "PATH_BTN": "瀏覽...",
        "BTN_RE": "重測",
        "LAB_A1": "1-1. {遊戲資料夾}在哪裡",
        "LAB_A2": "1-2. 遊戲需求與電腦狀況",
        "LAB_A3": "1-3. 安裝網路版遊戲",
        "LAB_B1": "2-1. 下載 MHServerEmu",
        "LAB_B2": "2-2. 本機網路服務狀況",
        "LAB_B3": "2-3. 安裝單機版遊戲",
        "LAB_C1": "3-1. 選擇伺服器 IP",
        "LAB_C2": "3-2. 安裝區網伺服器",
        ###########################################################################
        "MSG_A1_1": ">目前 MarvelHeroes Omega 遊戲有兩個公開下載點:\n (本遊戲歷經多次改版, 在此僅用遊戲版本 2.16a [檔案版本 1.52.0.1700])\n\n>  ",
        "MSG_A1_2": "https://steamdb.info/app/226320/info/",
        "MSG_A1_3": "\n 此需在 Steam 擁有本遊戲才能下載, 預設的安裝路徑可能是:\n C:\\Program Files (x86)\\Steam\\steamapps\\common\\{Marvel Heroes Omega}\n\n>  ",
        "MSG_A1_4": "https://archive.org/",
        "MSG_A1_5": "\n 搜尋 \"omega 2.16a\", 建議下載後解壓縮至 C:\\, D:\\ 等根目錄.\n (在 archive.org 下載的版本是綠色軟體)\n",
        "MSG_A1_6": "\n 圖中的灰色區塊就是{遊戲資料夾}, 裡面必須完整包含藍色區塊的三個資料夾.\n {遊戲資料夾}可以任意更名, 也可以搬移至其它位置.\n\n",
        "MSG_A1_7": ">請[瀏覽...]指出你的{遊戲資料夾}所在路徑, 以進行安裝.\n",
        "MSG_A1_8": ">已確認{遊戲資料夾}, 請[下一步].\n",
        "MSG_A1_9": ">這不是{遊戲資料夾}, 請[瀏覽...]重選.\n",
        ###########################################################################
        "MSG_A2_1": ">選取的遊戲資料夾資訊:\n 遊戲資料夾: %s\n",
        "MSG_A2_2": " 遊戲執行檔: %s\n",
        "MSG_A2_3": " 檔案版本: %s\n\n",
        "MSG_A2_4": ">遊戲最低 Windows 系統需求:\n 作業系統: Vista/Win7/Win8/Win10 32/64 位元\n 處理器: Intel Core 2 Duo 2.1GHz / AMD Athlon X2 2.1GHz\n 顯示卡: Nvidia 8800 / ATI HD3800 / Intel HD 3000 (512 VRAM)\n 硬碟: 30 GB\n\n",
        "MSG_A2_5": ">你的電腦配備(僅供參考):\n 作業系統: %s\n",
        "MSG_A2_6": " 處理器: %s\n",
        "MSG_A2_6-1": " 邏輯處理器數: %s\n",
        "MSG_A2_7": " 記憶體: %s\n",
        "MSG_A2_8": " 顯示卡: %s\n",
        "MSG_A2_9": " 顯示卡驅動程式: %s\n\n",
        "MSG_A2_10": ">你的電腦遊戲依賴套件:\n D3D: %s\n",
        "MSG_A2_11": " VC++ 2008 Runtime (MSVCRT9): %s\n",
        "MSG_A2_12": " VC++ 2010 Runtime (MSVCRT10): %s\n",
        "MSG_A2_13": " VC++ 2013 Runtime (MSVCRT13): %s\n",
        "MSG_A2_14": " .NET 8: %s\n\n",
        "MSG_A2_15": ">請安裝欠缺的依賴套件(安裝後重開機才會生效):",
        "MSG_A2_16": "\n D3D: ",
        "MSG_A2_17": "\n VC++ 2008 Runtime: ",
        "MSG_A2_18": "\n VC++ 2010 Runtime: ",
        "MSG_A2_19": "\n VC++ 2013 Runtime: ",
        "MSG_A2_20": "\n .NET 8: ",
        "MSG_A2_21": ">確認電腦符合需求後, 請[下一步].\n",
        ########################################################################
        "MSG_A3_1": ">請參閱伺服器清單, 前往喜歡的伺服器註冊帳號:\n",
        "MSG_A3_2": " (這些伺服器各自獨立, 帳號並不通用)\n ",
        "MSG_A3_3": "\n\n>已於遊戲資料夾建立部份伺服器的遊戲執行檔, 例如:\n Project T.A.H.I.T.I:  %s\\_Play_TAHITI.bat\n (Council of Ancients, Omega Node, The Secret Wars 亦同)\n\n",
        "MSG_A3_4": ">執行 _Play_*.bat 批次檔, 就能連線至對應的伺服器進行多人遊戲.\n",
        "MSG_A3_5": '\n>要如何修改 .bat 批次檔以連線至其它伺服器?\n -使用"記事本"編輯要修改的 _play_*.bat 批次檔.\n',
        "MSG_A3_6": ' -如下圖, 把藍色部份改成新伺服器的網址或IP.\n -通常用伺服器的"官網"網址, 去掉https://就對了, 不能有空白.\n',
        "MSG_A3_7": ">網路版遊戲已安裝完成. 請關閉視窗結束程式.\n",
        ########################################################################
        "MSG_B1_1": ">下載 MHServerEmu Stable v1.0.0:\n  ",
        "MSG_B1_2": "\n -將下載的壓縮檔直接放至{遊戲資料夾}, 不要解壓縮. \n",
        "MSG_B1_3": " -若{遊戲資料夾}已有 Apache24/MHServerEmu, 請確認非執行中, 未被檔案總管開啟.\n",
        "MSG_B1_4": " -EMU 需要 .Net8, 還會不定期以 Nightly-release 版本更新, 請關注: ",
        "MSG_B1_5": "\n -此 Apache24/MHServerEmu/與本工具, 都是綠色軟體.\n\n",
        "MSG_B1_6": ">MHServerEmu-1.0.0.zip 安裝作業失敗:\n  %s\n",
        "MSG_B1_7": ">MHServerEmu-1.0.0.zip 不存在.\n",
        "MSG_B1_8": ">完成操作後, 請[下一步].\n",
        ########################################################################
        "MSG_B2_1": ">EMU 伺服器需要 Http 服務, 使用通訊埠 80, 8080, 443, 4306. 必須確定這些埠號未被佔用, 否則伺服器將無法正常運行.\n",
        "MSG_B2_2": "\n>你的電腦 80/8088/443/4306 埠使用現況:\n",
        "MSG_B2_3": " -需求通訊埠均未被使用.\n",
        "MSG_B2_4": " -通訊埠: %s\n",
        "MSG_B2_5": "   進程: %s\n",
        "MSG_B2_6": "   應用程式: %s\n",
        "MSG_B2_7": "   服務名稱: %s\n",
        "MSG_B2_8": "\n>請排除上列被佔用的通訊埠, 如果不知道該怎麼作, 可洽詢 ChatGPT/Gemini.\n",
        "MSG_B2_9": ">確認需求通訊埠可用後, 請[下一步].\n",
        ########################################################################
        "MSG_B3_1": ">安裝 MHServerEmu ...\n -無需執行 EMU 預設的 setup.exe, 但也不衝突.\n -可與 Birost 並用.\n\n",
        "MSG_B3_2": ">安裝錯誤, 複制 *.sip 檔案失敗:\n %s",
        "MSG_B3_3": ">已於遊戲資料夾建立 Offline_Play.bat, 執行它就能開始單機遊戲.\n",
        "MSG_B3_4": " -若有新版 Nightly-release, 只需將 zip 放至到{遊戲資料夾}, Offline_Play.bat 便會自動安裝, 並備份/還原重要檔案.\n",
        "MSG_B3_5": " -Offline_Play.bat 執行後只會有一個 CMD 視窗, 關閉它就會關閉 MHServerEmu 和 Apache.\n",
        "MSG_B3_6": " -若遊戲軟體莫名無解打不開... 可嘗試更名(刪除)資料夾: ",
        "MSG_B3_7": "\n -新增帳號, 請至瀏覽器 Dashboard 頁面的 Create Account.\n",
        "MSG_B3_8": ">單機版遊戲已安裝完成. 請關閉視窗結束程式.\n",
        ########################################################################
        "MSG_C1_1": ">要擔任伺服機, 必須提供一個連線 IP 給使用者, 最好是固定 IP. 若電腦有多個 IP, 別選無線網路.\n",
        "MSG_C1_1-1": " (注意: 開放網路擔任伺服器, 具有資安風險)\n",
        "MSG_C1_2": "\n>你的電腦 IP 資訊: \n",
        "MSG_C1_3": " -所有 IP: %s\n",
        "MSG_C1_4": " -連外 IP: %s\n",
        "MSG_C1_5": " -外網 IP: ",
        "MSG_C1_6": " (請標記本列以顯示IP)\n",
        "MSG_C1_7": ">使用下拉選單選擇 IP 後, 請[下一步].\n",
        "MSG_C1_8": " 找不到可用的 ip\n",
        ########################################################################
        "MSG_C2_1": ">網路伺服器等同開放的單機版, 單機版能作的它都能作, 甚至能在網路伺服器上多開遊戲端.\n 差別只在不能隨意關閉 MHServerEmu/Apache 視窗, 因為可能還有別人連線在玩.\n\n",
        "MSG_C2_2": ">這台 MHServerEmu 區網伺服器 IP 是: %s\n\n",
        "MSG_C2_3": ">已於{遊戲資料夾}建立以下 bat 檔:\n  #Host_Play(IP).bat, 執行就啟動伺服器+遊戲端 (和單機版用法完全相同).\n",
        "MSG_C2_4": "  #Host_Start(IP).bat, 只啟動伺服器, 不執行遊戲端, 也沒有更新功能.\n  #Lan_Play(IP).bat, 只執行遊戲端, 其它電腦也該使用.\n",
        "MSG_C2_5": "\n>其它電腦可以參考功能 1-3 的圖片說明, 修改現有的 bat 檔, 連線到這台網路伺服器. (建議直接 copy #Lan_Play(IP).bat)\n",
        "MSG_C2_6": "\n>伺服器的部份設置會影響連線遊戲端所見: 成就語言檔, 商城, add_G, 新聞...\n",
        "MSG_C2_7": " -新建帳號用的 E-mail, 可用假 E-Mail.\n -更多細節請拜訪 MHServerEmu GitHub.\n\n",
        "MSG_C2_8": ">網路伺服器已安裝完成. 請關閉視窗結束程式.\n",
        "MSG_C2_9": " (不建議在已完成設定的遊戲資料夾, 重覆使用本工具)\n",

    },
    "en_us": {
        "MSG_ONLINE": ">Connect to an internet server for multiplayer gameplay, similar to the original Gazillion official games (old accounts no longer exist). Just get the game client, pick a server, sign up for an account, and you’re ready to play.\n",
        "MSG_OFFLINE": ">Play the game in single-player mode on your PC without an internet connection. You act as the GM with full control over all modifications. Simply get the game client and install MHServerEmu.\n",
        "MSG_LAN_SERVER": ">Install a game server to allow multiple computers on a local area network to play together. Local networks include: home networks, school dorm networks, company intranets, etc. One computer needs to have the single-player version installed, and the other computers follow the online version setup.\n",
        "TITLE_MENU": "[ Menu ]",
        "TITLE_NOTE": "[ Status / Info ]",
        "TITLE_STEP": "[ Workflow ]",
        "RB_ONLINE": "Setup Online Game",
        "RB_OFFLINE": "Setup Offline Game",
        "RB_LAN_SERVER": "Setup LAN Server",
        "MENU_ZH_TW": "Trad. Chinese",
        "MENU_EN_US": "English",
        "BTN_GO": "GO!",
        "BTN_NEXT": "Next",
        "PATH_BTN": "Browse...",
        "BTN_RE": "Recheck",
        "LAB_A1": "1-1. Where is the {Game Folder}",
        "LAB_A2": "1-2. Requirements & system status",
        "LAB_A3": "1-3. Setup online mode",
        "LAB_B1": "2-1. Download MHServerEmu",
        "LAB_B2": "2-2. Local network service status",
        "LAB_B3": "2-3. Setup offline mode",
        "LAB_C1": "3-1. Select server IP",
        "LAB_C2": "3-2. Setup Lan server",
        ###########################################################################
        "MSG_A1_1": ">Marvel Heroes Omega currently has two public download sources:\n (This game has undergone multiple updates; here we only use game version 2.16a [file version 1.52.0.1700])\n\n>  ",
        "MSG_A1_2": "https://steamdb.info/app/226320/info/",
        "MSG_A1_3": "\n Must own on Steam to download. default install path may be:\n C:\\Program Files (x86)\\Steam\\steamapps\\common\\{Marvel Heroes Omega}\n\n>  ",
        "MSG_A1_4": "https://archive.org/",
        "MSG_A1_5": '\n Search for "omega 2.16a". It is recommended to extract it to a root directory such as C:\\ or D:\\ after downloading.\n (The version downloaded from archive.org is portable software.)\n',
        "MSG_A1_6": "\n The gray area in the image is the {Game Folder}, which must fully contain the three folders shown in blue.\n The {Game Folder} can be renamed freely and can also be moved to another location.\n\n",
        "MSG_A1_7": ">Please click [Browse...] to select your {Game Folder} and continue installation.\n",
        "MSG_A1_8": ">{Game Folder} confirmed. Please click [Next].\n",
        "MSG_A1_9": ">This is not the {Game Folder}. Please [Browse...] to reselect.\n",
        ###########################################################################
        "MSG_A2_1": ">{Game Folder} Information Found:\n Game Folder: %s\n",
        "MSG_A2_2": " Game Executable: %s\n",
        "MSG_A2_3": " File Version: %s\n\n",
        "MSG_A2_4":  ">Minimum Windows system requirements for the game:\n OS: Vista/Win7/Win8/Win10 32/64-bit\n CPU: Intel Core 2 Duo 2.1GHz / AMD Athlon X2 2.1GHz\n Graphics Card: Nvidia 8800 / ATI HD3800 / Intel HD 3000 (512 VRAM)\n Storage: 30 GB\n\n",
        "MSG_A2_5": ">Your PC Specs (Reference Only):\n OS: %s\n",
        "MSG_A2_6": " CPU: %s\n",
        "MSG_A2_6-1": " Logical CPU Count: %s\n",
        "MSG_A2_7": " RAM: %s\n",
        "MSG_A2_8": " Graphics Card: %s\n",
        "MSG_A2_9": " Graphics Driver: %s\n\n",
        "MSG_A2_10": ">Your PC's Game Dependencies:\n D3D: %s\n",
        "MSG_A2_11": " VC++ 2008 Runtime (MSVCRT9): %s\n",
        "MSG_A2_12": " VC++ 2010 Runtime (MSVCRT10): %s\n",
        "MSG_A2_13": " VC++ 2013 Runtime (MSVCRT13): %s\n",
        "MSG_A2_14": " .NET 8: %s\n\n",
        "MSG_A2_15": ">Please install missing Dependencies (Restart required for changes to take effect):",
        "MSG_A2_16": "\n D3D: ",
        "MSG_A2_17": "\n VC++ 2008 Runtime: ",
        "MSG_A2_18": "\n VC++ 2010 Runtime: ",
        "MSG_A2_19": "\n VC++ 2013 Runtime: ",
        "MSG_A2_20": "\n .NET 8: ",
        "MSG_A2_21": ">Please confirm that your computer meets the requirements, then click [Next].\n",
        ######################################################################
        "MSG_A3_1": ">Please refer to the server list and register an account on a server you prefer:\n",
        "MSG_A3_2": " (These servers are independent, and accounts are not shared.)\n ",
        "MSG_A3_3": "\n\n>Game executables for some servers have been created in the {Game Folder}, for example:\n Project T.A.H.I.T.I:  %s\\_Play_TAHITI.bat\n (Council of Ancients, Omega Node, The Secret Wars Same as above)\n\n",
        "MSG_A3_4": ">Run the _Play_*.bat file to connect to the corresponding server for multiplayer.\n",
        "MSG_A3_5": '\n>How to modify the .bat file to connect to other servers?\n -Use "Notepad" to edit the _Play_*.bat file you want to modify.\n',
        "MSG_A3_6": ' -As shown below, change the blue section to the new server\'s URL or IP address.\n -Usually, you can use the server\'s "official website" URL, just remove the "https://" and ensure there are no spaces.\n',
        "MSG_A3_7": ">Online game installation is complete. Please close the window to exit.\n",
        ######################################################################
        "MSG_B1_1": ">Download MHServerEmu Stable v1.0.0:\n  ",
        "MSG_B1_2": "\n -Place the downloaded ZIP directly into the {Game Folder}. Do NOT extract it.\n",
        "MSG_B1_3": " -If Apache24/MHServerEmu already exists in the {Game Folder}, make sure it is not running and not opened by File Explorer.\n",
        "MSG_B1_4": " -EMU requires .NET 8 and is updated irregularly with Nightly releases. Please follow: ",
        "MSG_B1_5": "\n -Here, Apache24, MHServerEmu, and this app are all portable applications.\n\n",
        "MSG_B1_6": ">MHServerEmu-1.0.0.zip installation failed:\n  %s\n",
        "MSG_B1_7": ">MHServerEmu-1.0.0.zip does not exist.\n",
        "MSG_B1_8": ">Once operations are complete, please click [Next].\n",
        ########################################################################
        "MSG_B2_1": ">The EMU server requires HTTP services and uses ports 80, 8080, 443, and 4306. You must ensure these ports are not in use; otherwise, the server will not run properly.\n",
        "MSG_B2_2": "\n>Current status of ports 80/8088/443/4306 on your PC:\n",
        "MSG_B2_3": " -All required ports are currently available.\n",
        "MSG_B2_4": " -Port: %s\n",
        "MSG_B2_5": "   Process: %s\n",
        "MSG_B2_6": "   Application: %s\n",
        "MSG_B2_7": "   Service Name: %s\n",
        "MSG_B2_8": "\n>Please free the ports listed above. If you are unsure how to do this, you may consult ChatGPT/Gemini.\n",
        "MSG_B2_9": ">Once the required ports are available, please click [Next].\n",
        ########################################################################
        "MSG_B3_1": ">Installing MHServerEmu ...\n -No need to run the default EMU setup.exe, but it does not conflict either.\n -Can be used together with 'Birost'.\n\n",
        "MSG_B3_2": ">Installation error, failed to copy *.sip files:\n %s",
        "MSG_B3_3": ">Offline_Play.bat has been created in the {Game Folder}. Run it to start the single-player game.\n",
        "MSG_B3_4": " -If there is a newer Nightly-release, just place the zip into the {Game Folder}, and Offline_Play.bat will automatically install it, backing up/restoring important files.\n",
        "MSG_B3_5": " -After running Offline_Play.bat, only one CMD window will appear. Closing it will shut down both MHServerEmu and Apache.\n",
        "MSG_B3_6": " -If the game software inexplicably fails to launch... you can try renaming (or deleting) the folder: ",
        "MSG_B3_7": "\n -To create an account, go to 'Create Account' on the browser Dashboard page.\n",
        "MSG_B3_8": ">Single-player installation is complete. Please close the window to exit.\n",
        #######################################################################
        "MSG_C1_1": ">To act as a server host, you must provide a connection IP address to users; a fixed IP is preferred. If the computer has multiple IP addresses, exclude WiFi IP.\n",
        "MSG_C1_1-1": " (Note: Running a server on an open network carries security risks)\n",
        "MSG_C1_2": "\n>Your computer IP information: \n",
        "MSG_C1_3": " -All IPs: %s\n",
        "MSG_C1_4": " -Outbound IP: %s\n",
        "MSG_C1_5": " -Public IP: ",
        "MSG_C1_6": " (Mark this line to display the IP)\n",
        "MSG_C1_7": ">Select an IP from the dropdown menu, then click [Next].\n",
        "MSG_C1_8": " No available IP found\n",
        ########################################################################
        "MSG_C2_1": ">A ServerHost is an open single-player setup; it can do everything single-player can, and even run multiple game clients.\nThe only difference is that you cannot freely close the MHServerEmu/Apache window, because other players may still be connected and playing.\n\n",
        "MSG_C2_2": ">This MHServerEmu LAN server IP is: %s\n\n",
        "MSG_C2_3": ">The following bat file has been created in the {Game Folder}:\n #Host_Play(IP).bat, Running it will start both the server & game client (same usage as single-player mode).\n",
        "MSG_C2_4": " #Host_Start(IP).bat, Starts only the server without launching the game client, and has no update function.\n #Lan_Play(IP).bat, Runs only the game client; other PCs should also use this.\n",
        "MSG_C2_5": "\n>Other PCs can refer to the image in Functions 1–3 to modify existing bat files and connect to this lan server. (It is recommended to directly copy #Lan_Play(IP).bat)\n",
        "MSG_C2_6": "\n>The server-side configuration may affect what connected clients see: achievement locale files, store, add_G, news...\n",
        "MSG_C2_7": " -The email used for creating an account can be a fake email.\n -For more details, please visit the MHServerEmu GitHub.\n\n",
        "MSG_C2_8": ">Lan server installation is complete. Please close the window to exit.\n",
        "MSG_C2_9": " (Avoid reusing this tool in {Game Folder} already set up.)",

    }
}


######################################################
# text 文字的特效表
TAG_STYLES = {
    "normal": {},
    "green": {"foreground": "green"},
    "orange": {"foreground": "orange"},
    "red": {"foreground": "red"},
    "blue": {"foreground": "blue"},
    "white": {"foreground": "white"},
    "mark": {"background": "yellow"},
    "highlight": {"foreground": "white", "background": "black"},
    "strikethrough": {"foreground": "gray", "overstrike": True},
    "link": {"foreground": "blue", "underline": True},
}


###################################################################
# 在 text 的顯示操作
class Logger:
    def __init__(self, text_widget, i18n):
        self.text = text_widget
        self.i18n = i18n
        self.img = None
        self.images = []
        self._setup_tags()

    def _setup_tags(self):
        default_font = tkfont.nametofont("TkDefaultFont")

        for tag, style in TAG_STYLES.items():
            self.text.tag_config(
                tag,
                font=default_font,
                spacing1=0,  # 段落上方間距
                spacing2=3,  # 行與行（包含自動換行）
                spacing3=3,  # 段落下方間距
                **style
            )

    ### 顯示圖片 ###############################################
    def log_image(self, img_or_file, pad_x=0):
        self.text.config(state="normal")

        if isinstance(img_or_file, str):
            img = tk.PhotoImage(file=resource_path(img_or_file))
        else:
            img = img_or_file

        if not hasattr(self, "images"):
            self.images = []
        self.images.append(img)

        bg = self.text.cget("bg")                           # 取得 Text 背景色
        frame = tk.Frame(self.text, bg=bg)                  # 容器（背景同步）
        spacer = tk.Frame(frame, width=pad_x, bg=bg)        # spacer（背景同步）
        spacer.pack(side="left")
        label = tk.Label(frame, image=img, bd=0, bg=bg)     # 圖片（背景同步）
        label.pack(side="left")
        self.text.window_create("end", window=frame)
        self.text.insert("end", "\n")

        self.text.update_idletasks()
        self.text.see("end-1c")
        self.text.config(state="disabled")

    #### 顯示 MESSAGE ##############################################
    def log(self, message, *args, tag="normal", link=None, raw=False, **kwargs):
        """
           message: i18n 的 key 或原始字串
           *args: 用於 % 格式化的變數 (例如 "apple")
           **kwargs: 用於 .format() 格式化的變數 (例如 name="apple")
        """
        msg = message if raw else self.i18n.tr(message)
        try:
            if args:
                msg = msg % args
            if kwargs:
                msg = msg.format(**kwargs)
        except Exception as e:
            msg = f"{msg} (Format Error: {e})"

        self.text.config(state="normal", wrap="word")
        if link:  # 帶 link 的訊息
            tag_name = f"link_{hash(link)}"
            small_font = tkfont.nametofont("TkDefaultFont").copy()
            small_font.configure(size=max(small_font.cget("size") - 3, 5))
            self.text.tag_config(tag_name, foreground="blue", underline=True, font=small_font)

            def callback(_event, url=link):
                webbrowser.open(url)

            self.text.tag_bind(tag_name, "<Button-1>", callback)
            self.text.tag_bind(tag_name, "<Enter>", lambda _event: self.text.config(cursor="hand2"))
            self.text.tag_bind(tag_name, "<Leave>", lambda _event: self.text.config(cursor=""))

            self.text.insert("end", msg, (tag, tag_name))
        else:
            self.text.insert("end", msg, tag)

        self.text.see("end")
        self.text.config(state="disabled")

    #### 插入分隔線 ###############################
    def insert_separator(self, height=2, color="#c0c0c0"):
        self.text.config(state="normal")

        self.text.insert("end", "\n")  # 單純換行
        self.text.update_idletasks()

        text_width = self.text.winfo_width()
        sep = tk.Frame(self.text, height=height, bg=color, width=text_width)
        self.text.window_create("end", window=sep)

        self.text.update_idletasks()
        self.text.insert("end", "\n")  # 分隔線後換行
        self.text.config(state="disabled")

    #### 清除 TEXT 內容 ###############################
    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")


#################################################################################
# 管理左下角 Step Frame
class StepManager:
    def __init__(self, ui, mho=None):
        self.ui = ui
        self.mho = mho
        self.master = ui.mainwindow
        self._icon_cache = {}
        self.steps = self._collect_steps()
        self.icons = self._collect_icons()

        self.status_icon_paths = {
            "null": "./images/null_30.png",
            "ok": "./images/true_30.png",
            "error": "./images/false_30.png",
        }

    def retranslate(self, tr):
        ui = self.ui
        ui.lab_txt_a1.configure(text=tr("LAB_A1"))
        ui.lab_txt_a2.configure(text=tr("LAB_A2"))
        ui.lab_txt_a3.configure(text=tr("LAB_A3"))
        ui.lab_txt_b1.configure(text=tr("LAB_B1"))
        ui.lab_txt_b2.configure(text=tr("LAB_B2"))
        ui.lab_txt_b3.configure(text=tr("LAB_B3"))
        ui.lab_txt_c1.configure(text=tr("LAB_C1"))
        ui.lab_txt_c2.configure(text=tr("LAB_C2"))

        if hasattr(ui, "btn_a1"):
            ui.btn_a1.configure(text=tr("BTN_NEXT"))
        if hasattr(ui, "btn_a2"):
            ui.btn_a2.configure(text=tr("BTN_NEXT"))
        if hasattr(ui, "btn_b1"):
            ui.btn_b1.configure(text=tr("BTN_NEXT"))
        if hasattr(ui, "btn_b2"):
            ui.btn_b2.configure(text=tr("BTN_NEXT"))
        if hasattr(ui, "btn_c1"):
            ui.btn_c1.configure(text=tr("BTN_NEXT"))

        if hasattr(ui, "path_btn_a1"):
            ui.path_btn_a1.configure(text=tr("PATH_BTN"))

        if hasattr(ui, "btn_b2_re"):
            ui.btn_b2_re.configure(text=tr("BTN_RE"))

    def _collect_steps(self):
        return [
            self.ui.frame_a1, self.ui.frame_a2, self.ui.frame_a3,
            self.ui.frame_b1, self.ui.frame_b2, self.ui.frame_b3,
            self.ui.frame_c1, self.ui.frame_c2,
        ]

    def _collect_icons(self):
        return [
            self.ui.lab_icon_a1, self.ui.lab_icon_a2, self.ui.lab_icon_a3,
            self.ui.lab_icon_b1, self.ui.lab_icon_b2, self.ui.lab_icon_b3,
            self.ui.lab_icon_c1, self.ui.lab_icon_c2,
        ]

    def hide_all(self):
        for f in self.steps:
            f.grid_remove()

    def show(self, step):
        frame = self._resolve(step)
        if frame:
            frame.grid()

            label = self._get_icon(step)
            if label and not getattr(label, "image", None):
                self.set_status(step, "null")

    def disable(self, step):
        frame = self._resolve(step)
        if not frame or getattr(frame, "_disabled", False):
            return

        frame._disabled = True

        def _disable(widget):
            for child in widget.winfo_children():
                try:
                    child.configure(state="disabled")
                except tk.TclError:
                    pass
                _disable(child)

        def _fade(widget):
            for child in widget.winfo_children():
                try:
                    child.configure(foreground="#888888")
                except tk.TclError:
                    pass
                _fade(child)

        _disable(frame)
        _fade(frame)

    def set_status(self, step, status):
        label = self._get_icon(step)
        if not label:
            return

        path = self.status_icon_paths.get(status)
        if not path:
            return

        if path not in self._icon_cache:
            try:
                self._icon_cache[path] = tk.PhotoImage( file=resource_path(path), master=self.master)
            except tk.TclError:
                return

        img = self._icon_cache[path]
        label.configure(image=img)
        label.image = img

    ##########################################################################
    def _resolve(self, step):
        if isinstance(step, int):
            return self.steps[step] if 0 <= step < len(self.steps) else None
        if isinstance(step, str):
            return getattr(self.ui, step, None)
        return step

    def _get_icon(self, step):
        frame = self._resolve(step)
        if frame in self.steps:
            idx = self.steps.index(frame)
            return self.icons[idx]
        return None


######################################################
# 處理圖片打包後的路徑問題
def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


######################################################
# 主 UI
class AppUI(easyReadyUI.AppUIUI):
    def __init__(self, master=None, solutions=None, game_folder_check=None, mho=None, on_next_clicked=None, is_required_port_free=None):
        self.i18n = I18N(TRANSLATIONS)
        super().__init__(master, translator=self.i18n.tr)
        self.game_folder_check = game_folder_check
        self.mho = mho
        self.solutions = solutions
        self.on_next_clicked = on_next_clicked
        self.is_required_port_free = is_required_port_free
        self._init_global_font()
        default_font = tkfont.nametofont("TkDefaultFont")
        self.text_r.configure(font=default_font)
        self.logger = Logger(self.text_r, self.i18n)
        self.text_r.configure(yscrollcommand=self.scrollbar_1.set)
        self.scrollbar_1.configure(command=self.text_r.yview)
        self.step_manager = StepManager(self, mho=self.mho)

        self.lang_controller = LanguageController(
            self,
            self.i18n,
            self.cbox_lang,
            ["zh_tw", "en_us"]
        )

        self.btn_a1.configure(command=lambda: self.on_next_clicked("frame_a1"))
        self.btn_a2.configure(command=lambda: self.on_next_clicked("frame_a2"))
        self.btn_b1.configure(command=lambda: self.on_next_clicked("frame_b1"))
        self.btn_b2.configure(command=lambda: self.on_next_clicked("frame_b2"))
        self.btn_c1.configure(command=lambda: self.on_next_clicked("frame_c1"))
        self.btn_b2_re.configure(command=lambda: self.is_required_port_free())

        self.lang_controller.retranslate_ui()
        self.step_manager.hide_all()
        self._bind_events()
        self.check_mode()

    #### Events // 路徑瀏覽器 ####################
    def _bind_events(self):
        self.path_btn_a1.bind("<<PathChooserPathChanged>>", self.on_path_changed)

    def on_path_changed(self, _event=None):
        path = self.path_btn_a1.cget("path")
        if path:
            path = os.path.normpath(path)
            self.game_folder_check(path, self)

    ### Frame_lu 單選鈕 + [GO]  // 主功能選單 動作處理  #############
    def check_mode(self):
        mode = self.v_selected.get()
        self.logger.clear()

        msg = {
            "offline": "MSG_OFFLINE",
            "lanhost": "MSG_LAN_SERVER"
        }.get(mode, "MSG_ONLINE")

        self.logger.log(msg)

    def on_go_clicked(self):                            # Frame_lu 按鈕
        self.logger.insert_separator()
        mode = self.v_selected.get()
        self.step_manager.disable("frame_lu")
        self.solutions(mode)                            # 呼叫主功能解決方案

    ### 設定字體大小 ###############################
    @staticmethod
    def _init_global_font():
        default_font = tkfont.nametofont("TkDefaultFont")

        default_font.configure(size=9)
        tkfont.nametofont("TkTextFont").configure(size=9)
        tkfont.nametofont("TkMenuFont").configure(size=9)
        tkfont.nametofont("TkHeadingFont").configure(size=9)
        tkfont.nametofont("TkFixedFont").configure(size=9)

        style = ttk.Style()
        style.configure(".", font=default_font)


######################################################
# 測試
if __name__ == "__main__":
    app = AppUI()

    app.run()
