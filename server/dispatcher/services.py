
import logging
import sys
from subprocess import PIPE, Popen
from threading  import Thread
import pprint
import socket
import time
import syslogmp
from sdp import *
from config import *

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, out2, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    for line in iter(out2.readline, b''):
        queue.put(line)
    out.close()

class Service(object):
    """
    service description class
    """
    def __init__(self, id, json):
        self.id = id.upper()
        self.type = json["type"]
        self.name = json["name"]
        self.cost = json["cost"]
        
    def stop(self):
        self.process.kill()
        
    def getLine(self):
        try:  line = self.queue.get_nowait()
        except Empty:
            return(None)
        else: 
            return(line.strip())
        
    def isAlive(self):
        return(self.thread.isAlive())
    
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
    HAproxy service description class
    """
    
    def run(self):
        self.createConfig()
        cmd=[Config.HAPROXY_BIN,"-Ds","-f", self.cfile]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        logging.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.process.pid))
        self.queue = Queue()
        self.thread = Thread(target=enqueue_output, args=(self.process.stdout, self.process.stderr, self.queue))
        #self.thread.daemon = True
        self.thread.start()
        
    def orchestrate(self):
        l=self.getLine()
        while (l<>None):
            logging.info("haproxy: %s" %(l))
            l=self.getLine()
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(Config.PREFIX+'/var/haproxy.sock')
        sock.settimeout(0.1)
        sock.send("show info\n")
        #logging.warning(sock.recv(1024))
        return(self.isAlive())
        
    def createConfig(self):
        tfile=Config.PREFIX + "/etc/haproxy_server.tmpl"
        self.cfile=Config.PREFIX + "/var/haproxy_%s.cfg" % (self.id)
        try:
            tf=open(tfile, "rb")
            tmpl=tf.read()
        except (IOError, OSError):
            logging.error("Cannot open haproxy template file %s" % (tfile))
            
        out=tmpl.format(
            maxconn=2000,
            timeout="1m",
            ctimeout="15s",
            f_logsocket=Config.PREFIX+'/var/log local0',
            f_sock=Config.PREFIX+'/var/haproxy.sock',
            header='X-ITNS-PaymentID',
            ctrluri='http://_ITNSVPN_',
            f_dh=Config.PREFIX+'/etc/dhparam.pem',
            cabase=Config.PREFIX+'/etc/ca/certs',
            crtbase=Config.PREFIX+'/etc/ca/certs',
            ctrldomain='_ITNSVPN_',
            f_site_pem=Config.PREFIX+'/etc/ca/certs/ha.both.pem',
            f_credit=Config.PREFIX+'/var/hasrv/credit-',
            f_status=Config.PREFIX+'/etc/ha_info.http',
            f_allow_src_ips=Config.PREFIX+'/etc/src_allow.ips',
            f_deny_src_ips=Config.PREFIX+'/etc/src_deny.ips',
            f_deny_dst_ips=Config.PREFIX+'/etc/dst_deny.ips',
            f_deny_dst_doms=Config.PREFIX+'/etc/dst_deny.doms'
            )
        try:
            cf=open(self.cfile, "wb")
            cf.write(out)
        except (IOError,OSError):
            logging.error("Cannot write haproxy config file %s" % (self.cfile))
        logging.info("Created haproxy config file %s" %(self.cfile))
    
class ServiceOvpn(Service):
    """
    HAproxy service description class
    """ 
    
    def run(self):
        self.createConfig()
        cmd=[Config.OPENVPN_BIN,"--config", self.cfile]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        logging.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.process.pid))
        self.queue = Queue()
        i=0
        self.mgmt=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        while (i<100):
            try:
                self.mgmt.connect(Config.PREFIX+'/var/ovpn.mgmt')
            except socket.error:
                time.sleep(0.1)
                i+=1
            else:
                break
        
        self.mgmt.settimeout(0.1)
        self.thread = Thread(target=enqueue_output, args=(self.process.stdout, self.process.stderr, self.queue))
        self.thread.start()
        
    def orchestrate(self):
        l=self.getLine()
        while (l<>None):
            logging.info("openvpn: %s" %(l))
            l=self.getLine()
        try:
            self.mgmt.send("hold release\n")
            print(self.mgmt.recv(4096))
        except socket.timeout:
            pass
        else:
            return(None)
        return(self.isAlive())
    
    def createConfig(self):
        tfile=Config.PREFIX + "/etc/openvpn_server.tmpl"
        self.cfile=Config.PREFIX + "/var/openvpn_%s.cfg" % (self.id)
        try:
            tf=open(tfile, "rb")
            tmpl=tf.read()
        except (IOError, OSError):
            logging.error("Cannot open openvpn template file %s" % (tfile))
        out=tmpl.format(
            port=1194,
            proto="udp",
            f_dh=Config.PREFIX+'/etc/dhparam.pem',
            f_ca=Config.PREFIX+'/etc/ca/certs/ca.cert.pem',
            f_crt=Config.PREFIX+'/etc/ca/certs/openvpn.cert.pem',
            f_key=Config.PREFIX+'/etc/ca/certs/openvpn.both.pem',
            f_ta=Config.PREFIX+'/etc/openvpn.tlsauth',
            workdir="/tmp",
            user="nobody",
            group="nogroup",
            f_status="status",
            iprange="10.10.10.0",
            ipmask="255.255.255.0",
            mgmt_sock=Config.PREFIX+'/var/ovpn.mgmt unix',
            reneg=60,
            mtu=1400,
            mssfix=1300
           )
        try:
            cf=open(self.cfile, "wb")
            cf.write(out)
        except (IOError,OSError):
            logging.error("Cannot write openvpn config file %s" % (self.cfile))
        logging.info("Created openvpn config file %s" %(self.cfile))

class ServiceSyslog(Service):
    
    def __init__(self,s):
        self.flog=s
        if (os.path.exists(s)):
            os.remove(s)
        self.sock=socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(s)
        self.sock.settimeout(0.1)
        
    def getLine(self):
        try:
            return(self.sock.recv(2048))
        except socket.timeout:
            return(None)
        
    def stop(self):
        os.remove(self.flog)

class Services(object):
    
    def __init__(self, sdpfile):
        self.data = dict()
        sdp = SDP()
        sdp.load(sdpfile)
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
            self.data[id.upper()] = so
        self.syslog=ServiceSyslog(Config.PREFIX + "/var/log")
            
    def run(self):
        for id in self.data:
            s = self.data[id]
            s.run()
    
    def createConfigs(self):
        for id in self.data:
            s = self.data[id]
            s.createConfig()
            
    def orchestrate(self):
        s=self.syslog.getLine()
        if (s!=None):
            message = syslogmp.parse(s)
            print(message.message)
        
        for id in self.data:
            s = self.data[id]
            if (not s.orchestrate()):
                logging.error("Service %s died! Exiting!" % (s.id))
                self.stop()
                sys.exit(3)

    def stop(self):
        for id in self.data:
            s = self.data[id]
            if (s.isAlive()):
                s.stop()
        self.syslog.stop()
            
    def show(self):
        for id in self.data:
            s = self.data[id]
            s.show()
            
    def get(self, id):
        return(self.data[id.upper()])
    
    