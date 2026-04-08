import glob
import locale
import socket
import shutil
import psutil
import requests
import zipfile
import subprocess
from pathlib import Path
from ctypes import wintypes
from library_share import *
from library_gui import *

try:
    import win32api  # 需要安裝 pywin32
except ImportError:
    win32api = None

######################################################################################################
# 全域變數集 (儲存程式全域設定，例如初始遊戲路徑)
class AppConfig:

    def __init__(self):
        self.ini = None                                                           # 預先建立 Class INI 的名字, 佔位
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):            # PyInstaller 打包後使用 _MEIPASS
            self.initial_path = ""                                                # 打包後自動路徑，可改成執行檔所在路徑
        else:
            self.initial_path = "E:\\Marvel Heroes Omega_1.52"                    # IDE 開發環境指定路徑

        self.selected_func = ""                       # 選擇的主功能
        self.b1_result = False                        # b1 作業結果
        self.local_ips = []                           # 本機 IP
        self.outbound_ip = None                       # 主要 IP
        self.public_ip = None                         # 外網 IP
        self.selected_ip = None                       # 選中的 IP

glb_vars = AppConfig()  # [建立 全域變數集]


######################################################################################################
# 電腦環境檢測 // 無參數 //無回傳, 結果存在變數群, 無=None, 有=相關資訊
class WindowsEnvironmentDetector:
    def __init__(self):
        self.windows_info = None
        self.win_arch= None
        self.cpu_name = None
        self.cpu_count = None
        self.ram_gb = None
        self.d3d_info = None
        self.vc2008 = None
        self.vc2010 = None
        self.vc2013 = None
        self.dotnet8 = None
        self.gpu_info = None
        self.gpu_driver = None

    def detect_all(self):
        self._detect_windows()
        self._detect_cpu()
        self._detect_ram()
        self._detect_gpu()
        self._detect_d3d()
        self._detect_vc_runtimes()
        self._detect_dotnet8()

    ### Windows -ok ###############################################
    def _detect_windows(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
            )

            def safe_get(name):
                try:
                    return winreg.QueryValueEx(key, name)[0]
                except OSError:
                    return None

            product_name = safe_get("ProductName")
            display_version = safe_get("DisplayVersion")  # Win10/11 主用
            release_id = safe_get("ReleaseId")  # fallback (舊 Win10)
            build = safe_get("CurrentBuildNumber")
            ubr = safe_get("UBR")

            if build is not None:
                build_str = str(build)
                if ubr is not None:
                    build_str = f"{build_str}.{ubr}"
            else:
                build_str = "Unknown"

            version_str = display_version or release_id or "Unknown"

            arch = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE")
            self.win_arch = "x64" if "64" in arch else "x86"

            try:
                lang = locale.getlocale()[0]
            except (ValueError, TypeError):
                lang = None

            parts = []
            if product_name:
                parts.append(product_name)

            if version_str != "Unknown":
                parts.append(version_str)

            parts.append(f"Build {build_str}")
            parts.append(f"{self.win_arch}")
            if lang:
                parts.append(lang)

            self.windows_info = ", ".join(parts)

        except OSError:
            self.windows_info = "Unknown Windows Version"

    ### CPU -ok ###################################################
    def _detect_cpu(self):
        try:
            import winreg
            key = winreg.OpenKey( winreg.HKEY_LOCAL_MACHINE,r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")     # 最準的名稱來源
            self.cpu_name = name.strip()
            self.cpu_count = os.cpu_count()

        except  OSError:
            try:
                import platform
                self.cpu_name = platform.processor()
            except (OSError, AttributeError):
                self.cpu_name = None

    ### RAM -ok ##################################################
    def _detect_ram(self):
        try:
            import psutil
            ram = psutil.virtual_memory().total / (1024 ** 3)
            self.ram_gb = f"{ram:.1f} GB"
        except (AttributeError, OSError):
            self.ram_gb = None

    ### Direct3D Feature Level -ok ###################################
    def _detect_d3d(self):
        try:
            d3d11 = ctypes.WinDLL("d3d11.dll")

            feature_levels = (ctypes.c_uint * 7)(
                0xb100,  # 11.1
                0xb000,  # 11.0
                0xa100,  # 10.1
                0xa000,  # 10.0
                0x9300,  # 9.3
                0x9200,  # 9.2
                0x9100  # 9.1
            )

            def try_create_device(driver_type):
                device = ctypes.c_void_p()
                context = ctypes.c_void_p()
                feature_level = ctypes.c_uint()

                result = d3d11.D3D11CreateDevice(
                    None,
                    driver_type,
                    None,
                    0,
                    ctypes.byref(feature_levels),
                    len(feature_levels),
                    7,
                    ctypes.byref(device),
                    ctypes.byref(feature_level),
                    ctypes.byref(context)
                )
                return result, feature_level.value

            D3D_DRIVER_TYPE_HARDWARE = 1
            hr, fl = try_create_device(D3D_DRIVER_TYPE_HARDWARE)

            if hr != 0:
                D3D_DRIVER_TYPE_WARP = 5
                hr, fl = try_create_device(D3D_DRIVER_TYPE_WARP)

            if hr != 0:
                self.d3d_info = None
                return

            mapping = {
                0xb100: "11.1",
                0xb000: "11.0",
                0xa100: "10.1",
                0xa000: "10.0",
                0x9300: "9.3",
                0x9200: "9.2",
                0x9100: "9.1",
            }

            level = mapping.get(fl)
            if level:
                self.d3d_info = f"Direct3D Feature Level {level}"
            else:
                self.d3d_info = None

        except (OSError, AttributeError, ctypes.ArgumentError):
            self.d3d_info = None

    ### VC++ Runtime (MSI enumeration) ###############################
    def _detect_vc_runtimes(self):

        try:
            guid_len = 39
            guid_buf = ctypes.create_unicode_buffer(guid_len)
            name_buf = ctypes.create_unicode_buffer(256)

            targets = {
                "2008": "Visual C++ 2008",
                "2010": "Visual C++ 2010",
                "2013": "Visual C++ 2013"
            }

            found = {
                "2008": False,
                "2010": False,
                "2013": False,
            }

            i = 0
            msi = ctypes.WinDLL("msi.dll")

            while True:
                res = msi.MsiEnumProductsW(i, guid_buf)
                if res != 0:
                    break

                name_len = wintypes.DWORD(256)

                if msi.MsiGetProductInfoW(
                        guid_buf,
                        "ProductName",
                        name_buf,
                        ctypes.byref(name_len)
                ) == 0:

                    product = name_buf.value

                    for key, text in targets.items():
                        if text in product:
                            found[key] = True
                i += 1

            # ✔ 對外只輸出結果（乾淨）
            self.vc2008 = "OK" if found["2008"] else None
            self.vc2010 = "OK" if found["2010"] else None
            self.vc2013 = "OK" if found["2013"] else None

        except (OSError, AttributeError, ctypes.ArgumentError):
            self.vc2008 = self.vc2010 = self.vc2013 = None

    ### .NET 8  ###################################################
    def _detect_dotnet8(self):

        try:
            output = subprocess.check_output(
                ["dotnet", "--list-runtimes"],
                stderr=subprocess.DEVNULL,
                text=True
            )

            found = False
            for line in output.splitlines():
                parts = line.split()
                if len(parts) < 2:
                    continue

                name = parts[0]
                version = parts[1]

                if version.startswith("8."):
                    if name in (
                            "Microsoft.NETCore.App",
                            "Microsoft.WindowsDesktop.App",
                    ):
                        found = True
                        break
            self.dotnet8 = "OK" if found else None

        except (subprocess.CalledProcessError, FileNotFoundError):
            self.dotnet8 = None

    ### GPU #######################################################
    def _detect_gpu(self):

        try:
            cmd = (
                "wmic path Win32_VideoController "
                "get Caption,AdapterRAM,DriverVersion,DriverDate /format:list"
            )

            output = subprocess.check_output(
                cmd,
                shell=True,
                stderr=subprocess.DEVNULL
            ).decode(errors="ignore")

            gpu_data = {}
            for line in output.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    gpu_data[key.strip()] = value.strip()

            model = gpu_data.get("Caption")
            raw_vram = gpu_data.get("AdapterRAM", "0")

            if raw_vram.isdigit():
                vram_gb = int(raw_vram) / (1024 ** 3)
                vram_text = f"{vram_gb:.1f} GB"
            else:
                vram_text = None

            if model and vram_text:
                self.gpu_info = f"{model} ({vram_text})"
            else:
                self.gpu_info = model

            version = gpu_data.get("DriverVersion")
            raw_date = gpu_data.get("DriverDate")
            if raw_date and len(raw_date) >= 8:
                date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            else:
                date = None

            if version and date:
                self.gpu_driver = f"{version} ({date})"
            else:
                self.gpu_driver = version

        except  (subprocess.CalledProcessError, FileNotFoundError, OSError):
            self.gpu_info = None
            self.gpu_driver = None

env = WindowsEnvironmentDetector()


######################################################################################################
# 檢測 Marvel Heroes Omega 遊戲是否存在 // 無參數  // 無回傳 : 結果均在 class 變數
class MarvelHeroesDetector:

    def __init__(self):
        self.game_path = ""                   # -遊戲路徑
        self.game_exe_path = None             # -執行檔名路徑(64/32之分)
        self.game_version = None              # -檔案版本 FileVersion (一般是抓這個)
        self.product_version = None           # -產品版本 ProductVersion
        self.game_exists = False              # -遊戲存在旗標


    def detect_game(self, path):              # [偵測 MarvelHeroes*.exe ]  // 各版本的執行檔名不太一樣
        arch_folder = "Win64" if env.win_arch == "x64" else "Win32"
        exe_pattern = os.path.join(
            path,
            "UnrealEngine3",
            "Binaries",
            arch_folder,
            "MarvelHeroes*.exe"
        )
        exe_list = glob.glob(exe_pattern)

        if exe_list:                                                                 # 遊戲執行檔存在, 就偵測{遊戲/檔案版本}
            self.game_exe_path = exe_list[0]
            versions = self._get_explorer_style_version(self.game_exe_path)
            self.game_version = versions.get("Explorer_FileVersion")
            self.product_version = versions.get("Explorer_ProductVersion")

        required_files = [                                                           # 檢查必要檔案與資料夾 // 2 個 .sip 檔和 CookedPCConsole 資料夾
            os.path.join(path, "Data", "Game", "Calligraphy.sip"),
            os.path.join(path, "Data", "Game", "mu_cdata.sip"),
        ]
        required_dirs = [
            os.path.join(
                path,
                "UnrealEngine3",
                "MarvelGame",
                "CookedPCConsole"
            )
        ]
        files_exist = all(os.path.isfile(f) for f in required_files)
        dirs_exist = all(os.path.isdir(d) for d in required_dirs)
        self.game_exists = bool(self.game_exe_path) and files_exist and dirs_exist

        if self.game_exists:
            self.game_path = path

    @staticmethod
    def _get_explorer_style_version(file_path):                                           # 抓取執行檔的 FileVersion / ProductVersion

        version_dll = ctypes.WinDLL("version.dll")
        size = version_dll.GetFileVersionInfoSizeW(file_path, None)
        if not size:
            return {"Explorer_FileVersion": None, "Explorer_ProductVersion": None}

        buffer = ctypes.create_string_buffer(size)
        version_dll.GetFileVersionInfoW(file_path, None, size, buffer)

        class VS_FIXEDFILEINFO(ctypes.Structure):                                          # --- FileVersion: 二進位 VS_FIXEDFILEINFO ---
            _fields_ = [
                ("dwSignature", wintypes.DWORD),
                ("dwStrucVersion", wintypes.DWORD),
                ("dwFileVersionMS", wintypes.DWORD),
                ("dwFileVersionLS", wintypes.DWORD),
                ("dwProductVersionMS", wintypes.DWORD),
                ("dwProductVersionLS", wintypes.DWORD),
            ]

        raw_ptr = ctypes.c_void_p()
        fixed_len = wintypes.UINT()
        binary_file_version = None
        if version_dll.VerQueryValueW(buffer, "\\", ctypes.byref(raw_ptr), ctypes.byref(fixed_len)):
            fixed_ptr = ctypes.cast(raw_ptr, ctypes.POINTER(VS_FIXEDFILEINFO))
            f = fixed_ptr.contents
            binary_file_version = "{}.{}.{}.{}".format(
                f.dwFileVersionMS >> 16, f.dwFileVersionMS & 0xFFFF,
                f.dwFileVersionLS >> 16, f.dwFileVersionLS & 0xFFFF
            )

        trans_ptr = ctypes.c_void_p()      # --- ProductVersion: 文字欄位 ---
        trans_len = wintypes.UINT()
        if version_dll.VerQueryValueW(buffer, r"\\VarFileInfo\\Translation", ctypes.byref(trans_ptr), ctypes.byref(trans_len)):
            p_trans = ctypes.cast(trans_ptr, ctypes.POINTER(ctypes.c_uint32))
            lang_id = "{:04x}{:04x}".format(p_trans[0] & 0xFFFF, (p_trans[0] >> 16) & 0xFFFF)
        else:
            lang_id = "040904b0"           # fallback

        def get_str(key):
            res_ptr = ctypes.c_wchar_p()
            res_len = wintypes.UINT()
            if version_dll.VerQueryValueW(buffer, f"\\StringFileInfo\\{lang_id}\\{key}", ctypes.byref(res_ptr), ctypes.byref(res_len)):
                return res_ptr.value
            return None

        return {
            "Explorer_FileVersion": binary_file_version,
            "Explorer_ProductVersion": get_str("ProductVersion")
        }

mho = MarvelHeroesDetector()                             # [建立 遊戲軟體 物件]
# ^^^^[ 物件 ]^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

############################################
# 建立 ini Class, 並初始化
def init_ini():
    glb_vars.ini=IniManager(mho.game_path)
    glb_vars.ini.init_from_text('''
[Logging]
ConsoleMinLevel=0
ConsoleMaxLevel=5

[Frontend]
BindIP=0.0.0.0   
Port=4306
PublicAddress=127.0.0.1 

[WebFrontend]
Address=localhost 
Port=8080
DashboardFileDirectory=Dashboard
DashboardUrlPath=/Dashboard/

[PlayerManager]
UseJsonDBManager=false
NewsUrl=http://localhost/news/index.html

[GroupingManager]
ServerName=MHServerEmu
MotdText=Welcome to Marvel Heroes! Type !commands for a list of available server commands.

[GameInstance]
NumWorkerThreads=1

[GameData]
LoadAllPrototypes=false
UseEquipmentSlotTableCache=false

[GameOptions]
LeaderboardsEnabled=false
InfinitySystemEnabled=true

[CustomGameOptions]
ESCooldownOverrideMinutes=-1.0
AutoUnlockAvatars=false       
AutoUnlockTeamUps=false
DisableMovementPowerChargeCost=false
EnableUltimatePrestige=false

[MTXStore]
GazillioniteBalanceForNewAccounts=10000
ESToGazillioniteConversionRatio=2.25   
ESToGazillioniteConversionStep=4       
HomePageUrl=http://localhost/store/index.html
HomeBannerPageUrl=http://localhost/store/images/banner.png
HeroesBannerPageUrl=http://localhost/store/images/banner.png
CostumesBannerPageUrl=http://localhost/store/images/banner.png
BoostsBannerPageUrl=http://localhost/store/images/banner.png
ChestsBannerPageUrl=http://localhost/store/images/banner.png
SpecialsBannerPageUrl=http://localhost/store/images/banner.png
RealMoneyUrl=https://localhost/MTXStore/AddG
BundleInfoUrl=http://localhost/bundles/
BundleImageUrl=http://localhost/bundles/images/
    ''')


#######################################################
# B3/C2 建立 offline_play.bat
def create_host_play_bat():
    site_ip = "localhost"
    filename = "Offline_Play.bat"

    if glb_vars.selected_func == "c":
        site_ip = glb_vars.selected_ip
        filename = f"#Host_Play({site_ip}).bat"

    bat_txt=rf'''@echo off
  chcp 65001 >nul 2>&1
  cd /d "%~dp0"
  set "GP=%cd%\"
  set "BAK=%GP%_On_Update.Bak\"
  set "EMU=%GP%MHServerEMU\"
  set APACHE_SERVER_ROOT=%cd%\Apache24

REM ===== ZIP sampo: MHServerEmu-nightly-20240114-Release-windows-x64.zip =====
  set "EMU_zip=MHServerEmu-nightly-*.zip"
  set "full_zip="
  if not exist "%EMU_zip%" goto CLEAR_TEMP

  for %%i in (%EMU_zip%) do (set "full_zip=%%~nxi")

  echo Update: %full_zip% ...
  md MHServerEMU.tmp>nul 2>&1 
  cd /d "%GP%MHServerEMU.tmp"  
  tar -xf "%GP%%full_zip%">nul 2>&1
  cd /d %GP%
  move /y %full_zip% "%full_zip%.bak">nul 2>&1

REM ===== Backup profiles, to ".\_On_Update.Bak" ===== 
  echo --Backup data files ...
  md "%BAK%Config.bak">nul 2>&1
  xcopy "%EMU%Config*.ini" "%BAK%Config.bak\" /C/R/Q/Y>nul 
  
  md "%BAK%account.bak">nul 2>&1
  xcopy "%EMU%data\Account.*" "%BAK%account.bak\" /C/R/Q/Y>nul 
  
  md "%BAK%LiveTuningData.bak">nul 2>&1
  xcopy "%EMU%Data\Game\LiveTuning\LiveTuningData*.json" "%BAK%LiveTuningData.bak\" /C/R/Q/Y>nul 

  md "%BAK%Patches.bak">nul 2>&1
  xcopy "%EMU%Data\Game\Patches\PatchData*.json" "%BAK%Patches.bak\" /C/R/Q/Y>nul 
  
  md "%BAK%MTXStore.bak">nul 2>&1
  xcopy "%EMU%data\Game\MTXStore\Catalog*.json" "%BAK%MTXStore.bak\" /C/R/Q/Y>nul
 
  md "%BAK%Achievements.bak">nul 2>&1
  xcopy "%EMU%Data\Game\Achievements\Achievement*.json" "%BAK%Achievements.bak\" /C/R/Q/Y>nul

  md "%BAK%Web.bak">nul 2>&1
  xcopy "%EMU%data\Web\" "%BAK%Web.bak\" /E/C/R/Q/Y>nul

REM ===== Nightly.Release SETUP ======  
  rd /s /q "%GP%MHServerEMU">nul 2>&1
  ren "%GP%MHServerEMU.tmp" "MHServerEMU" 
  echo --Install EMU OK.

REM ===== Restore backup file ===== 
  echo --Restore backup file ... 
  xcopy "%BAK%Config.bak\ConfigOverride.ini" "%EMU%" /C/R/Q/Y>nul 
  xcopy "%BAK%account.bak\Account.*" "%EMU%data\" /C/R/Q/Y>nul
  
  ren "%EMU%Data\Game\LiveTuning\LiveTuningData*.json" *.json.bak
  xcopy "%BAK%LiveTuningData.bak\LiveTuningData*.json" "%EMU%Data\Game\LiveTuning\" /C/R/Q/Y>nul

  ren "%EMU%\Data\Game\Patches\PatchData*.json" *.json.bak
  xcopy "%BAK%Patches.bak\PatchData*.json" "%EMU%Data\Game\Patches\" /C/R/Q/Y>nul

  ren "%EMU%Data\Game\MTXStore\catalog*.json" *.json.bak
  xcopy "%BAK%MTXStore.bak\catalog*.json" "%EMU%Data\Game\MTXStore\" /C/R/Q/Y>nul

  ren "%EMU%Data\Game\Achievements\Achievement*.json" *.json.bak
  xcopy "%BAK%Achievements.bak\Achievement*.json" "%EMU%Data\Game\Achievements\" /C/R/Q/Y>nul
  
  ren "%EMU%Data\Web\Dashboard\index.html" *.html.bak
  xcopy "%BAK%Web.bak\Dashboard\index.html" "%EMU%Data\Web\Dashboard\" /C/R/Q/Y>nul

  ren "%EMU%Data\Web\MTXStore\add-g.html" *.html.bak
  xcopy "%BAK%Web.bak\MTXStore\add-g.html" "%EMU%Data\Web\MTXStore\" /C/R/Q/Y>nul

REM ===== copy *.sip =====
  if not exist "%EMU%data\game\*.sip" (xcopy "%GP%data\game\*.sip" "%EMU%data\game\." /C/R/Q/Y>nul)

:CLEAR_TEMP
  rd /s /q "%temp%\Marvelheroes">nul 2>&1

:RUN_GAME 
  start /B "" "%APACHE_SERVER_ROOT%\bin\httpd.exe"
  cd /D "%EMU%"
  start /B "" MHServerEmu.exe
  cd /D "%GP%"  
  start /B "" "http://localhost:8080/Dashboard/"
  start /B "" ".\UnrealEngine3\Binaries\Win64\MarvelHeroesOmega.exe" -robocopy -nosteam -siteconfigurl={site_ip}/SiteConfig.xml 
'''

    output_path = Path(mho.game_path) / filename
    output_path.write_text(bat_txt, encoding="utf-8")


#######################################################
#  A3/C2 建立 Online_Play 批次檔
def create_online_play_bat():

    server_list = {
        "TAHITI": "mhtahiti.com",
        "TAHITI2": "2hiti.mhtahiti.com",
        "COA": "mho.councilofancients.com",
        "SecretWars": "the-secret-wars.com",
        "OmegaNode": "play.omeganode.org",
    }

    base_lines = [
        "@echo off",
        "chcp 65001 >nul",
        "set gamepath=%~dp0",
        "cd /D %gamepath%",
        "",
    ]

    if glb_vars.selected_ip:                   # glb_vars.selected_func == "c" && (glb_vars.selected_ip != None)
        url = glb_vars.selected_ip

        file = f"{mho.game_path}\\#Lan_Play({glb_vars.selected_ip}).bat"
        cmd_line = f'start "" /min "{mho.game_exe_path}" ^\n-robocopy -nosteam -siteconfigurl={url}/SiteConfig.xml'
        full_lines = base_lines + [cmd_line]

        with open(file, "w", encoding="utf-8", newline="\r\n") as f:
            f.write("\n".join(full_lines))
    else:                                               # glb_vars.selected_func == "a" or glb_vars.selected_func  (glb_vars.selected_ip = None)
        for server, url in server_list.items():
            file = f"{mho.game_path}\\_Play_{server}.bat"
            cmd_line = f'start "" /min "{mho.game_exe_path}" ^\n-robocopy -nosteam -siteconfigurl={url}/SiteConfig.xml'
            full_lines = base_lines + [cmd_line]

            with open(file, "w", encoding="utf-8", newline="\r\n") as f:
                f.write("\n".join(full_lines))


#######################################################
#  C2 建立 Host_Start 批次檔
def create_host_start_bat():

    content = [
        "@echo off",
        "chcp 65001 >nul 2>&1",
        'cd /d "%~dp0"',
        'set "GP=%cd%\\"',
        'set APACHE_SERVER_ROOT=%cd%\\Apache24',
        "",
        ":CLEAR_TEMP",
        'rd /s /q "%temp%\\Marvelheroes">nul 2>&1',
        "",
        ":RUN_SERVERS",
        'start /B "" "%APACHE_SERVER_ROOT%\\bin\\httpd.exe"',
        'cd /D "%GP%MHServerEMU\\"',
        'start /B "" MHServerEmu.exe',
        'start /B "" "http://localhost:8080/Dashboard/"'
    ]

    file_path = f"{mho.game_path}\\#Host_Start({glb_vars.selected_ip}).bat"

    with open(file_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(content))


####################################################################
# C2 更改 \Mhserver\ConfigOverride.ini 的 host 相官 IP/URL
def update_ini_host_ip():
    ip = glb_vars.selected_ip
    ini = glb_vars.ini

    mtx = {
        "HomePageUrl": f"http://{ip}/store/index.html",
        "HomeBannerPageUrl": f"http://{ip}/store/images/banner.png",
        "HeroesBannerPageUrl": f"http://{ip}/store/images/banner.png",
        "CostumesBannerPageUrl": f"http://{ip}/store/images/banner.png",
        "BoostsBannerPageUrl": f"http://{ip}/store/images/banner.png",
        "ChestsBannerPageUrl": f"http://{ip}/store/images/banner.png",
        "SpecialsBannerPageUrl": f"http://{ip}/store/images/banner.png",
        "RealMoneyUrl": f"https://{ip}/MTXStore/AddG",
        "BundleInfoUrl": f"http://{ip}/bundles/",
        "BundleImageUrl": f"http://{ip}/bundles/images/"
    }

    ini.set("Frontend", "PublicAddress", ip, save=False)
    ini.set("PlayerManager", "NewsUrl", f"http://{ip}/news/index.html", save=False)
    for k, v in mtx.items():
        ini.set("MTXStore", k, v, save=False)
    ini.save()


####################################################################
# C2 更改 \Apache24\htdocs\SiteConfig.xml 的 <str name="AuthServerAddress" value="localhost" />
def update_auth_server_address():
    import os

    file_path = os.path.join( mho.game_path, "Apache24","htdocs", "SiteConfig.xml")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        '<str name="AuthServerAddress" value="localhost" />',
        f'<str name="AuthServerAddress" value="{glb_vars.selected_ip}" />'
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


##################################################
# C1 取得 IP
def get_ips(config: AppConfig):
    local_ips = []

    for addrs in psutil.net_if_addrs().values():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                local_ips.append(addr.address)

    local_ips = list(set(local_ips))
    outbound_ip = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        outbound_ip = s.getsockname()[0]
    except OSError:
        pass
    finally:
        s.close()

    if outbound_ip and outbound_ip in local_ips:
        local_ips.remove(outbound_ip)
        local_ips.insert(0, outbound_ip)

    try:
        public_ip = requests.get("https://api.ipify.org", timeout=3).text
    except requests.RequestException:
        public_ip = None

    config.local_ips = local_ips
    config.outbound_ip = outbound_ip
    config.public_ip = public_ip


###########################################################################################################
# B3 對 ConfigOverride.ini: 初始化內容, 修改/新增 key, 移除 key, 讀取 key. (區段section, 鍵key, 值value)
class IniManager:
    def __init__(self, game_path):
        self.file_path = os.path.join(game_path, "MHServerEmu", "ConfigOverride.ini")
        self.encoding = "utf-8"
        self.lines = []
        self._ensure_file()
        self._load()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("")

    @staticmethod
    def _detect_encoding(raw: bytes) -> str:               # 偵測 ini 編碼
        if raw.startswith(b'\xef\xbb\xbf'):
            return "utf-8-sig"

        if raw.startswith(b'\xff\xfe'):
            return "utf-16-le"

        if raw.startswith(b'\xfe\xff'):
            return "utf-16-be"

        if len(raw) > 2:
            even_nulls = raw[0::2].count(0)
            odd_nulls = raw[1::2].count(0)

            if odd_nulls > even_nulls:
                try:
                    raw.decode("utf-16-le")
                    return "utf-16-le"
                except UnicodeDecodeError:
                    pass

            elif even_nulls > odd_nulls:
                try:
                    raw.decode("utf-16-be")
                    return "utf-16-be"
                except UnicodeDecodeError:
                    pass

        try:
            raw.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass

        try:
            encoding = locale.getpreferredencoding(False)
            raw.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            pass
        return "latin-1"

    def _load(self):
        with open(self.file_path, "rb") as f:
            raw = f.read()

        self.encoding = self._detect_encoding(raw)
        text = raw.decode(self.encoding)
        self.lines = text.splitlines()

    def _save(self):
        text = "\n".join(self.lines) + "\n"
        with open(self.file_path, "w", encoding=self.encoding) as f:
            f.write(text)

    # ini 大幅初始化, 使用的字典範例
    # sections = {
    #   "Section": { "key": "value" }
    # }
    def init_from_dict(self, sections: dict, save=True):
        new_lines = []

        for section, kv in sections.items():
            new_lines.append(f"[{section}]")
            for k, v in kv.items():
                new_lines.append(f"{k} = {v}")
            new_lines.append("")  # 空行

        self.lines = new_lines
        if save:
            self._save()

    # ini 大幅初始化, 使用''' 內容 ''' 範例
    def init_from_text(self, text: str, save=True):
        sections = {}
        current = None

        for line in text.splitlines():
            line = line.strip()

            if not line or line.startswith(";"):
                continue

            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                sections[current] = {}
            elif "=" in line and current:
                k, v = line.split("=", 1)
                sections[current][k.strip()] = v.strip()

        self.init_from_dict(sections, save=save)

    def _find_section(self, section):
        for i, line in enumerate(self.lines):
            if line.strip() == f"[{section}]":
                return i
        return -1

    def _find_key(self, section_index, key):
        for i in range(section_index + 1, len(self.lines)):
            line = self.lines[i].strip()

            if line.startswith("["):
                break

            # ❗ 跳過註解行
            if line.startswith(";"):
                continue

            if "=" in line:
                k = line.split("=", 1)[0].strip()
                if k == key:
                    return i
        return -1

    ### 函式1：寫入/覆蓋 ############################
    def set(self, section, key, value, save=True):
        sec_idx = self._find_section(section)
        if sec_idx == -1:
            # 新 section
            if self.lines and self.lines[-1] != "":
                self.lines.append("")

            self.lines.append(f"[{section}]")
            self.lines.append(f"{key} = {value}")

        else:
            key_idx = self._find_key(sec_idx, key)
            if key_idx == -1:
                # 插入到 section 尾
                insert_pos = sec_idx + 1
                while insert_pos < len(self.lines) and not self.lines[insert_pos].startswith("["):
                    insert_pos += 1
                self.lines.insert(insert_pos, f"{key} = {value}")
            else:
                self.lines[key_idx] = f"{key} = {value}"

        if save:
            self._save()

    ### 函式2：讀取 // key 存在, 回傳 value // 不存在, 回傳 None ###
    def get(self, section: str, key: str):
        sec_idx = self._find_section(section)
        if sec_idx == -1:
            return None

        key_idx = self._find_key(sec_idx, key)
        if key_idx == -1:
            return None

        line = self.lines[key_idx].lstrip("; ").strip()

        if "=" not in line:
            return ""

        return line.split("=", 1)[1].strip()

    ### 函式3：disable（加 ; ） #####################
    def disable(self, section, key, save=True):
        sec_idx = self._find_section(section)
        if sec_idx == -1:
            return

        key_idx = self._find_key(sec_idx, key)
        if key_idx == -1:
            return

        line = self.lines[key_idx]

        if not line.strip().startswith(";"):
            self.lines[key_idx] = "; " + line

        if save:
            self._save()

    ### 額外：手動存檔（給 GUI 用） #######
    def save(self):
        self._save()


##########################################################################
# B3 複製 *.sip 至 EMU\\data\game\.   // 回傳值: {True/False, "err_msg"}
def copy_game_sip_files():
    try:
        work_dir = mho.game_path

        src_dir = os.path.join(work_dir, "Data", "Game")
        dst_dir = os.path.join(work_dir, "MHServerEmu", "Data", "Game")
        files = ["Calligraphy.sip", "mu_cdata.sip"]

        for filename in files:
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, filename)

            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)

        return True, ""

    except Exception as e:
        msg = str(e).replace('\n', ' ').strip()            # 排除 \n 等可能破壞排版的字元
        return False, f"Copy_Error: {msg}"


