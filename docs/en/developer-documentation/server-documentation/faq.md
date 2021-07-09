
# FAQ

## Updating the dispatcher

To update the dispatcher, run the following commands from the directory that the lethean-vpn repo was initialized in:
```
git pull
./configure.sh --easy
make install
rm -f /opt/lthn/var/authids.db
sudo systemctl daemon-reload
sudo systemctl restart lthnvpnd
```



## Provider

### Q: Is it legal to be provider?
There can be local laws and legality issues in your country or company. Check your legislative about this. We cannot say universally that something is legal or not.
It can differ in countries over the world but you should follow at last some basic rules:

#### Safe your infrastructure #####
You should not allow user to connect to your own network until you are sure you want to. Please refer to [server documentation](/vpn/server-documentation) documentation about access lists.

#### Do not allow bad users to do bad things #####
This is probably most critical and complex part. Primary goal of entire Lethean project is privacy for users. But, of course, somebody can use privacy to harmful somebody other. 
It is your responsibility as a provider to do maximum against these users. Our project is here for good users which needs privacy. We will implement many features how to help you with this filtering.

#### Filter traffic #####
You can filter your traffic for specific sites. Please refer to [server documentation](/vpn/server-documentation)
 
### Q: As a provider, do I need audit log?
If somebody does something harmful, you are responsible as an exit node. It is up to you.

### Q: What is status of IPv4/IPv6 support?
Both client and server works perfectly on IPv4 network. We are working on full native IPv6 support but for now, see this matrix.

| Client  | Provider | Web        | Support             |
| ------- | -------- | -------    | ------------------- | 
| IPv4    | IPv4     | IPv4/IPv6  | Full                |
| IPv6    | IPv6     | IPv4/IPv6  | No-session-tracking |



 
