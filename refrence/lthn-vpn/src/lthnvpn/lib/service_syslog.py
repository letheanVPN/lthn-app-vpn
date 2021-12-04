import os
import select
import socket
import syslogmp
import re
from lthnvpn.lib.service import Service
from lthnvpn.lib import config, log, sessions

class ServiceSyslog(Service):
    
    def run(self):
        self.mgmtfile = config.Config.PREFIX + "/var/run/log"
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        if not config.CONFIG.isWindows():
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.sock.bind(self.mgmtfile)
            self.sock.settimeout(self.SOCKET_TIMEOUT)
        self.name = "Syslog server"
        super().run()

    def orchestrate(self):
        if config.CONFIG.isWindows():
            return True
        s = self.getLine()
        while (s != None):
            message = syslogmp.parse(s)
            if (message):
                msg = message.message.decode("utf-8")
                log.L.debug("syslog: " + repr(msg))
                # 127.0.0.1:45940 [04/Sep/2018:18:40:06.448] ssltunnel~ b-preproxy/s-proxy 1/0/0/12/+12 200 +37 - - ---- 2/2/1/1/0 0/0 {1ACCCCC|TO_PROXY_CONNECT|} "CONNECT www.idnes.cz:443 HTTP/1.1"
                p = re.search(
                    "(^\d*\.\d*\.\d*\.\d*)|(\[(.*)\]):(\d*) " # Host and port
                    + "\[(.*)\] " # Date 
                    + "(\w*)~? " # Frontend
                    + "(b-\w*)/(<?s-\w*>?) "  # Backend/Server
                    + "(.\d*/.\d*/.\d*/.\d*/.\d*) " # Times
                    + "(\d*) " # State
                    + ".*" # Not needed
                    + "{(.*)\|(.*)\|(.*)} " # authid, reason, overlimit
                    + '"(.*) (.*) (.*)"'
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
                    reason = p.group(10)
                    overlimit = p.group(11)
                    method = p.group(12)
                    uri = p.group(13)
                    proto = p.group(14)
                    if (server=="s-proxy"):
                        sessions.SESSIONS.add(authid, ip, port, method=method, uri=uri, proto=proto)
                    else:
                        log.L.debug("Ignoring haproxy log")
                else:
                    p = re.search("(^\d*\.\d*\.\d*\.\d*):(\d*) \[(.*)\] ssltunnel", msg)
                    if (p):
                        log.L.info("Ignoring haproxy log: " + repr(msg))
            s = self.getLine()
        
    def getLine(self):
        try:
            return(self.sock.recv(2048))
        except socket.timeout:
            return(None)