##########################################################################
# B1 檢查 EMU 1.0.zip 與安裝處理   // 回傳值: {True/False, "massage"}   //True:成功, False:失敗  // {False + ""}:ZIP 檔案不存在  // {False + "err_msg"}:作業失敗
def install_emu_zip():
    try:
        work_dir = mho.game_path
        os.path.isdir(work_dir)
        zip_path = os.path.join(work_dir, "MHServerEmu-1.0.0.zip")

        if not os.path.isfile(zip_path):
            return False, ""                                               # 回傳 {False, ""} = 無 ZIP 檔

        apache_dir = os.path.join(work_dir, "Apache24")
        mh_dir = os.path.join(work_dir, "MHServerEmu")
        if os.path.exists(apache_dir) or os.path.exists(mh_dir):           # 檢查資料夾是否存在, 存在就更名.
            time_str = datetime_string(7)

            try:
                if os.path.exists(apache_dir):
                    new_apache = os.path.join(work_dir, f"Apache24.{time_str}")
                    os.rename(apache_dir, new_apache)

                if os.path.exists(mh_dir):
                    new_mh = os.path.join(work_dir, f"MHServerEmu.{time_str}")
                    os.rename(mh_dir, new_mh)

            except Exception as e:
                return False, f"Folder_Rename_Error: {e}"                # 回傳 {False, "err_mag"} = 作業失敗

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:       # 解壓縮 + 覆寫
                zip_ref.extractall(work_dir)

        except Exception as e:
            return False, f"Unzip_Error: {e}"                            # 回傳 {False, "err_mag"} = 作業失敗
        return True, ""

    except Exception as e:
        return False, f"Unknown_Error: {e}"                              # 回傳 {False, "err_mag"} = 作業失敗


