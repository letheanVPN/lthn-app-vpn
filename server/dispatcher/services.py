
import logging
import sys
from subprocess import PIPE, Popen
from threading  import Thread
import pprint
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
        cmd=[Config.HAPROXY_BIN,"-f", self.cfile]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        logging.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.process.pid))
        self.queue = Queue()
        self.thread = Thread(target=enqueue_output, args=(self.process.stdout, self.process.stderr, self.queue))
        #self.thread.daemon = True
        self.thread.start()
        
    def check(self):
        l=self.getLine()
        while (l<>None):
            logging.info("haproxy: %s" %(l))
            l=self.getLine()
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
            f_logfile='ha.log local0',
            f_sock='haproxy.sock',
            header='X-ITNS-PaymentID',
            ctrluri='http://_ITNSVPN_',
            cabase='ca',
            crtbase='crt',
            ctrldomain='_ITNSVPN',
            f_site_pem='site.pem',
            f_credit='credit-',
            f_status='info.txt',
            f_allow_src_ips='allow.ips',
            f_deny_src_ips='deny.ips',
            f_deny_dst_ips='deny.ips',
            f_deny_dst_doms='deny.doms'
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
        self.thread = Thread(target=enqueue_output, args=(self.process.stdout, self.process.stderr, self.queue))
        #self.thread.daemon = True
        self.thread.start()
        
    def check(self):
        l=self.getLine()
        while (l<>None):
            logging.info("openvpn: %s" %(l))
            l=self.getLine()
        #if not self.process.poll():
        #    logging.error("Openvpn died! Exiting.")
        #    sys.exit(self.process.returncode)
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
            f_dh="dh4096",
            f_ca="ca.crt",
            f_crt="a.crt",
            f_key="a.pem",
            f_ta="tls.pem",
            workdir="/tmp",
            user="nobody",
            group="nogroup",
            f_status="status",
            iprange="10.10.10.0",
            ipmask="255.255.255.0",
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
            
    def runAll(self):
        for id in self.data:
            s = self.data[id]
            s.run()
            
    def checkAll(self):
        for id in self.data:
            s = self.data[id]
            if (not s.check()):
                logging.error("Service %s died! Exiting!" % (s.id))
                sys.exit(3)
                
    def stopAll(self):
        for id in self.data:
            s = self.data[id]
            s.stop()
            
    def show(self):
        for id in self.data:
            s = self.data[id]
            s.show()
            
    def get(self, id):
        return(self.data[id.upper()])
    
    