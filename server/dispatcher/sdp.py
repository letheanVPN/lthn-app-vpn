
import json
import logging
import sys
import re
import jsonpickle

class SDP(object):
    configFile = None
    dataLoaded = False
    # sample SDP dict
    data = dict(
        protocolVersion = 1,
        nodeType = '',
        provider = dict(
            id = '',
            name = ''
        ),
        certificates = {},
        wallet = 'publicWalletAddress',
        terms = 'Provider Terms',
        services = {},
    )

    """SDP functions"""
    def addService(self):
        # Create new SDP service
        self.load(None)
        ret = False
        while not ret:
            ret = self.isConfigured()

        s = SDPService(self.getUsedServiceIds())
        ret = False
        while not ret:
            ret = s.checkConfig()

        #FIXME cannot append raw JSON - need to append it as a dict
        #if ret:
        #    self.data['services'].append(s.getJson())

    def getUsedServiceIds(self):
        serviceIds = []
        for i in self.data['services']:
            serviceIds.append(i['id'])
        return serviceIds

    def editService(self):
        # Revise existing SDP service
        self.load(None)
        ret = False
        while not ret:
            ret = self.isConfigured()

        if (not self.data['services'] or len(self.data['services']) == 0):
            addService()
            return

        print('Select a service to edit (enter the number only): ')
        count = 1

        for i in self.data['services']:
            print('%d: %s [%s] [cost %.8f] (ID %s)' % (count, i['name'], i['type'], i['cost'], i['id']))
            count+=1

        choice = input('Select a service to edit (enter the number only): ')
        if (choice.isnumeric()):
            choice=int(choice) - 1
            if self.data['services'][choice]:
                # Select service and begin editing
                print('Editing service %s (ID %s)' % (self.data['services'][choice]['name'], self.data['services'][choice]['id']))
                encoded = jsonpickle.encode(self.data['services'][choice], unpicklable=False)
                # TODO add edit capabilities
                s = SDPService(self.getUsedServiceIds(), encoded)
                ret = False
                while not ret:
                    ret = s.checkConfig()

                #FIXME cannot replace with raw JSON - need to replace it as a dict
                #if ret:
                #    self.data['services'][choice] = s.getJson()
            else:
                logging.error('Invalid selection')
        else:
            logging.error('Invalid selection')

    def isConfigured(self):
        # Checks validity of data and forces configuration if invalid
        self.load(None)

        if (not isinstance(self.data['protocolVersion'], int) or
            self.data['protocolVersion'] < 1):
            logging.error('Invalid protocol version (%s)! Setting to 1.' % self.data['protocolVersion'])
            self.data['protocolVersion'] = 1

        validNodeTypes = ['residential', 'commercial', 'government']
        if (self.data['nodeType'] not in validNodeTypes):
            logging.error('Invalid node type.')
            if not self.setNodeType():
                return False

        if (len(self.data['provider']['id']) != 64 or not re.match('[a-zA-Z0-9]', self.data['provider']['id'])):
            if not self.setProviderId():
                return False

        if(not self.data['provider']['name'] or len(self.data['provider']['name']) > 16):
            if not self.setProviderName():
                return False

        if (not self.data['wallet'] or len(self.data['wallet']) != 97):
            if not self.setWalletAddr():
                return False

        if (not self.data['terms'] or len(self.data['terms']) > 50000):
            if not self.setProviderTerms():
                return False

        if (not self.data['certificates'] or len(self.data['certificates']) < 1):
            # TODO encode certs
            print('WARNING: No provider certificates found!')

        return True

    def setProviderId(self):
        print('Enter provider ID. This should come directly from `itnsdispatcher.py --generate-providerid FILE`')
        choice = input('[64 character hexadecimal] ').strip()
        if (len(choice) == 64 and re.match('^[a-zA-Z0-9]+$', choice)):
            self.data['provider']['id'] = choice
            return True
        else:
            logging.error('Provider ID format or length bad. The ID must be exactly 64 hexadecimal characters.')
            return False

    def setProviderTerms(self):
        choice = input('Enter provider terms. These will be displayed to users. Up to 50000 characters. ').strip()[:50000]
        if not choice:
            choice = 'None'

        self.data['terms'] = choice
        return True

    def setWalletAddr(self):
        choice = input('Enter wallet address. This wallet will receive all payments for services. ').strip()
        if (len(choice) != 97):
            logging.error('Wallets should be exactly 97 characters. Are you sure you entered a real wallet address?')
            return False
        if (choice[:2] != 'iz'):
            logging.error('Wallet addresses must start with iz. Do not enter an integrated address; one will be automatically generated for every client.')
            return False

        self.data['wallet'] = choice
        return True

    def setProviderName(self):
        choice = input('Enter provider name. This will be displayed to users. Use up to 16 alphanumeric characters, symbols allowed: ')
        if (len(choice) <= 16 and re.match('^[a-zA-Z0-9 ,.-_]+$', choice)):
            self.data['provider']['name'] = choice
            return True
        else:
            logging.error('Invalid provider name!')
            return False

    def setNodeType(self):
        choice = input('Enter provider type. [c]ommercial, [r]esidential, or [g]overnment? ').strip().lower()[:1]
        if (choice == 'c'):
            self.data['nodeType'] = 'commercial'
            return True
        elif (choice == 'r'):
            self.data['nodeType'] = 'residential'
            return True
        elif (choice == 'g'):
            self.data['nodeType'] = 'government'
            return True

        logging.error('Invalid provider type specified.')
        return False
    
    def getJson(self):
        self.load(None)
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=3)
        json = jsonpickle.encode(self.data, unpicklable=False)
        logging.info('Encoded SDP JSON: %s' % json)
        return json

    def save(self):
        self.load(None)
        if (self.configFile and self.dataLoaded):
            jsonStr = self.getJson()
            try:
                f = open(self.configFile, 'w')
                f.write(jsonStr)
                f.close()
                print('SDP configuration saved to %s' % self.configFile)
            except IOError:
                logging.error("Cannot write %s" % (self.configFile))
                sys.exit(1)

    def load(self, config):
        if self.dataLoaded:
            return

        if (self.configFile is None):
            self.configFile = config
        try:
            f = open(self.configFile, 'r')
            jsonStr = f.read()
            f.close()
            self.data = jsonpickle.decode(jsonStr)
            self.dataLoaded = True            
        except IOError:
            logging.error("Cannot read %s" % (self.configFile))
            sys.exit(1)
    def upload(self):
        """
        Upload to SDP server..
        """
    
    def listServices(self):
        ret = dict()
        for service in self.data["services"]:
            ret[service["id"]] = service["id"]
        return(ret)
    
    def getService(self, id):
        for value in self.data["services"]:
            if (value["id"] == id): 
                return(value)
            

