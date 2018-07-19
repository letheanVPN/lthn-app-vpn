
import config
import logging
import os
import pickle
import services
import time
from util import *

AUTHIDS = None

class AuthId(object):
    """
    Single paymentid session class.
    All payments for given authid are in one session.
    """
    
    def __init__(self, authid, serviceid, balance):
        self.id = authid
        self.balance = 0
        self.serviceid = serviceid
        self.created = time.time()
        self.charged_count = 0
        self.lastmodify = time.time()
        if (services.SERVICES.get(serviceid)):
            self.cost = services.SERVICES.get(serviceid).getCost()
        else:
            logging.warning("Dropping authid %s (serviceid %s does not exists)" % (authid, serviceid))
            return(None)
        if (balance > 0):
            self.topUp(balance)
        self.discharged_count = 0
        
    def getId(self):
        return(self.id)

    def getServiceId(self):
        return(self.serviceid)
    
    def show(self):
        logging.info("""PaymentId %s:
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
    
    def topUp(self, itns):
        if (itns > 0):
            self.balance += itns
            self.lastmodify = time.time()
            self.lastcharge = time.time()
            self.charged_count += 1
            logging.debug("Authid %s: Topup %f, new balance %f" % (self.getId(), itns, self.balance))
        for s in services.SERVICES.getAll():
            services.SERVICES.get(s).addAuthId(self.getId())
    
    def spend(self, itns):
        if (itns > 0):
            self.balance -= itns
            self.lastmodify = time.time()
            self.lastdisCharge = time.time()
            self.discharged_count += 1
            logging.debug("Authid %s: Spend %f, new balance %f" % (self.getId(), itns, self.balance))
        if (self.balance <= 0):
            for s in services.SERVICES.getAll():
                services.SERVICES.get(s).delAuthId(self.getId())
                
    def spendTime(self, minutes):
        self.spend(self.cost * minutes)
            
    def getBalance(self):
        return(self.balance)
    
    def checkAlive(self):
        return(self.balance > 0)

class AuthIds(object):
    """Active AUTHIDS sessions container"""
    
    def __init__(self):
        self.authids = {}
        self.lastmodify = time.time()
        
    def add(self, paymentid):
        logging.warning("New authid %s" % (paymentid.getId()))
        self.authids[paymentid.getId()] = paymentid
        
    def update(self, paymentid):
        if paymentid.getId() in self.authids.keys():
            self.topUp(paymentid.getId(), paymentid.getBalance())
        else:
            self.add(paymentid)
    
    def topUp(self, paymentid, balance):
        self.authids[paymentid].topUp(balance)

    def spend(self, paymentid, balance):
        self.authids[paymentid].spend(balance)
        
    def get(self, paymentid):
        if (paymentid in self.authids.keys()):
            return(self.authids[paymentid])
        else:
            return(None)
        
    def getAll(self):
        return(self.authids.keys())

    def remove(self, paymentid):
        if (self.get(paymentid)):
            logging.warning("Removing authid %s (balance=%s)" % (paymentid, self.get(paymentid).getBalance()))
            self.spend(paymentid, self.get(paymentid).getBalance())
        
    def toString(self):
        str = "%d ids, last updated %s\n" % (len(self.authids), timefmt(self.lastmodify))
        for id, paymentid in self.authids.items():
            str = str + paymentid.getId() + "\n"
        return(str)
        
    def show(self):
        logging.warning("Authids: %d ids, last updated %s" % (len(self.authids), timefmt(self.lastmodify)))
        for id, paymentid in self.authids.items():
            paymentid.show()
        
    def cleanup(self):
        fresh = 0
        deleted = 0
        for id in list(self.authids.keys()):
            if not self.authids[id].checkAlive():
                self.remove(id)
                deleted += 1
            else:
                fresh += 1
        logging.info("Authids clean: %d deleted, %d fresh" % (deleted, fresh))
        
    def load(self):
        if (os.path.isfile(config.Config.AUTHIDSFILE)):
            try:
                logging.info("Trying to load authids db from %s" % (config.Config.AUTHIDSFILE))
                aids = pickle.load(open(config.Config.AUTHIDSFILE, "rb"))
                for id in aids.getAll():
                    aids.get(id).topUp(0)
                return(aids)
            except (OSError, IOError) as e:
                logging.warning("Error reading or creating authids db %s" % (config.Config.AUTHIDSFILE))
                sys.exit(2)
        else:
            self.save()

    def save(self):
        self.cleanup()
        self.lastmodify = time.time()
        logging.info("Saving authids db into %s" % (config.Config.AUTHIDSFILE))
        with open(config.Config.AUTHIDSFILE, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
