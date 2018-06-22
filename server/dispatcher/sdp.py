
import json
import logging
import sys
import re

class SDP(object):
    configFile = None
    data = dict(
        protocolVersion = 1,
        nodeType = '',
        provider = dict(
            id = '',
            name = ''
        ),
        certificates = dict(),
        wallet = 'publicWalletAddress',
        terms = 'Provider Terms',
        services = [],
    )

    """SDP functions"""
    def addService(self):
        # Create new SDP service
        self.load(None)
        if not isConfigured():
            print('Initial configuration validation check failed. Fix configuration errors and try again.')
            sys.exit(1)

    def editService(self):
        # Revise existing SDP service
        self.load(None)
        if not isConfigured():
            print('Initial configuration validation check failed. Fix configuration errors and try again.')
            sys.exit(1)

        if (not self.data.service or len(self.data.services) == 0):
            addService()
            return

        print('Select a service to edit (enter the number only): ')
        count = 1

        for i in self.data.services:
            print('%d: %s  (ID %s)' % (count, i.name, i.id))
            count+=1

        choice = input('Select a service to edit (enter the number only): ')
        if (choice.isnumeric()):
            if self.data.services[choice]:
                # Select service and begin editing
                print('Editing service %s (ID %s)' % (self.data.services[choice].name, self.data.services[choice].id))
                # TODO add edit capabilities
            else:
                print('Invalid selection')
        else:
            print('Invalid selection')

    def isConfigured(self):
        # Checks validity of data and forces configuration if invalid
        self.load()

        if (not self.data.protocolVersion.isnumeric()):
            print('Invalid protocol version (%s)! Setting to 1.' % self.data.protocolVersion)
            self.data.protocolVersion = 1

        validNodeTypes = ['residential', 'commercial', 'government']
        if (self.data.nodeType not in validNodeTypes):
            print('Invalid node type.')
            if not setNodeType():
                return false

        if (len(self.data.provider.id) != 64 or not re.match('[A-F0-9+/=]', self.data.provider.id)):
            print('Provider ID is invalid. Must be 64 character Base64 string.')
            return false

        if(not self.data.provider.name or len(self.data.provider.name) > 16):
            if not setProviderName():
                return false

        if (not self.data.wallet or len(self.data.wallet) != 97):
            if not setWalletAddr():
                return false

        if (not self.data.terms or len(self.data.terms) > 50000):
            if not setProviderTerms():
                return false

        if not self.data.certificates:
            # TODO encode certs
            print('WARNING: No provider certificates found!')

        return true

    def setProviderTerms(self):
        choice = input('Enter provider terms. These will be displayed to users. Up to 50000 characters. ').strip()[:50000]
        if not choice:
            choice = 'None'

        self.data.terms = choice
        return true

    def setWalletAddr(self):
        choice = input('Enter wallet address. This wallet will receive all payments for services. ').strip()
        if (len(choice) != 97):
            print('Wallets should be exactly 97 characters. Are you sure you entered a real wallet address?')
            return false
        if (choice[:1] != 'i'):
            print('Wallet addresses must start with i. Do not enter an integrated address; one will be automatically generated for every client.')
            return false

        self.data.wallet = choice
        return true

    def setProviderName(self):
        choice = input('Enter provider name. This will be displayed to users. Use up to 16 alphanumeric characters, symbols allowed: ')
        if (len(choice) <= 16 and re.match('^[a-zA-Z0-9 ,.-_]+$', choice)):
            self.data.provider.name = choice
            return true
        else:
            print('Invalid provider name!')
            return false

    def setNodeType(self):
        choice = input('Enter provider type. [c]ommercial, [r]esidential, or [g]overnment? ').strip().lower()[:1]
        if (choice == 'c'):
            self.data.nodeType = 'commercial'
            return true
        elif (choice == 'r'):
            self.data.nodeType = 'residential'
            return true
        elif (choice == 'g'):
            self.data.nodeType = 'government'
            return true

        print('Invalid provider type specified.')
        return false
    
    def load(self, config):
        if (self.configFile is None):
            self.configFile = config
        try:
            self.data = json.load(open(self.configFile))
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
    id = ''
    name = ''
