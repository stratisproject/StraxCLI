"""
Version: 1.0.0
Author: Velocity-plus
Github: https://github.com/Velocity-plus
Date: 10-05-2021
For instructions how to use, visit straxrpi.miew.org
If you want to give me a tip me, check the link above!
"""
import json
import requests
from requests import exceptions
from threading import Thread
from time import sleep

API_URL = "http://localhost:17103"
API_URL_EXTERNAL = "https://strax.miew.org/api/1.0/stratis/straxcli"


class TempData:
    def __init__(self):
        self.version = ""
        self.msg = ""
        self.temp_mem = {'password': '',
                         'passphrase': '',
                         'walletname': '',
                         'creationDate': None,
                         'wallets': [],
                         'latest_block': -1}

    def get_copy(self):
        return self.temp_mem

    def clear(self):
        self.temp_mem['password'] = ''
        self.temp_mem['passphrase'] = ''
        self.temp_mem['walletname'] = ''
        self.temp_mem['creationDate'] = None


class Caching(Thread):
    def __init__(self, data):
        super().__init__()
        self.temp_mem = data
        self.running = True
        self.pause = 10
        self.frac = 8

    def run(self):
        while self.running:
            self.getLatestBlockCaching()
        print("Done, bye!")

    def quit(self):
        self.running = False
        exit()

    def getLatestBlockCaching(self):
        subs = API_URL_EXTERNAL
        try:
            r = requests.get(subs, timeout=6)
            if r.status_code == 200:
                js = json.loads(r.content)
                self.temp_mem['latest_block'] = js['latest_block']
        except exceptions.RequestException:
            pass

        for x in range(self.pause * self.frac):
            if self.running:
                sleep(x / self.frac)


