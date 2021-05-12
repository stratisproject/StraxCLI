"""
Version: 1.0.0
Author: Velocity-plus
Github: https://github.com/Velocity-plus
Date: 10-05-2021
For instructions how to use, visit straxrpi.miew.org
If you want to give me a tip me, check the link above!
"""

from time import sleep
from interface.node import NodeAPI
from interface.node import Caching
from interface.node import TempData
from interface.node import API_URL_VERSION_CHECK
from getpass import getpass
import requests
from requests import exceptions
import json

Data = TempData()
Cache = Caching(Data.temp_mem)
Cache.start()
Node = NodeAPI(Data.temp_mem)

VERSION = "1.0.0"


class StraxCLI:
    def __init__(self, data):
        self.temp_data = data
        self.startup = True

    def input_prompt_pass(self):
        print("< Please note that characters are invisible when typed")
        walletPasswd = getpass("Password: ")
        walletPasswdConf = getpass("Re-type password: ")
        if walletPasswd != walletPasswdConf:
            print("Password didn't match, please try again.")
            self.input_prompt_pass()

        self.temp_data['password'] = walletPasswdConf

    def input_prompt_ph(self):
        print("< Please note that characters are invisible when typed.")
        print("< If you have no passphrase for your wallet, press enter for blank.")
        walletPh = getpass("Passphrase: ")
        if walletPh != '':
            walletPhConf = getpass("Re-type passphrase: ")
            if walletPh != walletPhConf:
                print("Passphrase didn't match, please try again.")
                self.input_prompt_ph()
            self.temp_data['passphrase'] = walletPh

    def input_temp_info(self):
        if self.temp_data['walletname'] == '' and self.temp_data['password'] == '':
            walletName = input("Wallet Name: ")
            self.temp_data['walletname'] = walletName
            self.input_prompt_pass()

    def cli_start(self):
        print(" ")
        print("> Checking StraxNode connection...")
        if self.startup:
            Node.get_latest_block()
            self.startup = False

        if Node.is_node_alive()['alive']:
            print("> StraxNode is: Online... Menu initializing.. \n ")
            sleep(1)
            self.cli_display()
        else:
            print("> StraxNode is offline, please start the StraxNode")
            print("> CMD: sudo screen dotnet ~/StraxNode/Stratis.StraxD.dll run -mainnet")
            Cache.quit()

    def cli_display(self):

        # Check for staking
        is_staking = Node.is_staking()

        print("------------- StraxCLI menu -------------")
        print(">> Staking Status: %s" % is_staking['msg'])

        # Check Sync and Current block
        is_synced = Node.is_fully_synced()
        get_sync_info = Node.get_sync_info()

        print(">> Fully Synced: %s | Current Block: %s" % (is_synced['msg'], get_sync_info))
        print(" ")

        if is_staking['enabled']:
            print("> 1. Stop Staking")
        else:
            print("> 1. Start Staking")

        print("> 2. Check balance")
        print("> 3. Re-Sync Wallet")
        print("> 4. Recover Wallet")
        print("> 5. Remove Wallet")
        print(" ")
        print("> 6. Refresh")
        print("> 7. Quit")
        print(" ")
        print("Your Wallets: %s" % (Node.get_wallets()))
        print("------------------------------------------")
        print("Please Select an item from the menu")
        choice = input("Select: ")
        try:
            choice = int(choice)
            self.cli_select(choice)
        except ValueError:
            print("< Not a valid choice, please try again")
            self.cli_start()

    def cli_select(self, choice):
        if choice == 1:
            is_staking = Node.is_staking()
            if is_staking['enabled']:
                print("> Stopping staking... Please wait")
                stop_staking = Node.action_stop_staking()
                if stop_staking['succes']:
                    print("< Staking stopped sucessfully!")
            else:
                self.input_temp_info()
                print("< Enabling staking for wallet: %s.." % self.temp_data['walletname'])
                ss = Node.action_start_staking(self.temp_data['walletname'], self.temp_data['password'])
                if ss['succes']:
                    print("< Checking if you are actually staking...")
                    is_synced = Node.is_fully_synced()
                    if not is_synced['synced']:
                        print(
                            "< NOTE: You are not fully synced, staking won't be active before fully synced with the network")
                        print("< Your sync progression is: %s" % (Node.get_sync_info()))
                    sleep(8)
                    is_staking = Node.is_staking()
                    print("< Stacking: %s" % is_staking['msg'])
                else:
                    print("Something went wrong, when trying to stake. Error code: %s" % ss['code'])

            print("< Loading main menu again. Please wait...")
            sleep(2)

        elif choice == 2:
            self.question_balance()

        elif choice == 3:
            self.question_sync_from_date()

        elif choice == 4:
            self.question_recover_wallet()

        elif choice == 5:
            self.question_remove_wallet()

        if choice in (1, 2, 3, 4, 5, 6):
            self.cli_start()

        if choice == 7:
            print("Bye bye, Thank you (please wait a moment..)")
            print("Closing script...")
        else:
            print("Not a valid number, please use 1-7 (it can take a moment before exiting..)")

        Cache.quit()

    def question_balance(self):
        print("< Please fill out the fields below:")
        walletName = input("Wallet Name: ")
        print("< Retrieving balance for wallet: %s..." % walletName)
        balance = Node.get_balance(walletName)
        if balance['succes']:
            is_synced = Node.is_fully_synced()
            if not is_synced['synced']:
                print("> NOTE: You are not fully synced with network, your current amount might not be accurate!")
                print("> Sync progression: b: %s" % Node.get_sync_info())
            print("> Your balance is %s STRAX (Confirmed)" % balance['amount'])
        else:
            print("Something went wrong, please try again. Error code: %s" % balance['code'])

    def question_sync_from_date(self):
        print("> Please fill out the fields below:")
        walletName = input("Wallet Name: ")
        date = input("Date yy-mm-dd: ")
        print("< Re-syncing you transactions from %s to present." % date)
        sync_from = Node.action_sync_from_date(date, True, walletName)
        if sync_from['succes']:
            print("Syncing started! Nice.")
        else:
            print("Something went wrong, please try again. Error code: %s" % sync_from['code'])

    def question_recover_wallet(self):
        print("> Recover Wallet...")
        print("> Please fill out the fields below")
        mnemoic = input("Secret Words: ")
        self.input_prompt_pass()
        self.input_prompt_ph()
        walletname = input("Enter any wallet name: ")
        creationDate = input("Creation date yy-mm-dd: ")
        print("< Recovering wallet... (this can take a while)..")
        recover = Node.action_recover_wallet(mnemoic, self.temp_data['password'], self.temp_data['passphrase'],
                                             walletname, creationDate)
        if recover['succes']:
            print("< Wallet recovered succesfully with alias: %s" % walletname)
            print("> Syncing your wallet transactions, please wait")
            sleep(3)
            sync_tran = Node.action_sync_from_date(creationDate, True, walletname)
            if sync_tran['succes']:
                print("< Syncing started! Great.")
            else:
                print("< Could not sync your transactions, you will have re-sync in the main menu. Error code: %s" %
                      sync_tran['code'])
            print("< Loading main menu, please wait...")
            sleep(5)

        else:
            print("< Something went wrong, please try recovering your wallet again. Error code: %s" % recover['code'])

    def question_remove_wallet(self):
        print("<< !!REMOVE WALLET!! >>")
        walletName = input("Wallet Name: ")
        confirm = input("> Are you sure want to remove %s (y/n): " % walletName)
        if confirm.lower() in ("y", "yes"):
            rm_wallet = Node.action_remove_wallet(walletName)
            if rm_wallet['succes']:
                print("< Wallet %s removed succesfully!" % walletName)
            else:
                print("< Something went wrong, please try again.. Error code: %s" % rm_wallet['code'])
        else:
            print("> Operation cancelled!")


def _StraxCLIvCheck():
    print(">>>>> Checking for new version... <<<<<")
    subs = API_URL_VERSION_CHECK
    try:
        r = requests.get(subs, timeout=3)
        if r.status_code == 200:
            js = json.loads(r.content)
            latest_version = js['latest_version']
            latest_msg = js["latest_msg"]
            if latest_version == latest_version:
                print(">>>>>> You are running the latest version: %s <<<<<<<" % VERSION)
                if latest_msg != '':
                    print(latest_msg)
            else:
                print(">>>>>> There is a new version available for StraxCLI: %s -> %s <<<<<<<" % (
                VERSION, latest_version))
                print("> Please make sure you are always running the latest version")
                print("> You can download new releases from https://github.com/stratisproject/StraxCLI/releases")

    except exceptions.RequestException:
        print("> Could not check for new version, continuing...")
        print("> You are running version: %s" % VERSION)


_StraxCLIvCheck()
StraxCLI = StraxCLI(Data.temp_mem)
StraxCLI.cli_start()
