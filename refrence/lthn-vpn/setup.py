import setuptools
from distutils.core import setup

setup(name='lethean-vpn',
    version='0.1',
    description='Lethean VPN',
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        'certifi',
        'cffi',
        'charset-normalizer',
        'ConfigArgParse',
        'cryptography',
        'dnspython',
        'ed25519',
        'idna',
        'jsonpickle',
        'psutil',
        'pycparser',
        'requests',
        'syslogmp',
        'urllib3'
    ],
    entry_points = {
        'console_scripts': [
            'lthnvpnc=lthnvpn.client.lthnvpnc:entry',
            'lthnvpnd=lthnvpn.daemon.lthnvpnd:entry',
            'lvmgmt=lthnvpn.daemon.lvmgmt:entry',
        ]
    }
)