class NodeAPI:
    def __init__(self, data):
        self.API_URL = API_URL
        self.temp_mem = data

    def is_node_alive(self):
        subs = "/api/Node/Status"
        try:
            r = requests.get(self.API_URL + subs)
            if r.status_code == 200:
                return {'succes': True, 'alive': True, 'data': r.content, 'msg': None, 'code': r.status_code}
            else:
                return {'succes': True, 'alive': False, 'data': r.content, 'msg': None, 'code': r.status_code}
        except exceptions.RequestException:
            return {'succes': False, 'alive': False, 'data': None, 'msg': None}

    def is_fully_synced(self):
        subs = "/api/Dashboard/Stats"
        try:
            r = requests.get(self.API_URL + subs)

            if r.status_code == 200:
                data = r.text.splitlines()

                fsync = False
                wallets = []
                wline = False

                for line in data:
                    if "Synced with Network" in line:
                        if "Yes" in line:
                            fsync = True
                    if wline:
                        wallets.append(line.split("/")[0])
                    if "Wallets" in line:
                        wline = True

                self.temp_mem['wallets'] = wallets
                if fsync:
                    msg = 'Yes'
                else:
                    msg = 'No'
                return {'succes': True, 'synced': fsync, 'data': data, 'msg': msg, 'code': r.status_code}
            else:
                return {'succes': False, 'synced': False, 'data': None, 'msg': None, 'code': r.status_code}

        except exceptions.RequestException:
            return {'succes': False, 'synced': False, 'data': None,
                    'msg': 'Something went wrong with checking network sync.', 'code': None}

    def is_staking(self):
        subs = "/api/Staking/getstakinginfo"
        try:
            r = requests.get(self.API_URL + subs)
            js = json.loads(r.content)
            if r.status_code == 200:
                sEnabled = js['enabled']
                sStaking = js['staking']
                if sEnabled and sStaking:
                    msg = "Yes"
                elif sEnabled:
                    msg = "Enabled (Not staking yet)"
                else:
                    msg = "No"
                return {'succes': True, 'staking': sStaking, 'enabled': sEnabled, 'data': js, 'msg': msg,
                        'code': r.status_code}
            else:
                return {'succes': False, 'staking': False, 'enabled': False, 'data': js,
                        'msg': 'Not available - please refresh', 'code': r.status_code}
        except exceptions.RequestException:
            return {'succes': False, 'staking': False, 'enabled': False, 'data': None,
                    'msg': 'Something went wrong with checking '
                           'staking status, try again.', 'code': None}

    def action_recover_wallet(self, mnemoic, passwd, passphrase, walletname, creationDate):
        subs = "/api/Wallet/create"
        params = {"mnemonic": mnemoic,
                  "password": passwd,
                  "passphrase": passphrase,
                  "name": walletname,
                  "creationDate": creationDate}
        try:
            r = requests.post(url=self.API_URL + subs, json=params)
            if r.status_code == 200:

                self.temp_mem['password'] = passwd
                self.temp_mem['walletname'] = walletname
                self.temp_mem['creationDate'] = creationDate

                return {'succes': True, 'data': r.content, 'msg': None, 'code': r.status_code}
            else:
                return {'succes'
                        : False, 'data': r.content, 'msg': None, 'code': r.status_code}

        except exceptions.RequestException:
            return {'succes': False, 'data': None, 'msg': None, 'code': None}

    def action_remove_wallet(self, walletname):
        subs = "/api/Wallet/remove-wallet"
        r = requests.delete(url=self.API_URL + subs + "?WalletName=%s" % walletname)
        if r.status_code == 200:
            return {'succes': True, 'data': r.content, 'msg': None, 'code': r.status_code}
        else:
            return {'succes': False, 'data': r.content, 'msg': None, 'code': r.status_code}

    def get_balance(self, walletname):
        subs = "/api/Wallet/balance"

        r = requests.get(url=self.API_URL + subs + "?WalletName=%s&IncludeBalanceByAddress=false" % walletname)
        js = json.loads(r.content)
        if r.status_code == 200:
            bList = js["balances"]
            total = 0
            for b in bList:
                total += b["amountConfirmed"] / 100000000
            return {'succes': True, 'amount': total, 'data': js, 'msg': None, 'code': r.status_code}
        else:
            return {'succes': False, 'amount': None, 'data': js, 'msg': None, 'code': r.status_code}

    def get_block_count(self):
        subs = "/api/BlockStore/getblockcount"
        r = requests.get(url=self.API_URL + subs)
        js = json.loads(r.content)
        if r.status_code == 200:
            return {'succes': True, 'count': js, 'data': js, 'msg': None, 'code': r.status_code}

        return {'succes': False, 'count': js, 'data': js, 'msg': None, 'code': r.status_code}

    def action_start_staking(self, walletname, password):
        subs = "/api/Staking/startstaking"
        params = {"password": password, 'name': walletname}
        r = requests.post(url=self.API_URL + subs, json=params)
        if r.status_code == 200:
            return {'succes': True, 'data': r.content, 'msg': None, 'code': r.status_code}
        else:
            return {'succes': False, 'data': r.content, 'msg': "Could not start staking, perhaps wrong password?",
                    'code': r.status_code}

    def action_stop_staking(self):
        subs = "/api/Staking/stopstaking"
        r = requests.post(url=self.API_URL + subs, json="true")
        if r.status_code == 200:
            return {'succes': True, 'data': r.content, 'msg': None, 'code': r.status_code}
        else:
            return {'succes': False, 'data': r.content, 'msg': None, 'code': r.status_code}

    def action_sync_from_date(self, date, all, walletName):
        subs = "/api/Wallet/sync-from-date"
        params = {"date": date, 'all': all, 'walletName': walletName}
        r = requests.post(url=self.API_URL + subs, json=params)
        if r.status_code == 200:
            return {'succes': True, 'data': r.content, 'msg': None, 'code': r.status_code}
        else:
            return {'succes': False, 'data': r.content, 'msg': None, 'code': r.status_code}

    def get_sync_info(self):
        try:
            call_gbc = self.get_block_count()
            cBlock = int(call_gbc['count'])
            lBlock = int(self.temp_mem['latest_block'])
            ratio = round((cBlock / lBlock) * 100, 2)
            if lBlock != -1:
                if cBlock > lBlock:
                    return "%s/%s (100%%)" % (cBlock, cBlock)
                return "%s/%s (%s%%)" % (cBlock, lBlock, ratio)

            return "%s (??%%)" % cBlock
        except:
            return "??, please refresh"

    def get_wallets(self):
        return "".join([w + " " for w in self.temp_mem['wallets']])

    def get_latest_block(self):
        subs = API_URL_EXTERNAL
        try:
            r = requests.get(subs, timeout=6)
            if r.status_code == 200:
                js = json.loads(r.content)
                self.temp_mem['latest_block'] = js['latest_block']
        except exceptions.RequestException:
            pass
