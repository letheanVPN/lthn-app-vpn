from service import Service
import config
import os
import sys
import re
import log
import time
import select
from subprocess import Popen
from subprocess import PIPE
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceOvpn(Service):
    """
    Openvpn service class
    """ 
    
    OPTS = dict(
        http_proxy = "localhost:3128",
        crt = None, key = None, crtkey = None,
        reneg = 600
    )
    OPTS_HELP = dict(
        http_proxy = "HTTP proxy used for connection to ovpn",
        reneg = "Renegotiation interval"
    )
    
    def run(self):
        self.createConfig()
        verb = "3"
        if (config.Config.OPENVPN_SUDO):
            cmd = ["/usr/bin/sudo", config.Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb]
        else:
            cmd = [config.Config.SUDO_BIN, Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        time.sleep(0.3)
        if (os.path.exists(self.pidfile)):
            with open (self.pidfile, "r") as p:
                self.pid = int(p.readline().strip())
        else:
            self.pid = self.process.pid
        log.L.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.pid))
        self.stdout = select.poll()
        self.stderr = select.poll()
        self.stdout.register(self.process.stdout, select.POLLIN)
        self.stderr.register(self.process.stderr, select.POLLIN)
        self.mgmtConnect("127.0.0.1", "11112")
        log.L.warning("Started service %s[%s]" % (self.name, self.id))
        
    def mgmtAuthClient(self, cid, kid):
        global AUTHIDS
        
        username = ""
        password = ""
        untrusted_ip = ""
        untrusted_port = ""
        msg = self.mgmtRead()
        while (True):
            if (msg==None):
                continue
            p = re.search(">CLIENT:ENV,END", msg)
            if (p):
                break
            p = re.search(">CLIENT:ENV,username=(.*)", msg)
            if (p):
                username = p.group(1)
            p = re.search(">CLIENT:ENV,password=(.*)", msg)
            if (p):
                password = p.group(1)
            p = re.search(">CLIENT:ENV,untrusted_ip=(.*)", msg)
            if (p):
                untrusted_ip = p.group(1)
            p = re.search(">CLIENT:ENV,untrusted_port=(.*)", msg)
            if (p):
                untrusted_port = p.group(1)
            msg = self.mgmtRead()
            
        if (username == password and AUTHIDS.get(username)):
            log.L.warning("Client %s authorized with %s." % (untrusted_ip, username))
            self.mgmtWrite("client-auth %s %s\r\n" % (cid, kid))
            self.mgmtWrite("END\r\n")
        else:
            log.L.warning("Bad username/password %s/%s" % (username, password))
            self.mgmtWrite("client-deny %s %s \"Bad auth\"\r\n" % (cid, kid))
        
    def mgmtEvent(self, msg):
        p = re.search("^>CLIENT:CONNECT,(\d*),(\d*)", msg)
        if (p):
            cid = p.group(1)
            kid = p.group(2)
            self.mgmtAuthClient(cid, kid)
        
    def unHold(self):
        self.mgmtWrite("hold release\r\n")
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
            
    def stop(self):
        self.mgmtWrite("signal SIGTERM\r\n")
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
        log.L.warning("Stopped service %s[%s]" % (self.name, self.id))
        return()
    
    def orchestrate(self):
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
        if (self.initphase):
            self.unHold()
            self.initphase = None
        l = self.getLine()
        while (l is not None):
            log.L.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
            l = self.getLine()
        
        return(self.isAlive())
    
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        self.cfgfile = self.dir + "/cfg"
        self.pidfile = self.dir + "/pid"
        self.mgmtfile = self.dir + "/mgmt"
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        tfile = config.Config.PREFIX + "/etc/openvpn_server.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open openvpn template file %s" % (tfile))
        with open (config.Config.PREFIX + '/etc/ca/certs/ca.cert.pem', "r") as f:
            f_ca = "".join(f.readlines())
        with open (config.Config.PREFIX + '/etc/ca/certs/openvpn.cert.pem', "r") as f:
            f_crt = "".join(f.readlines())
        with open (config.Config.PREFIX + '/etc/ca/certs/openvpn.both.pem', "r") as f:
            f_key = "".join(f.readlines())        
        with open (config.Config.PREFIX + '/etc/openvpn.tlsauth', "r") as f:
            f_ta = "".join(f.readlines())
        out = tmpl.decode("utf-8").format(
                          port=11194,
                          proto="udp",
                          f_dh=config.Config.PREFIX + '/etc/dhparam.pem',
                          tunnode=config.Config.PREFIX + '/dev/net/tun',
                          f_ca=f_ca,
                          f_crt=f_crt,
                          f_key=f_key,
                          f_ta=f_ta,
                          workdir="/tmp",
                          user="nobody",
                          group="nogroup",
                          f_status="status",
                          iprange="10.10.10.0",
                          ipmask="255.255.255.0",
                          mgmt_sock="127.0.0.1 11112",
                          reneg=60,
                          mtu=1400,
                          mssfix=1300
                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
        except (IOError, OSError):
            log.L.error("Cannot write openvpn config file %s" % (self.cfgfile))
        log.L.info("Created openvpn config file %s" % (self.cfgfile))
        
    def createClientConfig(self):
        tfile = Config.PREFIX + "/etc/openvpn_client.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open openvpn template file %s" % (tfile))
            sys.exit(1)
        with open (Config.PREFIX + '/etc/ca/certs/ca.cert.pem', "r") as f:
            f_ca = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/ca/certs/openvpn.cert.pem', "r") as f:
            f_crt = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/openvpn.tlsauth', "r") as f:
            f_ta = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/dhparam.pem', "r") as f:
            f_dh = "".join(f.readlines())
        out = tmpl.decode("utf-8").format(
                          port=11194,
                          proto="udp",
                          ip="172.17.4.14",
                          f_ca=f_ca,
                          f_crt=f_crt,
                          f_ta=f_ta,
                          reneg=60,
                          mtu=1400,
                          mssfix=1300
                          )
        try:
            print(out)
            sys.exit()
        except (IOError, OSError):
            log.L.error("Cannot write openvpn config file")

