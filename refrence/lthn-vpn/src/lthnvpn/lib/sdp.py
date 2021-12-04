import base64
import ed25519
import json
import jsonpickle
import os
import pprint
import re
import sys
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen
from lthnvpn.lib import config, log

class SDP(object):
    configFile = None
    dataLoaded = False
    certsDir = None
    
    # sample SDP dict
    data = dict(
                protocolVersion=1,                
                provider=dict(
                    id='{providerid}',
                    name='',
                    nodeType='{nodetype}',
                    certificates={},
                    wallet='{walletaddress}',
                    terms='{providerterms}',
                ),                                
                services=[],
                )

    """SDP functions"""
    def addService(self, cap):
        # Create new SDP service
        self.load(None)
        ret = False
        while not ret:
            ret = self.isConfigured(cap)

        s = SDPService(self.getUsedServiceIds(), None, self.certsDir)
        ret = False
        while not ret:
            ret = s.checkConfig(cap)

        if ret:
            self.data['services'].append(s.data)

    def getUsedServiceIds(self):
        serviceIds = []
        for i in self.data['services']:
            serviceIds.append(i['id'])
        return serviceIds

    def editService(self, cap):
        # Revise existing SDP service
        self.load(None)
        ret = False
        while not ret:
            ret = self.isConfigured(cap)

        if (not self.data['services'] or len(self.data['services']) == 0):
            addService(cap)
            return

        count = 1

        for i in self.data['services']:
            print('%d: %s [%s] [cost %s] (ID %s)' % (count, i['name'], i['type'], i['cost'], i['id']))
            count += 1

        choice = input('Select a service to edit (enter the number only): ')
        if (choice.isnumeric()):
            choice = int(choice) - 1
            if self.data['services'][choice]:
                # Select service and begin editing
                print('Editing service %s (ID %s)' % (self.data['services'][choice]['name'], self.data['services'][choice]['id']))
                encoded = jsonpickle.encode(self.data['services'][choice], unpicklable=False)
                s = SDPService(self.getUsedServiceIds(), encoded, self.certsDir)
                ret = False
                while not ret:
                    ret = s.checkConfig(cap.CAP, self.data['services'][choice]['id'])

                if ret:
                    self.data['services'][choice] = s.data
                    return True
            else:
                log.L.error('Invalid selection')
        else:
            log.L.error('Invalid selection')

    def isConfigured(self, cap):
        # Checks validity of data and forces configuration if invalid
        self.load(None)

        if (not isinstance(self.data['protocolVersion'], int) or
            self.data['protocolVersion'] < 1):
            log.L.error('Invalid protocol version (%s)! Setting to 1.' % self.data['protocolVersion'])
            self.data['protocolVersion'] = 1

        validNodeTypes = ['residential', 'commercial', 'government']
        if (self.data['provider']['nodeType'] not in validNodeTypes):
            if not self.setNodeType(config.CONFIG.CAP.nodeType):
                return False

        if (len(self.data['provider']['id']) != 64 or not re.match(r'[a-zA-Z0-9]', self.data['provider']['id'])):
            if not self.setProviderId(config.CONFIG.CAP.providerid):
                return False
        
        if(not self.data['provider']['name'] or len(self.data['provider']['name']) > 16):
            if not self.setProviderName(config.CONFIG.CAP.providerName):
                return False

        if (not self.data['provider']['wallet'] or len(self.data['provider']['wallet']) != 97):
            if not self.setWalletAddr(config.CONFIG.CAP.walletAddr):
                return False

        if (not self.data['provider']['terms'] or len(self.data['provider']['terms']) > 50000):
            if not self.setProviderTerms(cap.providerTerms):
                return False

        if (not self.data['provider']['certificates'] or len(self.data['provider']['certificates']) < 1):
            if not self.loadCertificate(cap.providerCa):
                # need to use exit() here or the script will loop
                # above it loops intentionally to get user input but here it's pointless
                sys.exit(1)

        return True

    def loadCertificate(self, ca=None):
        if (self.certsDir is None and ca is None):
            log.L.error('Failed to locate certificates!')
            return False
        else:
            if (ca):
                caCert = ca
            else:
                caCert = self.certsDir + '/ca.cert.pem'

            if (not os.path.isfile(caCert)):
                log.L.error('Failed to find CA cert file %s! Did you run `make ca PASS="password"`?' % caCert)
                return False
            try:
                f = open(caCert, 'r')
                caCertContents = f.read()
                f.close()
            except IOError:
                log.L.error("Failed to read %s" % caCert)
                return False

            certStart = "-----BEGIN CERTIFICATE-----"
            certEnd = "-----END CERTIFICATE-----"
            if (caCertContents and certStart in caCertContents and certEnd in caCertContents):
                caCertContents = re.sub(r'[\n\r]+', '', caCertContents)
                """start = caCertContents.index(certStart)                
                caCertParsed = caCertContents[start + len(certStart):]
                end = caCertParsed.index(certEnd)
                caCertParsed = caCertParsed[:end]"""
                caCertParsed = caCertContents
                log.L.info('Found new CA cert %s..%s, adding to config' % (caCertParsed[:8], caCertParsed[len(caCertParsed) - 5:len(caCertParsed)]))
                if not self.data['provider']['certificates']:
                    self.data['provider']['certificates'] = []

                certObjectToAppend = {}
                certObjectToAppend['content'] = caCertParsed
                certObjectToAppend['id'] = 0
                certObjectToAppend['cn'] = 'ignored' #remove after SDP is updated - this field is unnecessary

                self.data['provider']['certificates'].append(certObjectToAppend)
                return True
            else:
                log.L.error('CA certificate file: %s' % caCert)
                log.L.error('The CA certificate file does not contain the expected contents. Try deleting it and running `make ca` again.')
                return False
        return False
    
    def setCertificates(self, crt):
        self.data['provider']['certificates'] = {}
        self.data['provider']['certificates']['cn'] = 'ignored'
        self.data['provider']['certificates']['id'] = 0
        self.data['provider']['certificates']['content'] = crt
        return True
    
    def getCertificates(self):
        certStart = "-----BEGIN CERTIFICATE-----"
        certEnd = "-----END CERTIFICATE-----"
        ca = self.data['provider']['certificates'][0]['content']
        p = re.search(certStart + '(.*)' + certEnd, ca)
        if (p):
            ca = certStart + '\n' + p.group(1) + '\n' + certEnd
            return(ca)
        else:
            return(ca)
    
    def getProviderId(self):
        return(self.data['provider']['id'])

    def setProviderId(self, providerid=None):
        if (providerid == None):
            print('Enter provider ID (PUBLIC KEY). This should come directly from `lthnvpnd.py --generate-providerid FILE` - make sure it is the file ending in .public, not .seed or .private!')
            choice = input('[64 character hexadecimal] ').strip()
        else:
            choice = providerid
        if (len(choice) == 64 and re.match(r'^[a-zA-Z0-9]+$', choice)):
            self.data['provider']['id'] = choice
            return True
        else:
            log.L.error('Provider ID format or length bad. The ID must be exactly 64 hexadecimal characters.')
            return self.setProviderId()

    def setProviderTerms(self, terms=None):
        if (terms == None):
            choice = input('Enter provider terms. These will be displayed to users. Up to 50000 characters. ').strip()[:50000]
        else:
            choice = terms
        if not choice:
            choice = 'None'

        self.data['provider']['terms'] = choice
        return True

    def setWalletAddr(self, addr=None):
        if (addr == None):
            choice = input('Enter wallet address. This wallet will receive all payments for services. ').strip()
        else:
            choice = addr
        if (len(choice) != 97):
            log.L.error('Wallets should be exactly 97 characters. Are you sure you entered a real wallet address?')
            return self.setWalletAddr()
        if (choice[:2] != 'iz'):
            log.L.error('Wallet addresses must start with iz. Do not enter an integrated address; one will be automatically generated for every client.')
            return self.setWalletAddr()

        self.data['provider']['wallet'] = choice
        return True
    
    def getProviderName(self):
        return(self.data['provider']['name'])

    def setProviderName(self, name=None):
        if (name == None):
            choice = input('Enter provider name. This will be displayed to users. Use up to 16 alphanumeric characters, symbols allowed: ')
        else:
            choice = name
        if (len(choice) <= 16 and re.match(r'^[a-zA-Z0-9 ,.-_]+$', choice)):
            self.data['provider']['name'] = choice
            return True
        else:
            log.L.error('Invalid provider name!')
            return self.setProviderName()
        
    def getServiceById(self, sid):
        for item in self.data["services"]:
            if sid==item['id']:
                return(item)

    def setNodeType(self, type):
        self.data['provider']['nodeType'] = type
        return True
        
    def getJson(self):
        self.load(None)
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=3)
        json = jsonpickle.encode(self.data, unpicklable=False)
        log.L.debug('Encoded SDP JSON: %s' % json)
        return json

    def save(self, cfg):
        self.load(None)
        if (self.configFile and self.dataLoaded):
            jsonStr = self.getJson()
            try:
                f = open(self.configFile, 'w')
                f.write(jsonStr)
                f.close()
                print('SDP configuration saved to %s' % self.configFile)
            except IOError:
                log.L.error("Cannot write %s" % (self.configFile))
                sys.exit(1)
                
    def loadJson(self, j):
        self.data=j
        self.dataLoaded=True
        return(True)
        
    def load(self, cfgf, prefix=None):
        if self.dataLoaded:
            return

        if prefix != None:
            self.certsDir = prefix + '/etc/ca/certs'
            if not os.path.exists(self.certsDir):
                log.L.error('Certs directory does not exist or is unreadable (%s)!' % self.certsDir)
                log.L.error('Make sure you ran `make install` without errors.')
                self.certsDir = None

        if (self.configFile is None):
            self.configFile = cfgf
        try:
            if (self.configFile != None):
                f = open(self.configFile, 'r')
                jsonStr = f.read()
                f.close()
                self.data = jsonpickle.decode(jsonStr)
            self.dataLoaded = True            
        except IOError:
            log.L.error("Cannot read SDP file %s" % (self.configFile))
            
    def upload(self, cfg):
        """
        Upload JSON to SDP
        """
        jsonConfig = self.getJson()
        if not jsonConfig:
            log.L.error('Failed to load config for uploading! Make sure the SDP config path is correct.')
            return False

        payload = base64.urlsafe_b64encode(jsonConfig.encode('utf-8'))

        # begin ed25519 signing
        header = base64.urlsafe_b64encode(b'{"alg":"EdDSA"}')
        signingInput = payload
        key  = cfg.CAP.providerkey
        if (not key or len(key) != 64 or not re.match(r'^[a-zA-Z0-9]+$', key)):
            log.L.error('Invalid private key entered, must be 64 hexadecimal characters.')
            return False

        signing_key = ed25519.SigningKey(key.encode("utf-8"), encoding="hex")
        signedPayload = signing_key.sign(signingInput)
        verifying_key = ed25519.VerifyingKey(cfg.CAP.providerid, encoding="hex")
        if verifying_key.to_ascii(encoding="hex").lower() != signing_key.get_verifying_key().to_ascii(encoding="hex").lower():
            log.L.warning('Provider ID may be incorrect - failed to match provider ID to private-derived public key!')

        try:
            verifying_key.verify(signedPayload, signingInput)
            log.L.info('Signed data validated successfully!')
        except ed25519.BadSignatureError:
            log.L.error(base64.urlsafe_b64decode(signingInput).decode("utf-8"))
            log.L.error('Failed to validate signed data for SDP. Are you sure you entered a valid private key?')
            return False

        encodedSignedPayload = signedPayload.hex()
        # end ed25519 signing

        sdpAddServiceEndpoint = cfg.CAP.sdpUri['sdp'] + '/services/add/'

        log.L.info('Using SDP endpoint %s' % sdpAddServiceEndpoint)

        request = Request(sdpAddServiceEndpoint, jsonConfig.encode())
        request.add_header('JWS', header.decode('utf-8') + '.' + signingInput.decode('utf-8') + '.' + encodedSignedPayload)
        log.L.debug('JWS header: ' + header.decode('utf-8') + '.' + signingInput.decode('utf-8') + '.' + encodedSignedPayload)
        request.add_header('Content-Type', 'application/json')
        
        try:
            response = urlopen(request).read()
            jsonResp = json.loads(response.decode('utf-8'))
            if jsonResp and jsonResp['status'] == '0':
                log.L.warning('SDP upload succeeded!')
            else:
                log.L.error('SDP upload server response: %s' % response)
            return True
        except HTTPError as err:
            error_message = err.read()
            if error_message:
                try:
                    jsonErr = json.loads(error_message.decode('utf-8'))
                except json.decoder.JSONDecodeError:
                    log.L.error('Failed to parse JSON from SDP.')
            if not jsonErr or not self.handleSdpError(jsonErr):
               	log.L.error('Request headers %s' % request.headers)
               	log.L.error('Request data %s' % request.data)
               	log.L.error('Error %s sending data to SDP server: %s\n\n%s\n%s' % (error_message, err.code, err.reason, err.headers))

        return False
    
    def handleSdpError(self, jsonErr):
        if jsonErr and jsonErr['status']:
            log.L.error('Failed to upload service/provider config to SDP server!')
            if jsonErr['status'] == '1000' and 'Payment_id' in jsonErr['message']:
                log.L.error('You must send payment to the SDP before your service(s) will be uploaded! See documentation.')
            elif jsonErr['status'] == '1000':
                log.L.error('%s' % jsonErr['message'])
            elif jsonErr['status'] == '2000':
                log.L.error('Error validating your service config: %s' % jsonErr['message'])
            elif jsonErr['status'] == '5000':
                log.L.error('Error in protocol version. Sdp.jsonErr format may be incorrect or your dispatcher is out of date.')
            else:
                if jsonErr['message']:
                    log.L.error('Error in SDP config: %s' % jsonErr['message'])
                else:
                    log.L.error('Error in SDP config: %s' % jsonErr)

            return True
        else:
            return False

    def listServices(self):
        ret = []
        for item in self.data["services"]:
            ret.append(item['id'])
        return(ret)
    
    def getService(self, id):
        for item in self.data["services"]:
            if item['id'] == id:
                return item

        return False
            

