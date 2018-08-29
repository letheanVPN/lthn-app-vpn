from service import Service
import os
import socket
import log
import re
import authids
import services
import sessions
import config

class ServiceMgmt(Service):
    
    def __init__(self, s):
        self.id  = "MS"
        self.name = "Mgmt"
        self.type = "management"
        self.mgmtip = "socket"
        self.mgmtport = s
        self.mgmtfile = s
        self.pidfile = None
        self.process = None
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        self.mgmt = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.mgmt.bind(self.mgmtfile)
        self.mgmt.listen(1)
        self.mgmt.setblocking(0)
        
    def orchestrate(self):
        try:
            self.conn, addr = self.mgmt.accept()
            if (self.conn):
                s = self.mgmtRead()
        except OSError as o:
            pass
        
    def mgmtConnect(self):
            return
        
    def mgmtRead(self, inside=None):
        line = ""
        try:
            line = self.conn.recv(8192).decode("utf-8")
        except socket.timeout:
            pass
        except OSError as o:
            pass
        else:
            pass
        if (line != ""):
            log.L.debug("%s[%s]-mgmt-in: %s" % (self.type, self.id, repr(line)))
            self.mgmtEvent(line)
            return(line)
        else:
            return(None)
        
    def mgmtWrite(self, msg, inside=None):
        try:
            log.L.debug("%s[%s]-mgmt-out: %s" % (self.type, self.id, repr(msg)))
            self.conn.send(msg.encode("utf-8"))
        except socket.timeout:
            pass
        except OSError as o:
            pass
        else:
            pass
        
    def mgmtEvent(self, msg):
        p = re.search("^show authid (.*)", msg)
        if (p):
            a = p.group(1)
            self.showAuthId(a)
            self.conn.close()
            return()
        p = re.search("^show authid$", msg)
        if (p):
            self.showAuthIds()
            self.conn.close()
            return()
        p = re.search("^topup (.*) (.*)", msg)
        if (p):
            a = p.group(1).upper()
            i = float(p.group(2))
            self.topUpAuthId(a, i)
            self.conn.close()
            return()
        p = re.search("^spend (.*) (.*)", msg)
        if (p):
            a = p.group(1).upper()
            i = float(p.group(2))
            self.spendAuthId(a, i)
            self.conn.close()
            return()
        p = re.search("^startspend (.*)", msg)
        if (p):
            a = p.group(1).upper()
            self.startSpendAuthId(a)
            self.conn.close()
            return()
        p = re.search("^add authid (.*) (.*)", msg)
        if (p):
            a = p.group(1).upper()
            s = p.group(2).upper()
            self.addAuthId(a, s)
            self.conn.close()
            return()
        p = re.search("^del authid (.*)", msg)
        if (p):
            a = p.group(1).upper()
            self.delAuthId(a)
            self.conn.close()
            return()
        p = re.search("^del authid (.*)", msg)
        if (p):
            a = p.group(1).upper()
            self.delAuthId(a)
            self.conn.close()
            return()
        p = re.search("^show session (.*)", msg)
        if (p):
            s = p.group(1)
            self.showSession(s)
            self.conn.close()
            return()
        p = re.search("^show session$", msg)
        if (p):
            self.showSessions()
            self.conn.close()
            return()
        p = re.search("^kill session (.*)", msg)
        if (p):
            s = p.group(1)
            self.delSession(s)
            self.conn.close()
            return()
        p = re.search("^refresh$", msg)
        if (p):
            config.Config.FORCE_REFRESH = True
            self.mgmtWrite("Forcing refresh of authids and sessions now.\n")
            self.conn.close()
            return()
        p = re.search("^save$", msg)
        if (p):
            if (config.CONFIG.AUTHIDSFILE != ""):
                config.Config.FORCE_SAVE = True
                self.mgmtWrite("Forcing save of authids now.\n")
            else:
                self.mgmtWrite("Authids save is not enabled.\n")
            self.conn.close()
            return()
        p = re.search("^loglevel (DEBUG|INFO|WARNING|ERROR)", msg)
        if (p):
            s = p.group(1)
            log.L.setLevel(s)
            self.mgmtWrite("Log level set to %s.\n" % (s))
            self.conn.close()
            return()
        p = re.search("^help", msg)
        if (not p):
            self.mgmtWrite("Unknown command!\n")
        self.mgmtWrite("show authid [authid]\n")
        self.mgmtWrite("show session [sessionid]\n")
        self.mgmtWrite("kill session <sessionid>\n")
        self.mgmtWrite("topup <authid> <itns>\n")
        self.mgmtWrite("spend <authid> <itns>\n")
        self.mgmtWrite("startspend <authid>\n")
        self.mgmtWrite("add authid <authid> <serviceid>\n")
        self.mgmtWrite("del authid <authid>\n")
        self.mgmtWrite("loglevel {DEBUG|INFO|WARNING|ERROR}\n")
        self.mgmtWrite("refresh\n")
        self.mgmtWrite("cleanup\n")
        self.conn.close()
        return()
        
    def showSessions(self):
        self.mgmtWrite(sessions.SESSIONS.toString())
        
    def showSession(self, id):
        if sessions.SESSIONS.get(id):
            self.mgmtWrite(sessions.SESSIONS.get(id).toString())
    
    def delSession(self, id):
        s = sessions.SESSIONS.get(id)
        if s:
            srv = services.SERVICES.get(s.getServiceId())
            service_sessions = srv.getSessions()
            killed = 0
            for sid in service_sessions.keys():
                ss = service_sessions[sid]
                if ("id" in ss):
                    sess = sessions.SESSIONS.find(s.getServiceId(), ss['ip'], ss['port'])
                    if sess:
                        # Session does not exists in our db - kill it.
                        services.SERVICES.get(s.getServiceId()).killSession(sid)
                        self.mgmtWrite("Killed session %s (%s:%s)\n" % (sid, ss['ip'], ss['port']))
                        killed = 1
            if (killed==0):
                self.mgmtWrite("Session %s not found!\n" % (sid))
            
    def showAuthIds(self):
        self.mgmtWrite(authids.AUTHIDS.toString())
    
    def showAuthId(self,id):
        if authids.AUTHIDS.get(id):
            self.mgmtWrite(authids.AUTHIDS.get(id).toString())
        else:
            self.mgmtWrite("Bad Authid.\n")
        
    def addAuthId(self, id, sid):
        if (authids.AUTHIDS.get(id)):
            self.mgmtWrite("This authid already exists!\n")
        else:
            if (services.SERVICES.get(sid)):
                authid = authids.AuthId(id, sid, 100000)
                authids.AUTHIDS.update(authid)
                self.mgmtWrite("Added (" + authid.toString() + ")\n")
            else:
                self.mgmtWrite("Bad serviceid?\n")
                
    def delAuthId(self, id):
        if (authids.AUTHIDS.get(id)):
            self.mgmtWrite("Deleted (" + authids.AUTHIDS.get(id).toString() + ")\n")
            authids.AUTHIDS.remove(id)
        else:
            self.mgmtWrite("Bad authid?\n")
        
    def topUpAuthId(self, id, itns):
        if (authids.AUTHIDS.get(id)):
            authids.AUTHIDS.get(id).topUp(float(itns), "MGMT")
            self.mgmtWrite("TopUp (" + authids.AUTHIDS.get(id).toString() + ")\n")
        else:
            self.mgmtWrite("Bad authid?\n")
    
    def spendAuthId(self, id, itns):
        if (authids.AUTHIDS.get(id)):
            authids.AUTHIDS.get(id).spend(float(itns), "MGMT")
            self.mgmtWrite("Spent (" + authids.AUTHIDS.get(id).toString() + ")\n")
        else:
            self.mgmtWrite("Bad authid?\n")
    
    def startSpendAuthId(self, id):
        if (authids.AUTHIDS.get(id)):
            authids.AUTHIDS.get(id).startSpending()
            self.mgmtWrite("Spending.\n")
        else:
            self.mgmtWrite("Bad authid?\n")
            
    def stop(self):
        super().stop()

