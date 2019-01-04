
import base64
import config
import json
import log
import os
import sys
import time
import hashlib
from urllib.request import Request
from urllib.request import urlopen

class SDPList(object):
    
    data = {}
    
    def uriCacheFile(self, uri):
        return(config.Config.CAP.sdpCacheDir + "/" + hashlib.sha256(uri.encode("utf-8")).hexdigest() + ".json")
    
    def downloadUri(self, uri):
        sfile = self.uriCacheFile(uri)
        if self.isFresh(uri):
            log.L.info('SDP cache %s is fresh, not reloading.' % sfile)
            cf = open(sfile, "rb")
            return(cf.read())
        log.L.info('Downloading SDP from %s' % uri)
        request = Request(uri)
        request.add_header('Content-Type', 'application/json')
        try:
            response = urlopen(request).read()
            jsonResp = json.loads(response.decode('utf-8'))
            if jsonResp and jsonResp['protocolVersion']:
                sfile = self.uriCacheFile(uri)
                try:
                    cf = open(sfile, "wb")
                    cf.write(response)
                    return response
                except (IOError, OSError):
                    log.L.error("Cannot write SDP cache %s" % (sfile))
                    sys.exit(2)
            else:
                print("aaaa")
        except Exception as err:
            log.L.error("Cannot fetch from SDP server!")
            log.L.error(err)
            sys.exit(2)
        return True

    def get(self, urls=None, filter=None):
        if not urls:
            urls = { 'sdp': config.Config.CAP.sdpUri['sdp'] + '/services/search' }
        json=[]
        for id_ in urls:
            j = self.downloadUri(urls[id_])
            self.parseRemoteSdp(j, id_, urls[id_])
            json.append(j)
        self.parseLocalSdp()
    
    def isFresh(self, uri):
        sfile = self.uriCacheFile(uri)
        if os.path.isfile(sfile):
            stat = os.stat(sfile)
            if (time.time()-stat.st_mtime > config.Config.CAP.sdpCacheExpiry):
                return(None)
            else:
                return(True)
        else:
            return(None)
        
    def list(self):
        return(self.data.keys())
    
    def getProviderSDP(self, id_):
        if id_ in self.data:
            return(self.data[id_])
        else:
            return None
        
    def parseLocalSdp(self):
        if (os.path.exists(config.CONFIG.SDPFILE)):
            try:
                jf = open(config.CONFIG.SDPFILE, "r")
                localSdp = jf.read()
                cf = open(config.CONFIG.PREFIX + "/etc/ca/certs/ca.cert.pem", "r")
                localCa = cf.read()
            except (IOError, OSError):
                log.L.warning("Cannot read local SDP file %s" % (config.CONFIG.SDPFILE))
            localJson = json.loads(localSdp)
            localJson['provider']['certificates'] = {}
            localJson['provider']['certificates']['cn'] = 'ignored'
            localJson['provider']['certificates']['id'] = 0
            localJson['provider']['certificates']['content'] = localCa
            localJson['provider']['fqdn'] = 'local'
            id_ = localJson["provider"]["id"]
            self.data[id_]=localJson
        
    def parseRemoteSdp(self, sdp, fqdn, uri):
        allJson = json.loads(sdp.decode('utf-8'))
        for prov in allJson['providers']:
            pid = prov['provider']
            providerJson = dict(
                protocolVersion=1,                
                provider=dict(
                    id='{providerid}',
                    name='',
                    nodeType='{nodetype}',
                    certificates={},
                    wallet='{walletaddress}',
                    terms='{providerterms}',
                    fqdn=fqdn,
                    uri=uri
                ),                                
                services=[],
                )
            providerJson['provider']['id'] = pid
            providerJson['provider']['name'] = prov['providerName']
            providerJson['provider']['wallet'] = prov['providerWallet']
            ca = base64.b64decode(prov['certArray'][0]['certContent']).decode('utf-8')
            providerJson['provider']['certificates'] = {}
            providerJson['provider']['certificates']['cn'] = 'ignored'
            providerJson['provider']['certificates']['id'] = 0
            providerJson['provider']['certificates']['content'] = ca
            sid = prov["id"]
            stype = prov["type"]
            log.L.info("Adding service type %s %s/%s to SDP list" % (stype, pid, sid))
            service=dict(
                id=sid,
                type=prov["type"],
                name=prov["name"],
                allowRefunds=prov["allowRefunds"],
                firstVerificationsNeeded=prov["firstVerificationsNeeded"],
                subsequentVerificationsNeeded=prov["subsequentVerificationsNeeded"],
                downloadSpeed=prov["downloadSpeed"],
                uploadSpeed=prov["uploadSpeed"],
                firstPrePaidMinutes=prov["firstPrePaidMinutes"],
                subsequentPrePaidMinutes=prov["subsequentPrePaidMinutes"],
                cost=prov["cost"]
            )
            if prov["type"]=="proxy":
                service["proxy"]=prov["proxy"]
            else:
                service["vpn"]=prov["vpn"]
            if pid not in self.data:
                self.data[pid]=providerJson
            self.data[pid]["services"].append(service)
                    
