from service import Service
import os
import socket
import logging
import re
import authids
import services
import sessions

class ServiceMgmt(Service):
    
    def __init__(self, s):
        self.flog = s
        self.id  = "MS"
        self.name = "Mgmt"
        self.type = "management"
        self.mgmtip = "socket"
        self.mgmtport = s
        self.mgmtfile = s
        if (os.path.exists(s)):
            os.remove(s)
        self.mgmt = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.mgmt.bind(s)
        self.mgmt.listen(1)
        self.mgmt.setblocking(0)
        logging.warning("Started service %s[%s]" % (self.name, self.id))
        
    def orchestrate(self):
        try:
            self.conn, addr = self.mgmt.accept()
            if (self.conn):
                s = self.mgmtRead()
        except OSError as o:
            pass
            
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
            logging.debug("%s[%s]-mgmt-in: %s" % (self.type, self.id, repr(line)))
            self.mgmtEvent(line)
            return(line)
        else:
            return(None)
        
    def mgmtWrite(self, msg, inside=None):
        try:
            logging.debug("%s[%s]-mgmt-out: %s" % (self.type, self.id, repr(msg)))
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
            if (authids.AUTHIDS.get(a)):
                self.showAuthId(a)
            else:
                self.mgmtWrite("Bad authid.")
            self.conn.close()
            return()
        p = re.search("^show authid$", msg)
        if (p):
            self.showAuthIds()
            self.conn.close()
            return()
        p = re.search("^topup (.*) (.*)", msg)
        if (p):
            a = p.group(1)
            i = p.group(2)
            self.topUpAuthId(a, i)
            self.conn.close()
            return()
        p = re.search("^spend (.*) (.*)", msg)
        if (p):
            a = p.group(1)
            i = p.group(2)
            self.spendAuthId(a, i)
            self.conn.close()
            return()
        p = re.search("^add authid (.*) (.*)", msg)
        if (p):
            a = p.group(1)
            s = p.group(2)
            self.addAuthId(a, s)
            self.conn.close()
            return()
        p = re.search("^del authid (.*)", msg)
        if (p):
            a = p.group(1)
            self.delAuthId(a)
            self.conn.close()
            return()
        p = re.search("^del authid (.*)", msg)
        if (p):
            a = p.group(1)
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
        p = re.search("^del session (.*)", msg)
        if (p):
            s = p.group(1)
            self.delSessions(s)
            self.conn.close()
            return()
        p = re.search("^help", msg)
        if (not p):
            self.mgmtWrite("Unknown command!\n")
        self.mgmtWrite("show authid [authid]\n")
        self.mgmtWrite("show session [sessionid]\n")
        self.mgmtWrite("del session sessionid\n")
        self.mgmtWrite("topup authid itns\n")
        self.mgmtWrite("spend authid itns\n")
        self.mgmtWrite("add authid serviceid\n")
        self.mgmtWrite("del authid authid\n")
        self.conn.close()
        return()
        
    def showSessions(self):
        self.mgmtWrite(sessions.SESSIONS.toString())
        
    def showSession(self, id):
        if sessions.SESSIONS.get(id):
            self.mgmtWrite(sessions.SESSIONS.get(id).toString())
        
    def showAuthIds(self):
        self.mgmtWrite(authids.AUTHIDS.toString())
    
    def showAuthId(self,id):
        if authids.AUTHIDS.get(id):
            self.mgmtWrite(authids.AUTHIDS.get(id).toString())
        
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
            self.mgmtWrite("Removed (" + authids.AUTHIDS.get(id).toString() + ")\n")
            authids.AUTHIDS.remove(id)
        else:
            self.mgmtWrite("Bad authid?\n")
        
    def topUpAuthId(self, id, itns):
        if (authids.AUTHIDS.get(id)):
            authids.AUTHIDS.get(id).topUp(int(itns))
            self.mgmtWrite("TopUp (" + authids.AUTHIDS.get(id).toString() + ")\n")
        else:
            self.mgmtWrite("Bad authid?\n")
    
    def spendAuthId(self, id, itns):
        if (authids.AUTHIDS.get(id)):
            authids.AUTHIDS.get(id).spend(int(itns))
            self.mgmtWrite("Spent (" + authids.AUTHIDS.get(id).toString() + ")\n")
        else:
            self.mgmtWrite("Bad authid?\n")
            
    def stop(self):
        if (os.path.exists(self.flog)):
            os.remove(self.flog)
        logging.warning("Stopped service %s[%s]" % (self.name, self.id))

