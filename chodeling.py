import os
import re
import sys
import math
import time
import json
import asyncio
import logging
import datetime
import keyboard
import threading
from pathlib import Path
from decimal import Decimal
from colorama import Fore, Style
from twitchAPI.twitch import Twitch, TwitchUser
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent, TwitchBackendException
from twitchAPI.chat import Chat, EventData, ChatMessage
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME, Document

# ToDo; Add 'upsidedown text to everything' easter egg
# ToDo; Add stats for time added (also rework chodebot & user documents to keep track & write script to scrape past logs to build data)

if getattr(sys, 'frozen', False):
    folder_name = "Thee ChodelingApp"
    if sys.platform == "win32":
        from ctypes import windll, create_unicode_buffer
        buf = create_unicode_buffer(260)
        if windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:
            data_path = f"{Path(buf.value)}\\{folder_name}\\"
        else:
            data_path = f"{Path(os.environ['USERPROFILE']) / 'Documents'}\\{folder_name}\\"
    else:
        data_path = f"{Path.home() / 'Documents'}\\{folder_name}\\"
else:
    data_path = f"{os.path.dirname(__file__)}\\"

directories = {
    "auth": f"{data_path}auth\\",
    "data": f"{data_path}data\\",
    "logs": f"{data_path}logs\\",
    "logs_archive": f"{data_path}logs\\archive_log\\"
}

auth_json = f"{directories['auth']}auth_info.json"
chodeling_string = f"{directories['auth']}chodeling_string.txt"
twitch_token = f"{directories['auth']}twitch_token.json"

Path(directories['auth']).mkdir(parents=True, exist_ok=True)
Path(directories['data']).mkdir(parents=True, exist_ok=True)
Path(directories['logs']).mkdir(parents=True, exist_ok=True)
Path(directories['logs_archive']).mkdir(parents=True, exist_ok=True)

nl = "\n"
logger_list = []


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch
        self.commands_available = {
            "general": [
                "clip",
                "command",
                "discord",
                "followage",
                "lastcomment",
                "lurk",
                "pointsburn",
                "pointsgamble",
                "sr",
                "throne",
                "tip",
                "treat"
            ],
            "rank": [
                "givepoints",
                "levelcheck",
                "levelleader",
                "pointscheck",
                "pointsleader"
            ],
            "mini_games": [
                "bet",
                "bingo",
                "bite",
                "burn",
                "cutline",
                "fight",
                "fish",
                "heist",
                "iq",
                "jail",
                "kick",
                "lick",
                "numberize",
                "pants",
                "pinch",
                "pounce",
                "pp",
                "punch",
                "slap",
                "tag",
                "tickle",
                "unoreverse",
                "untag"
            ],
            "counter": [
                "ats",
                "cod",
                "jointscount",
                "streamcount"
            ],
            "marathon": [
                "freepack",
                "ice",
                "loots",
                "lube",
                "time2add",
                "timecurrent",
                "timemax",
                "timepause",
                "timerate",
                "timesofar",
                "time"
            ],
            "special": [
                "angryflip",
                "attn",
                "chodyhug",
                "flip",
                "free",
                "fuck",
                "holyshit"
                "hug",
                "shit"
                "petty",
                "rageflip",
                "unflip",
                "unholyshit",
                "vanish"
            ],
            "chodelings": [
                "ak",
                "beckky",
                "carnage",
                "clammy",
                "moist",
                "dark",
                "fire",
                "hour",
                "joe",
                "lore",
                "moony",
                "mullens",
                "mull",
                "pious",
                "queenpenguin",
                "ronin",
                "rubi",
                "shat",
                "silencer",
                "toodles",
                "whoudini",
                "willsmash",
                "xbox"
            ],
            "mods": [
                "shutdown"
            ],
            "unlisted": [
                "addlurk",
                "addpoints",
                "addtime",
                "cardlube",
                "changerate",
                "clearlists",
                "cuss",
                "direction",
                "pausetime",
                "remtime",
                "rtag",
                "test"
            ]
        }
        self.const = {
            "bingo_cost": 10000,
            "level": 150,
            "free_pack": 28800,
            "wait_bet": 600,
            "wait_heist": 21600
        }
        self.data_settings = {
            "flash": f"{directories['data']}flash.txt",
            "line_dash": f"{directories['data']}line_separator.txt",
            "types_always_display": f"{directories['data']}types_always_display.txt",
            "types_heist": f"{directories['data']}types_heist.txt",
            "types_sort": f"{directories['data']}types_sort.txt",
            "types_xp_display": f"{directories['data']}types_xp_display.txt",
            "window_length": f"{directories['data']}window_length.txt",
            "xp_bar_key": f"{directories['data']}xp_bar_key.txt"
        }
        self.length = 100
        self.line_dash = "-"
        self.login_details = {
            "target_id": "268136120",
            "target_name": "TheeChody"
        }
        self.settings = {
            "types_always_display": (
                "auto_cast_remaining",
                "level",
                "points",
                "points_xp"
            ),
            "types_heist": (
                "basic_bitches",
                "barely_able",
                "semi-pro",
                "professionals",
                "thee_a-team"
            ),
            "types_sort": (
                "alphabetic",
                "quantity",
                "value",
                "value_individual"
            ),
            "types_xp_display": (
                "xp_percent",
                "xp_progress",
                "xp_both"
            )
        }
        self.special_commands = {
            "bet": "^B",
            "bbet": "^BB",
            "fish": "^F",
            "fish_beet": "^RB",
            "fish_stroke": "^RS",
            "free_pack": "^C",
            "heist": "^H",
            "joints_count_update": "^J",
            # "quit": "^Q"
        }
        self.special_users = {
            "bingo": {
                "carnage_deamon": "659640208",
                "Free2Escape": "777768639"
            },
            "game_admin": {
                "TheeChodebot": "1023291886"
            }
        }
        self.target_scopes = [
            AuthScope.CHAT_READ,
            AuthScope.CHAT_EDIT,
            AuthScope.USER_BOT,
            AuthScope.USER_WRITE_CHAT
        ]
        self.variables_channel = {}
        self.variables = {}

    async def check_permissions(self, user_id: str, perm_check: str) -> bool:
        bingo_mods = list(self.special_users['bingo'].values())
        channel_mods = self.variables_channel['mods']
        game_admins = list(self.special_users['game_admin'].values())
        try:
            if user_id == self.login_details['target_id']:
                return True
            elif perm_check == "game_admin" and user_id in game_admins:
                return True
            elif perm_check == "mods" and user_id in channel_mods:
                return True
            elif perm_check == "mini_game_bingo" and user_id in list(bingo_mods + channel_mods + game_admins):
                return True
            return False
        except Exception as error_permission_check:
            await self.msg_error("check_permissions", "Generic Error", error_permission_check)
            return False

    def data_check(self):
        def write_new_file(filename: str, var_write: str):
            with open(filename, "w", encoding="utf-8") as file:
                file.write(var_write)
            logger.info(f"{fortime()}: '{filename}'\nFile NOT FOUND, CREATED!")
            time.sleep(2.5)

        for setting, path in self.data_settings.items():
            try:
                if not os.path.exists(path):
                    if setting == "flash":
                        write_new_file(path, "4, 0.5")
                    elif setting == "line_dash":
                        write_new_file(path, "-")
                    elif setting == "window_length":
                        write_new_file(path, "100")
                    elif setting == "xp_bar_key":
                        write_new_file(path, "#")
                    else:
                        write_new_file(path, str(self.settings[setting][0]))
            except Exception as error_writing_new_file:
                asyncio.run(self.msg_error("bot.data_check", f"Error writing new file\n{setting} to {path}\nWill shutdown in 10 seconds", error_writing_new_file))
                time.sleep(10)
                return False
        return True

    def long_dashes(self):
        return f"{self.line_dash * self.length}"

    def set_dashes(self):
        self.length = read_file(self.data_settings['window_length'], int)
        self.line_dash = read_file(self.data_settings['line_dash'], str)

    def set_vars(self):
        channel_document = asyncio.run(refresh_document_channel())
        self.variables_channel['mods'] = channel_document['data_lists']['mods']
        self.variables_channel['heist'] = channel_document['data_games']['heist']
        self.variables_channel['upgrades_fish'] = channel_document['data_games']['fish']['upgrades']
        for setting, setting_path in self.data_settings.items():
            if setting not in ("line_dash", "window_length"):
                self.variables[setting] = read_file(setting_path, str)

    @staticmethod
    async def check_self_id(chodeling_id: str):
        if chodeling_id == user.id:
            print(colour("yellow", "Can't choose yourself!!"))
            await asyncio.sleep(3)
            return False
        return True

    @staticmethod
    async def check_self_name(chodeling_name: str):
        if chodeling_name == user.display_name.lower():
            print(colour("yellow", "Can't choose yourself!!"))
            await asyncio.sleep(3)
            return False
        return True

    @staticmethod
    async def go_back(main_menu: bool = False):
        print('Returning to Main Menu' if main_menu else 'Going Back')
        await asyncio.sleep(1)

    @staticmethod
    async def invalid_entry(invalid_type: type(str) | type(int)):
        print(f"{colour('red', 'Invalid')} {colour('yellow', 'Number' if invalid_type == int else 'Text')} {colour('red', 'entry, try again')}")
        await asyncio.sleep(2)

    @staticmethod
    async def msg_error(function_name: str, error_type: any, error_str: any):
        logger.error(f"{colour('yellow', f'{bot.long_dashes()}')}\n"
                     f"{colour('red', f'{fortime()}: Error in {function_name}')}\n"
                     f"{colour('yellow', f'{error_type}')}\n"
                     f"{colour('red', f'{error_str}')}\n"
                     f"{colour('yellow', f'{bot.long_dashes()}')}")
        await asyncio.sleep(5)

    @staticmethod
    async def msg_no_perm():
        cls()
        print(await top_bar("Permission Error"))
        input(f"{colour('yellow', 'Required Permissions Not Satisfied!!')}\n"
              "Hit Enter to go back")
        await bot.go_back()

    @staticmethod
    async def not_programmed():
        cls()
        print(await top_bar("Not Programmed Yet"))
        input(f"{colour('yellow', 'One Day....')} 😝\n"
              "Hit Enter To Go Back")
        await bot.go_back()


# ----------- Bot Functions -----------
async def auth_bot():
    twitch_helper = UserAuthenticationStorageHelper(bot, bot.target_scopes, Path(twitch_token))
    await twitch_helper.bind()
    logger.info(f"{fortime()}: Bot Authenticated Successfully!!\n{bot.long_dashes()}")


def check_db_auth() -> dict | None:
    def fetch_stock_auth() -> dict | None:
        db_string = read_file(chodeling_string, str)
        if db_string is None:
            return None
        return {
            "bot_id": None,
            "secret_id": None,
            "db_string": db_string
        }

    if not os.path.exists(auth_json):
        stock_json = fetch_stock_auth()
        if stock_json is None:
            logger.error(f"{fortime()}: Error setting DB String!! Did you setup thee auth stuff right? Reach out to TheeChody")
            time.sleep(15)
            return None
        save_json(stock_json, auth_json, True)
    auth_dict = read_file(auth_json, {"json": True})
    if None in (auth_dict['bot_id'], auth_dict['secret_id']):
        auth_dict = update_auth_json(auth_dict)
    return auth_dict


def check_numbered_list(list_check: list) -> list:
    new_list = []
    for item in list_check:
        while item.startswith(" "):
            try:
                item = item.lstrip(" ")
            except Exception as error_stripping_whitespace:
                asyncio.run(bot.msg_error("check_numbered_list", "Error stripping whitespace from start", error_stripping_whitespace))
                break
        try:
            new_list.append(remove_period_area(item.lower()))
        except Exception as error_appending_new_list:
            asyncio.run(bot.msg_error("check_numbered_list", f"Error appending '{item}' to new_list", error_appending_new_list))
            new_list.append(item.lower())
            continue
    return new_list


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def colour(_colour: str, str_: str) -> str:
    if _colour == "blue":
        _colour = Fore.BLUE
    elif _colour == "cyan":
        _colour = Fore.CYAN
    elif _colour == "green":
        _colour = Fore.GREEN
    elif _colour == "purple":
        _colour = Fore.MAGENTA
    elif _colour == "red":
        _colour = Fore.RED
    elif _colour == "yellow":
        _colour = Fore.YELLOW
    else:
        _colour = Fore.RESET
    return f"{_colour}{str_}{Fore.RESET}"


def connect_mongo(db, db_string, alias):
    try:
        client = connect(db=db, host=db_string, alias=alias)
        logger.info(f"{fortime()}: MongoDB Connected\n{bot.long_dashes()}")
        time.sleep(1)
        client.get_default_database(db)
        logger.info(f"{fortime()}: Database Loaded\n{bot.long_dashes()}")
        return client
    except Exception as e:
        logger.error(f"{fortime()}: Error Connecting MongoDB -- {e}")
        return None


async def disconnect_mongo():
    try:
        disconnect_all()
        logger.info(f"{bot.long_dashes()}\nDisconnected from MongoDB")
    except Exception as e:
        logger.error(f"{fortime()}: Error Disconnection MongoDB -- {e}")
        return


async def fetch_setting(setting: str) -> int | tuple:
    if setting == "sortby":
        try:
            return bot.settings['types_sort'].index(bot.variables['types_sort'])
        except ValueError:
            await bot.msg_error("fetch_setting", f"{bot.variables['types_sort']}' is not valid!! (Returning Index 0)", ValueError)
            return 0
    elif setting == "flash":
        try:
            flash_frequency, flash_speed = bot.variables['flash'].split(', ', maxsplit=1)
            return int(flash_frequency), float(flash_speed)
        except Exception as error_returning_flash:
            await bot.msg_error("fetch_setting", "Returning flash Settings (Default '4, 0.5' Returned)", error_returning_flash)
            return 4, 0.5
    elif setting == "heist":
        try:
            return bot.settings['types_heist'].index(bot.variables['types_heist']) + 1
        except Exception as error_returning_heist:
            await bot.msg_error("fetch_setting", "heist_setting", error_returning_heist)
            return 0
    else:
        await bot.msg_error("fetch_setting", "Invalid Entry (Returning Index 0)", f"{setting} is not a valid setting!!!")
        return 0


async def flash_window(event_type: str):
    flash_frequency, flash_speed = await fetch_setting("flash")
    if event_type == "attn":
        colour = "47"
    elif event_type == "auto_cast_expired":
        colour = "30"
    else:
        colour = "27"
    os.system(f"color {colour}")
    await asyncio.sleep(flash_speed)
    for x in range(1, flash_frequency):
        os.system(f"color 07")
        await asyncio.sleep(flash_speed)
        os.system(f"color {colour}")
        await asyncio.sleep(flash_speed)
    os.system(f"color 07")


def fortime() -> str:
    return datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S')


async def get_auth_user_id() -> TwitchUser | None:
    user = None
    user_info = bot.get_users()
    try:
        async for entry in user_info:
            if type(entry) == TwitchUser:
                user = entry
                break
            else:
                await bot.msg_error("get_auth_user_id", "Generic Error", "NO USER FOUND IN 'user_info'")
                return None
    except Exception as e:
        await bot.msg_error("get_auth_user_id", "Generic Error", e)
        return None
    return user


def get_chodelings():
    chodelings_collection = mongo_db.twitch.get_collection('users')
    return chodelings_collection.find({})


def get_length(item: float | int | list | str) -> int:
    if type(item) in (int, float):
        return len(str(item))
    elif type(item) == list:
        length = 0
        for _item in item:
            _length = len(_item)
            length = _length if _length > length else length
        return length
    else:
        return len(item)


def hotkey_listen():
    clear_code = '\033'
    try:
        keyboard.add_hotkey("ctrl+shift+b", lambda: keyboard.write(f"{clear_code}{bot.special_commands['bet']}\r"))
        keyboard.add_hotkey("ctrl+shift+c", lambda: keyboard.write(f"{clear_code}{bot.special_commands['free_pack']}\r"))
        keyboard.add_hotkey("ctrl+shift+d+b", lambda: keyboard.write(f"{clear_code}{bot.special_commands['bbet']}\r"))
        keyboard.add_hotkey("ctrl+shift+f", lambda: keyboard.write(f"{clear_code}{bot.special_commands['fish']}\r"))
        keyboard.add_hotkey("ctrl+shift+h", lambda: keyboard.write(f"{clear_code}{bot.special_commands['heist']}\r"))
        keyboard.add_hotkey("ctrl+shift+j", lambda: keyboard.write(f"{clear_code}{bot.special_commands['joints_count_update']}\r"))
        # keyboard.add_hotkey("ctrl+shift+q", lambda: keyboard.write(f"{clear_code}{bot.special_commands['quit']}\r"))
        keyboard.add_hotkey("ctrl+shift+r+b", lambda: keyboard.write(f"{clear_code}{bot.special_commands['fish_beet']}\r"))
        keyboard.add_hotkey("ctrl+shift+s+r", lambda: keyboard.write(f"{clear_code}{bot.special_commands['fish_stroke']}\r"))
        keyboard.wait()
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'hotkey_listen' -- {e}")


async def log_shutdown(logger_list: list):
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{directories['logs']}{entry}", f"{directories['logs_archive']}{entry}")
            print(f"{entry} moved to archives..")
        except Exception as e:
            print(e)
            pass


