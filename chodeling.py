import os
import sys
import math
import time
import asyncio
import logging
import datetime
import keyboard
import threading
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv
from colorama import Fore, Style
from twitchAPI.twitch import Twitch, TwitchUser
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent, TwitchBackendException
from twitchAPI.chat import Chat, EventData, ChatMessage  #, ChatSub, ChatCommand
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME, Document

# ToDo; Add 'upsidedown text to everything' easter egg
# ToDo; Add stats for time added (also rework chodebot & user documents to keep track & write script to scrape past logs to build data)

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal"
else:
    application_path = os.path.dirname(__file__)

directories = {
    "data": f"{application_path}\\data\\",
    "logs": f"{application_path}\\logs\\",
    "logs_archive": f"{application_path}\\logs\\archive_log\\"
}

Path(directories['data']).mkdir(parents=True, exist_ok=True)
Path(directories['logs']).mkdir(parents=True, exist_ok=True)
Path(directories['logs_archive']).mkdir(parents=True, exist_ok=True)

load_dotenv()
bot_id = os.getenv("bot_id")
bot_secret = os.getenv("bot_secret")
db_string = os.getenv("db_string")

nl = "\n"
logger_list = []
long_dashes = "-" * 100


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch
        self.data_settings = {
            "flash": f"{directories['data']}flash.txt",
            "types_heist": f"{directories['data']}types_heist.txt",
            "types_always_display": f"{directories['data']}types_always_display.txt",
            "types_sort": f"{directories['data']}types_sort.txt"
        }
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
        self.login_details = {
            "target_id": "268136120",
            "target_name": "TheeChody"
        }
        self.settings = {
            "types_always_display": (
                "auto_cast_remaining",
                "level",
                "points",
                "points_xp",
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
            )
        }
        self.special_commands = {
            "bet": "^B",
            "bbet": "^BB",
            "fish": "^F",
            "fish_beet": "^RB",
            "fish_stroke": "^RS",
            "heist": "^H",
            "joints_count_update": "^J",
            # "quit": "^Q"
        }
        self.special_users = {
            "bingo": {
                "carnage_deamon": "659640208",
                "Free2Escape": "777768639"
            }
        }
        self.target_scopes = [
            AuthScope.CHAT_READ,
            AuthScope.CHAT_EDIT,
            AuthScope.USER_BOT,
            AuthScope.USER_WRITE_CHAT
        ]

    @staticmethod
    async def check_permissions(user_id: str, perm_check: str) -> bool:
        try:
            channel_document = await refresh_document_channel()
            mods = channel_document['data_lists']['mods']
            if user_id == channel_document['_id']:
                return True
            elif perm_check == "mod" and user_id in mods:
                return True
            elif perm_check == "mini_game_bingo" and (user_id in mods or user_id in bot.special_users['bingo'].values()):
                return True
            return False
        except Exception as error_permission_check:
            await bot.error_msg("check_permissions", "Generic Error", error_permission_check)
            return False

    @staticmethod
    async def check_self_id(chodeling_id: str):
        if chodeling_id == user.id:
            print("Can't choose yourself!!")
            await asyncio.sleep(3)
            return False
        return True

    @staticmethod
    async def check_self_name(chodeling_name: str):
        if chodeling_name == user.display_name.lower():
            print("Can't choose yourself!!")
            await asyncio.sleep(3)
            return False
        return True

    @staticmethod
    async def error_msg(function_name: str, error_type: any, error_str: any):
        logger.error(f"{fortime()}: Error in '{function_name}' -- {error_type}\n{error_str}")
        await asyncio.sleep(5)

    @staticmethod
    async def go_back(main_menu: bool = False):
        print('Returning to Main Menu' if main_menu else 'Going Back')
        await asyncio.sleep(1)

    @staticmethod
    async def invalid_entry(invalid_type: type(str) | type(int)):
        print(f"Invalid{' Number' if invalid_type == int else ''} entry, try again")
        await asyncio.sleep(2)

    @staticmethod
    async def msg_no_perm():
        input("Required Permissions Not Satisfied!!\n"
              "Hit Enter to go back")
        await bot.go_back()


