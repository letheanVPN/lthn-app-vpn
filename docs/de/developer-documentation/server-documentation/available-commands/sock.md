## Management interface
The dispatcher has a management interface available by default in */opt/lthn/var/run/mgmt*.
You can manually add or remove authids and query its status.
```
echo "help" | socat stdio /opt/lthn/var/run/mgmt
show authid [authid]
show session [sessionid]
kill session <sessionid>
topup <authid> <itns>
spend <authid> <itns>
add authid <authid> <serviceid>
del authid <authid>
loglevel {DEBUG|INFO|WARNING|ERROR}
refresh
cleanup

```

Example 1: Show sessions:
```
echo "show session" | socat stdio /opt/lthn/var/run/mgmt
Added (authid2: serviceid=1a, created=Tue Jul 17 19:39:07 2018,modified=Tue Jul 17 19:39:07 2018, balance=100000.000000, perminute=0.001000, minsleft=100000000.000000, charged_count=1, discharged_count=0

```

Example 2: Topup authid:
```
 echo "topup 1abbcc 1" | socat stdio /opt/lthn/var/run/mgmt
TopUp (1abbcc: serviceid=1a, created=Tue Jul 17 19:39:07 2018,modified=Tue Jul 17 19:39:47 2018, balance=100001.000000, perminute=0.001000, minsleft=100001000.000000, charged_count=2, discharged_count=0

```
