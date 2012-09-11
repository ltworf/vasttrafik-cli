import urllib2
import json

class Vasttrafik:
    def __init__(self,key,api="api.vasttrafik.se/bin/rest.exe/v1"):
        self.key = key
        self.api = api
        
    def request(self,service,param):
        url = "http://%s/%s?format=json&jsonpCallback=processJSON&authKey=%s&%s" % (self.api,service,self.key,param)
        f = urllib2.urlopen(url,timeout=10)
    
        r= ""
    
        while True:
            l = f.read()
            if len(l)==0:
                break
            r+=l
        f.close()
        return r
        
    def location(self,user_input):
        '''Returns a list of Stop objects, completing from the user input'''
        a = self.request("location.name","input=%s" % user_input)
        b = json.loads(a[13:-2]) #They return me some crap around the json
        c=b["LocationList"]['StopLocation']
        
        return [Stop(i) for i in c]

class Stop(object):
    '''The object represents a stop
    
    it has attributes:
    id
    idx
    lon
    lat
    name
    '''
    def __init__(self,d):
        self.id = d['id']
        self.idx = d['idx']
        self.lat = d['lat']
        self.lon = d['lon']
        self.name = d['name']
    def __unicode__(self):
        return self.name
    def __repr__(self):
        d={'id':self.id,'idx':self.idx,'lat':self.lat,'lon':self.lon,'name':self.name}
        return d.__repr__()
    def __eq__(self,o):
        '''Compares using the id field'''
        if not isinstance(o,Stop):
            return False
        return self.id == o.id