def max_length(item: str, length: int, n: int = None) -> str:
    if n is not None:
        return f"{' ' * (length - len(str(n)))}{item}"
    else:
        return f"{item}{' ' * (length - len(item))}"


def numberize(n: float, decimals: int = 2) -> str:
    """
    :param n: number to be numberized
    :param decimals: number of decimal places to round to
    :return: converted number

    Converts numbers like:
    1,000 -> 1K
    1,000,000 -> 1M
    1,000,000,000 -> 1B
    1,000,000,000,000 -> 1T
    """
    def drop_zero(n: Decimal):
        """
        :param: n: number to be numberized
        :return: zero'd number

        Drop trailing 0s
        For example:
        10.100 -> 10.1
        """
        n = str(n)
        return n.rstrip('0').rstrip('.') if '.' in n else n

    def round_num(n: Decimal, decimals: int = 2):
        """
        :param: n: number to round
        :param: decimals: number of decimal places to round number
        :return: rounded number

        For example:
        10.0 -> 10
        10.222 -> 10.22
        """
        return n.to_integral() if n == n.to_integral() else round(n.normalize(), decimals)

    is_negative_string = ""
    if n < 0:
        is_negative_string = "-"
    n = abs(Decimal(n))
    if n < 1000:
        return is_negative_string + str(drop_zero(round_num(n, decimals)))
    elif 1000 <= n < 1000000:
        if n % 1000 == 0:
            return is_negative_string + str(int(n / 1000)) + "K"
        else:
            n = n / 1000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "K"
    elif 1000000 <= n < 1000000000:
        if n % 1000000 == 0:
            return is_negative_string + str(int(n / 1000000)) + "M"
        else:
            n = n / 1000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "M"
    elif 1000000000 <= n < 1000000000000:
        if n % 1000000000 == 0:
            return is_negative_string + str(int(n / 1000000000)) + "B"
        else:
            n = n / 1000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "B"
    elif 1000000000000 <= n < 1000000000000000:
        if n % 1000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000)) + "T"
        else:
            n = n / 1000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "T"
    elif 1000000000000000 <= n < 1000000000000000000:
        if n % 1000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000)) + "Qd"
        else:
            n = n / 1000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Qd"
    elif 1000000000000000000 <= n < 1000000000000000000000:
        if n % 1000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000)) + "Qn"
        else:
            n = n / 1000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Qn"
    elif 1000000000000000000000 <= n < 1000000000000000000000000:
        if n % 1000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000)) + "Sx"
        else:
            n = n / 1000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Sx"
    elif 1000000000000000000000 <= n < 1000000000000000000000000000:
        if n % 1000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000)) + "Sp"
        else:
            n = n / 1000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Sp"
    elif 1000000000000000000000000 <= n < 1000000000000000000000000000000:
        if n % 1000000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000000)) + "Oc"
        else:
            n = n / 1000000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "Oc"
    elif 1000000000000000000000000000 <= n < 1000000000000000000000000000000000:
        if n % 1000000000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000000000)) + "No"
        else:
            n = n / 1000000000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "No"
    elif 1000000000000000000000000000000 <= n < 1000000000000000000000000000000000000:
        if n % 1000000000000000000000000000000000 == 0:
            return is_negative_string + str(int(n / 1000000000000000000000000000000000)) + "De"
        else:
            n = n / 1000000000000000000000000000000000
            return is_negative_string + str(drop_zero(round_num(n, decimals))) + "De"
    else:
        return is_negative_string + str(n)


async def print_status(status: bool, reason: str = "", error: bool = False):
    if status:
        print(colour("green", "Message Sent To Chat Successfully"))
    else:
        print_msg = f"{colour('red', 'Message Send Failed')}\n{reason}"
        if error:
            await bot.msg_error("special_command", "msg_fail", print_msg)
        else:
            print(print_msg)
    await asyncio.sleep(2 if status else 10 if error else 3)


def read_file(file_name: str, return_type: type(bool) | type(dict) | type(float) | type(int) | type(list) | type(str)) -> bool | dict | float | int | list | str | None:
    def open_file(json_: bool = False):
        with open(file_name, "r", encoding="utf-8") as file:
            if json_:
                return json.load(file)
            else:
                return file.read()

    try:
        if return_type == bool:
            variable = open_file()
            if variable == "True":
                return True
            elif variable == "False":
                return False
            else:
                return f"ValueError Converting {variable} to {return_type}"
        elif type(return_type) == dict:
            if return_type['json']:
                return open_file(True)
            else:
                return dict(open_file())
        elif return_type == dict:
            return dict(open_file())
        elif type(return_type) == list:
            variable = open_file()
            if return_type[1] == "split":
                variable = variable.split(return_type[2], maxsplit=return_type[3])
            elif return_type[1] == "splitlines":
                variable = variable.splitlines()
            if return_type[0] == map:
                return list(map(str, variable))
            else:
                return list(variable)
        elif return_type in (int, float):
            variable = float(open_file())
            if return_type == float:
                return variable
            return int(variable)
        else:
            return open_file()
    except FileNotFoundError:
        logger.error(f"{fortime()}: {file_name} Doesn't Exist!")
        time.sleep(5)
        return None
    except ValueError:
        variable = open_file()
        return f"ValueError Converting {variable} (type; {type(variable)}) to {return_type}"
    except Exception as e:
        error_msg = f"{fortime()}: Error in 'read_file' -- Generic Error -- {e}"
        logger.error(error_msg)
        time.sleep(5)
        return error_msg


async def refresh_document_channel() -> Document | None:
    try:
        channel_collection = mongo_db.twitch.get_collection("channels")
        return channel_collection.find_one({"_id": bot.login_details['target_id']})
    except FileNotFoundError:
        await bot.msg_error("refresh_document_channel", "FileNotFound", FileNotFoundError)
        return None
    except Exception as e:
        await bot.msg_error("refresh_document_channel", "Generic", e)
        return None


async def refresh_document_user(target_user: int | str = None) -> Document | None:
    try:
        users_collection = mongo_db.twitch.get_collection('users')
        if target_user is None:
            return users_collection.find_one({"_id": user.id})
        elif type(target_user) == int:
            return users_collection.find_one({"_id": str(target_user)})
        elif type(target_user) == str:
            return users_collection.find_one({"name": target_user})
        else:
            await bot.msg_error("refresh_document_user", "INTERNAL ERROR (INVALID 'target_user' TYPE)", f"EXPECTED TYPES: int | str | None -- GOT {type(target_user)}")
            return None
    except FileNotFoundError:
        await bot.msg_error("refresh_document_user", "FileNotFound", FileNotFoundError)
        return None
    except Exception as e:
        await bot.msg_error("refresh_document_user", "Generic", e)
        return None


def remove_period_area(var: str) -> str:
    try:
        index = var.index('.')
        return var[index+2:]
    except ValueError:
        return var


def save_json(dict_: dict, file_save: str, first_create: bool = False):
    if dict_ is not None:
        with open(file_save, "w", encoding="utf-8") as file:
            json.dump(dict_, file, indent=4, ensure_ascii=False)
        if first_create:
            logger.info(f"{fortime()}: First Time Run Detected!!\n'{auth_json}' File Created!")
            time.sleep(5)


async def send_chat_msg(msg: str) -> (bool, str, bool):
    try:
        await bot.send_chat_message(bot.login_details['target_id'], user.id, msg)
        return True, "", False
    except TwitchBackendException:
        try:
            await asyncio.sleep(3)
            await bot.send_chat_message(bot.login_details['target_id'], user.id, msg)
            return True, colour("yellow", "TwitchBackendException Handled OK"), False
        except Exception as error_twitch_backend:
            return False, f"TwitchBackendException Handled FAIL\n{error_twitch_backend}", True
    except Exception as general_error:
        return False, f"Generic Error\n{general_error}", True


def setup_logger(name: str, log_file: str, logger_list: list, level=logging.INFO):
    try:
        local_logger = logging.getLogger(name)
        handler = logging.FileHandler(f"{directories['logs']}{log_file}", mode="w", encoding="utf-8")
        if name == "logger":
            console_handler = logging.StreamHandler()
            local_logger.addHandler(console_handler)
        local_logger.setLevel(level)
        local_logger.addHandler(handler)
        logger_list.append(f"{log_file}")
        return local_logger
    except Exception as e:
        print(f"{fortime()}: ERROR in setup_logger - {name}/{log_file}/{level} -- {e}")
        time.sleep(15)
        logger_list.append(None)
        return None


def style(style_: str, str_: str) -> str:
    if style_ == "bright":
        style_ = Style.BRIGHT
    elif style_ == "dim":
        style_ = Style.DIM
    else:
        style_ = Style.NORMAL
    return f"{style_}{str_}{Style.RESET_ALL}"


async def special_command(key_stroke: str):
    msg_send, status, reason, error = "", False, "", False
    try:
        if key_stroke == bot.special_commands['bet']:
            msg = "!bet"
            now_time = datetime.datetime.now()
            user_document = await refresh_document_user()
            if user_document['data_games']['gamble']['last'] is None:
                msg_send = msg
            elif now_time.timestamp() - user_document['data_games']['gamble']['last'].timestamp() < bot.const['wait_bet']:
                wait_time = int(bot.const['wait_bet'] - (now_time.timestamp() - user_document['data_games']['gamble']['last'].timestamp()))
                reason = colour("yellow", f"Gotta Wait {str(datetime.timedelta(seconds=wait_time)).title()}")
            else:
                msg_send = msg
        elif key_stroke == bot.special_commands['bbet']:
            msg_send = "!bet doubleb"
        elif key_stroke == bot.special_commands['fish']:
            user_document = await refresh_document_user()
            cast_difference = bot.variables_channel['upgrades_fish']['rod'][str(user_document['data_games']['fish']['upgrade']['rod'])]['autocast_limit'] - user_document['data_games']['fish']['auto']['cast']
            if cast_difference > 0:
                msg_send = f"!fish {cast_difference if user.id != bot.special_users['bingo']['Free2Escape'] else '6969'}"
            else:
                reason = colour("yellow", "Already At Maximum Auto Casts!!")
        elif key_stroke == bot.special_commands['fish_beet']:
            msg_send = "!fish beet rod"
        elif key_stroke == bot.special_commands['fish_stroke']:
            msg_send = "!fish stroke rod"
        elif key_stroke == bot.special_commands['free_pack']:
            msg = "!freepack"
            now_time = datetime.datetime.now()
            user_document = await refresh_document_user()
            if user_document['data_user']['dates']['daily_cards'][1] is None:
                msg_send = msg
            elif now_time.timestamp() - user_document['data_user']['dates']['daily_cards'][1].timestamp() < bot.const['free_pack']:
                reason = colour("yellow", f"Gotta Wait {str(datetime.timedelta(seconds=int(bot.const['free_pack'] - (now_time.timestamp() - user_document['data_user']['dates']['daily_cards'][1].timestamp())))).title()}")
            else:
                msg_send = msg
        elif key_stroke == bot.special_commands['heist']:
            msg = f"!heist {await fetch_setting('heist')}"
            now_time = datetime.datetime.now()
            user_document = await refresh_document_user()
            if user_document['data_games']['heist']['gamble']['last'] is None:
                msg_send = msg
            elif now_time.timestamp() - user_document['data_games']['heist']['gamble']['last'].timestamp() < bot.const['wait_heist']:
                reason = colour("yellow", f"Gotta Wait {str(datetime.timedelta(seconds=int(bot.const['wait_heist'] - (now_time.timestamp() - user_document['data_games']['heist']['gamble']['last'].timestamp())))).title()}")
            else:
                msg_send = msg
        elif key_stroke == bot.special_commands['joints_count_update']:
            if await bot.check_permissions(user.id, "mods"):
                msg_send = f"!jointscount update 1"
            else:
                reason = colour("red", "You can't do that!")
        # ToDo; Figure this shit out
        # elif key_stroke == bot.special_commands['quit']:
        #     pass
        else:
            reason = colour("red", f"{key_stroke} NOT VALID")
        if reason != "" and msg_send == "":
            await print_status(status, reason, error)
        else:
            status, reason, error = await send_chat_msg(msg_send)
            await print_status(status, reason, error)
    except Exception as update_number_error:
        await print_status(status, f"{fortime()}: Error in 'special_command' -- key_stroke; {key_stroke} -- Generic Error\n{update_number_error}", True)


def title(text, valid_chars='_/\\|:;".,(') -> str:
    def capitalize_match(match):
        word = match.group(0)
        return word[0].upper() + word[1:].lower() if word else word

    return re.compile(rf"([^{re.escape(valid_chars)}\s]+)").sub(capitalize_match, text)


async def top_bar(left_side: str) -> str:
    def level_mult(level_check: int):
        return 1.0 + ((level_check / 2) * level_check if level_check > 1 else 0)

    try:
        slots = []
        dashes = ""
        xp_key = bot.variables['xp_bar_key']
        user_document = await refresh_document_user()
        xp = user_document['data_user']['rank']['xp']
        boost = user_document['data_user']['rank']['boost']
        level = user_document['data_user']['rank']['level']
        level_before = level - 1
        xp_needed_current = (bot.const['level'] * level_mult(level)) * level
        xp_needed_last = (bot.const['level'] * level_mult(level_before)) * level_before
        xp_needed = xp_needed_current - xp_needed_last
        xp_into_level = max(0, xp - xp_needed_last)
        base_ratio = max(0, min(xp_into_level / xp_needed, 1))
        boosted_ratio = max(0, min((xp_into_level + boost) / xp_needed, 1))
        base_slots = math.floor(base_ratio * bot.length)
        boosted_slots = math.floor(boosted_ratio * bot.length) - base_slots
        empty_slots = bot.length - base_slots - boosted_slots
        slots.extend(["purple"] * base_slots)
        slots.extend(["blue"] * boosted_slots)
        slots.extend(["normal"] * empty_slots)
        try:
            if bot.variables['types_xp_display'] == bot.settings['types_xp_display'][0]:
                xp_text = f"{base_ratio * 100:.2f}%{f'{xp_key * 3}{numberize((boost / xp_needed) * 100)}%' if boost > 0 else ''}"
            elif bot.variables['types_xp_display'] == bot.settings['types_xp_display'][1]:
                xp_text = f"{numberize(xp_into_level)}/{numberize(xp_needed)}{f'{xp_key * 3}{numberize(boost)}' if boost > 0 else ''}"
            elif bot.variables['types_xp_display'] == bot.settings['types_xp_display'][2]:
                xp_text = f"{numberize(xp_into_level)}/{numberize(xp_needed)}({base_ratio * 100:.2f}%){f'{xp_key * 3}{numberize(boost)}({numberize((boost / xp_needed) * 100)}%)' if boost > 0 else ''}"
            else:
                xp_text = f"INVALID SETTING '{bot.variables['types_xp_display']}'".replace(' ', xp_key)
        except Exception as error_fetching_xp_show:
            xp_text = f"INVALID SETTING '{bot.variables['types_xp_display']}' | {str(error_fetching_xp_show).upper()}".replace(' ', xp_key)
        center_index = (bot.length - len(xp_text)) // 2
        for n, digit in enumerate(str(level)):
            slots[n] = (slots[n], digit)
        for n, digit in enumerate(reversed(str(level + 1))):
            slots[-(n + 1)] = (slots[-(n + 1)], digit)
        for n, char in enumerate(xp_text):
            slot_index = center_index + n
            if 0 <= slot_index < len(slots):
                slots[slot_index] = (slots[slot_index], char)
        for s in slots:
            if isinstance(s, tuple):
                _colour, char = s
                dashes += colour(_colour, char)
            else:
                dashes += colour(s, xp_key)
        try:
            if bot.variables['types_always_display'] == bot.settings['types_always_display'][0]:
                right_side = f"{numberize(user_document['data_games']['fish']['auto']['cast'])}/{numberize(bot.variables_channel['upgrades_fish']['rod'][str(user_document['data_games']['fish']['upgrade']['rod'])]['autocast_limit'])}"
            elif bot.variables['types_always_display'] == bot.settings['types_always_display'][1]:
                right_side = f"{user_document['data_user']['rank']['level']:,}"
            elif bot.variables['types_always_display'] == bot.settings['types_always_display'][2]:
                right_side = numberize(user_document['data_user']['rank']['points'])
            elif bot.variables['types_always_display'] == bot.settings['types_always_display'][3]:
                right_side = f"{numberize(user_document['data_user']['rank']['xp'])}/{numberize(xp_needed_current)}"
            else:
                right_side = f"INVALID SETTING '{bot.variables['types_always_display']}'"
        except Exception as error_fetching_always_show:
            right_side = f"INVALID SETTING | {str(error_fetching_always_show).upper()}"
        return f"{left_side}{' ' * (bot.length - (len(left_side) + len(str(right_side))))}{right_side}\n{dashes}"
    except Exception as error_creating_top_bar:
        await bot.msg_error("top_bar", "Generic Error", error_creating_top_bar)
        return f"{left_side}\n{bot.long_dashes()}"