async def app_settings():
    async def check_var(key_check: str, var_check: str) -> bool:
        if read_file(bot.data_settings[key_check], str) == var_check.lower():
            print(f"Your sort type is already set to {var_check.replace('_', ' ').title()}")
            await bot.go_back()
            return True
        return False

    async def set_setting(setting_key: str):
        while True:
            cls()
            options = []
            print(await top_bar(f"Default {setting_key.replace('_', ' ').title()} Setting"))
            try:
                for n, var in enumerate(bot.settings[setting_key], start=1):
                    options.append(f"{n}. {var.replace('_', ' ').title()}")
            except Exception as error_printing_display_variables:
                await bot.error_msg("app_settings", "Error Printing Settings Options", error_printing_display_variables)
            user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{long_dashes}\n"
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

    async def write_var(key_write: str, var_write: str):
        with open(bot.data_settings[key_write], "w") as file:
            file.write(var_write.lower())
        print(f"{key_write.replace('_', ' ').title()} Variable set to: {var_write.replace('_', ' ').title()}")
        await bot.go_back()

    while True:
        cls()
        print(await top_bar("App Settings"))
        user_input = input("Enter 1 To Change Default Display Variable\n"
                           "Enter 2 To Change Default Sorting Variable\n"
                           "Enter 3 To Change Flash Settings\n"
                           "Enter 4 To Change Default Heist Crew\n"
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
                async def set_setting(setting_type: str):
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
                                        break
                                    except Exception as error_writing_new_values:
                                        await bot.error_msg("app_settings", "Setting Flash Settings", error_writing_new_values)

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
                            await set_setting("frequency")
                        elif user_input == 2:
                            await set_setting("speed")
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 4:
                await set_setting("types_heist")
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


def check_numbered_list(list_check: list) -> list:
    new_list = []
    for item in list_check:
        new_list.append(remove_period_area(item.lower()))
    return new_list


async def chodeling_commands():
    async def show_command_category(command_key: str):
        while True:
            cls()
            user_document = await refresh_document_user()
            if command_key in ("mods", "unlisted") and not await bot.check_permissions(user_document['_id'], "owner"):
                await bot.msg_no_perm()
                break
            options = []
            print(await top_bar(f"{command_key.title()} Commands"))
            try:
                for n, cmd in enumerate(sorted(bot.commands_available[command_key], key=lambda x: x), start=1):
                    options.append(f"{n}. {cmd}")
            except Exception as error_printing_command:
                await bot.error_msg("chodeling_commands", f"show_command '{command_key}'", error_printing_command)
            user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{long_dashes}\n"
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
        print(await top_bar("Commands Area"))
        try:
            for n, key in enumerate(sorted(bot.commands_available.keys(), key=lambda x: x), start=1):
                options.append(f"{n}. {key}")
        except Exception as error_fetching_commands:
            await bot.error_msg("chodeling_commands", "Fetching Specific Commands", error_fetching_commands)
        user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                           f"{long_dashes}\n"
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
                await show_command_category(remove_period_area(options[user_input - 1]))
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        elif len(options) > 0 and user_input.lower() in check_numbered_list(options):
            await show_command_category(user_input.lower())
        else:
            await bot.invalid_entry(str)


async def chodeling_stats():
    while True:
        cls()
        user_document = await refresh_document_user()
        print(await top_bar("Rank Information"))
        try:
            print(f"Points; {numberize(user_document['data_user']['rank']['points'])}\n"
                  f"Level; {user_document['data_user']['rank']['level']:,}\n"
                  f"XP; {numberize(user_document['data_user']['rank']['xp'])}\n"
                  f"XP Boost; {numberize(user_document['data_user']['rank']['boost'])}")
        except Exception as error_printing_chodeling_stats:
            await bot.error_msg("chodeling_stats", "Error Printing Chodeling Stats", error_printing_chodeling_stats)
        user_input = input(f"{long_dashes}\n"
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
                print("Not Programmed Yet")
                await asyncio.sleep(3)
            elif user_input == 6:
                print("Not Programmed Yet")
                await asyncio.sleep(3)
            elif user_input == 7:
                print("Not Programmed Yet")
                await asyncio.sleep(3)
            elif user_input == 8:
                print("Not Programmed Yet")
                await asyncio.sleep(3)
            else:
                await bot.invalid_entry(int)
        elif user_input in bot.special_commands.values():
            await special_command(user_input)
        else:
            await bot.invalid_entry(str)


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def colour(colour_: str, str_: str) -> str:
    if colour_ == "blue":
        colour_ = Fore.BLUE
    elif colour_ == "cyan":
        colour_ = Fore.CYAN
    elif colour_ == "green":
        colour_ = Fore.GREEN
    elif colour_ == "purple":
        colour_ = Fore.MAGENTA
    elif colour_ == "red":
        colour_ = Fore.RED
    else:
        colour_ = Fore.RESET
    return f"{colour_}{str_}{Fore.RESET}"


def connect_mongo(db, alias):
    try:
        client = connect(db=db, host=db_string, alias=alias)
        logger.info(f"{fortime()}: MongoDB Connected\n{long_dashes}")
        time.sleep(1)
        client.get_default_database(db)
        logger.info(f"{fortime()}: Database Loaded\n{long_dashes}")
        return client
    except Exception as e:
        logger.error(f"{fortime()}: Error Connecting MongoDB -- {e}")
        return None


async def disconnect_mongo():
    try:
        disconnect_all()
        logger.info(f"{long_dashes}\nDisconnected from MongoDB")
    except Exception as e:
        logger.error(f"{fortime()}: Error Disconnection MongoDB -- {e}")
        return


async def display_stats_bingo():
    async def build_board(game_board: dict, item_list: list, minor_pattern: str) -> dict:
        chodeling_board = {}
        try:
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
                    index = index_bingo(item, item_list) + 1
                    chodeling_board[row][index] = f"{style('bright' if minor_pattern_hit or status else 'normal', colour('cyan' if minor_pattern_hit else 'green' if status else 'red', str(index)))}"
                    # chodeling_board[row][index] = f"{style('bright', colour('cyan' if minor_pattern_hit else 'green' if status else 'red', str(index)))}"
        except Exception as error_building_board:
            await bot.error_msg("display_stats_bingo", "Building Board", error_building_board)
        return chodeling_board

    async def check_bingo_game_status() -> bool:
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        if None in (user_document['data_games']['bingo']['current_game']['game_type'], channel_document['data_games']['bingo']['current_game']['game_type']):
            cmd = "'!bingo join'"
            game_type = channel_document['data_games']['bingo']['current_game']['game_type']
            if game_type is not None:
                game_type = game_type.replace('_', ' ').title()
            input(f"{'No Bingo Game Running' if game_type is None else f'There is a {game_type} running{nl}Use {cmd} to join'}\n"
                  "Hit Enter To Go Back")
            await bot.go_back()
            return False
        return True

    def index_bingo(item: str, item_list: list) -> int:
        return item_list.index(item)

    async def print_board(chodeling_board: dict, own_board: bool = True, chodeling_name: str = ""):
        try:
            print(f"{long_dashes}\n"
                  f"{'Your' if own_board else chodeling_name} Bingo Board\n"
                  f"{long_dashes}")
            dashes = '-' * ((5 * len(chodeling_board)) + (len(chodeling_board) + 1))
            print(dashes)
            for row, items in chodeling_board.items():
                print(f"{print_row(items)}\n{dashes}")
        except Exception as error_printing_board:
            await bot.error_msg("display_stats_bingo", "Printing Board", error_printing_board)

    async def print_items(items_print: dict):
        try:
            for n, (item, status) in enumerate(items_print.items(), start=1):
                print(f"{style('bright' if status else 'normal', colour('green' if status else 'red', f' {n}. {item}' if n < 10 else f'{n}. {item}'))}")
                # print(f"{style('bright', colour('green' if status else 'red', f' {n}. {item}' if n < 10 else f'{n}. {item}'))}")
        except Exception as error_printing_list:
            await bot.error_msg("display_stats_bingo", "Printing Available List", error_printing_list)

    def print_row(items: dict) -> str:
        str_ = "|"
        for index, item in items.items():
            if len(str(index)) == 1:
                space_left, space_right = 2, 2
            elif len(str(index)) == 2:
                space_left, space_right = 1, 2
            else:
                space_left, space_right = 1, 1
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
            user_document = await refresh_document_user()
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
            await bot.error_msg("display_stats_bingo", "Error Refreshing user_stats", error_refreshing_stats)
        return user_stats

    while True:
        cls()
        options = []
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        print(await top_bar("Bingo Options"))
        try:
            if None not in (user_document['data_games']['bingo']['current_game']['game_type'], channel_document['data_games']['bingo']['current_game']['game_type']):
                options = ["Enter 1 To View Game Info", "Enter 2 To View Your Board"]
        except Exception as error_building_options:
            await bot.error_msg("display_stats_bingo", "Error Building Options", error_building_options)
        options.append("Enter 3 To View History")
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
                    chodeling_board = await build_board(chodeling_document['data_games']['bingo']['current_game']['game_board'], list(game_dict['items'].keys()), game_dict['chosen_pattern'][1])
                    print(await top_bar(f"Current Game Board For {chodeling_name}"))
                    if len(chodeling_board) > 0:
                        await print_items(game_dict['items'])
                        await print_board(chodeling_board, False if chodeling_name != user.display_name.lower() else True, f"{chodeling_name}'s")
                    input(f"{long_dashes}\n"
                          f"Hit Enter To {'Continue' if not last_board else 'Go Back'}")
                    if last_board:
                        await bot.go_back()

                while True:
                    cls()
                    if not await check_bingo_game_status():
                        break
                    options = []
                    channel_document = await refresh_document_channel()
                    game_dict = channel_document['data_games']['bingo']['current_game']
                    print(await top_bar("Current Game Info"))
                    try:
                        print(f"Board Size: {game_dict['board_size']}x{channel_document['data_games']['bingo']['current_game']['board_size']}\n"
                              f"Game Type: {game_dict['game_type'].replace('_', ' ').title()}\n"
                              f"Major Jackpot: {numberize(game_dict['major_bingo_pot'])}\n"
                              f"Major Pattern: {game_dict['chosen_pattern'][0].replace('_', ' ').title()}\n"
                              f"Minor Pattern: {game_dict['chosen_pattern'][1].replace('_', ' ').title()}")
                    except Exception as error_printing_bingo_game_info:
                        await bot.error_msg("display_stats_bingo", "Printing Bingo Game Info", error_printing_bingo_game_info)
                    try:
                        for n, chodeling_name in enumerate(sorted(game_dict['chodelings'].keys(), key=lambda x: x), start=1):
                            options.append(f"{n}. {chodeling_name}")
                    except Exception as error_building_chodelings_options:
                        await bot.error_msg("display_stats_bingo", "Error Building Chodeling Options", error_building_chodelings_options)
                    if len(options) > 0:
                        print(f"{long_dashes}\n"
                              f"Chodeling's In Game;\n"
                              f"{long_dashes}\n"
                              f"{nl.join(options)}")
                    user_input = input(f"{long_dashes}\n"
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
                async def call_action(action_to_call: str):
                    status = await send_chat_msg(f"!bingo action {action_to_call.title()}")
                    print(f"Call '{action_to_call.title()}' {'Succeeded' if status else 'Failed'}")
                    await asyncio.sleep(2)

                while True:
                    cls()
                    if not await check_bingo_game_status():
                        break
                    user_document = await refresh_document_user()
                    channel_document = await refresh_document_channel()
                    bingo_perm = await bot.check_permissions(user.id, "mini_game_bingo")
                    print(await top_bar(f"{channel_document['data_games']['bingo']['current_game']['game_type'].title()} Items Available"))
                    await print_items(channel_document['data_games']['bingo']['current_game']['items'])
                    chodeling_board = await build_board(user_document['data_games']['bingo']['current_game']['game_board'],
                                                        list(channel_document['data_games']['bingo']['current_game']['items'].keys()),
                                                        channel_document['data_games']['bingo']['current_game']['chosen_pattern'][1])
                    if len(chodeling_board) > 0:
                        await print_board(chodeling_board)
                    user_input = input(f"{long_dashes}\n"
                                       f"{f'Enter # Or Type Out Item To Call{nl}' if bingo_perm else ''}"
                                       f"Enter 0 To Go Back\n"
                                       f"Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif user_input.isdigit():
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif bingo_perm and user_input <= len(channel_document['data_games']['bingo']['current_game']['items']):
                            await call_action(list(channel_document['data_games']['bingo']['current_game']['items'].keys())[user_input - 1])
                        else:
                            await bot.invalid_entry(int)
                    elif user_input in bot.special_commands.values():
                        await special_command(user_input)
                    elif bingo_perm and user_input.lower() in check_numbered_list(list(channel_document['data_games']['bingo']['current_game']['items'].keys())):
                        await call_action(user_input.lower())
                    else:
                        await bot.invalid_entry(str)
            elif user_input == 3:
                while True:
                    cls()
                    user_stats = await refresh_stats()
                    print(await top_bar("Bingo Stats"))
                    if len(user_stats) > 0:
                        try:
                            points_won = user_stats['total_points_won']
                            total_games = user_stats['total_games']
                            total_major_bingo = user_stats['total_major_bingo']
                            total_minor_bingo = user_stats['total_minor_bingo']
                            print(f"Total Games: {numberize(user_stats['total_games'])}\n"
                                  f"Total Major Bingo's: {numberize(user_stats['total_major_bingo'])}{'' if total_major_bingo == 0 else f' | {total_major_bingo / total_games * 100:.2f}%'}{'' if user_stats['total_major_bingo'] == 0 else f' ({numberize(points_won)})'}\n"
                                  f"Total Minor Bingo's: {numberize(user_stats['total_minor_bingo'])}{'' if total_minor_bingo == 0 else f' | {total_minor_bingo / total_games * 100:.2f}%'}{'' if total_minor_bingo == 0 else f' ({numberize(total_minor_bingo * 10000)})'}")
                            if len(user_stats['game_types']) > 0:
                                for game_type in list(sorted(user_stats['game_types'].keys(), key=lambda x: x)):
                                    print(f"{game_type.replace('_', ' ').title()} Games Played: {numberize(user_stats['game_types'][game_type])} | {user_stats['game_types'][game_type] / total_games * 100:.2f}%")
                        except Exception as error_printing_user_stats:
                            await bot.error_msg("display_stats_bingo", "Error Printing user_stats", error_printing_user_stats)
                    user_input = input(f"{long_dashes}\n"
                                       f"Enter 1 To View Individual Games\n"
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
                                async def show_date(key_date: str):
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
                                                await bot.error_msg("display_stats_bingo", "Generic Error", f"Error fetching {chodeling_name} bingo game data for {str(game_channel_dict['game_started_time'])}")
                                            else:
                                                chodeling_board = await build_board(game_data['game_board'], list(game_channel_dict['items'].keys()), game_channel_dict['chosen_pattern'][1])
                                                if len(chodeling_board) > 0:
                                                    await print_items(game_channel_dict['items'])
                                                    await print_board(chodeling_board, False, f"{chodeling_name}'s")
                                                input(f"{long_dashes}\n"
                                                      f"Hit Enter To Go Back")
                                                await bot.go_back()

                                        while True:
                                            cls()
                                            game_user_dict = user_document['data_games']['bingo']['history'][key_date][key_time]
                                            game_channel_dict = channel_document['data_games']['bingo']['history'][key_date][user_document['data_games']['bingo']['history'][key_date][key_time]['game_started'].strftime('%I:%M%p').removeprefix('0').lower()]
                                            date_start_formatted = game_channel_dict['game_started_time'].strftime("%y/%m/%d")
                                            time_start_formatted = game_channel_dict['game_started_time'].strftime('%I:%M%p').removeprefix('0').lower()
                                            date_end_formatted = game_channel_dict['game_ended_time'].strftime("%y/%m/%d")
                                            time_end_formatted = game_channel_dict['game_ended_time'].strftime('%I:%M%p').removeprefix('0').lower()
                                            points_won = game_user_dict['points_won']
                                            options = []
                                            for n, chodeling in enumerate(list(sorted(game_channel_dict['chodelings'].keys(), key=lambda x: x)), start=1):
                                                options.append(f"{n}. {chodeling}")
                                            print(await top_bar(f"{date_start_formatted} {time_start_formatted} - {f'{date_end_formatted} ' if date_end_formatted != date_start_formatted else ''}{time_end_formatted}"))
                                            print(f"Game Type: {game_user_dict['game_type'].replace('_', ' ').title()}\n"
                                                  f"Bingo Board Size: {game_channel_dict['board_size']}x{game_channel_dict['board_size']}\n"
                                                  f"Major Bingo Jackpot: {numberize(game_channel_dict['major_bingo_pot'])}\n"
                                                  f"Major Bingo Pattern: {game_channel_dict['chosen_pattern'][0].replace('_', ' ').title()} ({game_user_dict['major_bingo']}{f'({numberize(points_won)})' if game_user_dict['major_bingo'] else ''})\n"
                                                  f"Minor Bingo Pattern: {game_channel_dict['chosen_pattern'][1].replace('_', ' ').title()} ({game_user_dict['minor_bingo']})\n"
                                                  f"{long_dashes}")
                                            await print_items(game_channel_dict['items'])
                                            chodeling_board = await build_board(game_user_dict['game_board'], list(game_channel_dict['items'].keys()), game_channel_dict['chosen_pattern'][1])
                                            if len(chodeling_board) > 0:
                                                await print_board(chodeling_board)
                                            print(f"{long_dashes}\n"
                                                  f"Chodelings Who Played;\n"
                                                  f"{long_dashes}\n"
                                                  f"{nl.join(options)}")
                                            user_input = input(f"{long_dashes}\n"
                                                               f"Enter # Or Type Chodeling To View Their Board\n"
                                                               f"Enter 0 To Go Back\n"
                                                               f"Enter Nothing To Refresh\n")
                                            if user_input == "":
                                                pass
                                            elif user_input in bot.special_commands.keys():
                                                await special_command(user_input)
                                            elif user_input.isdigit():
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
                                            else:
                                                await bot.invalid_entry(str)

                                    while True:
                                        cls()
                                        options = []
                                        user_document = await refresh_document_user()
                                        print(await top_bar(f"{key_date} Games"))
                                        try:
                                            for n, key_time in enumerate(user_document['data_games']['bingo']['history'][key_date].keys(), start=1):
                                                options.append(f"{n}. {key_time}")
                                        except Exception as error_building_bingo_date:
                                            await bot.error_msg("display_stats_bingo", f"Error Building Times For {key_date}", error_building_bingo_date)
                                        if len(options) > 0:
                                            print(nl.join(options))
                                        user_input = input(f"{long_dashes}\n"
                                                           f"{f'Enter # Or Time To View Game Data{nl}' if len(options) > 0 else ''}"
                                                           f"Enter 0 To Go Back\n"
                                                           f"Enter Nothing To Refresh\n")
                                        if user_input == "":
                                            pass
                                        elif user_input in bot.special_commands.values():
                                            await special_command(user_input)
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
                                        else:
                                            await bot.invalid_entry(str)

                                cls()
                                options = []
                                user_document = await refresh_document_user()
                                print(await top_bar("Bingo History"))
                                try:
                                    if len(user_document['data_games']['bingo']['history']) == 0:
                                        input("You don't have any bingo history yet!!\nHit Enter To Go Back")
                                        await bot.go_back()
                                        break
                                    for n, date in enumerate(user_document['data_games']['bingo']['history'].keys(), start=1):
                                        options.append(f"{n}. {date}")
                                except Exception as error_building_bingo_games:
                                    await bot.error_msg("display_stats_bingo", "Error Building Bingo Games", error_building_bingo_games)
                                if len(options) > 0:
                                    print(nl.join(options))
                                user_input = input(f"{long_dashes}\n"
                                                   f"{f'Enter # Or Date To Choose Date{nl}' if len(options) > 0 else ''}"
                                                   f"Enter 0 To Go Back\n"
                                                   f"Enter Nothing To Refresh\n")
                                if user_input == "":
                                    pass
                                elif user_input in bot.special_commands.values():
                                    await special_command(user_input)
                                elif user_input.isdigit():
                                    user_input = int(user_input)
                                    if user_input == 0:
                                        await bot.go_back()
                                        break
                                    elif user_input <= len(options):
                                        await show_date(remove_period_area(options[user_input - 1]))
                                    else:
                                        await bot.invalid_entry(int)
                                elif user_input.lower() in check_numbered_list(options):
                                    await show_date(user_input.lower())
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


async def display_stats_fight():
    async def detailed_options(key: str):
        async def detailed_stats(name: str):
            async def display_fight_times(key_date: str):
                async def display_fight(key_time: str):
                    cls()
                    print(await top_bar(f"{key_date.replace('-', '/')} {key_time} {name} {key.replace('_', ' ').title()} Fight"))
                    try:
                        for key_fight, key_data in user_document['data_games']['fight'][key][name][key_date][key_time].items():
                            if type(key_data) == list:
                                options_list = []
                                for item in key_data:
                                    try:
                                        # options_list.append("None" if item is None else item if type(item) not in (float, int) else numberize(item))
                                        options_list.append(item if type(item) not in (float, int) else numberize(item))
                                    except Exception as error_list_item:
                                        options_list.append(error_list_item)
                                        continue
                                print(f"{key_fight.replace('_', ' ').title()}: {' '.join(options_list)}")
                            else:
                                try:
                                    print(f"{key_fight.replace('_', ' ').title()}: {key_data if type(key_data) not in (float, int) else numberize(key_data)}")
                                except Exception as error_printing_item:
                                    logger.error(f"{key_fight} ERROR: {error_printing_item}")
                                    continue
                    except Exception as error_building_fight_data:
                        await bot.error_msg("display_stats_fight", f"Error Building Fight Data For {name} {key_date} {key_time}", error_building_fight_data)
                    input(f"{long_dashes}\nHit Enter To Go Back")
                    await bot.go_back()

                while True:
                    cls()
                    options = []
                    user_document = await refresh_document_user()
                    print(await top_bar(f"Detailed {key.replace('_', ' ').title()} Times for {key_date.replace('-', '/')} for {name}"))
                    try:
                        for n, time_ in enumerate(user_document['data_games']['fight'][key][name][key_date].keys(), start=1):
                            options.append(f"{n}. {time_}")
                    except Exception as error_building_fight_times:
                        await bot.error_msg("display_fight_stats", f"Error Building Fight Times for {name}", error_building_fight_times)
                    user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                       f"{long_dashes}\n"
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
                    await bot.error_msg("display_stats_fight", "Error Building Detailed Stats", error_building_detailed_stats)
                return user_stats

            while True:
                cls()
                options = []
                user_document = await refresh_document_user()
                user_stats = await refresh_stats()
                print(await top_bar(f"{key.title()} against {name}"))
                try:
                    for stat_name, stat in user_stats.items():
                        print(f"{stat_name.replace('_', ' ').title()}: {numberize(stat)}")
                except Exception as error_printing_detailed_stats:
                    await bot.error_msg("display_stats_fight", "Error Printing Detailed Stats", error_printing_detailed_stats)
                try:
                    for n, date in enumerate(user_document['data_games']['fight'][key][name].keys(), start=1):
                        options.append(f"{n}. {date}")
                except Exception as error_building_fight_dates:
                    await bot.error_msg("display_stats_fight", f"Error Building Fight Dates for {name}", error_building_fight_dates)
                user_input = input(f"{f'{long_dashes}{nl}{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                   f"{long_dashes}\n"
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
            print(await top_bar(f"{key.title()} Fights"))
            for key_, value_ in user_stats[key].items():
                try:
                    print(f"{key_.replace('_', ' ').title()}: {numberize(value_)}")
                except Exception as error_printing_stats:
                    await bot.error_msg("display_stats_fight", f"Error printing {key} user_stats", error_printing_stats)
                    continue
            try:
                for n, chodeling in enumerate(list(sorted(user_document['data_games']['fight'][key].keys(), key=lambda x: x)), start=1):
                    options.append(f"{n}. {chodeling}")
            except Exception as error_building_detailed_options:
                await bot.error_msg("display_stats_fight", "Error Building Detailed Options", error_building_detailed_options)
            user_input = input(f"{f'{long_dashes}{nl}{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{long_dashes}\n"
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
            await bot.error_msg("display_stats_fight", "Error Building user_stats", error_building_user_stats)
            return {}
        return user_stats

    while True:
        cls()
        user_stats = await refresh_stats()
        print(await top_bar("Fight Stats"))
        try:
            print(f"Fights Total: {numberize(user_stats['aggressor']['fights_total'] + user_stats['defender']['fights_total'])}\n"
                  f"Lost Total: {numberize(user_stats['aggressor']['fights_lost'] + user_stats['defender']['fights_lost'])}\n"
                  f"Tied Total: {numberize(user_stats['aggressor']['fights_tied'] + user_stats['defender']['fights_tied'])}\n"
                  f"Wins Total: {numberize(user_stats['aggressor']['fights_won'] + user_stats['defender']['fights_won'])}\n"
                  f"Points Lost: {numberize(user_stats['aggressor']['points_lost'] + user_stats['defender']['points_lost'])}\n"
                  f"Points Won: {numberize(user_stats['aggressor']['points_won'] + user_stats['defender']['points_won'])}")
        except Exception as error_printing_all_stats:
            await bot.error_msg("display_stats_fight", "Error printing all stats", error_printing_all_stats)
        user_input = input(f"{long_dashes}\n"
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
            if sortby == 0:
                for key, value in dict_.items():
                    len_key = len(key)
                    len_value = len(f"{numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})")
                    left_length = len_key if len_key > left_length else left_length
                    right_length = len_value if len_value > right_length else right_length
            else:
                for value in dict_.values():
                    len_value = len(numberize(value[0])) if sortby == 1 else len(f' {numberize(value[1])} {numberize(value[1] / value[0])} ')
                    len_value_right = len(f"Worth {numberize(value[1])} ({f'{numberize(value[1])})' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})") if sortby <= 2 else len(f"{numberize(value[0])} Times ")
                    left_length = len_value if len_value > left_length else left_length
                    right_length = len_value_right if len_value_right > right_length else right_length
            for key, value in dict(sorted(dict_.items(), key=lambda x: x[1 if sortby >= 1 else 0][0 if sortby == 0 else sortby - 1] if sortby <= 2 else x[1][1] / x[1][0])).items():
                if sortby == 0:
                    print(space(f"Worth {numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", right_length, False, space(key, left_length, middle_txt=f'{type_.title()} {value[0]} Times')))
                elif sortby == 1:
                    print(space(f"Worth {numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", right_length, False, space(numberize(value[0]), left_length, middle_txt=key)))
                elif sortby == 2:
                    print(space(f'{numberize(value[0])} Times ', right_length, False, space(f"{numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", left_length, middle_txt=key)))
                else:
                    print(space(f'{numberize(value[0])} Times ', right_length, False, space(f"{numberize(value[1])} ({f'{numberize(value[1])}' if -1 <= value[0] <= 1 else f'{numberize(value[1] / value[0])}'})", left_length, middle_txt=key)))

    async def cutline_stats():
        async def detailed_stats(key_cut: str):
            async def print_details(name: str):
                cls()
                print(await top_bar(f"{name} has {f'made you loose;' if key_cut == 'cut_by' else f'lost;'}"))
                await sort_print_list(user_document['data_games']['fish']['totals']['line'][key_cut][name], "cut")
                input(f"{long_dashes}\nEnter To Return")
                await bot.go_back()

            while True:
                cls()
                user_document = await refresh_document_user()
                if len(user_document['data_games']['fish']['totals']['line'][key_cut]) == 0:
                    print("No one has cut your line yet!" if key_cut == "cut_by" else "You haven't cut anyone's line yet!")
                    input("Hit Enter To Go Back")
                    await bot.go_back()
                    break
                print(await top_bar("Others Who Have Cut Your Line;" if key_cut == "cut_by" else f"Chodelings Who's Lines You've Cut;"))
                options = []
                try:
                    for n, name in enumerate(sorted(user_document['data_games']['fish']['totals']['line'][key_cut].keys(), key=lambda x: x), start=1):
                        options.append(f"{n}. {name}")
                except Exception as error_printing_cutline_options:
                    await bot.error_msg("display_stats_fish", "Error Displaying Cutline Detailed Stats", error_printing_cutline_options)
                user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                   f"{long_dashes}\n"
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
                print(f"Own Line Cut Times: {numberize(user_stats['cut_line']['own_line_times_cut'])}\n"
                      f"Own Line Cut Points {'Lost' if user_stats['cut_line']['own_line_points_lost'] > 0 else 'Saved'}: {numberize(user_stats['cut_line']['own_line_points_lost'] if user_stats['cut_line']['own_line_points_lost'] > 0 else abs(user_stats['cut_line']['own_line_points_lost']))}\n"
                      f"Other Line Cut Times: {numberize(user_stats['cut_line']['other_line_times_cut'])}\n"
                      f"Other Line Cut Points {'Lost' if user_stats['cut_line']['other_line_points_lost'] > 0 else 'Saved'}: {numberize(user_stats['cut_line']['other_line_points_lost'] if user_stats['cut_line']['other_line_points_lost'] > 0 else abs(user_stats['cut_line']['other_line_points_lost']))}")
            except Exception as error_printing_cutline_stats:
                await bot.error_msg("display_stats_fish", "Printing CutLine Stats", error_printing_cutline_stats)
            user_input = input(f"{long_dashes}\n"
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
                print(f"{f'Remaining Casts: {numberize(auto_current_remaining)}/{auto_cast_limit}{nl}' if key_type == 'auto' else ''}"
                      f"Total Casts: {numberize(user_stats[key_type]['total_casts'])}\n"
                      f"{f'Total Cost: {auto_total_cost}{nl}' if key_type == 'auto' else ''}"
                      f"Total Gained: {numberize(user_stats[key_type]['total_points_gain'])}\n"
                      f"Total Lost: {numberize(user_stats[key_type]['total_points_lost'])}\n"
                      f"Unique Catches: {len(user_stats[key_type]['total_unique_dict']):,}/{user_stats['total_items']:,}")
            except Exception as error_detailed_stats:
                await bot.error_msg("display_stats_fish", f"Error Displaying user_stats for {key_type}", error_detailed_stats)
            user_input = input(f"{long_dashes}\n"
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
                        input(f"{long_dashes}\nHit Enter To Go Back")
                    except Exception as error_printing_auto_catches:
                        await bot.error_msg("display_stats_fish", f"Error Printing {key_type} Catches", error_printing_auto_catches)
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
                for key, value in channel_document['data_games']['fish']['upgrades'][key_type][str(user_stats['levels'][key_type])].items():
                    print(f"{key.replace('_', ' ').title()}: {value if key != 'cost' else numberize(value)}")
            except Exception as error_printing_detailed_stats:
                await bot.error_msg("display_stats_fish", f"Printing Detailed {key_type} Stats", error_printing_detailed_stats)
            input(f"{long_dashes}\n"
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
                      f"Rod: {user_stats['levels']['rod']} ({channel_document['data_games']['fish']['upgrades']['rod'][str(user_stats['levels']['rod'])]['name']})")
            except Exception as error_printing_fishing_levels:
                await bot.error_msg("display_stats_fishing", "Printing Fishing Levels", error_printing_fishing_levels)
            user_input = input(f"{long_dashes}\n"
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
                        "current_remaining_casts": user_document['data_games']['fish']['auto']['cast'],
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
                await bot.error_msg("display_stats_fish", "Error Building Return Dictionary", error_building_dict_return)
                return {}

            return dict_return
        except Exception as error_building_stats:
            await bot.error_msg("display_stats_fish", "Error Building Stats", error_building_stats)
            return {}

    def space(item: str, line_length: int, left: bool = True, left_item: str = "", middle_txt: str = ""):
        if left:
            # return f"{item}{' ' * (line_length + 2 - len(item))} | {middle_txt}"
            return f"{item}{' ' * (line_length - len(item))} | {middle_txt}"
        else:
            # return f"{' ' * (len(long_dashes) - (line_length + 2 - len(item) - len(item)))}{item}"
            return f"{left_item}{' ' * (len(long_dashes) - (len(left_item) + len(str(item))))}{item}"

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
            await bot.error_msg("display_stats_gamble", "Error Building user_stats", error_building_user_stats)
            return {}
        return user_stats

    while True:
        cls()
        user_stats = await refresh_stats()
        print(await top_bar("Gamble Stats"))
        for key, value in user_stats.items():
            for key_, value_ in value.items():
                try:
                    if key == "total":
                        print(f"{key.title()} {key_.replace('_', ' ').title()}: {value_}")
                    else:
                        print(f"{key_.replace('_', ' ').title()} {key.title()}: {value_}%")
                except Exception as error_printing_user_stats:
                    await bot.error_msg("display_stats_gamble", "Error Printing user_stats", error_printing_user_stats)
                    continue
        user_input = input(f"{long_dashes}\n"
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


async def fetch_setting(setting: str) -> int | tuple:
    if setting == "sortby":
        try:
            return bot.settings['types_sort'].index(read_file(bot.data_settings['types_sort'], str))
        except ValueError:
            await bot.error_msg("fetch_setting", f"{read_file(bot.data_settings['types_sort'], str)}' is not valid!! (Returning Index 0)", ValueError)
            return 0
    elif setting == "flash":
        try:
            flash_frequency, flash_speed = read_file(bot.data_settings['flash'], str).split(', ', maxsplit=1)
            return int(flash_frequency), float(flash_speed)
        except Exception as error_returning_flash:
            await bot.error_msg("fetch_setting", "Returning flash Settings (Default '4, 0.5' Returned)", error_returning_flash)
            return 4, 0.5
    elif setting == "heist":
        try:
            return bot.settings['types_heist'].index(read_file(bot.data_settings['types_heist'], str)) + 1
        except Exception as error_returning_heist:
            await bot.error_msg("fetch_setting", "heist_setting", error_returning_heist)
            return 0
    else:
        await bot.error_msg("fetch_setting", "Invalid Entry (Returning Index 0)", f"{setting} is not a valid setting!!!")
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
    return str(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'))


def fortime_long(time):
    try:
        return str(time.strftime("%y:%m:%d:%H:%M:%S"))[1:]
    except Exception as e:
        logger.error(f"Error creating formatted_long_time -- {e}")
        return None


async def get_long_sec(time):
    try:
        y, mo, d, h, mi, s = time.split(":")
        return int(y) * 31536000 + int(mo) * 2628288 + int(d) * 86400 + int(h) * 3600 + int(mi) * 60 + int(s)
    except Exception as e:
        logger.error(f"Error creating long_second -- {e}")
        return None


async def log_shutdown(logger_list: list):
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{directories['logs']}{entry}", f"{directories['logs_archive']}{entry}")
            print(f"{entry} moved to archives..")
        except Exception as e:
            print(e)
            pass


async def on_message(msg: ChatMessage):
    try:
        if msg.text.startswith(("$", "!", "¡")):
            return
        msg.text = msg.text.lower()
        if msg.user.id != bot.login_details['target_id']:
            if f"@{user.display_name.lower()}" in msg.text:
                await flash_window("attn")
        else:
            if msg.text.startswith(user.display_name.lower()) and "autocast expired" in msg.text:
                await flash_window("auto_cast_expired")
    except Exception as error_on_message:
        await bot.error_msg("on_message", "Generic Error", error_on_message)
        return


async def on_ready(event: EventData):
    try:
        await event.chat.join_room(bot.login_details['target_name'])
        logger.info(f"{fortime()}: Connected to {bot.login_details['target_name']} channel\n{long_dashes}")
    except Exception as e:
        await bot.error_msg("on_ready", f"Failed to connect to {bot.login_details['target_name']} channel", e)


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


def read_file(file_name: str, return_type: type(bool) | type(float) | type(int) | type(list) | type(str)) -> bool | float | int | list | str:
    with open(file_name, "r", encoding="utf-8") as file:
        variable = file.read()
    try:
        if return_type == bool:
            if variable == "True":
                return True
            elif variable == "False":
                return False
            else:
                return f"ValueError Converting {variable} to {return_type}"
        elif type(return_type) == list:
            if return_type[1] == "split":
                variable = variable.split(return_type[2], maxsplit=return_type[3])
            elif return_type[1] == "splitlines":
                variable = variable.splitlines()
            if return_type[0] == map:
                return list(map(str, variable))
            else:
                return list(variable)
        elif return_type in (int, float):
            variable = float(variable)
            if return_type == float:
                return variable
            return int(variable)
        else:
            return str(variable)
    except ValueError:
        return f"ValueError Converting {variable} (type; {type(variable)}) to {return_type}"
    except Exception as e:
        error_msg = f"{fortime()}: Error in 'read_file' -- Generic Error -- {e}"
        logger.error(error_msg)
        return error_msg


async def refresh_document_channel() -> Document | None:
    try:
        channel_collection = mongo_db.twitch.get_collection("channels")
        return channel_collection.find_one({"_id": bot.login_details['target_id']})
    except FileNotFoundError:
        await bot.error_msg("refresh_document_channel", "FileNotFound", FileNotFoundError)
        return None
    except Exception as e:
        await bot.error_msg("refresh_document_channel", "Generic", e)
        return None


async def refresh_document_user(target_user: int | str = None) -> Document | None:
    try:
        users_collection = mongo_db.twitch.get_collection('users')
        if target_user is None:
            return users_collection.find_one({"_id": user.id})
        elif type(target_user) == int:
            return users_collection.find_one({"_id": target_user})
        elif type(target_user) == str:
            return users_collection.find_one({"name": target_user})
        else:
            await bot.error_msg("refresh_document_user", "INTERNAL ERROR (INVALID 'target_user' TYPE)", f"EXPECTED TYPES: int | str -- GOT {type(target_user)}")
            return None
    except FileNotFoundError:
        await bot.error_msg("refresh_document_user", "FileNotFound", FileNotFoundError)
        return None
    except Exception as e:
        await bot.error_msg("refresh_document_user", "Generic", e)
        return None


def remove_period_area(var: str) -> str:
    try:
        index = var.index('.')
        return var[index+2:]
    except ValueError:
        return var


async def send_chat_msg(msg: str):
    try:
        await bot.send_chat_message(bot.login_details['target_id'], user.id, msg)
    except TwitchBackendException:
        try:
            await asyncio.sleep(3)
            await bot.send_chat_message(bot.login_details['target_id'], user.id, msg)
            logger.info(f"{fortime()}: TwitchBackendException Handled OK")
        except Exception as error_twitch_backend:
            await bot.error_msg("send_chat_msg", "TwitchBackendException Handled FAIL", error_twitch_backend)
            return False
    except Exception as general_error:
        await bot.error_msg("send_chat_msg", "Generic Error", general_error)
        return False
    return True


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
        formatted_time = fortime()
        print(f"{formatted_time}: ERROR in setup_logger - {name}/{log_file}/{level} -- {e}")
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
    async def msg_success():
        print(f"Message Sent To Chat Successfully")
        await asyncio.sleep(2)

    async def msg_fail(reason: str, error: bool = False):
        print_msg = f"Message Send Failed\n{reason}"
        if error:
            await bot.error_msg("special_command", "msg_fail", print_msg)
        else:
            print(print_msg)
            await asyncio.sleep(3)

    status, reason = False, ""
    try:
        if key_stroke == bot.special_commands['bet']:
            now_time = datetime.datetime.now()
            user_document = await refresh_document_user()
            if user_document['data_games']['gamble']['last'] is None:
                pass
            elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(user_document['data_games']['gamble']['last'])) < 600:
                wait_time = 600 - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(user_document['data_games']['gamble']['last'])))
                reason = f"Gotta Wait {str(datetime.timedelta(seconds=wait_time)).title()}"
            if reason == "":
                status = await send_chat_msg("!bet")
        elif key_stroke == bot.special_commands['bbet']:
            status = await send_chat_msg("!bet doubleb")
        elif key_stroke == bot.special_commands['fish']:
            user_document = await refresh_document_user()
            channel_document = await refresh_document_channel()
            cast_difference = channel_document['data_games']['fish']['upgrades']['rod'][str(user_document['data_games']['fish']['upgrade']['rod'])]['autocast_limit'] - user_document['data_games']['fish']['auto']['cast']
            if cast_difference > 0:
                status = await send_chat_msg(f"!fish {cast_difference if user.id != bot.special_users['bingo']['Free2Escape'] else '6969'}")
            else:
                reason = "Already At Maximum Auto Casts!!"
        elif key_stroke == bot.special_commands['fish_beet']:
            status = await send_chat_msg("!fish beet rod")
        elif key_stroke == bot.special_commands['fish_stroke']:
            status = await send_chat_msg("!fish stroke rod")
        elif key_stroke == bot.special_commands['heist']:
            now_time = datetime.datetime.now()
            user_document = await refresh_document_user()
            if user_document['data_games']['heist']['gamble']['last'] is None:
                pass
            elif await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(user_document['data_games']['heist']['gamble']['last'])) < 21600:
                wait_time = 21600 - (await get_long_sec(fortime_long(now_time)) - await get_long_sec(fortime_long(user_document['data_games']['heist']['gamble']['last'])))
                reason = f"Gotta Wait {str(datetime.timedelta(seconds=wait_time)).title()}"
            if reason == "":
                status = await send_chat_msg(f"!heist {await fetch_setting('heist')}")
        elif key_stroke == bot.special_commands['joints_count_update']:
            if await bot.check_permissions(user.id, "mod"):
                status = await send_chat_msg(f"!jointscount update 1")
            else:
                reason = f"You can't do that!"
        # ToDo; Figure this shit out
        # elif key_stroke == bot.special_commands['quit']:
        #     pass
        else:
            reason = f"{key_stroke} NOT VALID"
        if status:
            await msg_success()
        else:
            await msg_fail(reason)
    except Exception as update_number_error:
        await msg_fail(f"{fortime()}: Error in 'special_command' -- key_stroke; {key_stroke} -- Generic Error\n{update_number_error}", error=True)


async def top_bar(left_side: str) -> str:
    try:
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        level_check = user_document['data_user']['rank']['level'] + 1
        xp_perc = int(user_document['data_user']['rank']['xp'] / ((150 * float((level_check / 2) * level_check)) * level_check) * 100)
        xp_boost = math.ceil(user_document['data_user']['rank']['boost'] / ((150 * float((level_check / 2) * level_check)) * level_check) * 100)
        dashes = f"{colour('purple', '-' * (xp_perc - xp_boost))}{colour('blue', '-' * xp_boost)}{'-' * (len(long_dashes) - xp_perc)}"
        always_show = bot.settings['types_always_display'][bot.settings['types_always_display'].index(read_file(bot.data_settings['types_always_display'], str))]
        if always_show == bot.settings['types_always_display'][0]:
            right_side = f"{numberize(user_document['data_games']['fish']['auto']['cast'])}/{channel_document['data_games']['fish']['upgrades']['rod'][str(user_document['data_games']['fish']['upgrade']['rod'])]['autocast_limit']}"
        elif always_show == bot.settings['types_always_display'][1]:
            right_side = f"{user_document['data_user']['rank']['level']:,}"
        elif always_show == bot.settings['types_always_display'][2]:
            right_side = numberize(user_document['data_user']['rank']['points'])
        elif always_show == bot.settings['types_always_display'][3]:
            right_side = numberize(user_document['data_user']['rank']['xp'])
        else:
            return f"{left_side}\n{dashes}"
        return f"{left_side}{' ' * (len(long_dashes) - (len(left_side) + len(str(right_side))))}{right_side}\n{dashes}"
    except Exception as error_creating_top_bar:
        await bot.error_msg("top_bar", "Generic Error", error_creating_top_bar)
        return left_side


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
        logger.info(f"{long_dashes}\nShutdown Sequence Completed\n{long_dashes}")

    chat = await Chat(bot)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.start()

    await asyncio.sleep(2.5)
    while True:
        cls()
        try:
            user_input = input(f"{await top_bar('Main Menu')}\n"
                               "Enter 1 To View Profile\n"
                               "Enter 2 To View Commands\n"
                               "Enter 3 To View Leaderboards\n"
                               # "Enter 8 To Enter Profile Settings\n"
                               "Enter 9 To Change App Settings\n"
                               "Enter 0 To Shutdown Bot\n")
            if user_input.isdigit():
                user_input = int(user_input)
                if user_input == 0:
                    await shutdown()
                    break
                elif user_input == 1:
                    await chodeling_stats()
                elif user_input == 2:
                    await chodeling_commands()
                elif user_input == 3:
                    print("Not programmed yet")
                    await asyncio.sleep(3)
                elif user_input == 9:
                    await app_settings()
                else:
                    await bot.invalid_entry(int)
            elif user_input in bot.special_commands.values():
                await special_command(user_input)
            else:
                await bot.invalid_entry(str)
        except KeyboardInterrupt:
            print("EXITING")
            await shutdown()
            break
        except Exception as e:
            await bot.error_msg("run", "Generic Error", e)
            await asyncio.sleep(10)
            await shutdown()
            break


async def auth_bot() -> UserAuthenticationStorageHelper:
    twitch_helper = UserAuthenticationStorageHelper(bot, bot.target_scopes)
    await twitch_helper.bind()
    logger.info(f"{fortime()}: Bot Authenticated Successfully!!\n{long_dashes}")
    return twitch_helper


async def get_auth_user_id() -> TwitchUser | None:
    user = None
    user_info = bot.get_users()
    try:
        async for entry in user_info:
            if type(entry) == TwitchUser:
                user = entry
            else:
                await bot.error_msg("get_auth_user_id", "Generic Error", "NO USER FOUND IN 'user_info'")
    except Exception as e:
        await bot.error_msg("get_auth_user_id", "Generic Error", e)
        return None
    return user


def data_check():
    def write_new_file(filename: str, var_write: str):
        with open(filename, "w") as file:
            file.write(var_write)
        logger.info(f"{fortime()}: '{filename}'\nFile NOT FOUND, CREATED!")
        time.sleep(5)

    for setting, path in bot.data_settings.items():
        if not os.path.exists(path):
            if setting == "flash":
                write_new_file(path, f"4, 0.5")
            else:
                write_new_file(path, str(bot.settings[setting][0]))


def hotkey_listen():
    try:
        keyboard.add_hotkey("ctrl+shift+b", lambda: keyboard.write(f"\x1b{bot.special_commands['bet']}\r"))
        keyboard.add_hotkey("ctrl+shift+d+b", lambda: keyboard.write(f"\x1b{bot.special_commands['bbet']}\r"))
        keyboard.add_hotkey("ctrl+shift+f", lambda: keyboard.write(f"\x1b{bot.special_commands['fish']}\r"))
        keyboard.add_hotkey("ctrl+shift+h", lambda: keyboard.write(f"\x1b{bot.special_commands['heist']}\r"))
        keyboard.add_hotkey("ctrl+shift+j", lambda: keyboard.write(f"\x1b{bot.special_commands['joints_count_update']}\r"))
        # keyboard.add_hotkey("ctrl+shift+q", lambda: keyboard.write(f"\x1b{bot.special_commands['quit']}\r"))
        keyboard.add_hotkey("ctrl+shift+r+b", lambda: keyboard.write(f"\x1b{bot.special_commands['fish_beet']}\r"))
        keyboard.add_hotkey("ctrl+shift+r+s", lambda: keyboard.write(f"\x1b{bot.special_commands['fish_stroke']}\r"))
        keyboard.wait()
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'hotkey_listen' -- {e}")


if __name__ == "__main__":
    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger("logger", f"main_log--{init_time}.log", logger_list)
    # logger_track = setup_logger("logger_track", f"track_log--{init_time}.log", logger_list)
    if None in logger_list:
        print(f"One of thee loggers isn't setup right\n{logger}\nQuitting program")
        time.sleep(5)
    else:
        bot = BotSetup(bot_id, bot_secret)
        data_check()
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
                    mongo_db = connect_mongo("twitch", DEFAULT_CONNECTION_NAME)
                    time.sleep(1)
                    if mongo_db is None:
                        logger.error(f"{fortime()}: Error connecting to DB!! Exiting App")
                        time.sleep(2)
                        break
                    twitch_helper = asyncio.run(auth_bot())
                    user = asyncio.run(get_auth_user_id())
                    if user is not None:
                        keyboard_thread = threading.Thread(target=hotkey_listen, daemon=True)
                        keyboard_thread.start()
                        asyncio.run(run())
                    break
                else:
                    asyncio.run(bot.invalid_entry(int))
            else:
                asyncio.run(bot.invalid_entry(str))

    asyncio.run(log_shutdown(logger_list))
