import hashlib
import pprint
import random
import time
from lthnvpn.lib import authids, log, services


SESSIONS = None

class Session(object):
    
    def __init__(self, authid, srvid, ip, port, method=None, uri=None, proto=None, id=None, msg=None):
        if (not id):
            id = "%s:%s:%s:%s" % (srvid, authid, ip, port)
        self.id = id
        self.srvid = srvid
        self.authid = authid
        self.ip = ip
        self.port = port
        log.A.audit(log.A.SESSION, log.A.ADD, sessionid=self.id, serviceid=srvid, srcip=ip, srcport=port, method=method, uri=uri, msg=msg)
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
        return("")
    
    def toString(self):
        str = "%s: serviceid=%s, info=%s, created=%s,modified=%s, balance=%f, perminute=%f, minsleft=%f, charged_count=%d, discharged_count=%d\n" % (self.id, self.serviceid, self.conninfo, timefmt(self.created), timefmt(self.lastmodify), self.balance, self.cost, self.balance / self.cost, self.charged_count, self.discharged_count)
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
        
    def find(self, srv=None, ip=None, port=None, authid=None):
        if (srv and ip and port):
            for s in self.sessions:
                sess = self.get(s)
                if (sess.ip == ip and sess.port == port and sess.srvid == srv):
                    return(sess.getId())
        elif (srv and authid):
            for s in self.sessions:
                sess = self.get(s)
                if (sess.authid == authid and sess.srvid == srv):
                    return(sess.getId())
        elif (authid):
            for s in self.sessions:
                sess = self.get(s)
                if (sess.authid == authid):
                    return(sess.getId())
        else:
                return(None)
            
    def add(self, authid, ip, port, method=None, uri=None, proto=None, id=None, msg=None):
        aid = authids.AUTHIDS.get(authid)
        if (aid):
            sid = aid.getServiceId()
            session = Session(authid, sid, ip, port, method=method, uri=uri, proto=proto, id=id, msg=msg)
            self.sessions[session.getId()] = session
        else:
            log.L.warning("Ignoring session with unknown authid %s!" % (authid))
                
    def remove(self, id, msg=''):
        s = self.get(id)
        if (s):
            log.A.audit(log.A.SESSION, log.A.DEL, sessionid=id, msg=s.getInfo() + ' ' + msg)
            log.L.debug("Removing session " + id)
            self.sessions.pop(id)
        else:
            log.L.warning("Unknow sid (%s)to remove??" % (id))
            
    def refresh(self, looptime):
        deleted=0
        killed=0
        spent = 0
        notspent = 0
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
                authid = sess.getAuthId()
                aids[authid] = sid
                tobedeleted = None
                if (sess.getServiceId() == srv) and ((sess.ip + ':' + sess.port) not in service_sessions):
                    # Session in our db is stale
                    deleted = deleted + 1
                    tobedeleted = 'Session not active in service'
                elif not sess.isAlive():
                    # If session should not be alive (spent authid), delete it from db and kill session from service
                    tobedeleted = 'Session is not alive (spent authid)'
                    if (sess.ip + ':' + sess.port) in service_sessions:
                        service.killSession(service_sessions[sess.ip + ':' + sess.port], 'Spent: ' + sess.conninfo)
                        killed = killed + 1
                        deleted = deleted + 1
                aid = authids.AUTHIDS.get(authid)
                if self.find(authid=authid):
                    aid.startSpending()
                if tobedeleted:
                    self.remove(sid, tobedeleted)
            # List all active sessions in our db per service
            for sid in service_sessions.keys():
                ss = service_sessions[sid]
                if ("id" in ss):
                    sess = self.find(srv=srv, ip=ss['ip'], port=ss['port'])
                    if not sess:
                        # Session does not exists in our db - kill it.
                        service.killSession(ss['id'],'Inactive session')
                        killed = killed + 1
        for authid in authids.AUTHIDS.getAll():
            aid = authids.AUTHIDS.get(authid)
            if aid.isSpending():
                aid.spendTime(looptime)
                spent = spent + 1
            else:
                notspent = notspent + 1
        log.L.info("Sessions refresh: %d fresh, %d deleted, %d killed, %d spent authids, %d notspent authids" % (len(self.sessions), deleted, killed, spent, notspent))
     
    def toString(self):
        str = "%d sessions\n" % (len(self.sessions))
        for s in self.sessions:
                    str = str + "%s %s %s\n" % (self.sessions[s].getId(), self.sessions[s].getServiceId(), self.sessions[s].getAuthId())
        return(str)
    
    