def update_auth_json(current_dict: dict) -> dict:
    while True:
        cls()
        user_input = input("Enter In Client ID\n")
        if user_input == "":
            asyncio.run(bot.invalid_entry(str))
        else:
            current_dict['bot_id'] = user_input
            print(f"Setting '{current_dict['bot_id']}' as thee Client ID")
            time.sleep(2)
            break
    while True:
        cls()
        user_input = input("Enter In Secret ID\n")
        if user_input == "":
            asyncio.run(bot.invalid_entry(str))
        else:
            current_dict['secret_id'] = user_input
            print(f"Setting '{current_dict['secret_id']}' as thee Secret ID")
            time.sleep(2)
            break
    save_json(current_dict, auth_json)
    return current_dict


# ----------- ChodelingApp Functions -----------
async def chodeling_commands():
    async def show_command_category(command_key: str):
        if command_key in ("mods", "unlisted") and not await bot.check_permissions(user.id, "mods"):
            await bot.msg_no_perm()
        else:
            while True:
                cls()
                options = []
                length = get_length(len(bot.commands_available[command_key]))
                print(await top_bar(f"{command_key.title()} Commands"))
                try:
                    for n, cmd in enumerate(sorted(bot.commands_available[command_key], key=lambda x: x), start=1):
                        options.append(max_length(f"{n}. {cmd}", length, n))
                except Exception as error_printing_command:
                    await bot.msg_error("chodeling_commands", f"show_command '{command_key}'", error_printing_command)
                user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                   f"{bot.long_dashes()}\n"
                                   f"{f'Enter # Or Type Command To View{nl}' if len(options) > 0 else ''}"
                                   f"Enter 0 To Go Back\n")
                if user_input == "":
                    await bot.invalid_entry(str)
                elif user_input.isdigit():
                    user_input = int(user_input)
                    if user_input == 0:
                        await bot.go_back()
                        break
                    elif user_input <= len(options):
                        print(f"VALID -- You chose {remove_period_area(options[user_input - 1])}")
                        await asyncio.sleep(2)
                    else:
                        await bot.invalid_entry(int)
                elif user_input in bot.special_commands.values():
                    await special_command(user_input)
                elif user_input.lower() in check_numbered_list(options):
                    print(f"VALID -- You chose {user_input.lower()}")
                    await asyncio.sleep(2)
                else:
                    await bot.invalid_entry(str)

    while True:
        cls()
        options = []
        length = get_length(len(bot.commands_available.keys()))
        print(await top_bar("Commands Area"))
        try:
            for n, key in enumerate(sorted(bot.commands_available.keys(), key=lambda x: x), start=1):
                options.append(max_length(f"{n}. {key}", length, n))
        except Exception as error_fetching_commands:
            await bot.msg_error("chodeling_commands", "Fetching Specific Commands", error_fetching_commands)
        if len(options) > 0:
            for n, item in enumerate(check_numbered_list(options)):
                if item in ("mods", "unlisted") and not await bot.check_permissions(user.id, "mods"):
                    pass
                else:
                    print(options[n])
        user_input = input(f"{bot.long_dashes()}\n"
                           f"{f'Enter # Or Type Command To View{nl}' if len(options) > 0 else ''}"
                           f"Enter 0 To Go Back\n")
        if user_input == "":
            await bot.invalid_entry(str)
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back(True)
                break
            elif user_input <= len(options):
                await show_command_category(remove_period_area(options[user_input - 1]))
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        elif len(options) > 0 and user_input.lower() in check_numbered_list(options):
            await show_command_category(user_input.lower())
        else:
            await bot.invalid_entry(str)


