import os
import pickle
import time
import json
import requests
import socket
import sys
from requests.auth import HTTPDigestAuth
from lthnvpn.lib import log, config, services, util

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
        self.txids = dict()
        self.serviceid = serviceid.upper()
        self.confirmations = int(confirmations)
        self.height = int(height)
        self.created = time.time()
        self.charged_count = int(0)
        self.discharged_count = int(0)
        self.lastmodify = time.time()
        self.spending = None
        self.activated = None
        self.overalltime = 0
        self.invalid = None
        if (services.SERVICES.get(self.serviceid)):
            self.cost = services.SERVICES.get(self.serviceid).getCost()
        else:
            log.L.error("Bad authid %s (serviceid %s does not exists)" % (authid, serviceid))
            self.invalid = True
            return(None)
        if (float(balance) > 0):
            self.topUp(float(balance),msg="Init", txid=txid, confirmations=confirmations)
        
    def getId(self):
        return(self.id)
    
    def activate(self):
        self.activated = True
        log.L.info("Activating authid %s" % (self.getId()))
        self.getService().addAuthId(self)

    def deActivate(self):
        self.activated = None
        log.L.info("Deactivating authid %s" % (self.getId()))
        self.getService().delAuthId(self)
        
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

    def getServiceId(self):
        return(self.serviceid)
    
    def getService(self):
        return(services.SERVICES.get(self.serviceid))
    
    def getTimeLeft(self):
        return(self.balance / self.cost)
    
    def getTimeSpent(self):
        if self.spending: 
            return(int(self.overalltime/60))
        else:
            return(0)
        
    def isCreditOk(self):
        if self.invalid:
            log.L.info("Ignoring invalid authid %s" % (self.getId()))
            return(None)
        s = self.getService()
        if self.getTimeSpent()==0 and not self.isActivated():
            if self.getTimeLeft()<int(s.json["firstPrePaidMinutes"]):
                log.L.info("Not enough credit for authid %s and service %s (firstPrePaidMinutes=%s, balance=%s), need at least %s" % (self.getId(), self.getServiceId(), int(s.json["firstPrePaidMinutes"]), self.getBalance(), int(s.json["firstPrePaidMinutes"]) * float(s.getCost())))
                return(None)
            if self.getConfirmations()<int(s.json["firstVerificationsNeeded"]):
                log.L.info("Not enough confirmations for authid %s and service %s (firstVerificationsNeeded=%s, verifications=%s), need at least %s" % (self.getId(), self.getServiceId(), int(s.json["firstVerificationsNeeded"]), self.getConfirmations(), int(s.json["firstVerificationsNeeded"])))
                return(None)
            return(True)
        elif self.getTimeSpent()<int(s.json["firstPrePaidMinutes"]) and not self.isActivated():
            if self.getConfirmations()<int(s.json["firstVerificationsNeeded"]):
                log.L.info("Not enough confirmations for authid %s and service %s (firstVerificationsNeeded=%s, verifications=%s), need at least %s" % (self.getId(), self.getServiceId(), int(s.json["firstVerificationsNeeded"]), self.getConfirmations(), int(s.json["firstVerificationsNeeded"])))
                return(None)
            else:
                return(True)
        elif self.getTimeSpent()>int(s.json["firstPrePaidMinutes"]) and self.isActivated():
            if self.getTimeLeft() <= 0:
                log.L.info("Not enough credit for authid %s and service %s (subsequentPrePaidMinutes=%s, balance=%s), need at least 0" % (self.getId(), self.getServiceId(), int(s.json["firstPrePaidMinutes"]), self.getBalance()))
                return(None)
            else:
                if self.getConfirmations()<int(s.json["subsequentVerificationsNeeded"]):
                    log.L.info("Not enough confirmations for authid %s and service %s (subsequentVerificationsNeeded=%s, verifications=%s), need at least %s" % (self.getId(), self.getServiceId(), int(s.json["firstVerificationsNeeded"]), self.getConfirmations(), int(s.json["subsequentVerificationsNeeded"])))
                    return(None)
                else:
                    return(True)
        else:
            return(True)
                
    def show(self):
        log.L.info(self.toString())
        
    def getInfo(self):
        if self.isSpending():
            spending = "yes"
        else:
            spending = "no"
        if self.isActivated():
            activated = "yes"
        else:
            activated = "no"
        data={
            "id": self.id,
            "serviceid": self.serviceid,
            "created": util.timefmt(self.created),
            "modified": util.timefmt(self.lastmodify),
            "activated": activated,
            "spending": spending,
            "balance": self.getBalance(),
            "overall": self.getTimeSpent(),
            "left": self.getTimeLeft(),
            "confirmations": self.getConfirmations(),
            "charged_cnt": self.charged_count,
            "discharged_cnt": self.discharged_count,
            "txid": self.txid,
            "txid_history": ','.join(self.txids)
            }
        return(data)
    
    def toString(self):
        return(util.valuesToString(self.getInfo()))
    
    def toJson(self):
        return(util.valuesToJson(self.getInfo()))
    
    def isKnownTxId(self,txid):
        return(txid in self.txids)
    
    def topUp(self, lthn, msg="", txid=None, confirmations=None):
        """ TopUp authid. If lthn is zero, only update internal acls of services. If payment has same txid, only update confirmations"""
        if txid:
            if (self.isKnownTxId(txid)):
                self.confirmations=confirmations
                log.L.debug("Authid %s: Verified %s times." % (self.getId(), self.confirmations))
                return
            else:
                self.confirmations=0
                self.txids[txid] = txid
                self.txid = txid
                
        if (lthn > 0):
            self.balance += lthn
            self.lastmodify = time.time()
            self.lastcharge = time.time()
            self.charged_count += 1
            log.L.debug("Authid %s: Topup %.3f, new balance %.3f" % (self.getId(), lthn, self.balance))
            log.A.audit(log.A.AUTHID, log.A.MODIFY, paymentid=self.id, lthn="+%.3f" % (lthn)) 
        
        if self.isCreditOk() and not self.isActivated():
            self.activate()
        elif self.isCreditOk() and self.isActivated():
            log.L.info("Authid %s already activated." % (self.getId()))
        else:
            log.L.info("Authid %s has not enough credit." % (self.getId()))
           
    def startSpending(self):
        """ Start spending of authid """
        if (not self.spending):
            self.spending = time.time()
            log.L.debug("Authid %s: Start spending" % (self.getId()))
        
    def isSpending(self):
        """ If authid had at least one session, it is spending until zero. """
        return(self.spending)
    
    def spend(self, lthn, msg=""):
        """ Spend authid. If balance is not enough for given service, remove it from its acl. """
        if (lthn > 0):
            self.balance -= lthn
            self.lastmodify = time.time()
            self.overalltime += lthn/self.cost
            self.lastdisCharge = time.time()
            self.discharged_count += 1
            log.L.debug("Authid %s: Spent %f, new balance %f" % (self.getId(), lthn, self.balance))
            log.A.audit(log.A.AUTHID, log.A.MODIFY, paymentid=self.id, lthn="-%.3f" % (lthn))
        
        if not self.isCreditOk() and self.isActivated():
            self.deActivate()
                
    def spendTime(self, seconds):
        self.spend(self.cost * seconds / 60, "(%.2f minutes*%f)" % (seconds/60, self.cost))
        self.overalltime += seconds
            
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
    
    version = 2
    
    def __init__(self):
        self.authids = {}
        self.lastmodify = time.time()
        self.lastheight = 0
        
    def getVersion(self):
        if hasattr(self, 'version'):
            return(self.version)
        else:
            return(0)
        
    def add(self, payment):
        log.L.warning("New authid %s" % (payment.getId()))
        log.A.audit(log.A.AUTHID, log.A.ADD, paymentid=payment.getId(), lthn=payment.getBalance(), msg="init")
        self.authids[payment.getId()] = payment
        
    def update(self, auth_id, service_id, amount, confirmations, height=0, txid=None):
        if auth_id in self.authids.keys():
            # New payment for existing authid
            if (not self.authids[auth_id].isKnownTxId(txid)):
                self.topUp(auth_id, amount, msg="New txid %s" % (txid), txid=txid, confirmations=confirmations)
            else:
                # New confirmation for existing authid
                self.topUp(auth_id, 0, msg="Same txid", txid=txid, confirmations=confirmations)
        else:
            # First payment for new authid
            payment = AuthId(auth_id, service_id, amount, confirmations, height, txid)
            if not payment.invalid:
                self.add(payment)
    
    def topUp(self, paymentid, lthn, msg="", txid=None, confirmations=None):
        self.authids[paymentid].topUp(lthn, msg, txid, confirmations)

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
        p = self.get(paymentid)
        if (p):
            log.L.warning("Removing authid %s (balance=%.3f)" % (paymentid, p.getBalance()))
            log.A.audit(log.A.AUTHID, log.A.DEL, paymentid=paymentid, lthn=p.getBalance())
            p.getService().delAuthId(p)
            self.authids.pop(paymentid)
        
    def toString(self):
        str = "%d ids, last updated %s\npayment spending activated minutes_left\n" % (len(self.authids), util.timefmt(self.lastmodify))
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
        log.L.warning("Authids: %d ids, last updated %s" % (len(self.authids), util.timefmt(self.lastmodify)))
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
                log.L.info("Payment/confirmation for service %s, auth=%s, amount=%s, confirmations=%s, height=%s, txid=%s" % (service_id, auth_id, amount, confirmations, tx['height'], tx['txid']))

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
        if (config.Config.AUTHIDSFILE != "none"):
            try:
                self.lastmodify = time.time()
                log.L.debug("Saving authids db into %s" % (config.Config.AUTHIDSFILE))
                with open(config.Config.AUTHIDSFILE, 'wb') as output:
                    pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            except (OSError, IOError) as e:
                log.L.warning("Error writing authids db %s" % (config.Config.AUTHIDSFILE))
                sys.exit(2)
