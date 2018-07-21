
import authids
import hashlib
import pprint
import log
import random
import services
import time

SESSIONS = None

class Session(object):
    
    def __init__(self, authid, srvid, conninfo, id=None):
        if (not id):
            str = "%s" % (random.random())
            id = hashlib.sha256(str.encode("utf-8")).hexdigest()
        self.id = id
        self.srvid = srvid
        self.authid = authid
        self.conninfo = conninfo
        log.A.audit(log.A.SESSION, log.A.ADD, self.id)
        self.started = time.time()
    
    def isAlive(self):
        return(authids.AUTHIDS.get(self.authid))
    
    def getTime(self):
        return(time.time() - self.started)
    
    def getId(self):
        return(self.id)

    def getServiceId(self):
        return(self.srvid)

    def getAuthId(self):
        return(self.authid)

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
        
    def get(self,id):
        if (id in self.sessions):
            return(self.sessions[id])
        else:
            return(None)
        
    def add(self, authid, ip, port, conninfo='', id=None):
        aid = authids.AUTHIDS.get(authid)
        if (aid):
            sid = aid.getServiceId()
            if not id:
                id = sid + ':' + ip + ':' + port
            session = Session(authid, aid.getServiceId(), conninfo, id)
            self.sessions[id] = session
                
    def remove(self, id):
        s = self.get(id)
        if (s):
            log.A.audit(log.A.SESSION, log.A.DEL, id)
            log.L.debug("Removing session " + id)
            self.sessions.pop(id)
            
    def refresh(self, looptime):
        deleted=0
        killed=0
        # Get all services
        for srv in services.SERVICES.getAll():
            # For eaach service, list sessions from its internal
            service = services.SERVICES.get(srv)
            service_sessions = service.getSessions()
            # Compare with our sessions - remove all sessions in our db which are not alive
            # Create array of living authids to spend
            aids = {}
            for sid in list(self.sessions):
                sess = self.get(sid)
                aids[sid] = sess.getAuthId()
                if (sess.getServiceId() == srv) and (sid not in service_sessions):
                    deleted = deleted + 1
                    self.remove(sid)
                elif not sess.isAlive():
                    # If session is not alive (spended authid), delete it from db and kill session from service
                    self.remove(sid)
                    service.killSession(service_sessions[sid])
                    killed = killed + 1
                    deleted = deleted + 1
            # For all alive authids, spend time for last loop
            for aid in aids:
                aids[aid].spendTime(looptime)
            # List all active sessions in our db
            for sid in service_sessions.keys():
                sess = self.get(sid)
                if not sess:
                    # Session does not exists in our db - kill it.
                    service.killSession(service_sessions[sid])
                    killed = killed + 1
        log.L.info("Sessions refresh: %d deleted, %d killed, %d fresh" % (deleted, killed, len(self.sessions)))
     
    def toString(self):
        str = "%d sessions\n" % (len(self.sessions))
        for s in self.sessions:
                    str = str + "%s %s %s\n" % (self.sessions[s].getId(), self.sessions[s].getServiceId(), self.sessions[s].getAuthId())
        return(str)
    
    