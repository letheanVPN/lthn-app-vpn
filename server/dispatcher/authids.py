
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

AUTHIDS = None

class AuthId(object):
    """
    Single paymentid session class.
    All payments for given authid are in one session.
    """
    
    def __init__(self, authid, serviceid, balance, verifications, msg=""):
        self.id = authid
        self.balance = 0
        self.serviceid = serviceid
        self.verifications = verifications
        self.created = time.time()
        self.charged_count = 0
        self.lastmodify = time.time()
        if (services.SERVICES.get(serviceid)):
            self.cost = services.SERVICES.get(serviceid).getCost()
        else:
            log.L.error("Dropping authid %s (serviceid %s does not exists)" % (authid, serviceid))
            #log.A.audit(log.A.AUTHID, log.A.DEL, authid, "Serviceid %s does not exists" % (serviceid))
            return(None)
        if (balance > 0):
            self.topUp(balance)
        log.A.audit(log.A.AUTHID, log.A.ADD, authid, "init, balance=%s, verifications=%s" % (balance,verifications))
        self.discharged_count = 0
        
    def getId(self):
        return(self.id)
    
    def getBalance(self):
        return(self.balance)
    
    def getVerifications(self):
        return(self.verifications)

    def getServiceId(self):
        return(self.serviceid)
    
    def show(self):
        log.L.info("""PaymentId %s:
            serviceid %s,
            created at %s
            modified at %s
            balance %f
            cost per minute %f
            minutes left %f
            charged_count %d
            discharged_count %d
            """ % (self.id, self.serviceid, timefmt(self.created), timefmt(self.lastmodify), self.balance, self.cost, self.balance / self.cost, self.charged_count, self.discharged_count))
    
    def toString(self):
        str = "%s: serviceid=%s, created=%s,modified=%s, balance=%f, perminute=%f, minsleft=%f, charged_count=%d, discharged_count=%d\n" % (self.id, self.serviceid, timefmt(self.created), timefmt(self.lastmodify), self.balance, self.cost, self.balance / self.cost, self.charged_count, self.discharged_count)
        return(str)
    
    def topUp(self, itns, msg="", verifications=None):
        """ TopUp authid. If itns is zero, only update internal acls of services. If verifications is set, it is updated. """
        if verifications:
            self.verifications = verifications
        if (itns > 0):
            self.balance += itns
            self.lastmodify = time.time()
            self.lastcharge = time.time()
            self.charged_count += 1
            log.L.debug("Authid %s: Topup %f, new balance %f" % (self.getId(), itns, self.balance))
            log.A.audit(log.A.AUTHID, log.A.MODIFY, self.id, "topup,amount=%s,balance=%s %s" % (itns, self.balance, msg))
        for s in services.SERVICES.getAll():
            services.SERVICES.get(s).addAuthIdIfTopup(self)
    
    def spend(self, itns, msg=""):
        """ Spend authid. If balance is not enough for given service, remove it from its acl. """
        if (itns > 0):
            self.balance -= itns
            self.lastmodify = time.time()
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
        return(self.balance > 0)

class AuthIds(object):
    """Active AUTHIDS sessions container"""
    
    def __init__(self):
        self.authids = {}
        self.lastmodify = time.time()
        self.lastheight = 0
        
    def add(self, paymentid):
        log.L.warning("New authid %s" % (paymentid.getId()))
        self.authids[paymentid.getId()] = paymentid
        
    def update(self, paymentid):
        if paymentid.getId() in self.authids.keys():
            self.topUp(paymentid.getId(), paymentid.getBalance(), paymentid.getVerifications())
        else:
            self.add(paymentid)
    
    def topUp(self, paymentid, balance, verifications, msg=""):
        self.authids[paymentid].topUp(balance, msg)

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
            log.L.warning("Removing authid %s (balance=%s)" % (paymentid, self.get(paymentid).getBalance()))
            log.A.audit(log.A.AUTHID,log.A.DEL,paymentid, "%s" % (self.get(paymentid).getBalance()))
            for s in services.SERVICES.getAll():
                services.SERVICES.get(s).delAuthId(paymentid)
            self.authids.pop(paymentid)
        
    def toString(self):
        str = "%d ids, last updated %s\n" % (len(self.authids), timefmt(self.lastmodify))
        for id, paymentid in self.authids.items():
            str = str + paymentid.getId() + "\n"
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

    def walletJSONCall(method, height):
        d = {
            "id": "0",
            "method": method,
            "jsonrpc": "2.0",
            "params": {
                "in": True,
                "filter_by_height": True,
                "min_height": height,
                "max_height": 99999999
            }
        }
        # TODO put url, user and pass in config
        url = "http://127.0.0.1:13660/json_rpc"
        log.L.info("Calling RPC " + url)
        r = requests.post(url, data=json.dumps(d), auth=HTTPDigestAuth("dispatcher", "547fth87t2ytgj"), headers={"Content-Type": "application/json"})
        if (r.status_code == 200):
            return(r.text)
        else:
            log.L.warning("RPC error %s!" % (r.status_code))
            return(None)

    def getHeighFromWallet(self):
        """
        We should connect to wallet or daemon and get actual height
        Whe we loaded authids from disk, we will use last height processed but if we have clean db, we need to start here.
        """
        # TODO even though it works with hardcoded height, best to get the real starting eight
        return(100000)

    def getFromWallet(self):
        """
        Connect to wallet and ask for all self.authids from last height.
        """
        if (self.lastheight==0):
            self.lastheight = self.getHeighFromWallet()
        
        res = json.loads(walletJSONCall("get_vpn_transfers", self.lastheight))
        if (res['result']['in']):
            for tx in res['result']['in']:
                if (tx['height'] > self.lastheight):
                    self.lastheight = tx['height']

                service_id = tx['payment_id'][0:2]
                auth_id = tx['payment_id'][2:16]
                amount = tx['amount'] / 100000000
                log.L.info("Got payment for service " + service_id + " auth " + auth_id + " amount " + amount)

                # Create authid object from wallet
                s1 = AuthId(auth_id, service_id, amount, 1, "")
                # If serviceid is not alive, false will be returned and it will be automatically logged
                if (s1):
                    # This function will update authids db. Either it will add new if it does not exists or it will toupu existing.
                    # Internal logic is automatically applied to activate or not in corresponding services
                    self.update(s1)
            self.lastheight++
        
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

