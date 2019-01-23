# SDP provisioning by DNS

In addition to traditional Lethean SDP server, services can be provisioned by DNS records.
If provider wants to be found by FQDN syntax, DNS records must be filled. Clients can connect until they know FQDN of the service.
SDP provisioning is used when FQDN is used for provider. Like *provider.some.whe.re/1A*

## DNS TXT record

In order to fetch local SDP, TXT record must be present in FQDN of service:

```
provider.some.whe.re. IN TXT "lv=v3;sdp=https://some.whe.re/sdp.json;id=providerid"
```

 * lv means LTHN version to use (v3 or v4)
 * sdp is actual SDP url for download (same format as sdp.json on disk)
 * id is providerid
 * there can be more TXT records. Client will filter them automatically only to his version.

