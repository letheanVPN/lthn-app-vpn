
## Configure and install
The dispatcher is configured by a standard configure script. You can change basic parameters of proxy or VPN services via this script. It will ask you for all parameters and generate sdp.json and dispatcher.ini. Please note that config files will be generic and it is good to review and edit them before real usage. You can run the configure script again if you want to change parameters but you have to run *make clean* first.

If you use *FORCE=1* during `make install`, it will overwrite your configs and certificates/keys. Without this flag, all configs and keys are left untouched.

### Wallet
The dispatcher requires having a valid Lethean wallet configured before running, it requires having the wallet-vpn-rpc binary runing. Please note that there are two passwords passed to initialize the wallet-vpn-rpc binary; one for unlocking the wallet and one for dispatcher RPC calls.
You can download these binaries from [here](https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/697/lethean-cli-linux-64bit-letheanize-e45d13b.tar.bz2), or build from source using [lethean master](https://github.com/LetheanMovement/lethean/tree/master).
wallet-vpn-rpc initialization:
```bash
lethean-wallet-vpn-rpc --vpn-rpc-bind-port 13660 --wallet-file itnsvpn --rpc-login
dispatcher:<somepassword> --password <walletpassword>

```

 * *Note*: You cannot use same wallet for client and dispatcher!
 * *Note*: Using the `lethean-wallet-vpn-rpc` binary as described also requires having the `letheand` daemon running, or using a remote daemon. If you would prefer to use a remote daemon instead of running a daemon locally, we recommend using the Lethean team hosted node at **sync.lethean.io**

```bash
lethean-wallet-vpn-rpc --daemon-host sync.lethean.io
```

### Basic install
See ./configure.sh --help for more fine-tuned options
```bash
git clone https://github.com/LetheanMovement/lethean-vpn.git
cd lethean-vpn
pip3 install -r requirements.txt
./configure.sh --easy [--with-wallet-address <wallet_address>]
make install [FORCE=1]
```

### Public configuration - sdp.json
*/opt/lthn/etc/sdp.json* describes local services for orchestration. It is uploaded to SDP server by --upload-sdp option. Note that uploading to SDP server is paid service. <!--  **TODO add SDP server integration instructions** --> 
After installation, you will be instructed to generate the sdp.json file, which is required to run the dispatcher.
You can either answer questions using the wizard (*--generate-sdp*) or you can use cmdline params to set defaults. See help.
```bash
/opt/lthn/bin/lvmgmt --generate-sdp --wallet-address some_wallet_address [--sdp-service-name someName] ...

```

You may need to invoke lthnvpnd using `python3` if you receive dependency errors. If you opted to use the `--runas-user` and `--runas-group` setup params, you will also need to `su -` to that user or use `sudo` when using the dispatcher.
```bash
[su - vpnuser]
python3 /opt/lthn/bin/lthnvpnd ...
```

### Configuration Templates
### You can use one of the templates for proxy, vpn or mixed instalations.
** Just adapt according your node setup.
** Templates avaliable here https://github.com/LetheanMovement/lethean-vpn/tree/feature/luis/pi3v4/templates

### Private configuration - dispatcher.ini
*/opt/lthn/etc/dispatcher.ini* is a local file containing private information needed to run the  dispatcher. Do not upload it anywhere or share it with anyone as it contains private keys. You should also create a backup of this file.
By default, *make install* will generate a default file for you but you need to configure it to suit your needs.
File format:
```ini
[global]
;debug=DEBUG
ca={ca}
;provider-type=commercial
provider-id={providerid}
provider-key={providerkey}
provider-name=Provider
provider-terms=Some Terms
;provider-terms=@from_file.txt

;;; Wallet
;wallet-address={wallet_address}
;wallet-rpc-url=http://127.0.0.1:13660/json_rpc
;wallet-username={wuser}
;wallet-password={wpasword}

;;; SDP
;sdp-servers={sdpservers}

; Service specific options. Each section [service-id] contains settings for service with given id (need to correspond with SDP)
[service-1A]
name=Proxy
backend_proxy_server=localhost:3128
crt={hacrt}
key={hakey}
crtkey={haboth}

[service-1B]
crt={vpncrt}
key={vpnkey}
crtkey={vpnboth}
reneg=60

```






