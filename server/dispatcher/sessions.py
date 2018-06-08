
import time

SESSIONS = None

class Sessions(object):
    """
    Active sessions class. Session means connected client
    """
    
    def __init__(self):
        self.ha={}
        self.ovpn={}
        
    def startedHa(self, authid, conninfo):
        self.ha[authid]=1
        
    def startedOvpn(self, authid, conninfo):
        self.ovpn[authid]=1
        
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
        