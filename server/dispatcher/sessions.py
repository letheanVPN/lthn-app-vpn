
import time

class Sessions(object):
    """
    Active sessions class. Session means connected client
    """
    
    def __init__(self, authids):
        self.authids = authids
        self.data = {}
        
    def startedHa(self, authid, conninfo):
        paymentid = self.authids.get(authid)
        if not paymentid:
            logging.error("AuthId %s not in database!" % (authid))
            return(None)
        if not (authid in self.data):
            self.data[authid] = {"type": "haproxy", "started": time.time(), "conninfo": conninfo}
        
    def startedOvpn(self, authid, conninfo):
        paymentid = self.authids.get(authid)
        if not paymentid:
            logging.error("AuthId %s not in database!" % (authid))
            return(None)
        if not (authid in self.data):
            self.data[authid] = {"type": "vpn", "started": time.time(), "conninfo": conninfo}
        
    def stoppedHa(self, authid):
        paymentid = self.authids.get(authid)
        if not paymentid:
            logging.error("AuthId %s not in database!" % (authid))
            return(None)
        if authid in self.data.keys():
            conntime = (time.time()-self.data[authid]["started"]) / 60
            paymentid.spend(conntime)
    
    def stoppedOvpn(self, authid):
        paymentid = self.authids.get(authid)
        if not paymentid:
            logging.error("AuthId %s not in database!" % (authid))
            return(None)
        if authid in self.data.keys():
            conntime = (time.time()-self.data[authid]["started"]) / 60
            paymentid.spend(conntime)
            
    def updateOvpnSessions(self):
        self.startedOvpn(self, "authid8")

    def updateHaSessions(self):
        self.startedHaSession("authid1")
        