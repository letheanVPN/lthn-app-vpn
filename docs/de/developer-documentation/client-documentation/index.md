# Client Vpn Documentation

## Payments
This client will not pay anything for you. It only helps to create local configs and connect to remote service. It will instruct you in audit.log, how to pay for service.
It will wait until service is paid and checkes each 60 seconds if credit is still OK.

## Exiting from client
By default, client tries to connect and if there is some error, it exits after connect-timeout. Next, it waits for payment and if payment does not arrive, it exits after payment-timeout.
If you want to have client trying forever, use big numbers for timeouts. Keep in mind, that timeout starts as small number but it is increased by two in each loop to avoid network congestion.
You can use --fork-on-connect to fork to the background after successfull connect. This can be used for chaining (see below).

## Compatibility
There are two versions of dispatchers - v3 and v4. We changed names of headers due to letheanisation. If you want to connect to old (v3) dispatcher, use --compatibility v3.
Client will not connect if compatibility level does not match!

## Service URI format
Service URI are used to identify services over providers. It is unique over the world. There are two types of URI - SDP based and FQDN based.
While SDP based are fetched from central SDP server, FQDN based are fetched from local provider SDP server.

### General simple URI syntax

authid@provider/service

 * provider can be providerid or domain name
 * service can be serviceid or service name
 * authid can be ommited so it will be auto-generated. Do not forget that first two characters of authid must be same as serviceid.

If provider is fqdn and not providerid, client will use DNS to get info about SDP and provider. 

### More complex URI (provider chaining)

 * Using HTTP proxy: {authid1@provider1/service1}//proxy:port
 * Basic chaining: Connect to provider2 and use it as backend to connect to service1: {authid1@provider1/service1}//{authid2@provider2/service2}
 * More complex chaining (round-robin): {authid1@provider1/service1}//{authid2@provider2/service2,authid3@provider3/service3}


