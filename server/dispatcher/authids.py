
import config
import log
import os
import pickle
import services
import time
from util import *
import json
import requests
from requests.auth import HTTPDigestAuth
import socket
import sys

AUTHIDS = None

class AuthId(object):
    """
    Single paymentid session class.
    All payments for given authid are in one session.
    """
    
    def __init__(self, authid, serviceid, balance, confirmations, height=0, txid=None, msg=""):
        self.id = authid.upper()
        self.balance = float(0)
        self.txid = txid
        self.serviceid = serviceid.upper()
        self.confirmations = int(confirmations)
        self.height = int(height)
        self.created = time.time()
        self.overalltime = 0
        self.charged_count = int(0)
        self.lastmodify = time.time()
        self.activated = None
        if (services.SERVICES.get(self.serviceid)):
            self.cost = services.SERVICES.get(self.serviceid).getCost()
        else:
            log.L.error("Dropping authid %s (serviceid %s does not exists)" % (self.authid, self.serviceid))
            return(None)
        if (float(balance) > 0):
            self.topUp(float(balance))
        self.discharged_count = int(0)
        self.spending = None
        
    def getId(self):
        return(self.id)
    
    def getOverallTime(self):
        return(self.overalltime)
    
    def activate(self):
        self.activated = True

    def deActivate(self):
        self.activated = None
        
    def isActivated(self):
        return(self.activated)
    
    def confirm(self):
        self.confirmations = self.confirmations + 1
    
    def getBalance(self):
        return(self.balance)
    
    def getConfirmations(self):
        return(self.confirmations)
    
    def getHeight(self):
        return(self.height)
    
    def getTxId(self):
        return(self.txid)

    def getServiceId(self):
        return(self.serviceid)
    
    def getTimeLeft(self):
        return(self.balance / self.cost)
    
    def getTimeSpent(self):
        return(self.firstbalance / self.cost)
    
    def show(self):
        log.L.info(self.toString())
    
    def toString(self):
        if self.isSpending():
            spending = "yes"
        else:
            spending = "no"
        if self.isActivated():
            activated = "yes"
        else:
            activated = "no"
        str = "%s: serviceid=%s, created=%s, modified=%s, spending=%s, activated=%s, balance=%f, perminute=%.3f, minsleft=%f, charged_count=%d, discharged_count=%d\n" % (self.id, self.serviceid, timefmt(self.created), timefmt(self.lastmodify), spending, activated, self.balance, self.cost, self.balance / self.cost, self.charged_count, self.discharged_count)
        return(str)
    
    def toJson(self):
        if self.isSpending():
            spending = "yes"
        else:
            spending = "no"
        if self.isActivated():
            activated = "yes"
        else:
            activated= "no"
        str = '{"status": "OK", "activated": "%s", balance": "%.3f", "created":"%s", "minutes_overall": "%d", minutes_left": "%d", "spending": "%s", "charged_count": "%d", "spent_count": "%d"}' % (activated, self.getBalance(), timefmt(self.created), self.getOverallTime(), self.getTimeLeft(), spending, self.charged_count, self.discharged_count)
        return(str)
    
    def topUp(self, itns, msg="", confirmations=None):
        """ TopUp authid. If itns is zero, only update internal acls of services. If confirmations is set, it is updated. If it is same payment but more confirmations, ignore."""
        if confirmations:
            if (int(confirmations) >= self.confirmations):
                log.L.debug("Authid %s: Verified %s times." % (self.getId(), self.confirmations))
                self.confirmations = int(confirmations)
                
        if (itns > 0):
            self.balance += itns
            self.lastmodify = time.time()
            self.lastcharge = time.time()
            self.charged_count += 1
            log.L.debug("Authid %s: Topup %.3f, new balance %.3f" % (self.getId(), itns, self.balance))
            log.A.audit(log.A.AUTHID, log.A.MODIFY, self.id, "topup,amount=%.3f,balance=%.3f %s" % (itns, self.balance, msg))
        for s in services.SERVICES.getAll():
            services.SERVICES.get(s).addAuthIdIfTopup(self)
            
    def startSpending(self):
        """ Start spending of authid """
        if (not self.spending):
            self.spending = True
            log.L.debug("Authid %s: Start spending" % (self.getId()))
        
    def isSpending(self):
        """ If authid had at least one session, it is spending until zero. """
        return(self.spending)
    
    def spend(self, itns, msg=""):
        """ Spend authid. If balance is not enough for given service, remove it from its acl. """
        if (itns > 0):
            self.balance -= itns
            self.lastmodify = time.time()
            self.overalltime += itns/self.cost
            self.lastdisCharge = time.time()
            self.discharged_count += 1
            log.L.debug("Authid %s: Spent %f, new balance %f" % (self.getId(), itns, self.balance))
            log.A.audit(log.A.AUTHID, log.A.MODIFY, self.id, "spent,amount=%s,balance=%s %s" % (itns, self.balance, msg))
            for s in services.SERVICES.getAll():
                services.SERVICES.get(s).delAuthIdIfSpent(self)
                
    def spendTime(self, seconds):
        self.spend(self.cost * seconds / 60, "(%.2f minutes*%f)" % (seconds/60, self.cost))
            
    def getBalance(self):
        return(self.balance)
    
    def checkAlive(self):
        if (time.time()-self.created > config.CONFIG.CAP.maxToSpend):
            self.startSpending()
        return(
            self.balance > 0
            )

