import setuptools
from distutils.core import setup

setup(name='lethean-vpn',
    version='0.1',
    description='Lethean VPN',
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        'certifi==2021.10.8',
        'cffi==1.15.0',
        'charset-normalizer==2.0.9',
        'ConfigArgParse==1.5.3',
        'cryptography==36.0.0',
        'dnspython==2.1.0',
        'ed25519==1.5',
        'idna==3.3',
        'jsonpickle==2.0.0',
        'psutil==5.8.0',
        'pycparser==2.21',
        'requests==2.26.0',
        'syslogmp==0.4',
        'urllib3==1.26.7'
    ]
)
