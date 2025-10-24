import os
import sys
import time
import asyncio
import logging
import datetime
from colorama import Fore, Style
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv
from mongoengine import connect, disconnect_all, DEFAULT_CONNECTION_NAME, Document
from twitchAPI.twitch import Twitch, TwitchUser
from twitchAPI.type import AuthScope, ChatEvent, TwitchBackendException
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.chat import Chat, EventData, ChatCommand  #, ChatMessage, ChatSub

# ToDo; Add 'upsidedown text to everything' easter egg
# ToDo; Add stats for time added (also rework chodebot & user documents to keep track & write script to scrape past logs to build data)
# ToDo; Add "^F"(CTRL+F) then enter to top up auto-cast to limit from anywhere in the app

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

nl = "\n"
logger_list = []
long_dashes = "-------------------------------------------------------------------"


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch
        self.settings = {
            "types_always_display": (
                "auto_cast_remaining",
                "level",
                "points",
                "points_xp",
            ),
            "types_sort": (
                "alphabetic",
                "quantity",
                "value"
            )
        }
        self.target_scopes = [
            AuthScope.CHAT_READ,
            AuthScope.CHAT_EDIT,
            AuthScope.USER_BOT,
            AuthScope.USER_WRITE_CHAT
        ]
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
            "db_string": "DB_LOGIN_STRING",
            "target_id": "268136120",
            "target_name": "TheeChody"
        }
        self.data_settings = {
            "types_always_display": f"{directories['data']}types_always_display.txt",
            "types_sort": f"{directories['data']}types_sort.txt"
        }
        self.special_users = {
            "bingo": {
                "carnage_deamon": "659640208",
                "Free2Escape": "777768639"
            }
        }

    @staticmethod
    async def invalid_entry(invalid_type: type(str) | type(int)):
        print(f"Invalid{' Number' if invalid_type == int else ''} entry, try again")
        await asyncio.sleep(2)

    @staticmethod
    async def go_back(main_menu: bool = False):
        print('Returning to Main Menu' if main_menu else 'Going Back')
        await asyncio.sleep(2)

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
            logger.error(f"{fortime()}: Error in bot_check_perm\n{error_permission_check}")
            await asyncio.sleep(3)
            return False

    @staticmethod
    async def msg_no_perm():
        input("Required Permissions Not Satisfied!!\n"
              "Hit Enter to go back")
        await bot.go_back()


async def app_settings():
    while True:
        async def set_setting(setting_key: str):
            async def check_var(key_check: str, var_check: str) -> bool:
                if read_file(bot.data_settings[key_check], str) == var_check.lower():
                    print(f"Your sort type is already set to {var_check.replace('_', ' ').title()}")
                    await bot.go_back()
                    return True
                return False

            async def write_var(key_write: str, var_write: str):
                with open(bot.data_settings[key_write], "w") as file:
                    file.write(var_write.lower())
                print(f"Default Sorting Variable set to: {var_write.replace('_', ' ').title()}")
                await bot.go_back()

            while True:
                cls()
                options = []
                # print(f"Default {setting_key.replace('_', ' ').title()} Setting\n{long_dashes}")
                setting = setting_key.replace('_', ' ').title()
                print(await top_bar(f"Default {setting} Setting"))
                try:
                    for n, var in enumerate(bot.settings[setting_key]):
                        options.append(f"{n + 1}. {var.title()}")
                except Exception as error_printing_display_variables:
                    logger.error(f"{fortime()}: Error in 'run' -- Error printing Options-{setting_key.replace('_', ' ').title()} -- {error_printing_display_variables}")
                    await asyncio.sleep(3)
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
                elif user_input.lower() in check_numbered_list(options):
                    if not await check_var(setting_key, bot.settings[setting_key][bot.settings[setting_key].index(user_input.lower())]):
                        await write_var(setting_key, bot.settings[setting_key][bot.settings[setting_key].index(user_input.lower())])
                        break
                else:
                    await bot.invalid_entry(str)

        cls()
        print(await top_bar("App Settings"))
        user_input = input("Enter 1 To Change Default Display Variable\n"
                           "Enter 2 To Change Default Sorting Variable\n"
                           "Enter 3 To Change Flash Settings\n"
                           "Enter 0 To Return To Main Menu\n")
        if not user_input.isdigit():
            await bot.invalid_entry(str)
        else:
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back(True)
                break
            elif user_input == 1:
                await set_setting("types_always_display")
            elif user_input == 2:
                await set_setting("types_sort")
            elif user_input == 3:
                print("Not Programmed Yet")
                await asyncio.sleep(3)
            else:
                await bot.invalid_entry(int)


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
                for n, cmd in enumerate(sorted(bot.commands_available[command_key], key=lambda x: x)):
                    options.append(f"{n+1}. {cmd}")
            except Exception as error_printing_command:
                logger.error(f"{fortime()}: Error in 'chodeling_commands' -- show_command '{command_key}' -- {error_printing_command}")
                await asyncio.sleep(3)
            user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{long_dashes}\n"
                               f"Enter # or Command Name To View\n"
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
            for n, key in enumerate(sorted(bot.commands_available.keys(), key=lambda x: x)):
                options.append(f"{n+1}. {key}")
        except Exception as error_fetching_commands:
            logger.error(f"{fortime()}: Error in 'chodeling_commands' -- fetching specific commands -- {error_fetching_commands}")
            await asyncio.sleep(5)
        user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                           f"{long_dashes}\n"
                           f"Enter # or Command Name of command to view\n"
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
            logger.error(f"{fortime()}: Error in 'chodeling_stats' -- Error printing chodeling stats -- {error_printing_chodeling_stats}")
            await asyncio.sleep(3)
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
        elif not user_input.isdigit():
            await bot.invalid_entry(str)
        else:
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
                print("Not Programmed Yet")
                await asyncio.sleep(3)
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


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def colour(colour_: str, str_: str) -> str:
    if colour_ == "cyan":
        colour_ = Fore.CYAN
    elif colour_ == "green":
        colour_ = Fore.GREEN
    elif colour_ == "red":
        colour_ = Fore.RED
    else:
        colour_ = Fore.RESET
    return f"{colour_}{str_}{Fore.RESET}"