async def chodeling_leaderboards():
    async def show_leaderboard(leaderboard_name: str, leaderboard: dict):
        def space(item: str):
            return f"{' ' * (left_space - len(item))}{item}"

        cls()
        left_space = 0
        length = get_length(len(leaderboard.keys()))
        for value in leaderboard.values():
            if type(value) == list:
                len_comp = len(f"{numberize(value[0])}({numberize(value[1])}) | ")
            else:
                len_comp = len(f"{numberize(value)} | ")
            left_space = len_comp if len_comp > left_space else left_space
        print(await top_bar(f"{leaderboard_name} Leaderboard"))
        for n, (key, value) in enumerate(leaderboard.items(), start=1):
            try:
                str_ = max_length(f"{n}. ", length, n)
                if type(value) == list:
                    if len(value) > 2:
                        for nn in range(0, len(value)):
                            str_ += f"{numberize(value[nn])} | "
                    else:
                        str_ += space(f'{numberize(value[0])}({numberize(value[1])}) | ')
                    str_ += f"{key}"
                else:
                    str_ += f"{space(f'{numberize(value)} | ')}{key}"
                print(str_)
            except Exception as error_printing_str_:
                await bot.msg_error("chodeling_leaderboards", "Error printing str_", error_printing_str_)
                continue
        input(f"{bot.long_dashes()}\nHit Enter To Go Back")

    while True:
        cls()
        print(await top_bar("Chodeling Leaderboards"))
        user_input = input(f"Enter  1 To View Bingo Leaderboards\n"
                           f"Enter  2 To View Check-in Leaderboard\n"
                           f"Enter  3 To View Fight Leaderboards\n"
                           f"Enter  4 To View Fish Leaderboards\n"
                           f"Enter  5 To View Free Pack Leaderboard\n"
                           f"Enter  6 To View Gamble Leaderboards\n"
                           f"Enter  7 To View Heist Leaderboard\n"
                           f"Enter  8 To View Jail Leaderboards\n"
                           f"Enter  9 To View Rank Leaderboards\n"
                           f"Enter 10 To View Tag Leaderboards\n"
                           f"Enter  0 To Go Back\n")
        if user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back(True)
                break
            elif user_input == 1:
                while True:
                    async def build_bingo_dict(type_: str):
                        dict_ = {}
                        chodelings = get_chodelings()
                        for chodeling in chodelings:
                            total = 0
                            major = 0
                            major_points = 0
                            minor = 0
                            minor_points = 0
                            for date_ in chodeling['data_games']['bingo']['history'].values():
                                for data_ in date_.values():
                                    try:
                                        total += 1
                                        major += 1 if data_['major_bingo'] else 0
                                        if 'points_won' in data_:
                                            major_points += data_['points_won']
                                        minor += 1 if data_['minor_bingo'] else 0
                                        minor_points += 10000 if data_['minor_bingo'] else 0
                                    except Exception as error_building_bingo_dict:
                                        await bot.msg_error("chodeling_leaderboards", "Error building bingo dictionary", error_building_bingo_dict)
                                        continue
                            dict_[chodeling['name']] = total if type_ == "total" else [major, major_points] if type_ == "major" else [minor, minor_points]
                        return dict_

                    cls()
                    print(await top_bar("Bingo Leaderboard Options"))
                    user_input = input(f"Enter 1 To Sort By Total Games\n"
                                       f"Enter 2 To Sort By Major Bingo's\n"
                                       f"Enter 3 To Sort By Minor Bingo's\n"
                                       f"Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            dict_ = await build_bingo_dict("total")
                            await show_leaderboard("Total Bingo Games", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            dict_ = await build_bingo_dict("major")
                            await show_leaderboard("Major Bingo Wins", dict(sorted(dict_.items(), key=lambda x: x[1][0], reverse=True)))
                        elif user_input == 3:
                            dict_ = await build_bingo_dict("minor")
                            await show_leaderboard("Minor Bingo Wins", dict(sorted(dict_.items(), key=lambda x: x[1][0], reverse=True)))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 2:
                dict_ = {}
                chodelings = get_chodelings()
                for chodeling in chodelings:
                    dict_[chodeling['name']] = chodeling['data_user']['dates']['checkin_streak'][0]
                await show_leaderboard("Check-in", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
            elif user_input == 3:
                while True:
                    cls()
                    print(await top_bar("Fight Leaderboard Options"))
                    user_input = input("Enter 1 For Aggressor Leaderboard\n"
                                       "Enter 2 For Defender Leaderboard\n"
                                       "Enter 3 For Total Leaderboard\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        dict_ = {}
                        chodelings = get_chodelings()
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            for chodeling in chodelings:
                                total = 0
                                for name_ in chodeling['data_games']['fight']['aggressor'].values():
                                    for data_ in name_.values():
                                        try:
                                            total += len(data_.values())
                                        except Exception as error_:
                                            await bot.msg_error("chodeling_leaderboard", "Error building fight aggressor dictionary", error_)
                                            continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Fight", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            for chodeling in chodelings:
                                total = 0
                                for name_ in chodeling['data_games']['fight']['defender'].values():
                                    for data_ in name_.values():
                                        try:
                                            total += len(data_.values())
                                        except Exception as error_:
                                            await bot.msg_error("chodeling_leaderboard", "Error building fight defender dictionary", error_)
                                            continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Fight", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 3:
                            for chodeling in chodelings:
                                total = 0
                                for name_ in chodeling['data_games']['fight']['aggressor'].values():
                                    for data_ in name_.values():
                                        try:
                                            total += len(data_.values())
                                        except Exception as error_:
                                            await bot.msg_error("chodeling_leaderboard", "Error building fight aggressor dictionary", error_)
                                            continue
                                for name_ in chodeling['data_games']['fight']['defender'].values():
                                    for data_ in name_.values():
                                        try:
                                            total += len(data_.values())
                                        except Exception as error_:
                                            await bot.msg_error("chodeling_leaderboard", "Error building fight defender dictionary", error_)
                                            continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Fight", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 4:
                while True:
                    cls()
                    print(await top_bar("Fish Leaderboards"))
                    user_input = input(f"Enter 1 For Auto Casts Leaderboard\n"
                                       f"Enter 2 For Manual Casts Leaderboard\n"
                                       f"Enter 3 For Line Cuts Leaderboard\n"
                                       f"Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        dict_ = {}
                        chodelings = get_chodelings()
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            for chodeling in chodelings:
                                total = 0
                                for data_ in chodeling['data_games']['fish']['auto']['catches'].values():
                                    try:
                                        total += data_[0]
                                    except Exception as error_:
                                        await bot.msg_error("chodeling_leaderboard", "Error building auto catches", error_)
                                        continue
                                for data_ in chodeling['data_games']['fish']['totals']['auto']['catches'].values():
                                    try:
                                        total += data_[0]
                                    except Exception as error_:
                                        await bot.msg_error("chodeling_leaderboard", "Error building auto history catches", error_)
                                        continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Auto Cast", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            for chodeling in chodelings:
                                total = 0
                                for data_ in chodeling['data_games']['fish']['totals']['manual']['catches'].values():
                                    try:
                                        total += data_[0]
                                    except Exception as error_:
                                        await bot.msg_error("chodeling_leaderboard", "Error building manual catches", error_)
                                        continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Manual Cast", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 3:
                            while True:
                                cls()
                                dict_ = {}
                                print(await top_bar("Line Cuts Leaderboard Options"))
                                user_input = input("Enter 1 To Sort By Total Lines Cut\n"
                                                   "Enter 2 To Sort By Other Lines Cut\n"
                                                   "Enter 3 To Sort By Own Lines Cut\n"
                                                   "Enter 0 To Go Back\n")
                                if user_input.isdigit():
                                    chodelings = get_chodelings()
                                    user_input = int(user_input)
                                    if user_input == 0:
                                        await bot.go_back()
                                        break
                                    elif user_input == 1:
                                        for chodeling in chodelings:
                                            total = 0
                                            for name_ in chodeling['data_games']['fish']['totals']['line']['cut_by'].values():
                                                for data_ in name_.values():
                                                    try:
                                                        total += data_[0]
                                                    except Exception as error_:
                                                        await bot.msg_error("chodeling_leaderboard", "Error building line cut_by", error_)
                                                        continue
                                            for name_ in chodeling['data_games']['fish']['totals']['line']['cut_other'].values():
                                                for data_ in name_.values():
                                                    try:
                                                        total += data_[0]
                                                    except Exception as error_:
                                                        await bot.msg_error("chodeling_leaderboard", "Error building line cut_other", error_)
                                                        continue
                                            dict_[chodeling['name']] = total
                                        await show_leaderboard("Total Lines Cut", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                                    elif user_input == 2:
                                        for chodeling in chodelings:
                                            total = 0
                                            for name_ in chodeling['data_games']['fish']['totals']['line']['cut_other'].values():
                                                for data_ in name_.values():
                                                    try:
                                                        total += data_[0]
                                                    except Exception as error_:
                                                        await bot.msg_error("chodeling_leaderboard", "Error building line cut_other", error_)
                                                        continue
                                            dict_[chodeling['name']] = total
                                        await show_leaderboard("Other Lines Cut", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                                    elif user_input == 3:
                                        for chodeling in chodelings:
                                            total = 0
                                            for name_ in chodeling['data_games']['fish']['totals']['line']['cut_by'].values():
                                                for data_ in name_.values():
                                                    try:
                                                        total += data_[0]
                                                    except Exception as error_:
                                                        await bot.msg_error("chodeling_leaderboard", "Error building line cut_by", error_)
                                                        continue
                                            dict_[chodeling['name']] = total
                                        await show_leaderboard("Own Lines Cut", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                                    else:
                                        await bot.invalid_entry(int)
                                elif user_input in bot.special_commands.values():
                                    await special_command(user_input)
                                else:
                                    await bot.invalid_entry(str)
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 5:
                async def fetch_fish_packs(_chodeling: dict):
                    free_pack = "a FreePack Redemption"
                    total = 0
                    if free_pack in _chodeling['data_games']['fish']['auto']['catches'].keys():
                        total += _chodeling['data_games']['fish']['auto']['catches'][free_pack][0]
                    if free_pack in _chodeling['data_games']['fish']['totals']['auto']['catches'].keys():
                        total += _chodeling['data_games']['fish']['totals']['auto']['catches'][free_pack][0]
                    if free_pack in _chodeling['data_games']['fish']['totals']['manual']['catches'].keys():
                        total += _chodeling['data_games']['fish']['totals']['manual']['catches'][free_pack][0]
                    return total

                while True:
                    cls()
                    dict_ = {}
                    print(await top_bar("Free Pack Leaderboard Options"))
                    user_input = input("Enter 1 To Sort By Total Free Packs\n"
                                       "Enter 2 To Sort By Command Free Packs\n"
                                       "Enter 3 To Sort By Fish Free Packs\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        chodelings = get_chodelings()
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            for chodeling in chodelings:
                                try:
                                    dict_[chodeling['name']] = len(chodeling['data_user']['dates']['daily_cards'][2])
                                except Exception as _error:
                                    await bot.msg_error("chodeling_leaderboard", f"Error building {chodeling} free_pack dictionary", _error)
                                    continue
                            await show_leaderboard("Free Pack Total", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            for chodeling in chodelings:
                                try:
                                    dict_[chodeling['name']] = len(chodeling['data_user']['dates']['daily_cards'][2]) - await fetch_fish_packs(chodeling)
                                except Exception as _error:
                                    await bot.msg_error("chodeling_leaderboards", f"Error building {chodeling} freepack - fish dict entry", _error)
                                    continue
                            await show_leaderboard("Free Pack Command", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 3:
                            for chodeling in chodelings:
                                try:
                                    dict_[chodeling['name']] = await fetch_fish_packs(chodeling)
                                except Exception as _error:
                                    await bot.msg_error("chodeling_leaderboards", f"Error building {chodeling} freepack command dict", _error)
                                    continue
                            await show_leaderboard("Free Pack Fish", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 6:
                while True:
                    async def build_gamble_dict(type_: str):
                        dict_ = {}
                        chodelings = get_chodelings()
                        for chodeling in chodelings:
                            try:
                                gamble_ = chodeling['data_games']['gamble']
                                dict_[chodeling['name']] = gamble_['total'] if type_ == "total" else [gamble_['won'], gamble_['total_won']] if type_ == "won" else [gamble_['lost'], gamble_['total_lost']]
                            except Exception as error_building_gamble_dict:
                                await bot.msg_error("chodeling_leaderboards", "Error building gamble dict", error_building_gamble_dict)
                                continue
                        return dict_

                    cls()
                    print(await top_bar("Gamble Leaderboard Options"))
                    user_input = input(f"Enter 1 To Sort By Total Gambles\n"
                                       f"Enter 2 To Sort By Total Wins\n"
                                       f"Enter 3 To Sort By Total Losses\n"
                                       f"Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            dict_ = await build_gamble_dict("total")
                            await show_leaderboard("Gamble Total", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            dict_ = await build_gamble_dict("won")
                            await show_leaderboard("Gamble Wins", dict(sorted(dict_.items(), key=lambda x: x[1][0], reverse=True)))
                        elif user_input == 3:
                            dict_ = await build_gamble_dict("lost")
                            await show_leaderboard("Gamble Losses", dict(sorted(dict_.items(), key=lambda x: x[1][0], reverse=True)))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 7:
                async def build_general_dict(leader_type: str):
                    dict_ = {}
                    chodelings = get_chodelings()
                    for chodeling in chodelings:
                        total = 0
                        try:
                            for _game in chodeling['data_games']['heist'].values():
                                for _crew in _game['history'].values():
                                    for _date in _crew.values():
                                        if leader_type == "total":
                                            total += len(_date.keys())
                                        else:
                                            for _data in _date.values():
                                                total += 1 if _data['status'] and leader_type == "success" else 1 if not _data['status'] and leader_type == "fail" else 0
                        except Exception as error_:
                            await bot.msg_error("chodeling_leaderboard", f"Error building heist general dict for {chodeling}", error_)
                            continue
                        dict_[chodeling['name']] = total
                    await show_leaderboard(f"Heist {leader_type.title()}", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))

                while True:
                    cls()
                    print(await top_bar("Heist Leaderboard Options"))
                    user_input = input("Enter 1 To Sort By Total Heists\n"
                                       "Enter 2 To Sort By Crews\n"
                                       "Enter 3 To Sort By Successes\n"
                                       "Enter 4 To Sort By Fails\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():

                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            await build_general_dict("total")
                        elif user_input == 2:
                            async def build_heist_crew_dict(crew_name: str):
                                while True:
                                    while True:
                                        cls()
                                        print(await top_bar(f"{crew_name} Leaderboard Sort Options"))
                                        user_input = input("Enter 1 To Sort By Total\n"
                                                           "Enter 2 To Sort By Successes\n"
                                                           "Enter 3 To Sort By Fails\n"
                                                           "Enter 0 To Go Back\n")
                                        if user_input.isdigit():
                                            user_input = int(user_input)
                                            if user_input == 0:
                                                key_type = None
                                                await bot.go_back()
                                                break
                                            elif user_input == 1:
                                                key_type = "total"
                                                break
                                            elif user_input == 2:
                                                key_type = "success"
                                                break
                                            elif user_input == 3:
                                                key_type = "fail"
                                                break
                                            else:
                                                await bot.invalid_entry(int)
                                        elif user_input in bot.special_commands.values():
                                            await special_command(user_input)
                                        else:
                                            await bot.invalid_entry(str)
                                    if key_type is None:
                                        break
                                    dict_ = {}
                                    chodelings = get_chodelings()
                                    for chodeling in chodelings:
                                        try:
                                            total = 0
                                            if crew_name in chodeling['data_games']['heist']['gamble']['history']:
                                                for _date in chodeling['data_games']['heist']['gamble']['history'][crew_name].values():
                                                    if key_type == "total":
                                                        total += len(_date.keys())
                                                    else:
                                                        for _data in _date.values():
                                                            total += 1 if _data['status'] and key_type == "success" else 1 if not _data['status'] and key_type == "fail" else 0
                                            dict_[chodeling['name']] = total
                                        except Exception as _error:
                                            await bot.msg_error("chodeling_leaderboard", "build_heist_crew_dict", _error)
                                            continue
                                    await show_leaderboard(f"Heist {crew_name} {key_type.title()}", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))

                            while True:
                                cls()
                                options = []
                                length = get_length(list(bot.variables_channel['heist']['crews'].keys()))
                                print(await top_bar("Heist Leaderboard Sort By Crew Options"))
                                for n, _data in enumerate(bot.variables_channel['heist']['crews'].values(), start=1):
                                    try:
                                        options.append(max_length(f"{n}. {_data['name']}", length, n))
                                    except Exception as _error:
                                        await bot.msg_error("chodeling_leaderboard", "Error heist crew sort", _error)
                                        continue
                                if len(options) > 0:
                                    print(nl.join(options))
                                user_input = input(f"{bot.long_dashes()}\n"
                                                   f"{f'Enter # Or Name To Sort By Crew{nl}' if len(options) > 0 else ''}"
                                                   f"Enter 0 To Go Back\n")
                                if user_input.isdigit():
                                    user_input = int(user_input)
                                    if user_input == 0:
                                        await bot.go_back()
                                        break
                                    elif user_input <= len(options):
                                        await build_heist_crew_dict(remove_period_area(options[user_input - 1]).title())
                                    else:
                                        await bot.invalid_entry(int)
                                elif user_input.lower() in check_numbered_list(options):
                                    await build_heist_crew_dict(user_input.title())
                                elif user_input in bot.special_commands.values():
                                    await special_command(user_input)
                                else:
                                    await bot.invalid_entry(str)
                        elif user_input == 3:
                            await build_general_dict("success")
                        elif user_input == 4:
                            await build_general_dict("fail")
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 8:
                while True:
                    cls()
                    print(await top_bar("Jail Leaderboard Options"))
                    user_input = input("Enter 1 For Aggressor Leaderboard\n"
                                       "Enter 2 For Defender Leaderboard\n"
                                       "Enter 3 For Total Leaderboard\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        dict_ = {}
                        chodelings = get_chodelings()
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            for chodeling in chodelings:
                                total = 0
                                for name_ in chodeling['data_games']['jail']['history'].values():
                                    for data_ in name_['aggressor'].values():
                                        try:
                                            total += data_
                                        except Exception as error_:
                                            await bot.msg_error("chodeling_leaderboard", "Error building jail aggressor dictionary", error_)
                                            continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Jail", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            for chodeling in chodelings:
                                total = 0
                                for name_ in chodeling['data_games']['jail']['history'].values():
                                    for data_ in name_['defender'].values():
                                        try:
                                            total += data_
                                        except Exception as error_:
                                            await bot.msg_error("chodeling_leaderboard", "Error building jail defender dictionary", error_)
                                            continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Jail", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 3:
                            for chodeling in chodelings:
                                total = 0
                                for name_ in chodeling['data_games']['jail']['history'].values():
                                    for data_type in name_.values():
                                        for data_ in data_type.values():
                                            try:
                                                total += data_
                                            except Exception as error_:
                                                await bot.msg_error("chodeling_leaderboard", "Error building jail total dictionary", error_)
                                                continue
                                dict_[chodeling['name']] = total
                            await show_leaderboard("Jail", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 9:
                while True:
                    cls()
                    print(await top_bar("Rank Leaderboards"))
                    user_input = input(f"Enter 1 For Sort By Level\n"
                                       f"Enter 2 For Sort By Points\n"
                                       f"Enter 3 For Sort By XP Points\n"
                                       f"Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        dict_ = {}
                        chodelings = get_chodelings()
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            for chodeling in sorted(chodelings, key=lambda x: x['data_user']['rank']['level'], reverse=True):
                                try:
                                    dict_[chodeling['name']] = chodeling['data_user']['rank']['level']
                                except Exception as error_:
                                    await bot.msg_error("chodeling_leaderboard", "Error building rank level dictionary", error_)
                                    continue
                            await show_leaderboard("Level", dict_)
                        elif user_input == 2:
                            for chodeling in sorted(chodelings, key=lambda x: x['data_user']['rank']['points'], reverse=True):
                                try:
                                    dict_[chodeling['name']] = chodeling['data_user']['rank']['points']
                                except Exception as error_:
                                    await bot.msg_error("chodeling_leaderboard", "Error building rank points dictionary", error_)
                                    continue
                            await show_leaderboard("Points", dict_)
                        elif user_input == 3:
                            for chodeling in sorted(chodelings, key=lambda x: x['data_user']['rank']['xp'], reverse=True):
                                try:
                                    dict_[chodeling['name']] = chodeling['data_user']['rank']['xp']
                                except Exception as error_:
                                    await bot.msg_error("chodeling_leaderboard", "Error building rank xp dictionary", error_)
                                    continue
                            await show_leaderboard("XP Points", dict_)
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 10:
                while True:
                    async def build_tag_dict(key_name: str):
                        dict_ = {}
                        chodelings = get_chodelings()
                        for chodeling in chodelings:
                            dict_[chodeling['name']] = chodeling['data_games']['tag'][key_name]
                        return dict_

                    cls()
                    print(await top_bar("Tag Leaderboard Options"))
                    user_input = input("Enter 1 To Sort By Total Games\n"
                                       "Enter 2 To Sort By Total Successful Tags\n"
                                       "Enter 3 To Sort By Total Fail Tags\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            dict_ = await build_tag_dict('total')
                            await show_leaderboard("Tag Total Games", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 2:
                            dict_ = await build_tag_dict('success')
                            await show_leaderboard("Tag Successful Games", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        elif user_input == 3:
                            dict_ = await build_tag_dict('fail')
                            await show_leaderboard("Tag Fail Games", dict(sorted(dict_.items(), key=lambda x: x[1], reverse=True)))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def chodeling_profile():
    while True:
        cls()
        user_document = await refresh_document_user()
        print(await top_bar("Rank Information"))
        length = get_length(list(user_document['data_user']['rank'].keys()))
        for _key, _value in user_document['data_user']['rank'].items():
            try:
                print(f"{max_length(_key.title(), length)}: {f'{_value:,}' if _key == 'level' else numberize(_value)}")
            except Exception as error_printing_chodeling_stats:
                await bot.msg_error("chodeling_stats", "Error Printing Chodeling Stats", error_printing_chodeling_stats)
                continue
        user_input = input(f"{bot.long_dashes()}\n"
                           "Enter 1 To View Bingo Stats\n"
                           "Enter 2 To View Fight Stats\n"
                           "Enter 3 To View Fish Stats\n"
                           "Enter 4 To View Gamble Stats\n"
                           "Enter 5 To View Heist Stats\n"
                           "Enter 6 To View Jail Stats\n"
                           "Enter 7 To View Other Stats\n"
                           "Enter 8 To View Tag Stats\n"
                           "Enter 0 To Return To Main Menu\n"
                           "Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back(True)
                break
            elif user_input == 1:
                await display_stats_bingo()
            elif user_input == 2:
                await display_stats_fight()
            elif user_input == 3:
                await display_stats_fish()
            elif user_input == 4:
                await display_stats_gamble()
            elif user_input == 5:
                await display_stats_heist()
            elif user_input == 6:
                await display_stats_jail()
            elif user_input == 7:
                await display_stats_other()
            elif user_input == 8:
                await display_stats_tag()
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def chodeling_settings_app():
    async def check_var(key_check: str, var_check: str) -> bool:
        try:
            if read_file(bot.data_settings[key_check], str) == var_check:
                print(f"Your sort type is already set to {var_check.replace('_', ' ').title()}\n"
                      f"Try Again")
                await asyncio.sleep(3)
                return True
        except FileNotFoundError:
            await bot.msg_error("app_settings", "You deleted thee file didn't ya?", FileNotFoundError)
        return False

    async def write_var(key_write: str, var_write: str):
        try:
            with open(bot.data_settings[key_write], "w", encoding="utf-8") as file:
                file.write(var_write)
            if key_write == "line_dash":
                bot.line_dash = var_write
            elif key_write == "window_length":
                bot.length = int(var_write)
            else:
                bot.variables[key_write] = var_write
            print(f"{key_write.replace('_', ' ').title()} Variable set to: {var_write.replace('_', ' ').title()}")
        except Exception as error_writing_var:
            await bot.msg_error("app_settings", "Error writing var", error_writing_var)
        await bot.go_back()

    async def set_setting(setting_key: str):
        while True:
            cls()
            options = []
            length = get_length(len(bot.settings[setting_key]))
            print(await top_bar(f"Default {setting_key.replace('_', ' ').title()} Setting"))
            try:
                for n, var in enumerate(bot.settings[setting_key], start=1):
                    options.append(max_length(f"{n}. {var.replace('_', ' ').title()}", length, n))
            except Exception as error_printing_display_variables:
                await bot.msg_error("app_settings", "Error Printing Settings Options", error_printing_display_variables)
            user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{bot.long_dashes()}\n"
                               f"Enter X or Type Out Variable Name To Select\n"
                               f"Enter 0 To Go Back\n")
            if user_input == "":
                await bot.invalid_entry(str)
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input <= len(options):
                    if not await check_var(setting_key, bot.settings[setting_key][user_input - 1]):
                        await write_var(setting_key, bot.settings[setting_key][user_input - 1])
                        break
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            elif user_input.replace(' ', '_').lower() in check_numbered_list(options):
                if not await check_var(setting_key, bot.settings[setting_key][bot.settings[setting_key].index(user_input.replace(' ', '_').lower())]):
                    await write_var(setting_key, bot.settings[setting_key][bot.settings[setting_key].index(user_input.lower())])
                    break
            else:
                await bot.invalid_entry(str)

    while True:
        cls()
        print(await top_bar("App Settings"))
        user_input = input("Enter 1 To Change Default Display Variable\n"
                           "Enter 2 To Change Default Sorting Variable\n"
                           "Enter 3 To Change Flash Settings\n"
                           "Enter 4 To Change Default Heist Crew\n"
                           "Enter 5 To Change Default XP Display\n"
                           "Enter 6 To Change XP Bar Key\n"
                           "Enter 7 To Change Long Line Separator\n"
                           "Enter 0 To Return To Main Menu\n")
        if user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back(True)
                break
            elif user_input == 1:
                await set_setting("types_always_display")
            elif user_input == 2:
                await set_setting("types_sort")
            elif user_input == 3:
                async def set_setting_flash(setting_type: str):
                    while True:
                        cls()
                        print(await top_bar(f"{setting_type.title()} Setting"))
                        user_input = input(f"Enter New Desired {setting_type.title()} Setting\n"
                                           f"Enter 0 To Go Back\n")
                        if user_input in bot.special_commands.values():
                            await special_command(user_input)
                        else:
                            try:
                                user_input = float(user_input)
                            except ValueError:
                                print(f"Invalid Entry, '{user_input}' not converting into float type")
                                user_input = None
                                await asyncio.sleep(3)
                            if user_input is not None:
                                if user_input == 0:
                                    await bot.go_back()
                                    break
                                else:
                                    try:
                                        flash_frequency, flash_speed = await fetch_setting("flash")
                                        if setting_type == "frequency":
                                            flash_frequency = int(user_input)
                                        else:
                                            flash_speed = user_input
                                        await write_var("flash", f"{flash_frequency}, {flash_speed}")
                                    except Exception as error_writing_new_values:
                                        await bot.msg_error("app_settings", "Setting Flash Settings", error_writing_new_values)
                                    break

                while True:
                    cls()
                    print(await top_bar("Flash Settings"))
                    user_input = input("Enter 1 For Flash Frequency\n"
                                       "Enter 2 For Flash Speed\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            await set_setting_flash("frequency")
                        elif user_input == 2:
                            await set_setting_flash("speed")
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 4:
                await set_setting("types_heist")
            elif user_input == 5:
                await set_setting("types_xp_display")
            elif user_input == 6:
                while True:
                    cls()
                    print(await top_bar("Change XP Bar Key"))
                    user_input = input(f"Enter Desired XP Bar Key\n"
                                       f"(Only 1 Key (Future Pattern Compatibility))\n"
                                       f"(If trying to set a number as 'xp bar key', use 'NUMBER' or \"NUMBER\")\n"
                                       f"Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        else:
                            await bot.invalid_entry(int)
                    elif len(user_input) != 1 and not user_input.startswith(("'", '"')):
                        print("Too long of a key!!")
                        await asyncio.sleep(3)
                    elif user_input.startswith(("'", '"')):
                        if user_input.startswith("'"):
                            user_input = user_input.replace("'", "")
                        else:
                            user_input = user_input.replace('"', '')
                        if len(user_input) != 1:
                            print("Too long of a key!!")
                            await asyncio.sleep(3)
                        elif not await check_var('xp_bar_key', user_input):
                            await write_var('xp_bar_key', user_input)
                            break
                    else:
                        if not await check_var('xp_bar_key', user_input):
                            await write_var('xp_bar_key', user_input)
                            break
            elif user_input == 7:
                while True:
                    cls()
                    print(await top_bar("Long Line Separator Options"))
                    user_input = input("Enter 1 To Change Key\n"
                                       "Enter 2 To Change Width\n"
                                       "Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            while True:
                                cls()
                                print(await top_bar("Long Line Key"))
                                user_input = input("Enter new desired line key\n"
                                                   f"(Only 1 Key (Future Pattern Compatibility))\n"
                                                   f"(If trying to set a number as 'xp bar key', use 'NUMBER' or \"NUMBER\")\n"
                                                   "Enter 0 To Go Back\n")
                                if user_input.isdigit():
                                    user_input = int(user_input)
                                    if user_input == 0:
                                        await bot.go_back()
                                        break
                                    else:
                                        await bot.invalid_entry(int)
                                elif len(user_input) != 1 and not user_input.startswith(("'", '"')):
                                    print("Too long of a key!!")
                                    await asyncio.sleep(3)
                                elif user_input.startswith(("'", '"')):
                                    if user_input.startswith("'"):
                                        user_input = user_input.replace("'", "")
                                    else:
                                        user_input = user_input.replace('"', '')
                                    if len(user_input) != 1:
                                        print("Too long of a key!!")
                                        await asyncio.sleep(3)
                                    elif not await check_var('xp_bar_key', user_input):
                                        await write_var('xp_bar_key', user_input)
                                        break
                                elif user_input in bot.special_commands.values():
                                    await special_command(user_input)
                                else:
                                    if not await check_var("line_dash", user_input):
                                        await write_var("line_dash", user_input)
                                        break
                        elif user_input == 2:
                            while True:
                                cls()
                                print(await top_bar("Long Line Width"))
                                user_input = input("Enter new desired width\n"
                                                   "Enter 0 To Go Back\n")
                                if user_input.isdigit():
                                    user_input = int(user_input)
                                    if user_input == 0:
                                        await bot.go_back()
                                        break
                                    elif not await check_var("window_length", str(user_input)):
                                        await write_var("window_length", str(user_input))
                                        break
                                elif user_input in bot.special_commands.values():
                                    await special_command(user_input)
                                else:
                                    await bot.invalid_entry(str)
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def chodeling_settings_document():
    await bot.not_programmed()


async def display_stats_bingo():
    async def build_board(game_board: dict, item_list: list, minor_pattern: str) -> dict:
        chodeling_board = {}
        try:
            if len(game_board) == 0:
                return chodeling_board
            spaces_check = channel_document['data_games']['bingo']['patterns']['minor'][minor_pattern][str(len(game_board))]
            for row, items in game_board.items():
                chodeling_board[row] = {}
                for item, status in items.items():
                    minor_pattern_hit = False
                    if status:
                        for key, value in spaces_check.items():
                            if minor_pattern_hit:
                                break
                            for n, (key_board, value_board) in enumerate(game_board[key].items()):
                                if value_board and n in value and item == key_board:
                                    minor_pattern_hit = True
                                    break
                    index = item_list.index(item) + 1
                    chodeling_board[row][index] = f"{style('bright' if minor_pattern_hit or status else 'normal', colour('cyan' if minor_pattern_hit else 'green' if status else 'red', str(index)))}"
        except Exception as error_building_board:
            await bot.msg_error("display_stats_bingo", "Building Board", error_building_board)
        return chodeling_board

    async def call_action(action_to_call: str):
        channel_document = await refresh_document_channel()
        if channel_document['data_games']['bingo']['current_game']['game_type'] is not None:
            try:
                if channel_document['data_games']['bingo']['current_game']['items'][action_to_call]:
                    status, reason, error = False, f"'{action_to_call}' Is Already Called", False
                else:
                    status, reason, error = await send_chat_msg(f"!bingo action {action_to_call}")
            except Exception as error_calling_action:
                await print_status(False, str(error_calling_action), True)
                return
        else:
            status, reason, error = False, "Game Over/Not Running", False
        await print_status(status, reason, error)

    async def check_bingo_game_status(admin_check: bool = False) -> bool:
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        if admin_check:
            if channel_document['data_games']['bingo']['current_game']['game_type'] is None:
                while True:
                    cls()
                    options = []
                    length = get_length(len(channel_document['data_games']['bingo']['modes'].keys()))
                    for n, game_type in enumerate(channel_document['data_games']['bingo']['modes'].keys(), start=1):
                        options.append(max_length(f"{n}. {game_type}", length, n))
                    print(await top_bar("Bingo Game Type Options"))
                    user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                       f"{bot.long_dashes()}\n"
                                       "No Game Running!\n"
                                       "Enter # Or Type Game Type To Start\n"
                                       "Enter 0/Nothing To Go Back\n")
                    if user_input == "":
                        await bot.go_back()
                        return False
                    elif user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            return False
                        elif user_input <= len(options):
                            status, reason, error = await send_chat_msg(f"!bingo start {remove_period_area(options[user_input - 1])}")
                            await print_status(status, reason, error)
                            return status
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in check_numbered_list(options):
                        status, reason, error = await send_chat_msg(f"!bingo start {user_input}")
                        await print_status(status, reason, error)
                        return status
                    else:
                        await bot.invalid_entry(str)
        else:
            if None in (user_document['data_games']['bingo']['current_game']['game_type'], channel_document['data_games']['bingo']['current_game']['game_type']):
                cls()
                cmd = "'!bingo join'"
                game_type = channel_document['data_games']['bingo']['current_game']['game_type']
                if game_type is not None:
                    game_type = game_type.replace('_', ' ').title()
                print(await top_bar("You're Not In A Bingo Game"))
                input(f"{'No Bingo Game Running' if game_type is None else f'There is a {game_type} running{nl}Use {cmd} to join'}\n"
                      "Hit Enter To Go Back")
                await bot.go_back()
                return False
        return True

    async def print_board(chodeling_board: dict, own_board: bool = True, chodeling_name: str = ""):
        try:
            print(f"{bot.long_dashes()}\n"
                  f"{'Your' if own_board else chodeling_name} Bingo Board\n"
                  f"{bot.long_dashes()}")
            dashes = '-' * ((5 * len(chodeling_board)) + (len(chodeling_board) + 1))
            print(dashes)
            for row, items in chodeling_board.items():
                print(f"{print_row(items)}\n{dashes}")
        except Exception as error_printing_board:
            await bot.msg_error("display_stats_bingo", "Printing Board", error_printing_board)

    async def print_items(items_print: dict):
        try:
            length = get_length(len(items_print.keys()))
            for n, (item, status) in enumerate(items_print.items(), start=1):
                print(f"{style('bright' if status else 'normal', colour('green' if status else 'red', max_length(f'{n}. {item}', length, n)))}")
        except Exception as error_printing_list:
            await bot.msg_error("display_stats_bingo", "Printing Available List", error_printing_list)

    def print_row(items: dict) -> str:
        str_ = "|"
        for index, item in items.items():
            length = len(str(index))
            if length == 1:
                space_left, space_right = 2, 2
            elif length == 2:
                space_left, space_right = 1, 2
            elif length == 3:
                space_left, space_right = 1, 1
            elif length == 4:
                space_left, space_right = 0, 1
            else:
                space_left, space_right = 0, 0
            str_ += f"{' ' * space_left}{item}{' ' * space_right}|"
        return str_

    async def refresh_stats() -> dict:
        user_stats = {
            "game_types": {},
            "total_games": 0,
            "total_major_bingo": 0,
            "total_minor_bingo": 0,
            "total_points_won": 0
        }
        try:
            for game_date, game_time in user_document['data_games']['bingo']['history'].items():
                for game, data in game_time.items():
                    user_stats['total_games'] += 1
                    user_stats['total_points_won'] += data['points_won']
                    if data['game_type'] not in user_stats['game_types']:
                        user_stats['game_types'][data['game_type']] = 1
                    else:
                        user_stats['game_types'][data['game_type']] += 1
                    if data['major_bingo']:
                        user_stats['total_major_bingo'] += 1
                    if data['minor_bingo']:
                        user_stats['total_minor_bingo'] += 1
        except Exception as error_refreshing_stats:
            await bot.msg_error("display_stats_bingo", "Error Refreshing user_stats", error_refreshing_stats)
        return user_stats

    async def show_history():
        async def show_date(dict_date: dict, date_str: str):
            async def show_game(key_time: str):
                async def show_chodeling(chodeling_name: str):
                    cls()
                    game_data = None
                    chodeling_document = await refresh_document_user(chodeling_name)
                    for date_, times_ in chodeling_document['data_games']['bingo']['history'].items():
                        for _game_data in times_.values():
                            if _game_data['game_started'] == game_channel_dict['game_started_time']:
                                game_data = _game_data
                                break
                        if game_data is not None:
                            break
                    print(await top_bar(f"{date_start_formatted} {time_start_formatted} - {f'{date_end_formatted} ' if date_end_formatted != date_start_formatted else ''}{time_end_formatted} for {chodeling_name}"))
                    if game_data is None:
                        await bot.msg_error("display_stats_bingo", "Generic Error", f"Error fetching {chodeling_name} bingo game data for {str(game_channel_dict['game_started_time'])}")
                    else:
                        chodeling_board = await build_board(game_data['game_board'],
                                                            list(game_channel_dict['items'].keys()),
                                                            game_channel_dict['chosen_pattern'][1])
                        if len(chodeling_board) > 0:
                            await print_items(game_channel_dict['items'])
                            await print_board(chodeling_board, False, f"{chodeling_name}'s")
                    input(f"{bot.long_dashes()}\n"
                          f"Hit Enter To Go Back")
                    await bot.go_back()

                game_admin_dict = {
                    'game_board': {},
                    'major_bingo': False,
                    'minor_bingo': False,
                    'points_won': 0
                }
                while True:
                    cls()
                    if date_str in user_document['data_games']['bingo']['history']:
                        if key_time in user_document['data_games']['bingo']['history'][date_str]:
                            game_channel_dict = channel_document['data_games']['bingo']['history'][date_str][user_document['data_games']['bingo']['history'][date_str][key_time]['game_started'].strftime('%I:%M%p').removeprefix('0').lower()]
                            game_user_dict = user_document['data_games']['bingo']['history'][date_str][key_time]
                        else:
                            game_channel_dict = channel_document['data_games']['bingo']['history'][date_str][key_time]
                            game_user_dict = game_admin_dict
                    else:
                        game_channel_dict = channel_document['data_games']['bingo']['history'][date_str][key_time]
                        game_user_dict = game_admin_dict
                    date_start_formatted = game_channel_dict['game_started_time'].strftime("%y/%m/%d")
                    time_start_formatted = game_channel_dict['game_started_time'].strftime('%I:%M%p').removeprefix('0').lower()
                    date_end_formatted = game_channel_dict['game_ended_time'].strftime("%y/%m/%d")
                    time_end_formatted = game_channel_dict['game_ended_time'].strftime('%I:%M%p').removeprefix('0').lower()
                    points_won = game_user_dict['points_won']
                    options = []
                    length = get_length(len(game_channel_dict['chodelings'].keys()))
                    for n, chodeling in enumerate(list(sorted(game_channel_dict['chodelings'].keys(), key=lambda x: x)), start=1):
                        options.append(max_length(f"{n}. {chodeling}", length, n))
                    print(await top_bar(f"{date_start_formatted} {time_start_formatted} - {f'{date_end_formatted} ' if date_end_formatted != date_start_formatted else ''}{time_end_formatted}"))
                    print(f"Game Type          : {game_channel_dict['game_type'].replace('_', ' ').title()}\n"
                          f"Bingo Board Size   : {game_channel_dict['board_size']}x{game_channel_dict['board_size']}\n"
                          f"Major Bingo Jackpot: {numberize(game_channel_dict['major_bingo_pot'])}\n"
                          f"Major Bingo Pattern: {game_channel_dict['chosen_pattern'][0].replace('_', ' ').title()} ({game_user_dict['major_bingo']}{f'({numberize(points_won)})' if game_user_dict['major_bingo'] else ''})\n"
                          f"Minor Bingo Pattern: {game_channel_dict['chosen_pattern'][1].replace('_', ' ').title()} ({game_user_dict['minor_bingo']})\n"
                          f"{bot.long_dashes()}")
                    await print_items(game_channel_dict['items'])
                    chodeling_board = await build_board(game_user_dict['game_board'],
                                                        list(game_channel_dict['items'].keys()),
                                                        game_channel_dict['chosen_pattern'][1])
                    if len(chodeling_board) > 0:
                        await print_board(chodeling_board)
                    print(f"{bot.long_dashes()}\n"
                          f"Chodelings Who Played;\n"
                          f"{bot.long_dashes()}\n"
                          f"{nl.join(options)}")
                    user_input = input(f"{bot.long_dashes()}\n"
                                       f"Enter # Or Type Chodeling To View Their Board\n"
                                       f"Enter 0 To Go Back\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input <= len(options):
                            chodeling_name = remove_period_area(options[user_input - 1])
                            if await bot.check_self_name(chodeling_name):
                                await show_chodeling(chodeling_name)
                        else:
                            await bot.invalid_entry(int)
                    elif user_input.lower() in check_numbered_list(options):
                        if await bot.check_self_name(user_input.lower()):
                            await show_chodeling(user_input.lower())
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)

            while True:
                cls()
                options = []
                length = get_length(len(dict_date.keys()))
                print(await top_bar(f"{date_str} Games"))
                try:
                    for n, key_time in enumerate(dict_date.keys(), start=1):
                        options.append(max_length(f"{n}. {key_time}", length, n))
                except Exception as error_building_bingo_date:
                    await bot.msg_error("display_stats_bingo", f"Error Building Times For {date_str}", error_building_bingo_date)
                if len(options) > 0:
                    print(nl.join(options))
                user_input = input(f"{bot.long_dashes()}\n"
                                   f"{f'Enter # Or Time To View Game Data{nl}' if len(options) > 0 else ''}"
                                   f"Enter 0 To Go Back\n"
                                   f"Enter Nothing To Refresh\n")
                if user_input == "":
                    pass
                elif user_input.isdigit():
                    user_input = int(user_input)
                    if user_input == 0:
                        await bot.go_back()
                        break
                    elif user_input <= len(options):
                        await show_game(remove_period_area(options[user_input - 1]))
                    else:
                        await bot.invalid_entry(int)
                elif user_input.lower() in check_numbered_list(options):
                    await show_game(user_input.lower())
                elif user_input in bot.special_commands.values():
                    await special_command(user_input)
                else:
                    await bot.invalid_entry(str)

        while True:
            cls()
            channel_document = await refresh_document_channel()
            user_document = await refresh_document_user()
            user_stats = await refresh_stats()
            print(await top_bar("Bingo Stats"))
            if len(user_stats) > 0:
                try:
                    total_games_channel = 0
                    for _date in channel_document['data_games']['bingo']['history'].values():
                        total_games_channel += len(_date.values())
                    total_games = user_stats['total_games']
                    total_major_bingo = user_stats['total_major_bingo']
                    total_minor_bingo = user_stats['total_minor_bingo']
                    points_won = user_stats['total_points_won']
                    points_won_minor = total_minor_bingo * bot.const['bingo_cost']
                    dict_print = {
                        "total_games_played": f"{numberize(total_games)}/{numberize(total_games_channel)}{'' if total_games == 0 else f' | {total_games / total_games_channel * 100:.2f}% ({numberize(points_won + points_won_minor)})'}",
                        "total_major_bingos": f"{numberize(total_major_bingo)}{'' if total_major_bingo == 0 else f' | {total_major_bingo / total_games * 100:.2f}% ({numberize(points_won)})'}",
                        "total_minor_bingos": f"{numberize(total_minor_bingo)}{'' if total_minor_bingo == 0 else f' | {total_minor_bingo / total_games * 100:.2f}% ({numberize(points_won_minor)})'}"
                    }
                    if len(user_stats['game_types']) > 0:
                        for game_type in list(sorted(user_stats['game_types'].keys(), key=lambda x: x)):
                            dict_print[f"{game_type}_games_played"] = f"{numberize(user_stats['game_types'][game_type])} | {user_stats['game_types'][game_type] / total_games * 100:.2f}%"
                    length = get_length(list(dict_print.keys()))
                    length_middle = get_length(list(_value.split('|', maxsplit=1)[0] for _value in dict_print.values()))
                    for _key, _value in dict_print.items():
                        _key_form = _key.replace('_', ' ').title()
                        value_middle, value_end = _value.split('|', maxsplit=1)
                        print(f"{max_length(f'{_key_form}', length)}: {max_length(value_middle, length_middle)}|{value_end}")
                except Exception as error_building_dict_print:
                    await bot.msg_error("display_stats_bingo", "Error building dict_print", error_building_dict_print)
            user_input = input(f"{bot.long_dashes()}\n"
                               f"Enter 1 To View Your Games\n"
                               f"{f'Enter 2 To View All Games{nl}' if game_admin else ''}"
                               f"Enter 0 To Go Back\n"
                               f"Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input == 1:
                    while True:
                        cls()
                        options = []
                        user_document = await refresh_document_user()
                        print(await top_bar("Your Bingo History"))
                        try:
                            if len(user_document['data_games']['bingo']['history']) == 0:
                                input("You don't have any bingo history yet!!\nHit Enter To Go Back")
                                await bot.go_back()
                                break
                            length = get_length(len(user_document['data_games']['bingo']['history'].keys()))
                            for n, date in enumerate(user_document['data_games']['bingo']['history'].keys(), start=1):
                                options.append(max_length(f"{n}. {date}", length, n))
                        except Exception as error_building_bingo_games:
                            await bot.msg_error("display_stats_bingo", "Error Building Bingo Games", error_building_bingo_games)
                        if len(options) > 0:
                            print(nl.join(options))
                        user_input = input(f"{bot.long_dashes()}\n"
                                           f"{f'Enter # Or Date To Choose Date{nl}' if len(options) > 0 else ''}"
                                           f"Enter 0 To Go Back\n"
                                           f"Enter Nothing To Refresh\n")
                        if user_input == "":
                            pass
                        elif user_input.isdigit():
                            user_input = int(user_input)
                            if user_input == 0:
                                await bot.go_back()
                                break
                            elif user_input <= len(options):
                                await show_date(user_document['data_games']['bingo']['history'][remove_period_area(options[user_input - 1])], remove_period_area(options[user_input - 1]))
                            else:
                                await bot.invalid_entry(int)
                        elif user_input.lower() in check_numbered_list(options):
                            await show_date(user_document['data_games']['bingo']['history'][user_input.lower()], user_input.lower())
                        elif user_input in bot.special_commands.values():
                            await special_command(user_input)
                        else:
                            await bot.invalid_entry(str)
                elif user_input == 2:
                    while True:
                        if not game_admin:
                            await bot.msg_no_perm()
                            break
                        cls()
                        options = []
                        channel_document = await refresh_document_channel()
                        print(await top_bar("All Bingo History"))
                        try:
                            if len(channel_document['data_games']['bingo']['history']) == 0:
                                input("There ain't no bingo history to show!\n"
                                      "Hit Enter To Go Back")
                                await bot.go_back()
                                break
                            length = get_length(len(channel_document['data_games']['bingo']['history'].keys()))
                            for n, date in enumerate(channel_document['data_games']['bingo']['history'].keys(), start=1):
                                options.append(max_length(f"{n}. {date}", length, n))
                        except Exception as error_building_bingo_games:
                            await bot.msg_error("display_stats_bingo", "Error building bingo game options-game admin", error_building_bingo_games)
                        if len(options) > 0:
                            print(nl.join(options))
                        user_input = input(f"{bot.long_dashes()}\n"
                                           f"{f'Enter # Or Date To Choose Date{nl}' if len(options) > 0 else ''}"
                                           f"Enter 0 To Go Back\n"
                                           f"Enter Nothing To Refresh\n")
                        if user_input == "":
                            pass
                        elif user_input.isdigit():
                            user_input = int(user_input)
                            if user_input == 0:
                                await bot.go_back()
                                break
                            elif user_input <= len(options):
                                await show_date(channel_document['data_games']['bingo']['history'][remove_period_area(options[user_input - 1])], remove_period_area(options[user_input - 1]))
                            else:
                                await bot.invalid_entry(int)
                        elif user_input.lower() in check_numbered_list(options):
                            await show_date(channel_document['data_games']['bingo']['history'][user_input.lower()], user_input.lower())
                        elif user_input in bot.special_commands.values():
                            await special_command(user_input)
                        else:
                            await bot.invalid_entry(str)
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)

    bingo_perm = await bot.check_permissions(user.id, "mini_game_bingo")
    game_admin = await bot.check_permissions(user.id, "game_admin")
    while True:
        cls()
        options = []
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        print(await top_bar("Bingo Options"))
        try:
            if channel_document['data_games']['bingo']['current_game']['game_type'] is not None:
                options.append("Enter 1 To View Game Info")
                if user_document['data_games']['bingo']['current_game']['game_type'] is not None:
                    options.append("Enter 2 To View Your Board")
            options.append("Enter 3 To View History")
            if channel_document['data_games']['bingo']['current_game']['game_type'] is not None and user_document['data_games']['bingo']['current_game']['game_type'] is None:
                options.append("Enter 4 To Join Bingo Game")
            if game_admin:
                options.append("Enter 5 To Admin Bingo Game")
        except Exception as error_building_options:
            await bot.msg_error("display_stats_bingo", "Error Building Options", error_building_options)
        user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                           "Enter 0 To Go Back\n")
        if user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input == 1:
                async def show_chodeling_board(chodeling_name: str, last_board: bool = True):
                    cls()
                    chodeling_document = await refresh_document_user(chodeling_name)
                    chodeling_board = await build_board(chodeling_document['data_games']['bingo']['current_game']['game_board'],
                                                        list(game_dict['items'].keys()),
                                                        game_dict['chosen_pattern'][1])
                    print(await top_bar(f"Current Game Board For {chodeling_name}"))
                    if len(chodeling_board) > 0:
                        await print_items(game_dict['items'])
                        await print_board(chodeling_board, False if chodeling_name != user.display_name.lower() else True, f"{chodeling_name}'s")
                    input(f"{bot.long_dashes()}\n"
                          f"Hit Enter To {'Continue' if not last_board else 'Go Back'}")
                    if last_board:
                        await bot.go_back()

                while True:
                    if not await check_bingo_game_status(True if game_admin else False):
                        break
                    cls()
                    options = []
                    channel_document = await refresh_document_channel()
                    game_dict = channel_document['data_games']['bingo']['current_game']
                    length = get_length(len(game_dict['chodelings'].keys()))
                    print(await top_bar("Current Game Info"))
                    try:
                        print(f"Board Size   : {game_dict['board_size']}x{channel_document['data_games']['bingo']['current_game']['board_size']}\n"
                              f"Game Type    : {game_dict['game_type'].replace('_', ' ').title()}\n"
                              f"Major Jackpot: {numberize(game_dict['major_bingo_pot'])}\n"
                              f"Major Pattern: {game_dict['chosen_pattern'][0].replace('_', ' ').title()}\n"
                              f"Minor Pattern: {game_dict['chosen_pattern'][1].replace('_', ' ').title()}")
                    except Exception as error_printing_bingo_game_info:
                        await bot.msg_error("display_stats_bingo", "Printing Bingo Game Info", error_printing_bingo_game_info)
                    try:
                        for n, chodeling_name in enumerate(sorted(game_dict['chodelings'].keys(), key=lambda x: x), start=1):
                            options.append(max_length(f"{n}. {chodeling_name}", length, n))
                    except Exception as error_building_chodelings_options:
                        await bot.msg_error("display_stats_bingo", "Error Building Chodeling Options", error_building_chodelings_options)
                    if len(options) > 0:
                        print(f"{bot.long_dashes()}\n"
                              f"Chodeling's In Game;\n"
                              f"{bot.long_dashes()}\n"
                              f"{nl.join(options)}")
                    user_input = input(f"{bot.long_dashes()}\n"
                                       f"Enter all To Loop Through All Chodeling's Boards\n"
                                       f"Enter # Or Type Name Of Chodeling To View\n"
                                       f"Enter 0 To Go Back\n"
                                       f"Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif user_input.lower() == "all":
                        len_options = len(options)
                        for n, chodeling_name in enumerate(check_numbered_list(options), start=1):
                            await show_chodeling_board(chodeling_name, False if n < len_options else True)
                    elif user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input <= len(options):
                            await show_chodeling_board(remove_period_area(options[user_input - 1]))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    elif user_input.lower() in check_numbered_list(options):
                        await show_chodeling_board(user_input.lower())
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 2:
                while True:
                    if not await check_bingo_game_status():
                        break
                    cls()
                    user_document = await refresh_document_user()
                    channel_document = await refresh_document_channel()
                    print(await top_bar(f"{channel_document['data_games']['bingo']['current_game']['game_type'].title()} Items Available"))
                    await print_items(channel_document['data_games']['bingo']['current_game']['items'])
                    chodeling_board = await build_board(user_document['data_games']['bingo']['current_game']['game_board'],
                                                        list(channel_document['data_games']['bingo']['current_game']['items'].keys()),
                                                        channel_document['data_games']['bingo']['current_game']['chosen_pattern'][1])
                    if len(chodeling_board) > 0:
                        await print_board(chodeling_board)
                    user_input = input(f"{bot.long_dashes()}\n"
                                       f"{f'Enter # Or Type Out Item To Call{nl}' if bingo_perm or game_admin else ''}"
                                       f"Enter 0 To Go Back\n"
                                       f"Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif bingo_perm or game_admin and user_input <= len(channel_document['data_games']['bingo']['current_game']['items']):
                            await call_action(list(channel_document['data_games']['bingo']['current_game']['items'].keys())[user_input - 1])
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    elif bingo_perm or game_admin and user_input.lower() in check_numbered_list(list(channel_document['data_games']['bingo']['current_game']['items'].keys())):
                        await call_action(title(user_input))
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 3:
                await show_history()
            elif user_input == 4:
                if user_document['data_games']['bingo']['current_game']['game_type'] is not None:
                    input(f"You're already in a {user_document['data_games']['bingo']['current_game']['game_type'].replace('_', ' ').title()} game!!\n"
                          "Hit Enter To Go Back")
                    await bot.go_back()
                elif channel_document['data_games']['bingo']['current_game']['game_type'] is None:
                    input("There is no game running!!\n"
                          "Hit Enter To Go Back")
                    await bot.go_back()
                else:
                    status, reason, error = await send_chat_msg("!bingo join")
                    await print_status(status, reason, error)
            elif user_input == 5:
                # ToDo; Add ability to end game from admin area & in-game area if game_admin
                if not game_admin:
                    await bot.msg_no_perm()
                else:
                    while True:
                        if not await check_bingo_game_status(True):
                            break
                        cls()
                        channel_document = await refresh_document_channel()
                        print(await top_bar(f"{channel_document['data_games']['bingo']['current_game']['game_type'].title()} Items Available"))
                        await print_items(channel_document['data_games']['bingo']['current_game']['items'])
                        user_input = input(f"{bot.long_dashes()}\n"
                                           f"Enter # Or Type Out Item To Call\n"
                                           f"Enter 0 To Go Back\n"
                                           f"Enter Nothing To Refresh\n")
                        if user_input == "":
                            pass
                        elif user_input.isdigit():
                            user_input = int(user_input)
                            if user_input == 0:
                                await bot.go_back()
                                break
                            elif user_input <= len(channel_document['data_games']['bingo']['current_game']['items']):
                                await call_action(list(channel_document['data_games']['bingo']['current_game']['items'].keys())[user_input - 1])
                            else:
                                await bot.invalid_entry(int)
                        elif user_input in bot.special_commands.values():
                            await special_command(user_input)
                        elif user_input.lower() in check_numbered_list(list(channel_document['data_games']['bingo']['current_game']['items'].keys())):
                            await call_action(title(user_input))
                        else:
                            await bot.invalid_entry(str)
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def display_stats_fight():
    async def detailed_options(key: str):
        async def detailed_stats(name: str):
            async def display_fight_times(key_date: str):
                async def display_fight(key_time: str):
                    cls()
                    length = get_length(list(user_document['data_games']['fight'][key][name][key_date][key_time].keys()))
                    print(await top_bar(f"{key_date.replace('-', '/')} {key_time} {name} {key.replace('_', ' ').title()} Fight"))
                    for _key_fight, _key_data in user_document['data_games']['fight'][key][name][key_date][key_time].items():
                        try:
                            if type(_key_data) == list:
                                options_list = []
                                for item in reversed(_key_data):
                                    try:
                                        options_list.append(item if type(item) not in (float, int) else numberize(item))
                                    except Exception as error_list_item:
                                        options_list.append(error_list_item)
                                        continue
                                print(f"{max_length(_key_fight.replace('_', ' ').title(), length)}: {' - '.join(options_list)}")
                            else:
                                try:
                                    print(f"{max_length(_key_fight.replace('_', ' ').title(), length)}: {_key_data if type(_key_data) not in (float, int) else numberize(_key_data)}")
                                except Exception as error_printing_item:
                                    logger.error(f"{_key_fight} ERROR: {error_printing_item}")
                                    continue
                        except Exception as error_building_fight_data:
                            await bot.msg_error("display_stats_fight", f"Error Building Fight Data For {name} {key_date} {key_time}", error_building_fight_data)
                            continue
                    input(f"{bot.long_dashes()}\nHit Enter To Go Back")
                    await bot.go_back()

                while True:
                    cls()
                    options = []
                    user_document = await refresh_document_user()
                    length = get_length(len(user_document['data_games']['fight'][key][name][key_date].keys()))
                    print(await top_bar(f"Detailed {key.replace('_', ' ').title()} Times for {key_date.replace('-', '/')} for {name}"))
                    try:
                        for n, time_ in enumerate(user_document['data_games']['fight'][key][name][key_date].keys(), start=1):
                            options.append(max_length(f"{n}. {time_}", length, n))
                    except Exception as error_building_fight_times:
                        await bot.msg_error("display_fight_stats", f"Error Building Fight Times for {name}", error_building_fight_times)
                    user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                       f"{bot.long_dashes()}\n"
                                       f"{f'Enter # Or Type Date To View{nl}' if len(options) > 0 else ''}"
                                       f"Enter 0 To Go Back\n"
                                       f"Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input <= len(options):
                            await display_fight(remove_period_area(options[user_input - 1]))
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    elif user_input.lower() in check_numbered_list(options):
                        await display_fight(user_input.lower())
                    else:
                        await bot.invalid_entry(str)

            async def refresh_stats():
                user_stats = {
                    'fights_total': 0,
                    'fights_won': 0,
                    'fights_lost': 0,
                    'fights_tied': 0,
                    'points_lost': 0,
                    'points_won': 0
                }
                try:
                    for dates, times in user_document['data_games']['fight'][key][name].items():
                        for game_time, game_data in times.items():
                            user_stats['fights_total'] += 1
                            if game_data['won'] == "tied":
                                user_stats['fights_tied'] += 1
                            elif game_data['won']:
                                user_stats['fights_won'] += 1
                                user_stats['points_won'] += game_data['points_gained']
                            else:
                                user_stats['fights_lost'] += 1
                                user_stats['points_lost'] += game_data['points_lost']
                except Exception as error_building_detailed_stats:
                    await bot.msg_error("display_stats_fight", "Error Building Detailed Stats", error_building_detailed_stats)
                return user_stats

            while True:
                cls()
                options = []
                user_document = await refresh_document_user()
                user_stats = await refresh_stats()
                length = get_length(list(user_stats.keys()))
                print(await top_bar(f"{key.title()} against {name}"))
                for stat_name, stat in user_stats.items():
                    try:
                        print(f"{max_length(stat_name.replace('_', ' ').title(), length)}: {numberize(stat)}")
                    except Exception as error_printing_detailed_stats:
                        await bot.msg_error("display_stats_fight", "Error Printing Detailed Stats", error_printing_detailed_stats)
                        continue
                length = get_length(len(user_document['data_games']['fight'][key][name].keys()))

                for n, date in enumerate(user_document['data_games']['fight'][key][name].keys(), start=1):
                    try:
                        options.append(max_length(f"{n}. {date}", length, n))
                    except Exception as error_building_fight_dates:
                        await bot.msg_error("display_stats_fight", f"Error Building Fight Dates for {name}", error_building_fight_dates)
                        continue
                user_input = input(f"{f'{bot.long_dashes()}{nl}{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                   f"{bot.long_dashes()}\n"
                                   f"{f'Enter # Or Type Date To View{nl}' if len(options) > 0 else ''}"
                                   f"Enter 0 To Go Back\n"
                                   f"Enter Nothing To Refresh\n")
                if user_input == "":
                    pass
                elif user_input.isdigit():
                    user_input = int(user_input)
                    if user_input == 0:
                        await bot.go_back()
                        break
                    elif user_input <= len(options):
                        await display_fight_times(remove_period_area(options[user_input - 1]))
                    else:
                        await bot.invalid_entry(int)
                elif user_input in bot.special_commands.values():
                    await special_command(user_input)
                elif user_input.lower() in check_numbered_list(options):
                    await display_fight_times(user_input.lower())
                else:
                    await bot.invalid_entry(str)

        while True:
            cls()
            options = []
            user_document = await refresh_document_user()
            user_stats = await refresh_stats()
            length = get_length(list(user_stats[key].keys()))
            print(await top_bar(f"{key.title()} Fights"))
            for key_, value_ in user_stats[key].items():
                try:
                    print(f"{max_length(key_.replace('_', ' ').title(), length)}: {numberize(value_)}")
                except Exception as error_printing_stats:
                    await bot.msg_error("display_stats_fight", f"Error printing {key} user_stats", error_printing_stats)
                    continue
            try:
                length = get_length(len(user_document['data_games']['fight'][key].keys()))
                for n, chodeling in enumerate(list(sorted(user_document['data_games']['fight'][key].keys(), key=lambda x: x)), start=1):
                    options.append(max_length(f"{n}. {chodeling}", length, n))
            except Exception as error_building_detailed_options:
                await bot.msg_error("display_stats_fight", "Error Building Detailed Options", error_building_detailed_options)
            user_input = input(f"{f'{bot.long_dashes()}{nl}{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{bot.long_dashes()}\n"
                               f"{f'Enter # Or Type Chodeling To View{nl}' if len(options) > 0 else ''}"
                               f"Enter 0 To Go back\n"
                               f"Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input <= len(options):
                    await detailed_stats(remove_period_area(options[user_input - 1]))
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            elif len(options) > 0 and user_input.lower() in check_numbered_list(options):
                await detailed_stats(user_input.lower())
            else:
                await bot.invalid_entry(str)

    async def refresh_stats() -> dict:
        user_document = await refresh_document_user()
        user_stats = {
            'aggressor': {
                'fights_total': 0,
                'fights_lost': 0,
                'fights_tied': 0,
                'fights_won': 0,
                'points_lost': 0,
                'points_won': 0
            },
            'defender': {
                'fights_total': 0,
                'fights_lost': 0,
                'fights_tied': 0,
                'fights_won': 0,
                'points_lost': 0,
                'points_won': 0
            }
        }
        try:
            for key, value in user_document['data_games']['fight'].items():
                if key in user_stats.keys():
                    for chodelings, dates in value.items():
                        for date, times in dates.items():
                            for time, game_stats in times.items():
                                user_stats[key]['fights_total'] += 1
                                if game_stats['won'] == "tied":
                                    user_stats[key]['fights_tied'] += 1
                                elif game_stats['won']:
                                    user_stats[key]['fights_won'] += 1
                                    user_stats[key]['points_won'] += game_stats['points_gained']
                                else:
                                    user_stats[key]['fights_lost'] += 1
                                    user_stats[key]['points_lost'] += game_stats['points_lost']
        except Exception as error_building_user_stats:
            await bot.msg_error("display_stats_fight", "Error Building user_stats", error_building_user_stats)
            return {}
        return user_stats

    while True:
        cls()
        user_stats = await refresh_stats()
        print(await top_bar("Fight Stats"))
        try:
            print(f"Fights Total: {numberize(user_stats['aggressor']['fights_total'] + user_stats['defender']['fights_total'])}\n"
                  f"Lost Total  : {numberize(user_stats['aggressor']['fights_lost'] + user_stats['defender']['fights_lost'])}\n"
                  f"Tied Total  : {numberize(user_stats['aggressor']['fights_tied'] + user_stats['defender']['fights_tied'])}\n"
                  f"Wins Total  : {numberize(user_stats['aggressor']['fights_won'] + user_stats['defender']['fights_won'])}\n"
                  f"Points Lost : {numberize(user_stats['aggressor']['points_lost'] + user_stats['defender']['points_lost'])}\n"
                  f"Points Won  : {numberize(user_stats['aggressor']['points_won'] + user_stats['defender']['points_won'])}")
        except Exception as error_printing_all_stats:
            await bot.msg_error("display_stats_fight", "Error printing all stats", error_printing_all_stats)
        user_input = input(f"{bot.long_dashes()}\n"
                           f"Enter 1 To View Aggressor Fights\n"
                           f"Enter 2 To View Defender Fights\n"
                           f"Enter 0 To Go Back\n"
                           f"Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input == 1:
                await detailed_options('aggressor')
            elif user_input == 2:
                await detailed_options('defender')
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def display_stats_fish():
    async def sort_print_list(dict_: dict, type_: str):
        sortby = await fetch_setting("sortby")
        if sortby is not None:
            left_length = 0
            right_length = 0
            length = get_length(len(dict_.keys()))
            if sortby == 0:
                for n, (key, value) in enumerate(dict_.items(), start=1):
                    len_key = len(f"{max_length(f'{n}. ', length, n)}{key}")
                    len_value = len(f"{numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})")
                    left_length = len_key if len_key > left_length else left_length
                    right_length = len_value if len_value > right_length else right_length
            else:
                for n, value in enumerate(dict_.values(), start=1):
                    num_order = max_length(f"{n}. ", length, n)
                    len_value = len(f"{num_order}{numberize(value[0])}") if sortby == 1 else len(f' {num_order}{numberize(value[1])} {numberize(value[1] / value[0])} ')
                    len_value_right = len(f"Worth {numberize(value[1])} ({f'{numberize(value[1])})' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})") if sortby <= 2 else len(f"{numberize(value[0])} Times ")
                    left_length = len_value if len_value > left_length else left_length
                    right_length = len_value_right if len_value_right > right_length else right_length
            for n, (key, value) in enumerate(dict(sorted(dict_.items(), key=lambda x: x[1 if sortby >= 1 else 0][0 if sortby == 0 else sortby - 1] if sortby <= 2 else x[1][1] / x[1][0])).items(), start=1):
                if sortby == 0:
                    print(space(f"Worth {numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", right_length, False, space(f"{max_length(f'{n}. ', length, n)}{key}", left_length, middle_txt=f'{type_.title()} {value[0]} Times')))
                elif sortby == 1:
                    print(space(f"Worth {numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", right_length, False, space(f"{max_length(f'{n}. ', length, n)}{numberize(value[0])}", left_length, middle_txt=key)))
                elif sortby == 2:
                    print(space(f'{numberize(value[0])} Times', right_length, False, space(f"{max_length(f'{n}. ', length, n)}{numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", left_length, middle_txt=key)))
                else:
                    print(space(f'{numberize(value[0])} Times', right_length, False, space(f"{max_length(f'{n}. ', length, n)}{numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", left_length, middle_txt=key)))

    async def cutline_stats():
        async def detailed_stats(key_cut: str):
            async def print_details(name: str):
                cls()
                print(await top_bar(f"{name} has {f'made you loose;' if key_cut == 'cut_by' else f'lost;'}"))
                await sort_print_list(user_document['data_games']['fish']['totals']['line'][key_cut][name], "cut")
                input(f"{bot.long_dashes()}\nEnter To Return")
                await bot.go_back()

            while True:
                cls()
                user_document = await refresh_document_user()
                if len(user_document['data_games']['fish']['totals']['line'][key_cut]) == 0:
                    print("No one has cut your line yet!" if key_cut == "cut_by" else "You haven't cut anyone's line yet!")
                    input("Hit Enter To Go Back")
                    await bot.go_back()
                    break
                options = []
                length = get_length(len(user_document['data_games']['fish']['totals']['line'][key_cut].keys()))
                print(await top_bar("Others Who Have Cut Your Line;" if key_cut == "cut_by" else f"Chodelings Who's Lines You've Cut;"))
                try:
                    for n, name in enumerate(sorted(user_document['data_games']['fish']['totals']['line'][key_cut].keys(), key=lambda x: x), start=1):
                        options.append(max_length(f"{n}. {name}", length, n))
                except Exception as error_printing_cutline_options:
                    await bot.msg_error("display_stats_fish", "Error Displaying Cutline Detailed Stats", error_printing_cutline_options)
                user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                   f"{bot.long_dashes()}\n"
                                   f"{f'Enter # Or Type Chodeling To View{nl}' if len(options) > 0 else ''}"
                                   f"Enter 0 To Go Back\n"
                                   f"Enter Nothing To Refresh List\n")
                if user_input == "":
                    pass
                elif user_input.isdigit():
                    user_input = int(user_input)
                    if user_input == 0:
                        await bot.go_back()
                        break
                    elif user_input <= len(options):
                        await print_details(remove_period_area(options[user_input - 1]))
                    else:
                        await bot.invalid_entry(int)
                elif user_input in bot.special_commands.values():
                    await special_command(user_input)
                elif user_input.lower() in check_numbered_list(options):
                    await print_details(user_input.lower())
                else:
                    await bot.invalid_entry(str)

        while True:
            cls()
            user_stats = await refresh_user_stats()
            if len(user_stats) == 0:
                break
            print(await top_bar("CutLine Stats;"))
            try:
                dict_print = {
                    "own_line_cut_times": numberize(user_stats['cut_line']['own_line_times_cut']),
                    f"own_line_cut_points_{'lost' if user_stats['cut_line']['own_line_points_lost'] > 0 else 'saved'}": numberize(user_stats['cut_line']['own_line_points_lost'] if user_stats['cut_line']['own_line_points_lost'] > 0 else abs(user_stats['cut_line']['own_line_points_lost'])),
                    "other_line_cut_times": numberize(user_stats['cut_line']['other_line_times_cut']),
                    f"other_line_cut_points_{'lost' if user_stats['cut_line']['other_line_points_lost'] > 0 else 'saved'}": numberize(user_stats['cut_line']['other_line_points_lost'] if user_stats['cut_line']['other_line_points_lost'] > 0 else abs(user_stats['cut_line']['other_line_points_lost']))
                }
                length = get_length(list(dict_print.keys()))
                for _key, _value in dict_print.items():
                    print(f"{max_length(_key.replace('_', ' ').title(), length)}: {_value}")
            except Exception as error_printing_cutline_stats:
                await bot.msg_error("display_stats_fish", "Printing CutLine Stats", error_printing_cutline_stats)
            user_input = input(f"{bot.long_dashes()}\n"
                               "Enter 1 To View Detailed Own Line Cut Stats\n"
                               "Enter 2 To View Detailed Other Line Cut Stats\n"
                               "Enter 0 To Go Back\n"
                               "Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input == 1:
                    await detailed_stats("cut_by")
                elif user_input == 2:
                    await detailed_stats("cut_other")
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)

    async def detailed_cast_stats(key_type: str):
        while True:
            cls()
            user_stats = await refresh_user_stats()
            if len(user_stats) == 0:
                break
            print(await top_bar(f"{key_type.title()} Fishing Stats;"))
            try:
                auto_total_cost = numberize(user_stats['auto']['total_cost'])
                auto_current_remaining = user_stats['auto']['current_remaining_casts']
                auto_cast_limit = channel_document['data_games']['fish']['upgrades']['rod'][str(user_stats['levels']['rod'])]['autocast_limit']
                current_remaining_time = user_stats['auto']['current_remaining_time']
                dict_print = {
                    "remaining_casts": f"{numberize(auto_current_remaining)}/{auto_cast_limit}" if key_type == "auto" else None,
                    "time_since_initiated": current_remaining_time if key_type == "auto" else None,
                    "total_casts": numberize(user_stats[key_type]['total_casts']),
                    "total_cost": f"{auto_total_cost}" if key_type == "auto" else None,
                    "total_gained": numberize(user_stats[key_type]['total_points_gain']),
                    "total_lost": numberize(user_stats[key_type]['total_points_lost']),
                    "unique_catches": f"{len(user_stats[key_type]['total_unique_dict']):,}/{user_stats['total_items']:,}"
                }
                length = get_length(list(_key for _key, _value in dict_print.items() if _value is not None))
                for _key, _value in dict_print.items():
                    if _value is not None:
                        print(f"{max_length(_key.replace('_', ' ').title(), length)}: {_value}")
            except Exception as error_detailed_stats:
                await bot.msg_error("display_stats_fish", f"Error Displaying user_stats for {key_type}", error_detailed_stats)
            user_input = input(f"{bot.long_dashes()}\n"
                               f"Enter 1 To View Unique Catches List\n"
                               f"Enter 0 To Go Back\n"
                               f"Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input == 1:
                    cls()
                    try:
                        if len(user_stats[key_type]['total_unique_dict']) == 0:
                            print(f"You haven't caught anything via {key_type.title()} Casts yet!!")
                        else:
                            print(await top_bar(f"{key_type.title()} Fishing Unique Catches"))
                            await sort_print_list(user_stats[key_type]['total_unique_dict'], 'caught')
                        input(f"{bot.long_dashes()}\nHit Enter To Go Back")
                    except Exception as error_printing_auto_catches:
                        await bot.msg_error("display_stats_fish", f"Error Printing {key_type} Catches", error_printing_auto_catches)
                        input("\nHit Enter To Go Back")
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)

    async def upgrade_stats():
        async def detailed_stats(key_type: str):
            cls()
            user_stats = await refresh_user_stats()
            print(await top_bar(f"{key_type.title()} Detailed View"))
            try:
                length = get_length(list(channel_document['data_games']['fish']['upgrades'][key_type][str(user_stats['levels'][key_type])].keys()))
                for key, value in channel_document['data_games']['fish']['upgrades'][key_type][str(user_stats['levels'][key_type])].items():
                    print(f"{max_length(key.replace('_', ' ').title(), length)}: {value if key != 'cost' else numberize(value)}")
            except Exception as error_printing_detailed_stats:
                await bot.msg_error("display_stats_fish", f"Printing Detailed {key_type} Stats", error_printing_detailed_stats)
            input(f"{bot.long_dashes()}\n"
                  f"Hit Enter To Go Back")
            await bot.go_back()

        while True:
            cls()
            user_stats = await refresh_user_stats()
            if len(user_stats) == 0:
                break
            print(await top_bar("Fishing Levels;"))
            try:
                print(f"Line: {user_stats['levels']['line']} ({channel_document['data_games']['fish']['upgrades']['line'][str(user_stats['levels']['line'])]['name']})\n"
                      f"Lure: {user_stats['levels']['lure']} ({channel_document['data_games']['fish']['upgrades']['lure'][str(user_stats['levels']['lure'])]['name']})\n"
                      f"Reel: {user_stats['levels']['reel']} ({channel_document['data_games']['fish']['upgrades']['reel'][str(user_stats['levels']['reel'])]['name']})\n"
                      f"Rod : {user_stats['levels']['rod']} ({channel_document['data_games']['fish']['upgrades']['rod'][str(user_stats['levels']['rod'])]['name']})")
            except Exception as error_printing_fishing_levels:
                await bot.msg_error("display_stats_fishing", "Printing Fishing Levels", error_printing_fishing_levels)
            user_input = input(f"{bot.long_dashes()}\n"
                               "Enter 1 For Line Stats\n"
                               "Enter 2 For Lure Stats\n"
                               "Enter 3 For Reel Stats\n"
                               "Enter 4 For Rod Stats\n"
                               "Enter 0 To Go Back\n"
                               "Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input == 1:
                    await detailed_stats('line')
                elif user_input == 2:
                    await detailed_stats('lure')
                elif user_input == 3:
                    await detailed_stats('reel')
                elif user_input == 4:
                    await detailed_stats('rod')
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)

    async def refresh_user_stats() -> dict:
        try:
            user_document = await refresh_document_user()
            total_items = len(channel_document['data_games']['fish']['items'])
            auto_total_cost = user_document['data_games']['fish']['auto']['cost'] + user_document['data_games']['fish']['totals']['auto']['cost']
            remaining_auto_cast = user_document['data_games']['fish']['auto']['cast']
            line_level = user_document['data_games']['fish']['upgrade']['line']
            lure_level = user_document['data_games']['fish']['upgrade']['lure']
            reel_level = user_document['data_games']['fish']['upgrade']['reel']
            rod_level = user_document['data_games']['fish']['upgrade']['rod']
            total_points_auto_add, total_points_auto_loss = 0.0, 0.0
            total_points_man_add, total_points_man_loss = 0.0, 0.0
            total_cast_auto, total_cast_manual = 0, 0
            line_cut, line_cut_total_lost, lines_cut, lines_cut_total_lost = 0, 0.0, 0, 0.0
            total_unique_auto = {}
            total_unique_man = {}
            if len(user_document['data_games']['fish']['auto']['catches']) > 0:
                for key, value in user_document['data_games']['fish']['auto']['catches'].items():
                    if key != "CutLine":
                        total_cast_auto += value[0]
                        if value[1] >= 0:
                            total_points_auto_add += value[1]
                        else:
                            total_points_auto_loss += value[1]
                        if key not in total_unique_auto:
                            total_unique_auto[key] = value
                        else:
                            total_unique_auto[key][0] += value[0]
                            total_unique_auto[key][1] += value[1]
            if len(user_document['data_games']['fish']['totals']['auto']['catches']) > 0:
                for key, value in user_document['data_games']['fish']['totals']['auto']['catches'].items():
                    if key != "CutLine":
                        total_cast_auto += value[0]
                        if value[1] >= 0:
                            total_points_auto_add += value[1]
                        else:
                            total_points_auto_loss += value[1]
                        if key not in total_unique_auto:
                            total_unique_auto[key] = value
                        else:
                            total_unique_auto[key][0] += value[0]
                            total_unique_auto[key][1] += value[1]
            if len(user_document['data_games']['fish']['totals']['manual']['catches']) > 0:
                for key, value in user_document['data_games']['fish']['totals']['manual']['catches'].items():
                    if key != "CutLine":
                        total_cast_manual += value[0]
                        if value[1] >= 0:
                            total_points_man_add += value[1]
                        else:
                            total_points_man_loss += value[1]
                        if key not in total_unique_man:
                            total_unique_man[key] = value
                        else:
                            total_unique_man[key][0] += value[0]
                            total_unique_man[key][1] += value[1]
            if len(user_document['data_games']['fish']['totals']['line']['cut_by']) > 0:
                for key, value in user_document['data_games']['fish']['totals']['line']['cut_by'].items():
                    for key2, value2 in user_document['data_games']['fish']['totals']['line']['cut_by'][key].items():
                        line_cut += value2[0]
                        line_cut_total_lost += value2[1]
            if len(user_document['data_games']['fish']['totals']['line']['cut_other']) > 0:
                for key, value in user_document['data_games']['fish']['totals']['line']['cut_other'].items():
                    for key2, value2 in user_document['data_games']['fish']['totals']['line']['cut_other'][key].items():
                        lines_cut += value2[0]
                        lines_cut_total_lost += value2[1]
            try:
                dict_return = {
                    "total_items": total_items,
                    "auto": {
                        "current_remaining_casts": remaining_auto_cast,
                        "current_remaining_time": None if remaining_auto_cast == 0 else str(datetime.timedelta(seconds=int(datetime.datetime.now().timestamp() - user_document['data_games']['fish']['auto']['initiated'].timestamp()))),
                        "total_casts": total_cast_auto,
                        "total_cost": auto_total_cost,
                        "total_points_gain": total_points_auto_add,
                        "total_points_lost": total_points_auto_loss,
                        "total_unique_dict": total_unique_auto
                    },
                    "manual": {
                        "total_casts": total_cast_manual,
                        "total_points_gain": total_points_man_add,
                        "total_points_lost": total_points_man_loss,
                        "total_unique_dict": total_unique_man
                    },
                    "levels": {
                        "line": line_level,
                        "lure": lure_level,
                        "reel": reel_level,
                        "rod": rod_level
                    },
                    "cut_line": {
                        "own_line_times_cut": line_cut,
                        "own_line_points_lost": line_cut_total_lost,
                        "other_line_times_cut": lines_cut,
                        "other_line_points_lost": lines_cut_total_lost
                    }
                }
            except Exception as error_building_dict_return:
                await bot.msg_error("display_stats_fish", "Error Building Return Dictionary", error_building_dict_return)
                return {}

            return dict_return
        except Exception as error_building_stats:
            await bot.msg_error("display_stats_fish", "Error Building Stats", error_building_stats)
            return {}

    def space(item: str, line_length: int, left: bool = True, left_item: str = "", middle_txt: str = ""):
        if left:
            return f"{item}{' ' * (line_length - len(item))} | {middle_txt}"
        else:
            return f"{left_item}{' ' * (len(bot.long_dashes()) - (len(left_item) + len(str(item))))}{item}"

    while True:
        cls()
        channel_document = await refresh_document_channel()
        user_stats = await refresh_user_stats()
        if len(user_stats) == 0:
            break
        print(await top_bar("Fishing Options"))
        user_input = input("Enter 1 To View Auto Stats\n"
                           "Enter 2 To View Manual Stats\n"
                           "Enter 3 To View Line Cut Stats\n"
                           "Enter 4 To View Upgrades Details\n"
                           "Enter 0 To Go Back\n")
        if user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input == 1:
                await detailed_cast_stats('auto')
            elif user_input == 2:
                await detailed_cast_stats('manual')
            elif user_input == 3:
                await cutline_stats()
            elif user_input == 4:
                await upgrade_stats()
            else:
                await bot.invalid_entry(int)
            if len(user_stats) == 0:
                break
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def display_stats_gamble():
    async def refresh_stats():
        user_document = await refresh_document_user()
        try:
            user_stats = {
                "total": {
                    "bets": numberize(user_document['data_games']['gamble']['total']),
                    "won": numberize(user_document['data_games']['gamble']['won']),
                    "lost": numberize(user_document['data_games']['gamble']['lost']),
                    "points_won": numberize(user_document['data_games']['gamble']['total_won']),
                    "points_lost": numberize(user_document['data_games']['gamble']['total_lost'])
                },
                "percent": {
                    "win": f"{user_document['data_games']['gamble']['won'] / user_document['data_games']['gamble']['total'] * 100:.2f}",
                    "points_change": f"-{numberize(user_document['data_games']['gamble']['total_lost'])}" if user_document['data_games']['gamble']['total_won'] == 0 else numberize(user_document['data_games']['gamble']['total_won'] / user_document['data_games']['gamble']['total_lost'] * 100),

                }
            }
        except Exception as error_building_user_stats:
            await bot.msg_error("display_stats_gamble", "Error Building user_stats", error_building_user_stats)
            return {}
        return user_stats

    while True:
        cls()
        user_stats = await refresh_stats()
        length = get_length(list(f'{_key} {_key_}' for _key in user_stats.keys() for _key_ in user_stats[_key].keys()))
        print(await top_bar("Gamble Stats"))
        for _key, _value in user_stats.items():
            for _key_, _value_ in _value.items():
                try:
                    form__key_ = f"{_key_.replace('_', ' ').title()}"
                    if _key == "total":
                        print(f"{max_length(f'{_key.title()} {form__key_}', length)}: {_value_}")
                    else:
                        print(f"{max_length(f'{form__key_} {_key.title()}', length)}: {_value_}%")
                except Exception as error_printing_user_stats:
                    await bot.msg_error("display_stats_gamble", "Error Printing user_stats", error_printing_user_stats)
                    continue
        user_input = input(f"{bot.long_dashes()}\n"
                           f"Enter 0 To Go Back\n"
                           f"Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def display_stats_heist():
    async def display_crew(key_crew: str):
        async def display_date(key_date: str):
            async def display_time(key_time: str):
                cls()
                length = get_length(list(user_document['data_games']['heist']['gamble']['history'][key_crew][key_date][key_time].keys()))
                print(await top_bar(f"{key_date.replace('-', '/')} {key_time} Heist Result"))
                for heist_key, heist_data in user_document['data_games']['heist']['gamble']['history'][key_crew][key_date][key_time].items():
                    print(f"{max_length(heist_key.replace('_', ' ').title(), length)}: {heist_data if type(heist_data) not in (float, int) else numberize(heist_data)}")
                input(f"{bot.long_dashes()}\n"
                      f"Hit Enter To Go Back")
                await bot.go_back()

            while True:
                cls()
                options = []
                user_document = await refresh_document_user()
                length = get_length(len(user_document['data_games']['heist']['gamble']['history'][key_crew][key_date].keys()))
                print(await top_bar(f"{key_date.replace('-', '/')} Heists"))
                try:
                    for n, game_time in enumerate(user_document['data_games']['heist']['gamble']['history'][key_crew][key_date].keys(), start=1):
                        options.append(max_length(f"{n}. {game_time}", length, n))
                except Exception as error_printing_times:
                    await bot.msg_error("display_stats_heist", f"Error building times options for {key_date}", error_printing_times)
                user_input = input(f"{f'{bot.long_dashes()}{nl}{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                   f"{f'{bot.long_dashes()}{nl}Enter # Or Type Time To View{nl}' if len(options) > 0 else ''}"
                                   f"Enter 0 To Go Back\n"
                                   f"Enter Nothing To Refresh\n")
                if user_input == "":
                    pass
                elif user_input.isdigit():
                    user_input = int(user_input)
                    if user_input == 0:
                        await bot.go_back()
                        break
                    elif user_input <= len(options):
                        await display_time(remove_period_area(options[user_input - 1]))
                    else:
                        await bot.invalid_entry(int)
                elif user_input in bot.special_commands.values():
                    await special_command(user_input)
                elif user_input.lower() in check_numbered_list(options):
                    await display_time(user_input.lower())
                else:
                    await bot.invalid_entry(str)

        while True:
            cls()
            options = []
            user_document = await refresh_document_user()
            length = get_length(len(user_document['data_games']['heist']['gamble']['history'][key_crew].keys()))
            print(await top_bar(f"{key_crew} Heist Dates"))
            try:
                for n, date in enumerate(user_document['data_games']['heist']['gamble']['history'][key_crew].keys(), start=1):
                    options.append(max_length(f"{n}. {date}", length, n))
            except Exception as error_building_crew_dates:
                await bot.msg_error("display_stats_heist", "Error building crew dates", error_building_crew_dates)
            user_input = input(f"{f'{bot.long_dashes()}{nl}{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{f'{bot.long_dashes()}{nl}Enter # Or Type Date To View{nl}' if len(options) > 0 else ''}"
                               f"Enter 0 To Go Back\n"
                               f"Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input <= len(options):
                    await display_date(remove_period_area(options[user_input - 1]))
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            elif user_input.lower() in check_numbered_list(options):
                await display_date(user_input.lower())
            else:
                await bot.invalid_entry(str)

    async def refresh_global_stats():
        user_stats = {
            "total_heists": 0,
            "total_successful": 0,
            "total_fail": 0,
            "total_cost": 0,
            "total_gain": 0,
        }
        try:
            for game_dates in user_document['data_games']['heist']['gamble']['history'].values():
                for game_times in game_dates.values():
                    for game_data in game_times.values():
                        user_stats['total_heists'] += 1
                        user_stats['total_cost'] += game_data['heist_cost']
                        if game_data['status']:
                            user_stats['total_successful'] += 1
                            user_stats['total_gain'] += game_data['points_gained']
                        else:
                            user_stats['total_fail'] += 1
        except Exception as error_building_user_stats_global:
            await bot.msg_error("display_stats_heist", "Error building user_stats global", error_building_user_stats_global)
        return user_stats

    while True:
        cls()
        options = []
        user_document = await refresh_document_user()
        user_stats = await refresh_global_stats()
        length = get_length(list(user_stats.keys()))
        print(await top_bar("Heist History"))
        for _key, _value in user_stats.items():
            try:
                print(f"{max_length(_key.replace('_', ' ').title(), length)}: {numberize(_value)}")
            except Exception as error_printing_user_stats_global:
                await bot.msg_error("display_stats_heist", "Error printing user_stats global", error_printing_user_stats_global)
                continue
        print(bot.long_dashes())
        length = get_length(len(user_document['data_games']['heist']['gamble']['history'].keys()))
        for n, _game_date in enumerate(user_document['data_games']['heist']['gamble']['history'].keys(), start=1):
            try:
                options.append(max_length(f"{n}. {_game_date}", length, n))
            except Exception as error_building_crew_options:
                await bot.msg_error("display_stats_heist", "Error building crew options", error_building_crew_options)
                continue
        user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                           f"{bot.long_dashes()}\n"
                           f"{f'Enter # Or Type Crew To View{nl}' if len(options) > 0 else ''}"
                           f"Enter 0 To Go Back\n"
                           f"Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input <= len(options):
                await display_crew(remove_period_area(options[user_input - 1]))
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        elif user_input.lower() in check_numbered_list(options):
            await display_crew(user_input.lower())
        else:
            await bot.invalid_entry(str)


async def display_stats_jail():
    async def display_detailed_chodeling(chodeling_name: str):
        async def display_detailed_stats(key_type: str):
            cls()
            length = get_length(list(user_document['data_games']['jail']['history'][chodeling_name][key_type].keys()))
            print(await top_bar(f"Jail Stats -> {chodeling_name} {key_type.title()} Stats"))
            for _key, _value in user_document['data_games']['jail']['history'][chodeling_name][key_type].items():
                try:
                    print(f"{max_length(_key.replace('_', ' ').title(), length)}: {numberize(_value)}")
                except Exception as error_printing_chodeling_detailed_stats:
                    await bot.msg_error("display_stats_jail", f"Error printing {chodeling_name} detailed {key_type} stats", error_printing_chodeling_detailed_stats)
                    continue
            input(f"{bot.long_dashes()}\n"
                  f"Hit Enter To Go Back")

        while True:
            cls()
            options = []
            length = get_length(len(user_document['data_games']['jail']['history'][chodeling_name].keys()))
            print(await top_bar(f"Jail Stats -> {chodeling_name} Types"))
            for n, _type in enumerate(user_document['data_games']['jail']['history'][chodeling_name].keys(), start=1):
                try:
                    options.append(max_length(f"{n}. {_type.title()}", length, n))
                except Exception as error_building_detailed_chodeling_types:
                    await bot.msg_error("display_stats_jail", "Error building detailed chodeling types", error_building_detailed_chodeling_types)
                    continue
            if len(options) > 0:
                print(nl.join(options))
            user_input = input(f"{bot.long_dashes()}\n"
                               f"{f'Enter # Or Name Of Type Of Stats To View{nl}' if len(options) > 0 else ''}"
                               f"Enter 0 To Go Back\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input <= len(options):
                    await display_detailed_stats(remove_period_area(options[user_input - 1]).lower())
                else:
                    await bot.invalid_entry(int)
            elif user_input.lower() in check_numbered_list(options):
                await display_detailed_stats(user_input.lower())
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)

    async def display_detailed_stats_jail():
        while True:
            cls()
            options = []
            user_document = await refresh_document_user()
            keys_sorted = sorted(user_document['data_games']['jail']['history'].keys(), key=lambda x: x)
            length = get_length(len(keys_sorted))
            print(await top_bar("Jail Stats -> Chodeling Options"))
            for n, _chodeling in enumerate(keys_sorted, start=1):
                try:
                    options.append(max_length(f"{n}. {_chodeling}", length, n))
                except Exception as error_building_chodelings_stats_options:
                    await bot.msg_error("display_stats_jail", "Error building chodelings options detailed stats", error_building_chodelings_stats_options)
                    continue
            if len(options) > 0:
                print(nl.join(options))
            user_input = input(f"{bot.long_dashes()}\n"
                               f"{f'Enter # Or Name Of Chodeling To View Stats{nl}' if len(options) > 0 else ''}"
                               f"Enter 0 To Go Back\n"
                               f"Enter Nothing To Refresh\n")
            if user_input == "":
                pass
            elif user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await bot.go_back()
                    break
                elif user_input <= len(options):
                    await display_detailed_chodeling(remove_period_area(options[user_input - 1]))
                else:
                    await bot.invalid_entry(int)
            elif user_input.lower() in check_numbered_list(options):
                await display_detailed_chodeling(user_input.lower())
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)

    async def refresh_jail_stats():
        user_stats = {
            "total": 0,
            "success": 0,
            "fail": 0,
            "fished": user_document['data_games']['jail']['fish_jails'],
            "escaped": 0,
            "early_release": user_document['data_games']['jail']['early_release'],
            "shielded": user_document['data_games']['jail']['shield_times'],
            "uno_reverse": 0
        }
        for _chodeling in user_document['data_games']['jail']['history'].values():
            for _data in _chodeling.values():
                try:
                    user_stats['success'] += _data['success']
                    user_stats['fail'] += _data['fail']
                    user_stats['escaped'] += _data['escaped']
                    user_stats['uno_reverse'] += _data['uno_reverse']
                except Exception as error_in_refresh_jail_stats_loop:
                    await bot.msg_error("display_stats_jail", "Error in refresh_jail_stats loop", error_in_refresh_jail_stats_loop)
                    continue
        for _key, _value in user_stats.items():
            if _key != "total":
                user_stats['total'] += _value
        return user_stats

    while True:
        cls()
        user_document = await refresh_document_user()
        user_stats = await refresh_jail_stats()
        length = get_length(list(user_stats.keys()))
        print(await top_bar("Jail Stats"))
        for _key, _value in user_stats.items():
            print(f"{max_length(_key.replace('_', ' ').title(), length)}: {numberize(_value)}")
        user_input = input(f"{bot.long_dashes()}\n"
                           f"Enter 1 To View Detailed Stats\n"
                           f"Enter 0 To Go Back\n"
                           f"Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input == 1:
                await display_detailed_stats_jail()
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def display_stats_other():
    await bot.not_programmed()


async def display_stats_tag():
    while True:
        cls()
        user_document = await refresh_document_user()
        length = get_length(list(user_document['data_games']['tag'].keys()))
        print(await top_bar("Tag Stats"))
        try:
            for _key, _value in user_document['data_games']['tag'].items():
                print(f"{max_length(_key.title(), length)}: {numberize(_value)}")
        except Exception as error_printing_tag_stats:
            await bot.msg_error("display_stats_tag", "Error Printing Tag Stats", error_printing_tag_stats)
        user_input = input(f"{bot.long_dashes()}\n"
                           f"Enter 0 To Go Back\n"
                           f"Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif user_input.isdigit():
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


async def on_message(msg: ChatMessage):
    try:
        if msg.text.startswith(("$", "!", "¡")):
            return
        msg.text = msg.text.lower()
        if msg.user.id != bot.login_details['target_id']:
            if f"{user.display_name.lower()}" in msg.text:
                await flash_window("attn")
        else:
            if msg.text.startswith(user.display_name.lower()) and "autocast expired" in msg.text:
                await flash_window("auto_cast_expired")
    except Exception as error_on_message:
        await bot.msg_error("on_message", "Generic Error", error_on_message)
        return


async def on_ready(event: EventData):
    try:
        await event.chat.join_room(bot.login_details['target_name'])
        logger.info(f"{fortime()}: Connected to {bot.login_details['target_name']} channel\n{bot.long_dashes()}")
    except Exception as e:
        await bot.msg_error("on_ready", f"Failed to connect to {bot.login_details['target_name']} channel", e)


# ----------- Main App Functions -----------
async def run():
    async def shutdown():
        cls()
        chat.stop()
        await asyncio.sleep(1)
        await bot.close()
        logger.info(f"Twitch Processes Shutdown")
        await asyncio.sleep(1)
        await disconnect_mongo()
        await asyncio.sleep(1)
        logger.info(f"{bot.long_dashes()}\nShutdown Sequence Completed\n{bot.long_dashes()}")

    chat = await Chat(bot)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.start()

    await asyncio.sleep(2.5)
    while True:
        cls()
        try:
            print(await top_bar('Main Menu'))
            user_input = input("Enter 1 To View Commands\n"
                               "Enter 2 To View Leaderboards\n"
                               "Enter 3 To View Profile\n"
                               "Enter 8 To Change App Settings\n"
                               "Enter 9 To Change Profile Settings\n"
                               "Enter 0 To Shutdown Bot\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await shutdown()
                    break
                elif user_input == 1:
                    await chodeling_commands()
                elif user_input == 2:
                    await chodeling_leaderboards()
                elif user_input == 3:
                    await chodeling_profile()
                elif user_input == 8:
                    await chodeling_settings_app()
                elif user_input == 9:
                    await chodeling_settings_document()
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)
        except KeyboardInterrupt:
            # ToDo; Fix This BULLSHIT
            print("EXITING")
            await shutdown()
            break
        except Exception as e:
            await bot.msg_error("run", "Generic Error", e)
            await asyncio.sleep(10)
            await shutdown()
            break


if __name__ == "__main__":
    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger("logger", f"main_log--{init_time}.log", logger_list)
    if None in logger_list:
        print(f"One of thee loggers isn't setup right\n{nl.join(logger_list)}\nQuitting program")
        time.sleep(10)
    else:
        auth_dict = check_db_auth()
        if auth_dict is not None:
            bot = BotSetup(auth_dict['bot_id'], auth_dict['secret_id'])
            status = bot.data_check()
            if status:
                bot.set_dashes()
                while True:
                    cls()
                    user_input = input("Enter 1 to start bot\nEnter 0 to exit\n")
                    if user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            logger.info("Exiting App")
                            time.sleep(2)
                            break
                        elif user_input == 1:
                            cls()
                            mongo_db = connect_mongo("twitch", auth_dict['db_string'], DEFAULT_CONNECTION_NAME)
                            time.sleep(1)
                            if mongo_db is None:
                                logger.error(f"{fortime()}: Error connecting to DB!! Exiting App")
                                time.sleep(10)
                                break
                            asyncio.run(auth_bot())
                            user = asyncio.run(get_auth_user_id())
                            if user is not None:
                                bot.set_vars()
                                keyboard_thread = threading.Thread(target=hotkey_listen, daemon=True)
                                keyboard_thread.start()
                                asyncio.run(run())
                            break
                        else:
                            asyncio.run(bot.invalid_entry(int))
                    else:
                        asyncio.run(bot.invalid_entry(str))

    asyncio.run(log_shutdown(logger_list))
