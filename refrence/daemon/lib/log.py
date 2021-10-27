
import logging
import util
import config

class Log(object):
    
    def __init__(self, handler=None, level=logging.WARNING, name='lthn'):
        logging.basicConfig(level=level,
                    format='%(asctime)s %(name)-12s %(process)d %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    )
        self.logger = logging.getLogger(name)
        if (handler):
            self.logger.addHandler(handler)
        self.logger.setLevel(level)
    
    def debug(self, msg, *args, **kwargs):
        return self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        return self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        return self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        return self.logger.error(msg, *args, **kwargs)
                
class Audit(object):
    
    ADD = "ADD"
    DEL = "DEL"
    KILL = "KILL"
    START  = "START"
    STOP  = "STOP"
    MODIFY = "MOD"
    UPLOAD = "UPLOAD"
    NPAYMENT = "NEED_PAYMENT"
    AUTHID =  "AUTHID"
    SESSION = "SESSION"
    SERVICE = "SERVICE"
    SWALLET = "SDP_WALLET"
    PWALLET = "PROVIDER_WALLET"
    SDP = "SDP"
    
    def __init__(self, handler=None, level=logging.INFO, anon=True, name='audit'):
        self.logger = logging.getLogger('audit')
        if (handler):
            formatter = logging.Formatter('%(asctime)s %(message)s')
            handler.setFormatter(formatter)
        else:
            handler = logging.StreamHandler()
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        self.anon = anon
        
    def audit(self, action, type, obj=None, anon=None, lthn=None, wallet=None, paymentid=None, sessionid=None, srcip=None, srcport=None, dstport=None, dstip=None, msg=None, method=None, uri=None, serviceid=None, cmd=None):
        if (anon=="yes" or (anon is None and self.anon is True)):
            if paymentid:
                paymentid = util.anonymise_paymentid(paymentid)
            if srcip:
                srcip = util.anonymise_ip(srcip)
            if uri:
                uri = util.anonymise_uri(uri)
        if cmd:
            cmd = repr(cmd)
        if msg:
            msg = repr(msg)
            
        
        json={
            'action': action,
            'type': type
            }
        if obj:
            json['obj'] = obj
        if lthn:
            json['lthn'] = lthn
        if wallet:
            json['wallet'] = wallet
        if paymentid:
            json['paymentid'] = paymentid
        if sessionid:
            json['sessionid'] = sessionid
        if srcip:
            json['srcip'] = srcip
        if dstip:
            json['dstip'] = dstip
        if srcport:
            json['srcport'] = srcport
        if dstport:
            json['dstport'] = dstport
        if msg:
            json['msg'] = msg
        if method:
            json['method'] = method
        if uri:
            json['uri'] = uri
        if serviceid:
            json['serviceid'] = serviceid
        if cmd:
            json['cmd'] = cmd
        if (config.Config.CAP.aj):
            txt = util.valuesToJson(json)
        else:
            txt = util.valuesToString(json, '=', ',', '')
            
        return(self.logger.info(txt))

L = None
A = None

