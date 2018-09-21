import time
import json

def timefmt(tme):
    return(time.strftime("%Y-%m-%d_%H:%M", time.localtime(tme)))

def valuesToString(values):
    str=""
    for k in values.keys():
        str = str + "%s:%s " % (k,values[k])
    return(str+"\n")

def valuesToJson(values):
    str=json.dumps(values)
    return(str)