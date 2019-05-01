from setuptools import setup

setup(
   name='lethean-vpn',
   version='3.1',
   description='Lethean VPN',
   author='Lukas Macura',
   author_email='lukas@lethean.io',
   install_requires=['syslogmp', 'ed25519', 'pprint', 'psutil', 'jsonpickle', 'configargparse', 'requests', 'dnspython' ],
)