class SDPService(object):
    # sample SDPService dict
    data = dict(
                id=None,
                disable=False,
                name=None,
                type=None,
                allowRefunds=False,
                cost=0.01,
                downloadSpeed=None,
                uploadSpeed=None,
                firstPrePaidMinutes=30,
                subsequentPrePaidMinutes=30,
                firstVerificationsNeeded=0,
                subsequentVerificationsNeeded=1,
                proxy=dict(
                    certificates=[],
                    endpoints=[],
                    port='',
                    terms='',
                    policy=dict(
                        addresses=dict(
                        blocked=[]
                        )
                    )
                ),
                vpn=dict(
                    certificates=[],
                    endpoints=[],
                    port='',
                    terms='',
                    policy=dict(
                        addresses=dict(
                            blocked=[]
                        )
                    ),
                    parameters=dict(
                        cyphers=[
                            "DESX-CBC",
                            "AES-256-CBC"
                        ],
                        mtuSize=1
                    )
                )
                )
    existingServiceIds = []
    certsDir = None

    def __init__(self, existingServiceIds_, thisService=None, certsDir=None):
        self.existingServiceIds = existingServiceIds_

        if (certsDir != None):
            self.certsDir = certsDir
            if not os.path.exists(self.certsDir):
                log.L.error('Certs directory does not exist (%s)! Make sure you ran `make install` without errors.' % self.certsDir)
                self.certsDir = None

        if (thisService != None):
            self.data = jsonpickle.decode(thisService)
            log.L.info('Loaded existing SDP service %s' % self.data['name'])
        else:
            log.L.info('Creating new SDP service...')

    def checkConfig(self, cap, id=None):
        if not id:
            self.setId(cap.serviceId)
        else:
            self.setId(id)
        ret = False
        
        while not ret:
            log.L.info('Setting service name')
            ret = self.setName(cap.serviceName)
        ret = False
        while not ret:
            log.L.info('Setting service type')
            ret = self.setType(cap.serviceType)
        ret = False
        while not ret:
            log.L.info('Setting service port')
            ret = self.setPort(cap.servicePort)
        ret = False
        while not ret:
            log.L.info('Setting service endpoint')
            ret = self.setEndpoints(cap.serviceFqdn)
        ret = False
        if not self.loadCertificate(cap.serviceCrt):
            sys.exit(1)
        ret = False
        while not ret:
            log.L.info('Setting service cost')
            ret = self.setCost(cap.serviceCost)
        ret = False
        while not ret:
            log.L.info('Setting service allow refunds')
            ret = self.setAllowRefunds(cap.serviceAllowRefunds)
        ret = False
        while not ret:
            log.L.info('Setting service disable')
            ret = self.setDisable(cap.serviceDisable)
        ret = False
        while not ret:
            log.L.info('Setting service download speed')
            ret = self.setDownloadSpeed(int(cap.serviceDownloadSpeed) * 1000 * 1000)
        ret = False
        while not ret:
            log.L.info('Setting service upload speed')
            ret = self.setUploadSpeed(int(cap.serviceUploadSpeed) * 1000 * 1000)
        ret = False
        while not ret:
            log.L.info('Setting service prepaid minutes')
            ret = self.setPrepaidMinutes(cap.servicePrepaidMinutes)
        ret = False
        while not ret:
            log.L.info('Setting service verifications needed')
            ret = self.setVerificationsNeeded(cap.serviceVerificationsNeeded)

        return True

    def setPort(self, port=None):
        nodeType = self.data['type']
        
        if (nodeType == 'openvpn'):
            nodeType = 'vpn'

        if nodeType not in self.data:
            self.data[nodeType] = []

        choice = ''
        count = 0
        validPortFound = False

        for i in self.data[nodeType]:
            validPortFound = False
            if 'port' not in i:
                i['port'] = ''

            if (self.isValidPort(i['port'])):
                validPortFound = True
                if (port):
                    choice = port
                else:
                    print('Existing proxy/VPN port for endpoint %s: %s' % (i['endpoint'], i['port']))
                    choice = input('Enter new proxy/VPN port [1-65535] [leave blank to keep existing] ')
                    
                if choice: 
                    break
            else:
                print('Existing proxy/VPN port for endpoint %s (%s) is empty or incorrect and must be resolved' % (i['endpoint'], i['port']))
                if (port):
                    choice = port
                else:
                    choice = input('Enter proxy/VPN port [1-65535] ') 
                if choice: break

            count += 1

        if (not choice and count == 0 and not validPortFound):
            if (port):
                choice = port
            else:
                choice = input('Enter proxy/VPN port [1-65535] ')

        if (not validPortFound and self.isValidPort(choice)):
            if len(self.data[nodeType]) == 0 or 'port' not in self.data[nodeType][count]:
                self.data[nodeType].append({})
            # TODO add support to collect UDP or other protocols for the port
            self.data[nodeType][count]['port'] = choice + '/TCP'
            return True
        elif validPortFound:
            return True
        else:
            log.L.error('The port you entered is not a valid number from 1 to 65535.')

        return False


    def setEndpoints(self, endpoint):
        nodeType = self.data['type']
        
        if (nodeType == 'openvpn'):
            nodeType = 'vpn'

        if nodeType not in self.data:
            self.data[nodeType] = []

        choice = ''
        count = 0
        validEndpointFound = False

        for i in self.data[nodeType]:
            validEndpointFound = False
            if 'endpoint' not in i:
                i['endpoint'] = ''

            if (self.isValidEndpoint(i['endpoint'])):
                validEndpointFound = True
                if (endpoint):
                    choice = endpoint
                else:
                    print('Existing proxy/VPN endpoint (service %d): %s' % (count, i['endpoint']))
                    choice = input('Enter new proxy/VPN endpoint in IP or FQDN format [leave blank to keep existing] ')
                if choice: 
                    break
            else:
                if (endpoint):
                    choice = endpoint
                else:
                    choice = input('Found new service. Enter proxy/VPN endpoint in IP or FQDN format ') 
                if choice: break

            count += 1

        if (not choice and count == 0 and not validEndpointFound):
            if (endpoint):
                choice = endpoint
            else:
                choice = input('Enter proxy/VPN endpoint in IP or FQDN format ')

        if (not validEndpointFound and self.isValidEndpoint(choice)):
            if len(self.data[nodeType]) == 0 or 'endpoint' not in self.data[nodeType][count]:
                self.data[nodeType].append({})

            self.data[nodeType][count]['endpoint'] = choice
            return True
        elif validEndpointFound:
            choice = input('Finished evaluating endpoints for this service. Would you like to add a new endpoint? [Y/n] ')
            if (choice.strip().lower() == 'y'):
                self.data[nodeType].append({})
                print('You will now be asked to re-evaluate the current endpoints before adding anew...')
                return False
            return True
        else:
            log.L.error('The endpoint you entered is not a valid IP (eg 172.16.1.1) or FQDN (eg my.test.com).')

        return False

    def isValidPort(self, testPort):
        if '/' in testPort:
            testPort = testPort[0:testPort.index('/')]
        if not testPort.isnumeric():
            return False
        testPort = int(testPort)
        if (testPort > 0 and testPort < 65535):
            return True
        else:
            return False

    def isValidEndpoint(self, testEndpoint):
        return re.match(r'((^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$))|(^\s*((?=.{1,255}$)(?=.*[A-Za-z].*)[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?(?:\.[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?)*)\s*$)', testEndpoint)

    def getJson(self):
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=3)
        json = jsonpickle.encode(self.data, unpicklable=False)
        log.L.info('Encoded SDP Service JSON: %s' % json)
        return json

    def loadCertificate(self, crt):

        #SDP now expects only the CA? to be determined - for now we hardcode id 0
        if 'certificates' not in self.data:
            self.data['certificates'] = []
            certObject = {}
            certObject['id'] = 0
            self.data['certificates'].append(certObject)   

        return True     
        #end hardcode       

        if (self.certsDir is None):
            if (crt is None):
                log.L.error('Failed to locate certificates!')
                return False
            
        if self.data['type'] == 'proxy':
            if (crt):
                cert = crt
            else:
                cert = self.certsDir + '/ha.cert.pem'
        elif self.data['type'] == 'vpn':
            if (crt):
                cert = crt
            else:
                cert = self.certsDir + '/openvpn.cert.pem'
        else:
            log.L.error('Failed to parse service type. Unable to load certificate.')
            return False

        if (not os.path.isfile(cert)):
            log.L.error('Failed to find CA cert file %s! Did you run `make ca PASS="password"`?' % cert)
            return False

        try:
            f = open(cert, 'r')
            certContents = f.read()
            f.close()
        except IOError:
            log.L.error("Failed to read %s" % cert)
            return False

        certStart = "-----BEGIN CERTIFICATE-----"
        certEnd = "-----END CERTIFICATE-----"
        if (certContents and certStart in certContents and certEnd in certContents):
            certContents = re.sub(r'[\n\r]+', '', certContents)
            """start = certContents.index(certStart)                
            certParsed = certContents[start + len(certStart):]
            end = certParsed.index(certEnd)
            certParsed = certParsed[:end]            
            """
            certParsed = certContents

            nodeType = self.data['type']

            if (nodeType == 'openvpn'):
                nodeType = 'vpn'

            if not self.data[nodeType]:
                self.data[nodeType] = []

            for i in self.data[nodeType]:
                if 'certificates' not in i:
                    i['certificates'] = []                    

                if (certParsed not in i['certificates']):
                    print('Found new proxy/VPN cert %s..%s, adding to config' % (certParsed[:8], certParsed[len(certParsed) - 5:len(certParsed)]))
                    i['certificates'].append(certParsed)         
       
            return True

        else:
            log.L.error('Certificate file: %s' % cert)
            log.L.error('The certificate file does not contain the expected contents. Try deleting it and running `make ca` again.')
            return False

        return False

    def setPrepaidMinutes(self, mins=None):
        if (mins):
            self.data['firstPrePaidMinutes'] = int(mins)
            return True
        
        print('How many minutes of access are required to be prepaid for the first payment from a client? Minimum 10, maximum 1440 minutes.')
        if (self.data['firstPrePaidMinutes'] and int(self.data['firstPrePaidMinutes']) >= 10 and int(self.data['firstPrePaidMinutes']) <= 1440):
            print('Existing value: %d' % self.data['firstPrePaidMinutes'])
            choice = input('Enter new number of minutes [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of minutes ').strip()

        if (choice):
            choice = int(choice)
            if (choice >= 10 and choice <= 1440):
                self.data['firstPrePaidMinutes'] = int(choice)
        else:
            if (not self.data['firstPrePaidMinutes']):
                return False

        # TODO limitations on things like number of prepaid minutes should come from a template at SDP server, or be 
        # hardcoded with much more lenient restrictions to allow for expansion of accepted values on the SDP later
        print('How many minutes of access are required to be prepaid for subsequent payments (after the first payment) from a client? Minimum 2, maximum 1440 minutes.')
        if (self.data['subsequentPrePaidMinutes'] and int(self.data['subsequentPrePaidMinutes']) > 1 and int(self.data['subsequentPrePaidMinutes']) <= 1440):
            print('Existing value: %d' % self.data['subsequentPrePaidMinutes'])
            choice = input('Enter new number of minutes [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of minutes ').strip()

        if (choice):
            choice = int(choice)
            if (choice > 1 and choice <= 1440):
                self.data['subsequentPrePaidMinutes'] = int(choice)
                return True
        else:
            if (self.data['subsequentPrePaidMinutes']):
                return True

        return False

    def setVerificationsNeeded(self, verifications=None):
        if (verifications):
            self.data['firstVerificationsNeeded'] = int(verifications)
            return True
        
        print('How many transaction confirmations are required for the first payment from a client? Minimum 0, maximum 2.')
        if (self.data['firstVerificationsNeeded'] and int(self.data['firstVerificationsNeeded']) >= 0 and int(self.data['firstVerificationsNeeded']) <= 2):
            print('Existing value: %d' % self.data['firstVerificationsNeeded'])
            choice = input('Enter new number of confirmations required [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of confirmations required ').strip()

        if (choice):
            choice = int(choice)
            if (choice >= 0 and choice <= 5):
                self.data['firstVerificationsNeeded'] = int(choice)
        else:
            if (not self.data['firstVerificationsNeeded']):
                return False

        # TODO limitations on things like number of prepaid minutes should come from a template at SDP server, or be 
        # hardcoded with much more lenient restrictions to allow for expansion of accepted values on the SDP later
        print('How many transaction confirmations are required for subsequent payments (after the first payment) from a client? Minimum 0, maximum 1.')
        if (self.data['subsequentVerificationsNeeded'] and int(self.data['subsequentVerificationsNeeded']) >= 0 and int(self.data['subsequentVerificationsNeeded']) <= 1):
            print('Existing value: %d' % self.data['subsequentVerificationsNeeded'])
            choice = input('Enter new number of subsequent confirmations required [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of subsequent confirmations required ').strip()

        if (choice):
            choice = int(choice)
            if (choice >= 0 and choice <= 1):
                self.data['subsequentVerificationsNeeded'] = choice
                return True
        else:
            if (self.data['subsequentVerificationsNeeded']):
                return True

        return False

    def setDisable(self, disable):
        self.data['disable'] = disable
        return True

    def setAllowRefunds(self, allow):
        self.data['allowRefunds'] = allow
        return True

    def setDownloadSpeed(self, speed=None):
        if (speed):
            self.data['downloadSpeed'] = int(speed)
            return True
        
        # TODO automate collection of node download/upload speed - consider github.com/sivel/speedtest-cli
        print('When entering download and upload speeds, it is strongly encouraged to be honest!')
        print('If you intentionally mislead users with forged speeds, you will likely receive poor reviews!')

        if (self.data['downloadSpeed'] and int(self.data['downloadSpeed']) > 0):
            print('Existing configured download speed: %d' % self.data['downloadSpeed'])
            choice = input('Enter new download speed per client in Mbits? [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter download speed per client in Mbits ').strip()

        if (choice):
            choice = int(choice)
            if (choice > 0 and choice < 99999999999):
                self.data['downloadSpeed'] = int(choice)
                return True
        else:
            if (self.data['downloadSpeed']):
                return True
        
        return False

    def setUploadSpeed(self, speed=None):
        if (speed):
            self.data['uploadSpeed'] = int(speed)
            return True
        
        # TODO automate collection of node download/upload speed - consider github.com/sivel/speedtest-cli

        if (self.data['uploadSpeed'] and int(self.data['uploadSpeed']) > 0):
            print('Existing configured upload speed: %d' % self.data['uploadSpeed'])
            choice = input('Enter new upload speed per client in Mbits? [leave blank to keep existing] ')
        else:
            choice = input('Enter upload speed per client in Mbits ')

        if (choice):
            choice = int(choice)
            if (choice > 0 and choice < 99999999999):
                self.data['uploadSpeed'] = int(choice)
                return True
        else:
            if (self.data['uploadSpeed']):
                return True
        
        return False


    def setCost(self, cost):
        if (self.data['cost']):
            if (cost):
                choice = float(cost)
            else:
                print('Existing cost: %.8f' % float(self.data['cost']))
                choice = input('Enter new cost? [leave blank to keep existing] ')
        else:
            if (cost):
                choice = cost
            else:
                choice = input('Enter cost: ').strip()

        if (choice):
            choice = float(choice)
            if (choice < 0.00000001):
                log.L.error('Cost must be at least 0.00000001!')
                return self.setCost()
            self.data['cost'] ="{:1.8f}".format(choice)
            return True
        else:
            if self.data['cost']:
                self.data['cost'] ="{:1.8f}".format(float(self.data['cost']))
                return True

        return False

    def setName(self, name=None):
        
        if (name == None):
            print('Specify name of service [32 characters, numbers and spaces allowed] ')

        if self.data['name']:
            print('Existing service name: %s' % self.data['name'])
            if (name):
                choice = name
            else:
                choice = input('New service name? [leave blank to keep existing] ').strip()
        else:
            if (name):
                choice = name
            else:
                choice = input('Enter service name: ').strip()

        if (choice):
            if (len(choice) <= 32 and re.match(r'^[a-zA-Z0-9 ,.-_]+$', choice)):
                self.data['name'] = choice
                return True
            else:
                log.L.error('Invalid service name format. Must be 32 characters or less. Allowed characters a-z 0-9 ,.-_')
        else:
            if self.data['name']:
                return True

        return False

    def setId(self, id=None):
        # we use two hex digits to represent the service ID (range = 16 [0x10] to 255 since two digits must be used)
        # auto increment
        if (id):
            self.data['id'] = id.upper()
        elif self.existingServiceIds and len(self.existingServiceIds) > 0:
            val = int(self.existingServiceIds[len(self.existingServiceIds) - 1], base=16)
            if (val <= 254):
                self.data['id'] = str(format(val + 1, 'X'))
            else:
                # TODO add code to restart service count from 0 and/or scan existingServiceIds to find an unused ID (if possible)
                log.L.critical('Only 240 services are supported! If you encountered this error, please contact the team to add code to support more services!')
                sys.exit(1)
        else:
            self.data['id'] = "1A"

    def setType(self, type):
        if self.data['type']:
            print('Existing service type: %s' % self.data['type'])
            print('Warning! If you switch service types (eg proxy to VPN), the existing proxy/VPN services will be erased!')
            if (type):
                choice = type
            else:
                choice = input('Select new service type? Enter [V]PN or [P]roxy, or leave blank to keep existing. ').strip().lower()[:1]
        else:
            if (type):
                choice = type
            else:
                choice = input('Which type of service is this? vpn or proxy? ').strip().lower()

        if (choice == 'proxy' or choice == 'p'):
            self.data['type'] = 'proxy'
            self.data['proxy'] = []
            self.data['vpn'] = []
            return True
        elif (choice == 'vpn' or choice == 'v'):
            self.data['type'] = 'vpn'
            self.data['proxy'] = []
            self.data['vpn'] = []
            return True
        else:
            if self.data['type'] == 'proxy' or self.data['type'] == 'vpn':
                return True

            log.L.error('Invalid option selected. Enter P for proxy or V for VPN.')
            return self.setType()
