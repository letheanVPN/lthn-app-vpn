from service import Service
import config
import os
import select
import socket
import logging
import syslogmp
import sessions
import re

class ServiceSyslog(Service):
    
    def __init__(self, s):
        self.flog = s
        self.id  = "SS"
        self.name = "Syslog server"
        self.type = "syslog"
        if (os.path.exists(s)):
            os.remove(s)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(s)
        self.sock.settimeout(self.SOCKET_TIMEOUT)
        logging.warning("Started service %s[%s]" % (self.name, self.id))
        
    def orchestrate(self):
        s = self.getLine()
        while (s != None):
            message = syslogmp.parse(s)
            if (message):
                msg = message.message.decode("utf-8")
                logging.debug("syslog: " + repr(msg))
                # '127.0.0.1:52784 [19/Jul/2018:16:51:19.461] cleartunnel preproxy/<NOSRV> 0/-1/-1/-1/+1 403 +188 - - PR-- 0/0/0/0/2 0/0 {authida1} "GET http://www.seznam.cz/ HTTP/1.1"\n'
                p = re.search(
                    "(^\d*\.\d*\.\d*\.\d*):(\d*) " # Host and port
                    + "\[(.*)\] " # Date
                    + "(\w*) " # Frontend
                    + "(\w*)/(<?\w*>?) "  # Backend/Server
                    + "(.\d*/.\d*/.\d*/.\d*/.\d*) " # Times
                    + "(\d*) " # State
                    + ".*" # Not needed
                    + "{(.*)}" # authid
                    , msg)
                if (p):
                    ip = p.group(1)
                    port = p.group(2)
                    dte = p.group(3)
                    frontend = p.group(4)
                    backend = p.group(5)
                    server = p.group(6)
                    code = p.group(8)
                    authid = p.group(9)
                    sessions.SESSIONS.add(authid, { ip:ip, port:port})
            s = self.getLine()
        
    def getLine(self):
        try:
            return(self.sock.recv(2048))
        except socket.timeout:
            return(None)

    def stop(self):
        if (os.path.exists(self.flog)):
            os.remove(self.flog)
        logging.warning("Stopped service %s[%s]" % (self.name, self.id))
