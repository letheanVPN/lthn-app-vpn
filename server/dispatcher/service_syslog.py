from service import Service
import config
import os
import select
import socket
import log
import syslogmp
import sessions
import re

class ServiceSyslog(Service):
    
    def __init__(self, s):
        self.flog = s
        self.id  = "SS"
        self.name = "Syslog server"
        self.type = "syslog"
        self.mgmtfile = None
        self.process = None
        self.pidfile = None
        if (os.path.exists(s)):
            os.remove(s)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(s)
        self.sock.settimeout(self.SOCKET_TIMEOUT)
        log.L.warning("Started service %s[%s]" % (self.name, self.id))
        
    def orchestrate(self):
        s = self.getLine()
        while (s != None):
            message = syslogmp.parse(s)
            if (message):
                msg = message.message.decode("utf-8")
                log.L.debug("syslog: " + repr(msg))
                # '1.2.3.4:46759 [16/Aug/2018:13:37:28.876] ssltunnel~ b-preproxy/s-proxy 0/0/0/1/+1 403 +351 - - ---- 3/3/3/3/0 0/0 {1A94893098405359} "CONNECT 172.19.4.2:5001 HTTP/1.1"\n'
                p = re.search(
                    "(^\d*\.\d*\.\d*\.\d*):(\d*) " # Host and port
                    + "\[(.*)\] " # Date 
                    + "(\w*)~? " # Frontend
                    + "(b-\w*)/(<?s-\w*>?) "  # Backend/Server
                    + "(.\d*/.\d*/.\d*/.\d*/.\d*) " # Times
                    + "(\d*) " # State
                    + ".*" # Not needed
                    + "{(.*)} " # authid
                    + '"(.*)"'
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
                    action = p.group(10)
                    sessions.SESSIONS.add(authid, ip, port, action)
                else:
                    p =re.search("(^\d*\.\d*\.\d*\.\d*):(\d*) \[(.*)\] ssl",msg)
                    if (p):
                        log.L.warning("Cannot parse haproxy log: " + repr(msg))
            s = self.getLine()
        
    def getLine(self):
        try:
            return(self.sock.recv(2048))
        except socket.timeout:
            return(None)

    def stop(self):
        if (os.path.exists(self.flog)):
            os.remove(self.flog)
        super().stop()