def connect_mongo(db, alias):
    try:
        client = connect(db=db, host=bot.login_details['db_string'], alias=alias)
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
    async def build_board(game_board: dict, item_list: list, minor_pattern: str) -> dict:  #, game_size: str):
        chodeling_board = {}
        try:
            for row, items in game_board.items():
                chodeling_board[row] = {}
                for item, status in items.items():
                    minor_pattern_hit = False
                    if status:
                        spaces_check = channel_document['data_games']['bingo']['patterns']['minor'][minor_pattern][str(len(game_board))]
                        # spaces_check = channel_document['data_games']['bingo']['patterns']['minor'][minor_pattern][game_size]
                        for key, value in spaces_check.items():
                            if minor_pattern_hit:
                                break
                            for n, (key_board, value_board) in enumerate(game_board[key].items()):
                                if value_board and n in value and item == key_board:
                                    minor_pattern_hit = True
                                    break
                    index = index_bingo(item, item_list) + 1
                    chodeling_board[row][index] = f"{style('bright' if minor_pattern_hit or status else 'normal', colour('cyan' if minor_pattern_hit else 'green' if status else 'red', str(index)))}"
        except Exception as error_building_board:
            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Building Board\n{error_building_board}")
            await asyncio.sleep(3)
        return chodeling_board

    async def check_bingo_game_status() -> bool:
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        if None in (user_document['data_games']['bingo']['current_game']['game_type'], channel_document['data_games']['bingo']['current_game']['game_type']):
            cmd = "'!bingo join'"
            game_type = channel_document['data_games']['bingo']['current_game']['game_type']
            if game_type is not None:
                game_type = game_type.replace('_', ' ').title()
            input(f"{'Bingo Game Has Ended' if game_type is None else f'There is a {game_type} running{nl}Use {cmd} to join'}\n"
                  "Hit Enter To Go Back")
            await bot.go_back()
            return False
        return True

    def index_bingo(item: str, item_list: list) -> int:
        return item_list.index(item)

    async def print_board(chodeling_board: dict):
        try:
            print(f"{long_dashes}\n"
                  f"Your Bingo Board\n"
                  f"{long_dashes}")
            dashes = '-' * ((5 * len(chodeling_board)) + (len(chodeling_board) + 1))
            print(dashes)
            for n, (row, items) in enumerate(chodeling_board.items()):
                print(f"{print_row(items)}\n{dashes}")
        except Exception as error_printing_board:
            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Printing Board\n{error_printing_board}")
            await asyncio.sleep(3)

    async def print_items(items_print: dict):
        try:
            for n, (item, status) in enumerate(items_print.items()):
                print(f"{style('bright' if status else 'normal', colour('green' if status else 'red', f'{n+1}. {item}'))}")
        except Exception as error_printing_list:
            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Printing Available List\n{error_printing_list}")
            await asyncio.sleep(3)

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
        try:
            user_stats = {
                "game_types": {},
                "total_games": 0,
                "total_major_bingo": 0,
                "total_minor_bingo": 0,
                "total_points_won": 0
            }
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
            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Error refreshing user_stats\n{error_refreshing_stats}")
            await asyncio.sleep(3)
            return {}
        return user_stats

    while True:
        cls()
        options = []
        game_options = False
        user_document = await refresh_document_user()
        channel_document = await refresh_document_channel()
        print(await top_bar("Bingo Options"))
        if None not in (user_document['data_games']['bingo']['current_game']['game_type'], channel_document['data_games']['bingo']['current_game']['game_type']):
            game_options = True
        try:
            if game_options:
                options = ["Enter 1 To View Game Info", "Enter 2 To View Your Board"]
            options.append("Enter 3 To View History")
        except Exception as error_building_options:
            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Error building options\n{error_building_options}")
            await asyncio.sleep(3)
        user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                           "Enter 0 To Go Back\n")
        if not user_input.isdigit():
            await bot.invalid_entry(str)
        else:
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input == 1:
                while True:
                    cls()
                    if not await check_bingo_game_status():
                        break
                    channel_document = await refresh_document_channel()
                    print(await top_bar("Current Game Info"))
                    try:
                        print(f"Board Size: {channel_document['data_games']['bingo']['current_game']['board_size']}x{channel_document['data_games']['bingo']['current_game']['board_size']}\n"
                              f"Game Type: {channel_document['data_games']['bingo']['current_game']['game_type'].replace('_', ' ').title()}\n"
                              f"Major Jackpot: {numberize(channel_document['data_games']['bingo']['current_game']['major_bingo_pot'])}\n"
                              f"Major Pattern: {channel_document['data_games']['bingo']['current_game']['chosen_pattern'][0].replace('_', ' ').title()}\n"
                              f"Minor Pattern: {channel_document['data_games']['bingo']['current_game']['chosen_pattern'][1].replace('_', ' ').title()}")
                    except Exception as error_printing_bingo_game_info:
                        logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Printing Bingo Game Info\n{error_printing_bingo_game_info}")
                        await asyncio.sleep(3)
                    user_input = input(f"{long_dashes}\n"
                                       f"Enter 0 To Go Back\n"
                                       f"Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif not user_input.isdigit():
                        await bot.invalid_entry(str)
                    else:
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        else:
                            await bot.invalid_entry(int)
            elif user_input == 2:
                async def call_action(action_to_call: str):
                    sleep_time = 5
                    action = f"!bingo action {action_to_call.title()}"
                    try:
                        await bot.send_chat_message(bot.login_details['target_id'], user.id, action)
                        print(f"Called {action_to_call.title()}")
                        await asyncio.sleep(sleep_time)
                    except TwitchBackendException:
                        try:
                            await asyncio.sleep(2)
                            await bot.send_chat_message(bot.login_details['target_id'], user.id, action)
                            logger.info(f"{fortime()}: TwitchBackendError Handled OK")
                            await asyncio.sleep(sleep_time)
                        except Exception as error_twitch_exception_attempt:
                            logger.error(f"{fortime()}: TwitchBackendError Handled FAIL\n{error_twitch_exception_attempt}")
                            await asyncio.sleep(3)
                    except Exception as error_call_action:
                        logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Call Action '{action_to_call}' -- {action}\n{error_call_action}")
                        await asyncio.sleep(3)

                while True:
                    cls()
                    if not await check_bingo_game_status():
                        break
                    user_document = await refresh_document_user()
                    channel_document = await refresh_document_channel()
                    bingo_perm = await bot.check_permissions(user.id, "mini_game_bingo")
                    print(await top_bar(f"{channel_document['data_games']['bingo']['current_game']['game_type'].title()} Items Available"))
                    await print_items(channel_document['data_games']['bingo']['current_game']['items'])
                    chodeling_board = await build_board(user_document['data_games']['bingo']['current_game']['game_board'], list(channel_document['data_games']['bingo']['current_game']['items'].keys()), channel_document['data_games']['bingo']['current_game']['chosen_pattern'][1])  #, str(channel_document['data_games']['bingo']['current_game']['board_size']))
                    if len(chodeling_board) > 0:
                        await print_board(chodeling_board)
                    user_input = input(f"\n{long_dashes}\n"
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
                            print(f"Total Games: {numberize(user_stats['total_games'])}\n"
                                  f"Total Major Bingo's: {numberize(user_stats['total_major_bingo'])}{f'({numberize(points_won)})' if user_stats['total_major_bingo'] > 0 else ''}\n"
                                  f"Total Minor Bingo's: {numberize(user_stats['total_minor_bingo'])}")
                            if len(user_stats['game_types']) > 0:
                                for game_type, times in user_stats['game_types'].items():
                                    print(f"{game_type.replace('_', ' ').title()} Games Played: {numberize(times)}")
                        except Exception as error_printing_user_stats:
                            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Error printing user_stats\n{error_printing_user_stats}")
                            await asyncio.sleep(3)
                    user_input = input(f"{long_dashes}\n"
                                       f"Enter 1 To View Individual Games\n"
                                       f"Enter 0 To Go Back\n"
                                       f"Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif not user_input.isdigit():
                        await bot.invalid_entry(str)
                    else:
                        user_input = int(user_input)
                        if user_input == 0:
                            await bot.go_back()
                            break
                        elif user_input == 1:
                            while True:
                                async def show_date(key_date: str):
                                    async def show_game(key_time: str):
                                        cls()
                                        channel_dict = channel_document['data_games']['bingo']['history'][key_date][user_document['data_games']['bingo']['history'][key_date][key_time]['game_started'].strftime('%I:%M%p').removeprefix('0').lower()]
                                        date_start_formatted = channel_dict['game_started_time'].strftime("%y/%m/%d")
                                        time_start_formatted = channel_dict['game_started_time'].strftime('%I:%M%p').removeprefix('0').lower()
                                        date_end_formatted = channel_dict['game_ended_time'].strftime("%y/%m/%d")
                                        time_end_formatted = channel_dict['game_ended_time'].strftime('%I:%M%p').removeprefix('0').lower()
                                        points_won = user_document['data_games']['bingo']['history'][key_date][key_time]['points_won']
                                        print(await top_bar(f"{date_start_formatted} {time_start_formatted} - {f'{date_end_formatted} ' if date_end_formatted != date_start_formatted else ''}{time_end_formatted}"))
                                        print(f"Game Type: {user_document['data_games']['bingo']['history'][key_date][key_time]['game_type'].replace('_', ' ').title()}\n"
                                              f"Major Bingo: {user_document['data_games']['bingo']['history'][key_date][key_time]['major_bingo']}{f'({numberize(points_won)})' if user_document['data_games']['bingo']['history'][key_date][key_time]['major_bingo'] else ''}\n"
                                              f"Minor Bingo: {user_document['data_games']['bingo']['history'][key_date][key_time]['minor_bingo']}\n"
                                              f"{long_dashes}")
                                        await print_items(channel_dict['items'])
                                        chodeling_board = await build_board(user_document['data_games']['bingo']['history'][key_date][key_time]['game_board'], list(channel_dict['items'].keys()), channel_dict['chosen_pattern'][1])  #, str(channel_dict['board_size']))
                                        if len(chodeling_board) > 0:
                                            await print_board(chodeling_board)
                                        input(f"{long_dashes}\n"
                                              f"Hit Enter To Go Back\n")

                                    while True:
                                        cls()
                                        options = []
                                        user_document = await refresh_document_user()
                                        print(await top_bar(f"{key_date} Games"))
                                        try:
                                            for n, key_time in enumerate(user_document['data_games']['bingo']['history'][key_date].keys()):
                                                options.append(f"{n+1}. {key_time}")
                                        except Exception as error_building_bingo_date:
                                            logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Error building times for {key_date}\n{error_building_bingo_date}")
                                            await asyncio.sleep(3)
                                        if len(options) > 0:
                                            print(nl.join(options))
                                        user_input = input(f"{long_dashes}\n"
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
                                    for n, date in enumerate(user_document['data_games']['bingo']['history'].keys()):
                                        options.append(f"{n+1}. {date}")
                                except Exception as error_building_bingo_games:
                                    logger.error(f"{fortime()}: Error in 'display_stats_bingo' -- Error building bingo games\n{error_building_bingo_games}")
                                    await asyncio.sleep(3)
                                if len(options) > 0:
                                    print(nl.join(options))
                                user_input = input(f"{long_dashes}\n"
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
                                        await show_date(remove_period_area(options[user_input - 1]))
                                    else:
                                        await bot.invalid_entry(int)
                                elif user_input.lower() in check_numbered_list(options):
                                    await show_date(user_input.lower())
                                else:
                                    await bot.invalid_entry(str)
                        else:
                            await bot.invalid_entry(int)
            else:
                await bot.invalid_entry(int)


async def display_stats_fight():
    async def detailed_options(key: str):
        async def detailed_stats(name: str):
            while True:
                cls()
                stats = {
                    'fights_total': 0,
                    'fights_won': 0,
                    'fights_lost': 0,
                    'fights_tied': 0,
                    'points_lost': 0,
                    'points_won': 0
                }
                user_document = await refresh_document_user()
                print(await top_bar(f"{key.title()} against {name}"))
                try:
                    for dates, times in user_document['data_games']['fight'][key][name].items():
                        for game_time, game_data in times.items():
                            stats['fights_total'] += 1
                            if game_data['won'] == "tied":
                                stats['fights_tied'] += 1
                            elif game_data['won']:
                                stats['fights_won'] += 1
                                stats['points_won'] += game_data['points_gained']
                            else:
                                stats['fights_lost'] += 1
                                stats['points_lost'] += game_data['points_lost']
                except Exception as error_building_detailed_stats:
                    logger.error(f"{fortime()}: Error in 'display_stats_fight' -- Error building detailed stats\n{error_building_detailed_stats}\n{long_dashes}")
                    await asyncio.sleep(3)
                try:
                    for name, stat in stats.items():
                        print(f"{name.replace('_', ' ').title()}: {numberize(stat)}")
                except Exception as error_printing_detailed_stats:
                    logger.error(f"{fortime()}: Error in 'display_stats_fight' -- Error printing detailed stats\n{error_printing_detailed_stats}\n{long_dashes}")
                    await asyncio.sleep(3)
                user_input = input(f"{long_dashes}\n"
                                   f"Enter 1 To View Detailed Fights\n"
                                   f"Enter 0 To Go Back\n"
                                   f"Enter Nothing To Refresh\n")
                if user_input == "":
                    pass
                elif not user_input.isdigit():
                    await bot.invalid_entry(str)
                else:
                    user_input = int(user_input)
                    if user_input == 0:
                        await bot.go_back()
                        break
                    elif user_input == 1:
                        print("Not Done")
                        await asyncio.sleep(3)
                    else:
                        await bot.invalid_entry(int)

        while True:
            cls()
            options = []
            user_document = await refresh_document_user()
            print(await top_bar(f"{key.title()} Fights"))
            try:
                for n, chodeling in enumerate(user_document['data_games']['fight'][key].keys()):
                    options.append(f"{n + 1}. {chodeling}")
            except Exception as error_building_detailed_options:
                logger.error(f"{fortime()}: Error in 'display_stats_fight' -- Error building detailed options\n{error_building_detailed_options}")
                await asyncio.sleep(3)
            user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                               f"{long_dashes}\n"
                               f"Enter # Or Type Chodeling To View Stats\n"
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
            elif len(options) > 0 and user_input.lower() in check_numbered_list(options):
                await detailed_stats(user_input.lower())
            else:
                await bot.invalid_entry(str)

    async def refresh_stats() -> dict:
        user_stats = {
            'aggressor': {
                'fights_lost': 0,
                'fights_tied': 0,
                'fights_total': 0,
                'fights_won': 0,
                'points_lost': 0,
                'points_won': 0
            },
            'defender': {
                'fights_lost': 0,
                'fights_tied': 0,
                'fights_total': 0,
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
            logger.error(f"{fortime()}: Error in 'display_stats_fight' -- Error building user_stats\n{error_building_user_stats}")
            await asyncio.sleep(3)
            return {}
        return user_stats

    while True:
        cls()
        user_document = await refresh_document_user()
        print(await top_bar("Fight Stats"))
        user_stats = await refresh_stats()
        if len(user_stats) > 0:
            try:
                print(f"Total Fights: {numberize(user_stats['aggressor']['fights_total'] + user_stats['defender']['fights_total'])}\n"
                      f"Total Lost: {numberize(user_stats['aggressor']['fights_lost'] + user_stats['defender']['fights_lost'])}\n"
                      f"Total Tied: {numberize(user_stats['aggressor']['fights_tied'] + user_stats['defender']['fights_tied'])}\n"
                      f"Total Wins: {numberize(user_stats['aggressor']['fights_won'] + user_stats['defender']['fights_won'])}\n"
                      f"Total Points Lost: {numberize(user_stats['aggressor']['points_lost'] + user_stats['defender']['points_lost'])}\n"
                      f"Total Points Won: {numberize(user_stats['aggressor']['points_won'] + user_stats['defender']['points_won'])}")
            except Exception as error_printing_fight_stats:
                logger.error(f"{fortime()}: Error in 'display_stats_fight' -- Error printing fight stats\n{error_printing_fight_stats}")
                await asyncio.sleep(3)
        user_input = input(f"{long_dashes}\n"
                           f"Enter 1 To View Aggressor Fights\n"
                           f"Enter 2 To View Defender Fights\n"
                           f"Enter 0 To Go Back\n"
                           f"Enter Nothing To Refresh\n")
        if user_input == "":
            pass
        elif not user_input.isdigit():
            await bot.invalid_entry(str)
        else:
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


async def display_stats_fish():
    async def refresh_stats() -> dict:
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
                logger.error(f"{fortime()}: Error in 'refresh_stats' -- 'fetch_fish_stats' -- Error Building Return Dictionary -- {error_building_dict_return}")
                await asyncio.sleep(5)
                return {}

            return dict_return
        except Exception as error_building_stats:
            logger.error(f"{fortime()}: Error in 'display_stats_fish' -- Error Building Stats -- {error_building_stats}")
            await asyncio.sleep(5)
            return {}

    channel_document = await refresh_document_channel()
    while True:
        async def detailed_stats(key_type: str):
            while True:
                cls()
                user_stats = await refresh_stats()
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
                    logger.error(f"{fortime()}: Error Displaying {key_type.title()} Fishing Stats -- Generic Error -- {error_detailed_stats}")
                user_input = input(f"{long_dashes}\n"
                                   f"Enter 1 To View Unique Catches List\n"
                                   f"Enter 0 To Go Back\n"
                                   f"Enter Nothing To Refresh\n")
                if user_input == "":
                    pass
                elif not user_input.isdigit():
                    await bot.invalid_entry(str)
                else:
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
                                print(f"{key_type.title()} Fishing Unique Catches\n{long_dashes}")
                                sortby = await fetch_setting("sortby")
                                if sortby is not None:
                                    for key, value in dict(sorted(user_stats[key_type]['total_unique_dict'].items(), key=lambda x: x[1 if sortby >= 1 else 0][0 if sortby == 0 else sortby - 1])).items():
                                        print(f"{key} | Caught: {value[0]:,} ({numberize(value[1])})")
                            input(f"{long_dashes}\nHit Enter To Go Back")
                        except Exception as error_printing_auto_catches:
                            logger.error(f"{fortime()}: Error in 'fetch_fish_stats' -- Error Printing Auto Catches -- {error_printing_auto_catches}")
                            input("\nHit Enter To Go Back")
                    else:
                        await bot.invalid_entry(int)

        cls()
        user_stats = await refresh_stats()
        if len(user_stats) == 0:
            break
        print(await top_bar("Fishing Options"))
        user_input = input("Enter 1 To View Auto Stats\n"
                           "Enter 2 To View Manual Stats\n"
                           "Enter 3 To View Line Cut Stats\n"
                           "Enter 4 To View Upgrades Details\n"
                           "Enter 0 To Go Back\n")
        if not user_input.isdigit():
            await bot.invalid_entry(str)
        else:
            user_input = int(user_input)
            if user_input == 0:
                await bot.go_back()
                break
            elif user_input == 1:
                await detailed_stats('auto')
            elif user_input == 2:
                await detailed_stats('manual')
            elif user_input == 3:
                async def detailed_stats(key_cut: str):
                    async def print_details(name: str):
                        cls()
                        sortby = await fetch_setting("sortby")
                        print(await top_bar(f"{name} has {f'made you loose;' if key_cut == 'cut_by' else f'lost;'}"))
                        if sortby is not None:
                            for key, value in dict(sorted(user_document['data_games']['fish']['totals']['line'][key_cut][name].items(), key=lambda x: x[1 if sortby >= 1 else 0][0 if sortby == 0 else sortby - 1])).items():
                                print(f"{key} | {numberize(value[0])} Times ({numberize(value[1])})")
                        input(f"{long_dashes}\nEnter To Return")

                    while True:
                        cls()
                        user_document = await refresh_document_user()
                        try:
                            if len(user_document['data_games']['fish']['totals']['line'][key_cut]) == 0:
                                print("No one has cut your line yet!" if key_cut == "cut_by" else "You haven't cut anyone's line yet!")
                                input("Hit Enter To Go Back")
                                await bot.go_back()
                                break
                            print(await top_bar("Others Who Have Cut Your Line;" if key_cut == "cut_by" else f"Chodelings Who's Lines You've Cut;"))
                            options = []
                            try:
                                for n, name in enumerate(sorted(user_document['data_games']['fish']['totals']['line'][key_cut].keys(), key=lambda x: x)):
                                    options.append(f"{n+1}. {name}")
                            except Exception as error_printing_cutline_options:
                                logger.error(f"{fortime()}: Error in 'display_stats_fish' -- 'cutline detailed stats' -- {error_printing_cutline_options}")
                                await asyncio.sleep(3)
                            user_input = input(f"{f'{nl.join(options)}{nl}' if len(options) > 0 else ''}"
                                               f"{long_dashes}\n"
                                               f"Enter # or Thee Username Of Who's Stats You Want To See\n"
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
                            elif user_input.lower() in check_numbered_list(options):
                                await print_details(user_input.lower())
                            else:
                                await bot.invalid_entry(str)
                        except Exception as error_looping_line_cutby:
                            logger.error(f"{fortime()}: Error in 'fetch_fish_stats' -- 'cutline stats' -- 'detailed_stats() -- Looping Line {key_cut} -- {error_looping_line_cutby}")
                            input("\nHit Enter To Go Back")
                            break

                while True:
                    cls()
                    user_stats = await refresh_stats()
                    if len(user_stats) == 0:
                        break
                    print(await top_bar("CutLine Stats;"))
                    try:
                        print(f"Own Line Cut Times: {numberize(user_stats['cut_line']['own_line_times_cut'])}\n"
                              f"Own Line Cut Points {'Lost' if user_stats['cut_line']['own_line_points_lost'] > 0 else 'Saved'}: {numberize(user_stats['cut_line']['own_line_points_lost'] if user_stats['cut_line']['own_line_points_lost'] > 0 else abs(user_stats['cut_line']['own_line_points_lost']))}\n"
                              f"Other Line Cut Times: {numberize(user_stats['cut_line']['other_line_times_cut'])}\n"
                              f"Other Line Cut Points {'Lost' if user_stats['cut_line']['other_line_points_lost'] > 0 else 'Saved'}: {numberize(user_stats['cut_line']['other_line_points_lost'] if user_stats['cut_line']['other_line_points_lost'] > 0 else abs(user_stats['cut_line']['other_line_points_lost']))}")
                    except Exception as error_printing_cutline_stats:
                        logger.error(f"{fortime()}: Error in 'fetch_fish_stats' -- Printing CutLine Stats -- {error_printing_cutline_stats}")
                    user_input = input(f"{long_dashes}\n"
                                       "Enter 1 To View Detailed Own Line Cut Stats\n"
                                       "Enter 2 To View Detailed Other Line Cut Stats\n"
                                       "Enter 0 To Go Back\n"
                                       "Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif not user_input.isdigit():
                        await bot.invalid_entry(str)
                    else:
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
            elif user_input == 4:
                while True:
                    async def detailed_stats(key_type: str):
                        cls()
                        user_stats = await refresh_stats()
                        print(await top_bar(f"{key_type.title()} Detailed View"))
                        try:
                            for key, value in channel_document['data_games']['fish']['upgrades'][key_type][str(user_stats['levels'][key_type])].items():
                                print(f"{key.title()}: {value}")
                        except Exception as error_printing_detailed_stats:
                            logger.error(f"{fortime()}: Error in 'display_stats_fish' -- printing detailed {key_type.title()} stats -- {error_printing_detailed_stats}")
                            await asyncio.sleep(5)
                        input(f"{long_dashes}\n"
                              f"Hit Enter To Go Back")
                        await bot.go_back()

                    cls()
                    user_stats = await refresh_stats()
                    if len(user_stats) == 0:
                        break
                    print(await top_bar("Fishing Levels;"))
                    try:
                        print(f"Line: {user_stats['levels']['line']} ({channel_document['data_games']['fish']['upgrades']['line'][str(user_stats['levels']['line'])]['name']})\n"
                              f"Lure: {user_stats['levels']['lure']} ({channel_document['data_games']['fish']['upgrades']['lure'][str(user_stats['levels']['lure'])]['name']})\n"
                              f"Reel: {user_stats['levels']['reel']} ({channel_document['data_games']['fish']['upgrades']['reel'][str(user_stats['levels']['reel'])]['name']})\n"
                              f"Rod: {user_stats['levels']['rod']} ({channel_document['data_games']['fish']['upgrades']['rod'][str(user_stats['levels']['rod'])]['name']})")
                    except Exception as error_printing_fishing_levels:
                        logger.error(f"{fortime()}: Error in 'display_stats_fishing' -- printing fishing levels -- {error_printing_fishing_levels}")
                        await asyncio.sleep(5)
                    user_input = input(f"{long_dashes}\n"
                                       "Enter 1 For Line Stats\n"
                                       "Enter 2 For Lure Stats\n"
                                       "Enter 3 For Reel Stats\n"
                                       "Enter 4 For Rod Stats\n"
                                       "Enter 0 To Go Back\n"
                                       "Enter Nothing To Refresh\n")
                    if user_input == "":
                        pass
                    elif not user_input.isdigit():
                        await bot.invalid_entry(str)
                    else:
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
            else:
                await bot.invalid_entry(int)
            if len(user_stats) == 0:
                break


async def fetch_setting(setting: str) -> int:
    if setting == "sortby":
        try:
            return bot.settings['types_sort'].index(read_file(bot.data_settings['types_sort'], str))
        except ValueError:
            logger.error(f"{fortime()}: Error fetching types_sort. '{read_file(bot.data_settings['types_sort'], str)}' is not valid!! Returning index 1")
            await asyncio.sleep(5)
            return 1
    else:
        logger.error(f"{fortime()}: Error in 'fetch_setting' -- {setting} is not a valid setting!!!")
        await asyncio.sleep(5)
        return 1


def fortime() -> str:
    try:
        return str(datetime.datetime.now().strftime('%y-%m-%d %H:%M:%S'))
    except Exception as e:
        logger.error(f"Error creating formatted_time -- {e}")
        return str(datetime.datetime.now())


async def log_shutdown(logger_list: list):
    logging.shutdown()
    for entry in logger_list:
        try:
            os.rename(f"{directories['logs']}{entry}", f"{directories['logs_archive']}{entry}")
            print(f"{entry} moved to archives..")
        except Exception as e:
            print(e)
            pass


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
        return f"{fortime()}: ValueError Converting {variable} (type; {type(variable)}) to {return_type}"
    except Exception as e:
        error_msg = f"{fortime()}: Error in 'read_file' -- Generic Error -- {e}"
        logger.error(error_msg)
        return error_msg


async def refresh_document_channel() -> Document | None:
    try:
        channel_collection = mongo_db.twitch.get_collection("channels")
        return channel_collection.find_one({"_id": bot.login_details['target_id']})
    except FileNotFoundError:
        logger.error(f"{fortime()}: Error in 'refresh_document_channel' -- FileNotFound!!!")
        return None
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'refresh_document_channel' -- Generic -- {e}")
        return None


async def refresh_document_user() -> Document | None:
    try:
        users_collection = mongo_db.twitch.get_collection('users')
        return users_collection.find_one({"_id": user.id})
    except FileNotFoundError:
        logger.error(f"{fortime()}: Error in 'refresh_document_user' -- FileNotFound!!!")
        return None
    except Exception as e:
        logger.error(f"{fortime()}: Error in 'refresh_document_user' -- Generic -- {e}")
        return None


def remove_period_area(var: str) -> str:
    try:
        index = var.index('.')
        return var[index+2:]
    except ValueError:
        return var


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


async def top_bar(left_side: str) -> str:
    try:
        channel_document = await refresh_document_channel()
        user_document = await refresh_document_user()
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
            return f"{left_side}\n{long_dashes}"
        return f"{left_side}{' ' * (len(long_dashes) - (len(left_side) + len(str(right_side))))}{right_side}\n{long_dashes}"
    except Exception as error_creating_top_bar:
        logger.error(f"{fortime()}: Error in 'run' -- Error creating top_bar -- {error_creating_top_bar}")
        await asyncio.sleep(3)
        return left_side


# async def on_message(msg: ChatMessage):
#     # print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')
#     pass


async def on_ready(event: EventData):
    try:
        await event.chat.join_room(bot.login_details['target_name'])
        logger.info(f"{fortime()}: Connected to {bot.login_details['target_name']} channel\n{long_dashes}")
    except Exception as e:
        logger.error(f"\n\n{fortime()}: Failed to connect to {bot.login_details['target_name']} channel -- {e}\n\n")


# async def on_sub(sub: ChatSub):
#     # print(f'New subscription in {sub.room.name}:\n'
#     #       f'  Type: {sub.sub_plan}\n'
#     #       f'  Message: {sub.sub_message}')
#     pass


async def test_command(cmd: ChatCommand):
    await cmd.reply(f"Ain't you trying to get Chodybot's attn? :P")


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
    # chat.register_event(ChatEvent.MESSAGE, on_message)
    # chat.register_event(ChatEvent.SUB, on_sub)
    chat.register_command('attn', test_command)

    chat.start()

    await asyncio.sleep(2.5)
    while True:
        cls()
        try:
            user_input = input(f"{await top_bar('Main Menu')}\n"
                               "Enter 1 To View Profile\n"
                               "Enter 2 To View Commands\n"
                               # "Enter 3 To View Leaderboards\n"
                               "Enter 8 To Enter Profile Settings\n"
                               "Enter 9 To Change App Settings\n"
                               # "Enter 9 To View Settings\n"
                               "Enter 0 To Shutdown Bot\n")
            if user_input == "":
                pass
            elif not user_input.isdigit():
                await bot.invalid_entry(str)
            else:
                user_input = int(user_input)
                if user_input == 0:
                    await shutdown()
                    break
                elif user_input == 1:
                    await chodeling_stats()
                elif user_input == 2:
                    await chodeling_commands()
                elif user_input == 8:
                    print("Not programmed yet")
                    await asyncio.sleep(3)
                elif user_input == 9:
                    await app_settings()
                else:
                    await bot.invalid_entry(int)
        except KeyboardInterrupt:
            print("EXITING")
            await shutdown()
            break
        except Exception as e:
            logger.error(f"{fortime()}: Generic Error\n{e}")
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
                logger.error(f"{fortime()}: Error getting user_id!!")
    except Exception as e:
        logger.error(f"{fortime()}: Error getting users!! -- {e}")
        return None
    return user


def data_check():
    def write_new_file(filename: str, var_write: str):
        with open(filename, "w") as file:
            file.write(var_write)
        logger.info(f"{fortime()}: '{filename}'\nFile NOT FOUND, CREATED!")
        time.sleep(5)

    if not os.path.exists(bot.data_settings['types_always_display']):
        write_new_file(bot.data_settings['types_always_display'], bot.settings['types_always_display'][2])
    if not os.path.exists(bot.data_settings['types_sort']):
        write_new_file(bot.data_settings['types_sort'], bot.settings['types_sort'][2])


if __name__ == "__main__":
    init_time = fortime().replace(' ', '--').replace(':', '-')
    logger = setup_logger("logger", f"main_log--{init_time}.log", logger_list)
    # logger_track = setup_logger("logger_track", f"track_log--{init_time}.log", logger_list)
    if None in logger_list:
        print(f"One of thee loggers isn't setup right\n{logger}\nQuitting program")
        time.sleep(5)
        proceed = False
    else:
        bot = BotSetup(bot_id, bot_secret)
        data_check()
        while True:
            cls()
            user_input = input("Enter 1 to start bot\nEnter 0 to exit\n")
            if not user_input.isdigit():
                asyncio.run(bot.invalid_entry(str))
            else:
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
                        asyncio.run(run())
                    break
                else:
                    print(f"{fortime()} You entered {user_input} which is not valid, try again")
                    time.sleep(2)
    asyncio.run(log_shutdown(logger_list))
