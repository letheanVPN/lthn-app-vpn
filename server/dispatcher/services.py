
import atexit
from config import *
import logging
from pprint import pprint
import re
from sdp import *
import select
import signal
import socket
from subprocess import PIPE
from subprocess import Popen
import sys
import syslogmp
from threading import Thread
import time
from authids import AuthIds, AuthId, AUTHIDS

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names
    
SERVICES = None

class Service(object):
    """
    Service class
    """
    
    def __init__(self, id, json):
        self.id = id.upper()
        self.type = json["type"]
        self.name = json["name"]
        self.cost = json["cost"]
        self.dir = Config.PREFIX + "/var/%s_%s/" % (self.type, self.id)
        self.initphase = True

    def stop(self):
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        if (os.path.exists(self.pidfile)):
            os.remove(self.pidfile)
        self.process.kill()
        
    def getLine(self):
        if (self.stderr.poll(0.05)):
            s = self.process.stderr.readline().strip()
            if (s != ""):
                return(s)
            else:
                return(None)
        else:
            if (self.stdout.poll(0.05)):
                s = self.process.stdout.readline().strip()
                if (s != ""):
                    return(s)
                else:
                    return(None)
            else:
                return(None)
            
    def mgmtConnect(self, ip, port):
        if (ip == "socket"):
            self.mgmt = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            self.mgmt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        i = 0
        while (i < 50):
            try:
                if (ip == "socket"):
                    self.mgmt.connect(self.mgmtfile)
                else:
                    self.mgmt.connect((ip, int(port)))
            except socket.error:
                time.sleep(0.1)
                i += 1
            else:
                break
        self.mgmt.settimeout(0.1)
        
    def mgmtRead(self):
        line = ""
        try:
            while True:
                self.mgmt.settimeout(0.1)
                c = self.mgmt.recv(1)
                if c != "\n" and c != "":
                    line += c
                else:
                    break
        except socket.timeout:
            pass
        else:
            pass
        if (line != ""):
            logging.debug("%s[%s]-mgmt-in: %s" % (self.type, self.id, line))
            self.mgmtEvent(line)
            return(line)
        else:
            return(None)
        
    def mgmtWrite(self, msg):
        try:
            logging.debug("%s[%s]-mgmt-out: %s" % (self.type, self.id, msg))
            self.mgmt.send(msg + "\n")
        except socket.timeout:
            pass
        else:
            pass
        
    def mgmtEvent(self, msg):
        pass

    def isAlive(self):
        self.process.poll()
        return(self.process.returncode == None)
    
    def getCost(self):
        return(self.cost)
    
    def getName(self):
        return(self.name)
    
    def getType(self):
        return(self.type)
    
    def getId(self):
        return(self.id)
    
    def show(self):
        logging.info("Service %s (%s), id %s" % (self.getName(), self.getType(), self.getId()))

class ServiceHa(Service):
    """
    HAproxy service class
    """
    
    def run(self):
        self.createConfig()
        cmd = [Config.HAPROXY_BIN, "-Ds", "-p", self.pidfile, "-f", self.cfgfile]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        time.sleep(0.3)
        if (os.path.exists(self.pidfile)):
            with open (self.pidfile, "r") as p:
                self.pid = int(p.readline().strip())
        else:
            self.pid = self.process.pid
        logging.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.pid))
        self.stdout = select.poll()
        self.stderr = select.poll()
        self.stdout.register(self.process.stdout, select.POLLIN)
        self.stderr.register(self.process.stderr, select.POLLIN)
        self.mgmtConnect("socket", self.mgmtfile)
        
    def stop(self):
        os.kill(self.pid, signal.SIGTERM)
    
    def isAlive(self):
        try:
            os.kill(self.pid, 0)
        except OSError:
            return False
        else:
            return True
        
    def orchestrate(self):
        l = self.getLine()
        while (l <> None):
            logging.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
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
        tfile = Config.PREFIX + "/etc/haproxy_server.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            logging.error("Cannot open haproxy template file %s" % (tfile))
            
        out = tmpl.format(
                          maxconn=2000,
                          timeout="1m",
                          ctimeout="15s",
                          f_logsocket=Config.PREFIX + '/var/log local0',
                          f_sock=self.mgmtfile,
                          header='X-ITNS-PaymentID',
                          ctrluri='http://_ITNSVPN_',
                          f_dh=Config.PREFIX + '/etc/dhparam.pem',
                          cabase=Config.PREFIX + '/etc/ca/certs',
                          crtbase=Config.PREFIX + '/etc/ca/certs',
                          ctrldomain='_ITNSVPN_',
                          f_site_pem=Config.PREFIX + '/etc/ca/certs/ha.both.pem',
                          f_credit=Config.PREFIX + '/var/hasrv/credit-',
                          f_status=Config.PREFIX + '/etc/ha_info.http',
                          f_allow_src_ips=Config.PREFIX + '/etc/src_allow.ips',
                          f_deny_src_ips=Config.PREFIX + '/etc/src_deny.ips',
                          f_deny_dst_ips=Config.PREFIX + '/etc/dst_deny.ips',
                          f_deny_dst_doms=Config.PREFIX + '/etc/dst_deny.doms'
                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out)
        except (IOError, OSError):
            logging.error("Cannot write haproxy config file %s" % (self.cfgfile))
        logging.info("Created haproxy config file %s" % (self.cfgfile))
    
