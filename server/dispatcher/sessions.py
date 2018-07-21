
import authids
import hashlib
import pprint
import log
import random
import services
import time

SESSIONS = None

class Session(object):
    
    def __init__(self, authid, srvid, ip, port, id=None):
        if (not id):
            id = "%s:%s:%s:%s" % (srvid, authid, ip, port)
        self.id = id
        self.srvid = srvid
        self.authid = authid
        self.ip = ip
        self.port = port
        log.A.audit(log.A.SESSION, log.A.ADD, self.id, "service=%s,ip=%s,port=%s" % (srvid, ip, port))
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
        
    def get(self, id):
        if (id in self.sessions):
            return(self.sessions[id])
        else:
            return(None)
        
    def find(self, srv, ip, port):
        for s in self.sessions:
            sess = self.get(s)
            if (sess.ip == ip and sess.port == port and sess.srvid == srv):
                return(sess.getId())
        
    def add(self, authid, ip, port, conninfo='', id=None):
        aid = authids.AUTHIDS.get(authid)
        if (aid):
            sid = aid.getServiceId()
            session = Session(authid, sid, ip, port, id)
            self.sessions[session.getId()] = session
                
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
                aids[sess.getAuthId()] = sid
                if (sess.getServiceId() == srv) and ((sess.ip + ':' + sess.port) not in service_sessions):
                    # Session in ur db is stale
                    deleted = deleted + 1
                    self.remove(sid)
                elif not sess.isAlive():
                    # If session should not be alive (spended authid), delete it from db and kill session from service
                    self.remove(sid)
                    if (sess.ip + ':' + sess.port) in service_sessions:
                        service.killSession(service_sessions[sess.ip + ':' + sess.port])
                        killed = killed + 1
                        deleted = deleted + 1
            # For all alive authids, spend time for last loop
            for aid in aids:
                authid = authids.AUTHIDS.get(aid)
                if authid:
                    authid.spendTime(looptime)
            # List all active sessions in our db
            for sid in service_sessions.keys():
                ss = service_sessions[sid]
                if ("id" in ss):
                    sess = self.find(srv, ss['ip'], ss['port'])
                    if not sess:
                        # Session does not exists in our db - kill it.
                        service.killSession(ss['id'])
                        killed = killed + 1
        log.L.info("Sessions refresh: %d deleted, %d killed, %d fresh" % (deleted, killed, len(self.sessions)))
     
    def toString(self):
        str = "%d sessions\n" % (len(self.sessions))
        for s in self.sessions:
                    str = str + "%s %s %s\n" % (self.sessions[s].getId(), self.sessions[s].getServiceId(), self.sessions[s].getAuthId())
        return(str)
    
    