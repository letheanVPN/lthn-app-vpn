#!/usr/bin/env python

import ed25519
import getopt
import json
import os
import pickle
from pprint import pprint
import sys

class Session(object):
    """
    Single paymentid session class.
    All payments for given paymentid are in one session.
    """
    
    def __init__(self, authid, price, balance):
        self.id = authid
        self.balance = balance
        self.price = price
        self.created = time()
        
    def getId(self):
        return(self.id)

    def show(self):
        print("PaymentId %s created at %s with balance %f and price %f per minute (%f minutes left).\n" % {self.id, self.created, self.balance, self.price, self.balance/self.price})
        
    def charge(self, balance):
        self.balance += balance
        self.lastModify = time()
        self.lastCharge = time()
    
    def disCharge(self, minutes):
        self.balance -= (self.price * minutes)
        self.lastModify = time()
        self.lastDisCharge = time()
        
    def checkAlive(self):
        return(self.balance > 0)

class Sessions(object):
    """Active sessions container"""
    
    def __init__(self):
        payments = {}
        
    def add(self, paymentid):
        self.payments[paymentid.getId()] = paymentid
        
    def charge(self, paymentid, balance):
        self.payments[paymentid].charge(balance)

    def disCharge(self, paymentid, balance):
        self.payments[paymentid].disCharge(balance)
        
    def exists(self,paymentid):
        return(paymentid in self.payments)

    def remove(self, paymentid):
        self.payments.pop(paymentid.getId())
        
    def show(self):
        print(self.payments.keys())
        
    def cleanup(self):
        for id, paymentid in self.payments.items():
            if paymentid.checkAlive():
                self.payments.pop(id)
                
    def save(self, filename):
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
            
class Config(object):
    """Configuration container"""
    
    def load(self, filename):
        self.data = json.load(open(filename))
        
    def get(self, key):
        idx=""
        for k in key.split("."):
            idx+="['"+k+"']"
        try: 
            exec("ret=self.data%s" % (idx))
        except KeyError:
            return(None)
        else:
            return(ret)

class SDP(object):
    """SDP functions"""
    
    def load(self, filename):
        self.data = json.load(open(filename))
        
def get_payments(height):
    """Connect to wallet and ask for all payments from last height"""
    
    payments={"id1": {"amount":"10"}}
    for key,value in payments:
        if sessions.exists(key):
            sessions.charge(key,value["amount"])
        else:
            sessions.add(key,value["amount"])
    
def main(argv):
    if (os.getenv('ITNSVPN_SYSCONFDIR')):
        configfile = os.getenv('ITNSVPN_SYSCONFDIR') + "/dispatcher.json"
        sdpfile = os.getenv('ITNSVPN_SYSCONFDIR') + "/sdp.json"
    else:
        configfile = '/opt/itns/etc/dispatcher.json'
        sdpfile = '/opt/itns/etc/sdp.json'
    try:
        opts, args = getopt.getopt(argv, "hf:s:", ["help", "config=", "sdp="])
    except getopt.GetoptError:
        print 'itnsvpnd.py -h'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print 'itnsvpnd.py [-h] [-f dispatcher.json] [-s sdp.json]'
            sys.exit()
        elif opt in ("-f", "--config"):
            configfile = arg
        elif opt in ("-s", "--sdp"):
            sdpfile = arg
          
    config = Config()
    config.load(configfile)
    
    sdp = SDP()
    sdp.load(sdpfile)
    
    sessions = Sessions()
    
    while ():
        
    
if __name__ == "__main__":
    main(sys.argv[1:])