##########################################################################
# b1 安裝 EMU 1.0.zip , 與結果處理
def post_install_emu_zip():

    result, err_msg = install_emu_zip()                       # 回傳值: {True/False, "massage"}, {False + ""}: ZIP 檔案不存在, {False + "err_msg"}: 作業失敗
    if result:
        gui.step_manager.set_status("frame_b1", "ok")
        init_ini()                                           # 建立 class ini, 並初始化內容值
    else:
        if err_msg == "":                                    # 去除奇怪的 "\n "
            gui.logger.log("MSG_B1_7", tag="red")
        else:
            gui.logger.log("MSG_B1_6", err_msg, tag="red")
        gui.step_manager.set_status("frame_b1", "error")

    glb_vars.b1_result = result                            # 將作業結果存入 class 全域變數


#########################################################################
#  B3 回傳 C:\Users\%username%\Documents\My Games\Marvel Heroes 連結
def get_mh_games_path_and_link():
    documents = Path.home() / "Documents"
    target_path = documents / "My Games" / "Marvel Heroes"
    resolved = target_path.resolve()

    return str(resolved), resolved.as_uri()


##########################################################################
# b2 需求埠與服務狀態
def get_service_map():
    service_map = {}
    try:
        output = subprocess.check_output(
            "sc queryex type= service state= all",
            shell=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        current_service = None
        for line in output.splitlines():
            line = line.strip()

            if line.startswith("SERVICE_NAME:"):
                current_service = line.split(":", 1)[1].strip()

            elif line.startswith("PID") and current_service:
                pid = int(line.split(":", 1)[1].strip())
                service_map.setdefault(pid, []).append(current_service)

    except Exception as e:
        print("ERR_FETCH_SERVICE_INFO_FAILED:", e)

    return service_map


##########################################################################
# B2 尋找需求埠的狀態
def find_ports():
    target_ports = {80, 8080, 443, 4306}
    service_map = get_service_map()
    results = []
    seen = set()                   # 用來去重 (port, pid)

    for conn in psutil.net_connections(kind='inet'):
        if not conn.laddr:
            continue

        port = conn.laddr.port
        pid = conn.pid
        if port not in target_ports or not pid:
            continue

        key = (port, pid)
        if key in seen:                # 已處理過就跳過
            continue
        seen.add(key)

        try:
            proc = psutil.Process(pid)
            exe = proc.exe()
            name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe = "N/A"
            name = "N/A"

        service_name = service_map.get(pid, None)
        results.append({
            "port": port,
            "pid": pid,
            "process": name,
            "path": exe,
            "service_name": service_name   # "if service_name is not None:" 可判斷是否為服務
        })

    return results


##########################################################################
# B2 檢測並顯示需求埠狀態
def is_required_port_free():
    results = find_ports()                # 當 results = [],{} 或 None 則代表port沒被佔用

    gui.logger.log("MSG_B2_2")
    if not results:                       # 指定 port未被佔用
        gui.logger.log("MSG_B2_3", tag="green")
        gui.step_manager.set_status("frame_b2", "ok")
        return True

    for r in results:
        gui.logger.log("MSG_B2_4", r['port'])             # print(f">Port: {r['port']}")
        process_pid = f"{r['process']} ({r['pid']})"
        gui.logger.log("MSG_B2_5", process_pid)           # print(f" -Process: {process_pid}")
        if r['path']:
            gui.logger.log("MSG_B2_6", r['path'])         # print(f" -Path: {r['path']}")
        if r['service_name']:
            srv_name = f"{', '.join(r['service_name'])}"
            gui.logger.log("MSG_B2_7", srv_name, )        # print(f" -Service Name: {srv_name}")

    gui.step_manager.set_status("frame_b2", "error")
    return False


#######################################################
# A2 mapping 轉換運行庫下載連結
def runtime_mapping(runtime, sys_arch):
    redist_download_link = {        # 使用原始字串 (r"") 確保反斜線內容不變
        ".net8": {
            "x64": "https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/8.0.25/windowsdesktop-runtime-8.0.25-win-x64.exe",
            "x86": "https://builds.dotnet.microsoft.com/dotnet/WindowsDesktop/8.0.25/windowsdesktop-runtime-8.0.25-win-x86.exe"
        },
        "vc2008": {
            "all": r"\InstallDependencies\MSVCRT9\vcredist_x86.exe",
        },
        "vc2010": {
            "x64": r"\InstallDependencies\MSVCRT10\vcredist_x64.exe",
            "x86": r"\InstallDependencies\MSVCRT10\vcredist_x86.exe"
        },
        "vc2013": {
            "x64": r"\InstallDependencies\MSVCRT13\vcredist_x64.exe",
            "x86": r"\InstallDependencies\MSVCRT13\vcredist_x86.exe"
        },
        "d3d": {
            "all": r"\InstallDependencies\DirectX\DXSETUP.exe"
        }
    }

    target = redist_download_link.get(runtime.lower())                   # 取得對應 runtime 的資料字典 (忽略大小寫以增加穩定性)
    if not target:
        return None

    out_link = target.get(sys_arch) or target.get("all")                 # 取得對應架構的連結，若無則取 "all"
    if not out_link:
        return None

    if not out_link.startswith("https"):                                 # 非 https 開頭的，就執行 file:/// 組合邏輯, 與 mho.game_path 組合
        return "file:///" + mho.game_path + out_link

    return out_link


#######################################################
# a1 檢查參數路徑是否為遊戲資料夾, 並作相關處理
def game_folder_check(pending_path, gui_obj):

    mho.detect_game(pending_path)
    if mho.game_exists:
        gui_obj.step_manager.set_status(0, "ok")
        gui_obj.logger.log("MSG_A1_8", tag="green")
        mho.game_path = pending_path
    else:
        gui_obj.step_manager.set_status(0, "error")
        gui_obj.logger.log("MSG_A1_9", tag="red")
        mho.game_path = ""


##################################################
#  通過[下一步]後的 frame 處理
def on_next_frame_handling(step_id):
    next_frame = {
        "frame_a1": "frame_a2",
        "frame_a2": "frame_a3",
        "frame_a3": "frame_b1",
        "frame_b1": "frame_b2",
        "frame_b2": "frame_b3",
        "frame_b3": "frame_c1",
        "frame_c1": "frame_c2",
    }

    next_id = next_frame.get(step_id)
    gui.step_manager.disable(step_id)
    gui.step_manager.show(next_id)
    gui.logger.insert_separator()


###################################################
# 按下[下一步]後的相關檢查與流程 // 不通過就什麼都不作
def on_next_clicked(step_id):

    if step_id == "frame_a1":
        if mho.game_path != "":                 # a1 通關條件: 正確的遊戲資料夾
            on_next_frame_handling(step_id)
            workflow_a2()

    elif step_id == "frame_a2":                 # a2 通關條件: 無, 全部放行
        on_next_frame_handling(step_id)
        workflow_a3()
    elif step_id == "frame_a3":                 # a3 通關條件: 無, 全部放行
        on_next_frame_handling(step_id)
        workflow_b1()
    elif step_id == "frame_b1":
        post_install_emu_zip()                  # 安裝 EMU_ZIP
        if glb_vars.b1_result:                  # b1 通關條件: EMU_ZIP 正確的處理
            on_next_frame_handling(step_id)
            workflow_b2()
    elif step_id == "frame_b2":                 # b2 通關條件: 無, 全部放行
        on_next_frame_handling(step_id)
        workflow_b3()
    elif step_id == "frame_b3":                 # b3 通關條件: 無, 全部放行
        on_next_frame_handling(step_id)
        workflow_c1()
    elif step_id == "frame_c1":                 # c1 通關條件: 有取得 IP
        glb_vars.selected_ip = gui.selected_ip.get()
        if glb_vars.local_ips:
            on_next_frame_handling(step_id)
            workflow_c2()
        else:
            workflow_c1(retry=True)


#############################################################################
# 方案流程(c2) lanhost
def workflow_c2():

    gui.logger.log("MSG_C2_1")
    gui.logger.log("MSG_C2_2", glb_vars.selected_ip, tag="green")

    update_auth_server_address()                     # 更改 SiteConfig.xml 裡的 IP/URL
    update_ini_host_ip()                             # 更改 ConfigOverride.ini 裡的 IP/URL
    create_host_play_bat()                           # 建立 #Host_Play(ip).bat
    create_online_play_bat()                         # 建立 #Lan_Play(ip).bat
    create_host_start_bat()                           # 建立 #Host_sStart(ip).bat

    gui.logger.log("MSG_C2_3", tag="mark")
    gui.logger.log("MSG_C2_4", tag="mark")
    gui.logger.log("MSG_C2_5", tag="green")
    gui.logger.log("MSG_C2_6")
    gui.logger.log("MSG_C2_7")
    gui.logger.log("MSG_C2_8", tag="highlight")
    gui.logger.log("MSG_C2_9")
    gui.step_manager.set_status("frame_c2", "ok")


#############################################################################
# 方案流程(c1) lanhost
def workflow_c1(retry=False):

    get_ips(glb_vars)                                             # 取得IP
    ips = ", ".join(glb_vars.local_ips)                           # 將 ips 轉為一列去頭尾純 IP 字串, 顯示用
    gui.cbox_c1["values"] = glb_vars.local_ips                    # 取 ips 當下拉選單值
    if not retry:
        gui.logger.log("MSG_C1_1")
        gui.logger.log("MSG_C1_1-1", tag="red")

    gui.logger.log("MSG_C1_2")
    if glb_vars.local_ips:
        gui.selected_ip.set(glb_vars.local_ips[0])                # 取 ips 第一筆當預設IP
        gui.logger.log("MSG_C1_3", ips)
        if not glb_vars.outbound_ip is None:
            gui.logger.log("MSG_C1_4", glb_vars.outbound_ip)

        if not glb_vars.public_ip is None:
            gui.logger.log("MSG_C1_5")
            gui.logger.log(glb_vars.public_ip, tag="white", raw=True)
            gui.logger.log("MSG_C1_6")

        gui.logger.log("\n", raw=True)
        gui.logger.log("MSG_C1_7", tag="highlight")
        gui.step_manager.set_status("frame_c1", "ok")
    else:
        gui.logger.log("MSG_C1_8", tag="red")
        gui.step_manager.set_status("frame_c1", "error")


#############################################################################
# 方案流程(B3) Offline
def workflow_b3():
    gui.logger.log("MSG_B3_1")

    result, err_msg = copy_game_sip_files()                      # 回傳值: {True/False, "err_msg"},
    if result:
        gui.logger.log("MSG_B3_3", tag="mark")
        gui.step_manager.set_status("frame_b3", "ok")
    else:
        gui.logger.log("MSG_B3_2", err_msg, tag="red")
        gui.step_manager.set_status("frame_b3", "error")

    gui.logger.log("MSG_B3_4", tag="mark")
    gui.logger.log("MSG_B3_5", tag="mark")

    profile_path, profile_url = get_mh_games_path_and_link()     # 取得 C:\Users\%username%\Documents\My Games\Marvel Heroes 路徑與 URL
    gui.logger.log("MSG_B3_6")
    gui.logger.log(profile_path, link=profile_url, raw=True)
    gui.logger.log("MSG_B3_7")

    if glb_vars.selected_func == "b":
        create_host_play_bat()                                   # 建立 Offline_play.bat
        gui.logger.log("\n", raw=True)
        gui.logger.log("MSG_B3_8", tag="highlight")
    else:
        on_next_clicked("frame_b3")                              # lanhost 跑這邊, 虛擬按下一步


#############################################################################
# 方案流程(B2) Offline
def workflow_b2():
    gui.logger.log("MSG_B2_1", tag="mark")

    pore_free = is_required_port_free()                   # 檢測需求埠被佔狀況
    if not pore_free:
        gui.logger.log("MSG_B2_8", tag="red")

    gui.logger.log("\n", raw="True")
    gui.logger.log("MSG_B2_9", tag="highlight")


#############################################################################
# 方案流程(B1) Offline
def workflow_b1():
    gui.logger.log("MSG_B1_1", tag="mark")
    gui.logger.log("https://github.com/Crypto137/MHServerEmu/releases/download/1.0.0/MHServerEmu-1.0.0.zip", link="https://github.com/Crypto137/MHServerEmu/releases/download/1.0.0/MHServerEmu-1.0.0.zip", tag="mark", raw=True)
    gui.logger.log("MSG_B1_2", tag="mark")
    gui.logger.log("MSG_B1_3")
    gui.logger.log("MSG_B1_4")
    gui.logger.log("https://github.com/Crypto137/MHServerEmu", link="https://github.com/Crypto137/MHServerEmu", raw=True)
    gui.logger.log("MSG_B1_5")
    gui.logger.log("MSG_B1_8", tag="highlight")


#############################################################################
# 方案流程(A3) online
def workflow_a3():
    gui.logger.log("MSG_A3_1", tag="mark")
    gui.logger.log("MSG_A3_2")
    gui.logger.log("https://pastebin.com/cWAyA9kt", link="https://pastebin.com/cWAyA9kt", raw=True)
    gui.logger.log("\n ", raw=True)
    gui.logger.log("https://www.reddit.com/r/marvelheroes/comments/1lgwf31/mh_emu_info_private_server_list", link="https://www.reddit.com/r/marvelheroes/comments/1lgwf31/mh_emu_info_private_server_list/", raw=True)

    gui.logger.log("MSG_A3_3", mho.game_path, tag="green")
    gui.logger.log("MSG_A3_4", tag="mark")
    gui.logger.log("MSG_A3_5")
    gui.logger.log("MSG_A3_6")
    gui.logger.log_image("./images/server.png", pad_x=8)

    gui.step_manager.set_status("frame_a3", "ok")
    create_online_play_bat()                           # 建立 online 用的 play.bat 群
    if glb_vars.selected_func == "a":
        gui.logger.log("\n", raw=True)
        gui.logger.log("MSG_A3_7", tag="highlight")
    else:
        on_next_clicked("frame_a3")                    # online / lanhost 跑這邊, 虛擬按下一步


#############################################################################
# 方案流程(A2) online
def workflow_a2():
    gui.logger.log("MSG_A2_1", mho.game_path, tag="mark")
    gui.logger.log("MSG_A2_2", mho.game_exe_path)
    gui.logger.log("MSG_A2_3", mho.game_version)
    gui.logger.log("MSG_A2_4")

    # env.d3d_info=env.vc2008=env.vc2010=env.vc2013=env.dotnet8=None    # Test
    gui.logger.log("MSG_A2_5", env.windows_info)
    gui.logger.log("MSG_A2_6", env.cpu_name)
    gui.logger.log("MSG_A2_6-1", env.cpu_count)
    gui.logger.log("MSG_A2_7", env.ram_gb)
    gui.logger.log("MSG_A2_8", env.gpu_info)
    gui.logger.log("MSG_A2_9", env.gpu_driver)
    gui.logger.log("MSG_A2_10", env.d3d_info)
    gui.logger.log("MSG_A2_11", env.vc2008)
    gui.logger.log("MSG_A2_12", env.vc2010)
    gui.logger.log("MSG_A2_13", env.vc2013)
    gui.logger.log("MSG_A2_14", env.dotnet8)

    critical_components = {
        "d3d_info": ("d3d", "MSG_A2_16"),
        "vc2008": ("vc2008", "MSG_A2_17"),
        "vc2010": ("vc2010", "MSG_A2_18"),
        "vc2013": ("vc2013", "MSG_A2_19"),
        "dotnet8": (".net8", "MSG_A2_20"),
    }

    missing_items = [k for k, v in critical_components.items() if getattr(env, k) is None]
    if missing_items:
        gui.step_manager.set_status("frame_a2", "error")
        gui.logger.log("MSG_A2_15")

        for item in missing_items:
            runtime_key, msg_id = critical_components[item]
            now_link = runtime_mapping(runtime_key, env.win_arch)
            gui.logger.log(msg_id)
            gui.logger.log(now_link, link=now_link, raw=True)
        gui.logger.log("\n\n", raw=True)
    else:
        gui.step_manager.set_status("frame_a2", "ok")

    gui.logger.log("MSG_A2_21", tag="highlight")


#############################################################################
# 主選單功能流程(A1) online
def solutions(want_to):
    mapping = {
        "online": "a",
        "offline": "b",
        "lanhost": "c"
    }

    gui.logger.log("MSG_A1_1")
    gui.logger.log("MSG_A1_2", link="https://steamdb.info/app/226320/info")
    gui.logger.log("MSG_A1_3")
    gui.logger.log("MSG_A1_4", link="https://archive.org")
    gui.logger.log("MSG_A1_5")
    gui.logger.log_image("./images/game_folder.png", pad_x=8)
    gui.logger.log("MSG_A1_6")
    gui.logger.log("MSG_A1_7", tag="highlight")

    gui.step_manager.show(gui.frame_a1)                  # 顯示 Frame_a1, 開始跑流程
    glb_vars.selected_func = mapping.get(want_to)


######################################################################################################
# 主程式
if __name__ == "__main__":                                 # 指定本程式是主程式段

    gui = AppUI(
        solutions=solutions,                               # 傳 solutions 給 AppUI (跨檔案)
        mho=mho,                                           # 傳 mho 給 AppUI 使用 (跨檔案)
        game_folder_check=game_folder_check,               # 傳 game_folder_check 給 AppUI (跨檔案)
        on_next_clicked=on_next_clicked,                   # 傳 on_next 給 AppUI (跨檔案)
        is_required_port_free=is_required_port_free        # 傳 is_required_port_free 給 AppUI (跨檔案)
    )

    env.detect_all()                                                 # 偵測電腦狀況
    root = gui.tk01
    root.title("[Marvel Heroes Omega 2.16a]  EasyReady v0.995")
    icon_path = resource_path("./images/EasyReady.ico")
    root.iconbitmap(icon_path)
    root.mainloop()
    gui.run()



