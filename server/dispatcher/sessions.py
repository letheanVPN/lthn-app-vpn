
import time
import authids
import services
import pprint
import random
import hashlib

SESSIONS = None

class Session(object):
    
    def __init__(self, authid, srvid, conninfo):
        str = "%s" % (random.random())
        self.id = hashlib.sha256(str.encode("utf-8")).hexdigest()
        self.conninfo = conninfo
        self.started = time.time()
        
    def getTime(self):
        return(time.time() - self.started)
    
    def getId(self):
        return(self.id)
    
    def getInfo(self):
        return(self.conninfo)
    
    def toString(self):
        str = "%s: serviceid=%s, created=%s,modified=%s, balance=%f, perminute=%f, minsleft=%f, charged_count=%d, discharged_count=%d\n" % (self.id, self.serviceid, timefmt(self.created), timefmt(self.lastmodify), self.balance, self.cost, self.balance / self.cost, self.charged_count, self.discharged_count)
        return(str)


class Sessions(object):
    """
    Active sessions class. Session means connected client
    """
    
    def __init__(self):
        self.sessions = {}
        self.count = 0
        
    def add(self, authid, conninfo):
        aid = authids.AUTHIDS.get(authid)
        if (aid):
            session = Session(authid, aid.getServiceId(), conninfo)
            sid = aid.getServiceId()
            if sid not in self.sessions:
                self.sessions[sid]={}
            self.count = self.count + 1
            if authid not in self.sessions[sid]:
                self.sessions[sid][authid] = { session }
            else:
                self.sessions[sid][authid].append(session) 
     
    def toString(self):
        str = "%d sessions\n" % (self.count)
        for srvid in self.sessions.keys():
            for aid in self.sessions[srvid].keys():
                for s in self.sessions[srvid][aid]:
                    str = str + "%s %s %s\n" % (s.getId(), aid, srvid)
        return(str)
    
    