class AuthIds(object):
    """Active AUTHIDS sessions container"""
    
    def __init__(self):
        self.authids = {}
        self.lastmodify = time.time()
        self.lastheight = 0
        
    def add(self, payment):
        log.L.warning("New authid %s" % (payment.getId()))
        log.A.audit(log.A.AUTHID, log.A.ADD, payment.getId(), "init, balance=%.3f, confirmations=%s" % (payment.getBalance(), payment.getConfirmations()))
        self.authids[payment.getId()] = payment
        
    def update(self, auth_id, service_id, amount, confirmations, height=0, txid=None):
        if auth_id in self.authids.keys():
            # New payment for existing authid
            if (txid != self.authids[auth_id].getTxId()):
                self.topUp(auth_id, amount, txid, confirmations)
            else:
                # New confirmation for existing authid
                self.topUp(auth_id, 0, "confirmation", confirmations)
        else:
            # First payment for new authid
            payment = AuthId(auth_id, service_id, amount, confirmations, height, txid)
            self.add(payment)
    
    def topUp(self, paymentid, amount, msg="", confirmations=None):
        self.authids[paymentid].topUp(amount, msg, confirmations)

    def spend(self, paymentid, balance, msg=""):
        self.authids[paymentid].spend(balance, msg)
        
    def get(self, paymentid):
        if (paymentid in self.authids.keys()):
            return(self.authids[paymentid])
        else:
            return(None)
        
    def getAll(self):
        return(self.authids.keys())

    def remove(self, paymentid):
        if (self.get(paymentid)):
            log.L.warning("Removing authid %s (balance=%.3f)" % (paymentid, self.get(paymentid).getBalance()))
            log.A.audit(log.A.AUTHID,log.A.DEL,paymentid, "%.3f" % (self.get(paymentid).getBalance()))
            for s in services.SERVICES.getAll():
                services.SERVICES.get(s).delAuthId(self.get(paymentid))
            self.authids.pop(paymentid)
        
    def toString(self):
        str = "%d ids, last updated %s\npayment spending activated minutes_left\n" % (len(self.authids), timefmt(self.lastmodify))
        for id, paymentid in self.authids.items():
            if paymentid.isSpending():
                spending = "yes"
            else:
                spending = "no"
            if paymentid.isActivated():
                activated = "yes"
            else:
                activated = "no"
            str = str + "%s %s %s %.1f\n" % (paymentid.getId(), spending, activated, paymentid.getTimeLeft())
        return(str)
        
    def show(self):
        log.L.warning("Authids: %d ids, last updated %s" % (len(self.authids), timefmt(self.lastmodify)))
        for id, paymentid in self.authids.items():
            paymentid.show()
            
    def list(self):
        return(self.authids)
        
    def cleanup(self):
        fresh = 0
        deleted = 0
        for id in list(self.authids.keys()):
            if not self.authids[id].checkAlive():
                self.remove(id)
                deleted += 1
            else:
                fresh += 1
        log.L.info("Authids cleanup: %d deleted, %d fresh" % (deleted, fresh))

    def walletJSONCall(self, method, params):
        d = {
            "id": "0",
            "method": method,
            "jsonrpc": "2.0",
            "params": params
        }
        url = config.CONFIG.CAP.walletUri
        log.L.debug("Calling wallet RPC " + url)
        try:
            r = requests.post(url, data=json.dumps(d), auth=HTTPDigestAuth(config.CONFIG.CAP.walletUsername, config.CONFIG.CAP.walletPassword), headers={"Content-Type": "application/json"})
            if (r.status_code == 200):
                j = json.loads(r.text)
                if ('result' in j):
                    return(r.text)
                else:
                    log.L.error("Wallet RPC error %s! Will not receive payments!" % (r.text))
                    return(None)
            else:
                log.L.error("Wallet RPC error %s! Will not receive payments!" % (r.status_code))
                return(None)
        except IOError:
            return(None)

    def getHeighFromWallet(self):
        """
        We should connect to wallet or daemon and get actual height
        Whe we loaded authids from disk, we will use last height processed but if we have clean db, we need to start here.
        """
        str = self.walletJSONCall("getheight", {})
        if (str):
            res = json.loads(str)
            return res['result']['height']
        else:
            return(None)


    def getFromWallet(self):
        """
        Connect to wallet and ask for all self.authids from last height.
        """
        cur_height = self.getHeighFromWallet()
        if (self.lastheight==0):
            if (config.CONFIG.CAP.initHeight==-1 and cur_height):
                self.lastheight = cur_height
            else:
                self.lastheight = config.CONFIG.CAP.initHeight
            
        params = {
            "in": True,
            "pool": True,
            "filter_by_height": True,
            "min_height": self.lastheight + 1,
            "max_height": 99999999
        }
        str = self.walletJSONCall("get_vpn_transfers", params)
        if (str):
            res = json.loads(str)
        else:
            return(None)

        txes = []
        if ('in' in res['result']):
            txes.extend(res['result']['in'])
        if ('pool' in res['result']):
            txes.extend(res['result']['pool'])
            
        if (len(txes) > 0):
            for tx in txes:
                if (tx['height'] > 0):
                    if (tx['height'] > cur_height):
                        log.L.warning("Wallet not in sync! Got a payment for a future block height")
                        break

                    confirmations = cur_height - tx['height'] + 1

                    if (confirmations >= 3 and tx['height'] > self.lastheight):
                        self.lastheight = tx['height']
                        
                else:
                    confirmations = 0
                        
                service_id = tx['payment_id'][0:2]
                auth_id = tx['payment_id'].upper()
                amount = tx['amount'] / 100000000
                log.L.info("Got payment for service %s, auth=%s, amount=%s, confirmations=%s, height=%s, txid=%s" % (service_id, auth_id, amount, confirmations, tx['height'], tx['txid']))

                # Try to update internal authid db with this payment
                self.update(auth_id, service_id, float(amount), int(confirmations), tx['height'], tx['txid'])
                
            log.L.info("All payments from wallet processed")  
        else:
            log.L.info("No new payments in wallet")
        return(True)
        
    def load(self):
        if (config.Config.AUTHIDSFILE != ""):
            if os.path.isfile(config.Config.AUTHIDSFILE):
                try:
                    log.L.info("Trying to load authids db from %s" % (config.Config.AUTHIDSFILE))
                    aids = pickle.load(open(config.Config.AUTHIDSFILE, "rb"))
                    for id in aids.getAll():
                        aids.get(id).topUp(0)
                    return(aids)
                except (OSError, IOError) as e:
                    log.L.warning("Error reading or creating authids db %s" % (config.Config.AUTHIDSFILE))
                    sys.exit(2)
            else:
                self.save()

    def save(self):
        if (config.Config.AUTHIDSFILE != ""):
            try:
                self.lastmodify = time.time()
                log.L.debug("Saving authids db into %s" % (config.Config.AUTHIDSFILE))
                with open(config.Config.AUTHIDSFILE, 'wb') as output:
                    pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            except (OSError, IOError) as e:
                log.L.warning("Error writing authids db %s" % (config.Config.AUTHIDSFILE))
                sys.exit(2)