class SDPService(object):
    # sample SDPService dict
    data = dict(
        id = '',
        name = '',
        type = 'proxy',
        allowRefunds = False,
        cost = 0.00000001,
        downloadSpeed = 100000,
        uploadSpeed = 100000,
        firstPrePaidMinutes = 2,
        subsequentPrePaidMinutes = 2,
        firstVerificationsNeeded = 1,
        subsequentVerificationsNeeded = 1,
        proxy = {},
        vpn = {},
    )
    existingServiceIds = []

    def __init__(self, existingServiceIds_, thisService = None):
        self.existingServiceIds = existingServiceIds_
        if (thisService != None):
            self.data = jsonpickle.decode(thisService)
            print('Loaded existing SDP service %s' % self.data['name'])
        else:
            print('Creating new SDP service...')

    def setup(self):
        print('You will be prompted to enter a series of information about the service.')

    def checkConfig(self):
        self.setId()
        ret = False
        while not ret:
            ret = self.setName()
        ret = False
        while not ret:
            ret = self.setType()
        ret = False
        while not ret:
            ret = self.setCost()
        ret = False
        while not ret:
            ret = self.setAllowRefunds()
        ret = False
        while not ret:
            ret = self.setDownloadSpeed()
        ret = False
        while not ret:
            ret = self.setUploadSpeed()
        ret = False
        while not ret:
            ret = self.setPrepaidMinutes()
        ret = False
        while not ret:
            ret = self.setVerificationsNeeded()

        # TODO add support for generating and configuring proxy and VPN dicts

        return True

    def getJson(self):
        json = jsonpickle.encode(self.data, unpicklable=False)
        logging.info('Encoded SDP Service JSON: %s' % json)
        return json

    def setPrepaidMinutes(self):
        print('How many minutes of access are required to be prepaid for the first payment from a client? Minimum 1, maximum 5 minutes.')
        if (self.data['firstPrePaidMinutes'] and int(self.data['firstPrePaidMinutes']) > 0 and int(self.data['firstPrePaidMinutes']) <= 5):
            print('Existing value: %d' % self.data['firstPrePaidMinutes'])
            choice = input('Enter new number of minutes [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of minutes ').strip()

        if (choice):
            choice = int(choice)
            if (choice > 0 and choice <= 5):
                self.data['firstPrePaidMinutes'] = choice
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
                self.data['subsequentPrePaidMinutes'] = choice
                return True
        else:
            if (self.data['subsequentPrePaidMinutes']):
                return True

        return False

    def setVerificationsNeeded(self):
        print('How many transaction confirmations are required for the first payment from a client? Minimum 0, maximum 2.')
        if (self.data['firstVerificationsNeeded'] and int(self.data['firstVerificationsNeeded']) >= 0 and int(self.data['firstVerificationsNeeded']) <= 2):
            print('Existing value: %d' % self.data['firstVerificationsNeeded'])
            choice = input('Enter new number of confirmations required [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of confirmations required ').strip()

        if (choice):
            choice = int(choice)
            if (choice > 0 and choice <= 5):
                self.data['firstVerificationsNeeded'] = choice
        else:
            if (not self.data['firstVerificationsNeeded']):
                return False

        # TODO limitations on things like number of prepaid minutes should come from a template at SDP server, or be 
        # hardcoded with much more lenient restrictions to allow for expansion of accepted values on the SDP later
        print('How many transaction confirmations are required for subsequent payments (after the first payment) from a client? Minimum 0, maximum 1 minutes.')
        if (self.data['subsequentVerificationsNeeded'] and int(self.data['subsequentVerificationsNeeded']) >= 0 and int(self.data['subsequentVerificationsNeeded']) <= 1):
            print('Existing value: %d' % self.data['subsequentVerificationsNeeded'])
            choice = input('Enter new number of confirmations required [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter number of confirmations required ').strip()

        if (choice):
            choice = int(choice)
            if (choice >= 0 and choice <= 1):
                self.data['subsequentVerificationsNeeded'] = choice
                return True
        else:
            if (self.data['subsequentVerificationsNeeded']):
                return True

        return False


    def setAllowRefunds(self):
        self.data['allowRefunds'] = False
        return True

    def setDownloadSpeed(self):
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
                self.data['downloadSpeed'] = choice
                return True
        else:
            if (self.data['downloadSpeed']):
                return True
        
        return False

    def setUploadSpeed(self):
        # TODO automate collection of node download/upload speed - consider github.com/sivel/speedtest-cli

        if (self.data['uploadSpeed'] and int(self.data['uploadSpeed']) > 0):
            print('Existing configured upload speed: %d' % self.data['uploadSpeed'])
            choice = input('Enter new upload speed per client in Mbits? [leave blank to keep existing] ')
        else:
            choice = input('Enter upload speed per client in Mbits ')

        if (choice):
            choice = int(choice)
            if (choice > 0 and choice < 99999999999):
                self.data['uploadSpeed'] = choice
                return True
        else:
            if (self.data['uploadSpeed']):
                return True
        
        return False


    def setCost(self):
        print('Enter service cost in Intense Coin (ITNS) per minute. You may use up to 8 decimal places. Minimum 0.00000001')
        if (self.data['cost']):
            print('Existing cost: %.8f' % self.data['cost'])
            choice = input('Enter new cost? [leave blank to keep existing] ')
        else:
            choice = input('Enter cost: ').strip()

        if (choice):
            choice = float(choice)
            if (choice < 0.00000001):
                logging.error('Cost must be at least 0.00000001!')
                return False
            self.data['cost'] = choice
            return True
        else:
            if self.data['cost']:
                return True

        return False

    def setName(self):
        print('Specify name of service [32 characters, numbers and spaces allowed] ')

        if self.data['name']:
            print('Existing service name: %s' % self.data['name'])
            choice = input('New service name? [leave blank to keep existing] ').strip()
        else:
            choice = input('Enter service name: ').strip()

        if (choice):
            if (len(choice) <= 32 and re.match('^[a-zA-Z0-9 ,.-_]+$', choice)):
                self.data['name'] = choice
                return True
            else:
                logging.error('Invalid service name format. Must be 32 characters or less. Allowed characters a-z 0-9 ,.-_')
        else:
            if self.data['name']:
                return True

        return False

    def setId(self):
        # we use two hex digits to represent the service ID (range = 16 [0x10] to 255 since two digits must be used)
        # auto increment
        if self.existingServiceIds and len(self.existingServiceIds) > 0:
            val = int(self.existingServiceIds[len(self.existingServiceIds) - 1], base=16)
            if (val <= 254):
                self.data['id'] = format(val + 1, 'X')
            else:
                # TODO add code to restart service count from 0 and/or scan existingServiceIds to find an unused ID (if possible)
                logging.critical('Only 240 services are supported! If you encountered this error, please contact the team to add code to support more services!')
                sys.exit(1)
        else:
            self.data['id'] = 10

    def setType(self):
        if self.data['type']:
            print('Existing service type: %s' % self.data['type'])
            choice = input('Select new service type? Enter [V]PN or [P]roxy, or leave blank to keep existing. ').strip().lower()[:1]
        else:
            choice = input('Which type of service is this? [V]PN or [P]roxy? ').strip().lower()[:1]

        if (choice == 'p'):
            self.data['type'] = 'proxy'
            return True
        elif (choice == 'v'):
            self.data['type'] = 'vpn'
            return True
        else:
            if self.data['type']:
                return True

            logging.error('Invalid option selected. Enter P for proxy or V for VPN.')
            return False