class ServiceOvpn(Service):
    """
    Openvpn service class
    """ 
    
    def run(self):
        self.createConfig()
        verb = "3"
        if (Config.OPENVPN_SUDO):
            cmd = ["/usr/bin/sudo", Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb]
        else:
            cmd = [Config.SUDO_BIN, Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        time.sleep(0.3)
        if (os.path.exists(self.pidfile)):
            with open (self.pidfile, "r") as p:
                self.pid = int(p.readline().strip())
        else:
            self.pid = self.process.pid
        logging.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.pid))
        self.stdout = select.poll()
        self.stderr = select.poll()
        self.stdout.register(self.process.stdout, select.POLLIN)
        self.stderr.register(self.process.stderr, select.POLLIN)
        self.mgmtConnect("127.0.0.1", "11112")
        
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
            logging.warning("Client %s authorized with %s." % (untrusted_ip, username))
            self.mgmtWrite("client-auth %s %s" % (cid, kid))
            self.mgmtWrite("END")
        else:
            logging.warning("Bad username/password %s/%s" % (username, password))
            self.mgmtWrite("client-deny %s %s \"Bad auth\"" % (cid, kid))
        
    def mgmtEvent(self, msg):
        p = re.search(">CLIENT:CONNECT,(\d*),(\d*)", msg)
        if (p):
            cid = p.group(1)
            kid = p.group(2)
            self.mgmtAuthClient(cid, kid)
        
    def unHold(self):
        self.mgmtWrite("hold release")
        l = self.mgmtRead()
        while (l <> None):
            l = self.mgmtRead()
            
    def stop(self):
        return()
    
    def orchestrate(self):
        l = self.mgmtRead()
        while (l <> None):
            l = self.mgmtRead()
        if (self.initphase):
            self.unHold()
            self.initphase = None
        l = self.getLine()
        while (l <> None):
            logging.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
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
        tfile = Config.PREFIX + "/etc/openvpn_server.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            logging.error("Cannot open openvpn template file %s" % (tfile))
        with open (Config.PREFIX + '/etc/ca/certs/ca.cert.pem', "r") as f:
            f_ca = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/ca/certs/openvpn.cert.pem', "r") as f:
            f_crt = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/ca/certs/openvpn.both.pem', "r") as f:
            f_key = "".join(f.readlines())        
        with open (Config.PREFIX + '/etc/openvpn.tlsauth', "r") as f:
            f_ta = "".join(f.readlines())
        out = tmpl.format(
                          port=11194,
                          proto="udp",
                          f_dh=Config.PREFIX + '/etc/dhparam.pem',
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
            cf.write(out)
        except (IOError, OSError):
            logging.error("Cannot write openvpn config file %s" % (self.cfgfile))
        logging.info("Created openvpn config file %s" % (self.cfgfile))
        
    def createClientConfig(self):
        tfile = Config.PREFIX + "/etc/openvpn_client.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            logging.error("Cannot open openvpn template file %s" % (tfile))
            sys.exit(1)
        with open (Config.PREFIX + '/etc/ca/certs/ca.cert.pem', "r") as f:
            f_ca = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/ca/certs/openvpn.cert.pem', "r") as f:
            f_crt = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/openvpn.tlsauth', "r") as f:
            f_ta = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/dhparam.pem', "r") as f:
            f_dh = "".join(f.readlines())
        out = tmpl.format(
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
            logging.error("Cannot create openvpn config file")

class ServiceSyslog(Service):
    
    def __init__(self, s):
        self.flog = s
        if (os.path.exists(s)):
            os.remove(s)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(s)
        self.sock.settimeout(0.1)
        
    def orchestrate(self):
        s = self.getLine()
        while (s != None):
            message = syslogmp.parse(s)
            if (message):
                logging.debug("syslog: " + message.message)
            s = self.getLine()
        
    def getLine(self):
        try:
            return(self.sock.recv(2048))
        except socket.timeout:
            return(None)

    def stop(self):
        if (os.path.exists(self.flog)):
            os.remove(self.flog)

class Services(object):
    
    def __init__(self):
        
        self.services = {}
        sdp = SDP()
        sdp.load()
        for id in sdp.listServices():
            s = sdp.getService(id)
            if (s["type"]):
                if (s["type"] == "vpn"):
                    so = ServiceOvpn(id, s)
                elif (s["type"] == "proxy"):
                    so = ServiceHa(id, s)
                else:
                    logging.error("Unknown service type %s in SDP!" % (s["type"]))
                    sys.exit(1)
            self.services[id.upper()] = so
        self.syslog = ServiceSyslog(Config.PREFIX + "/var/log")
            
    def run(self):
        for id in self.services:
            s = self.services[id]
            s.run()
        atexit.register(self.stop)
    
    def createConfigs(self):
        for id in self.services:
            s = self.services[id]
            s.createConfig()
            
    def orchestrate(self):
        self.syslog.orchestrate()
        for id in self.services:
            if (not self.services[id].orchestrate()):
                logging.error("Service %s died! Exiting!" % (self.services[id].id))
                self.stop()
                sys.exit(3)

    def stop(self):
        for id in self.services:
            s = self.services[id]
            if (s.isAlive()):
                s.stop()
        self.syslog.stop()
            
    def show(self):
        for id in self.services:
            s = self.services[id]
            s.show()
            
    def get(self, id):
        return(self.services[id.upper()])


