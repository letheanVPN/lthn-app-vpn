from service import Service
import config
import os
import select
import socket
import logging
import syslogmp

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
                logging.debug("syslog: " + message.message.decode("utf-8"))
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
