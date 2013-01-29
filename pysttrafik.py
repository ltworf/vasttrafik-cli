# -*- coding: utf-8 -*-
# coding=UTF-8
# pysttrafik
# Copyright (C) 2012 Salvo "LtWorf" Tomaselli
# 
# pysttrafik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
# author Salvo "LtWorf" Tomaselli <tiposchi@tiscali.it>

import urllib2
import urllib
import datetime
import re

try:
    import json
except:
    import simplejson
    json = simplejson.simplejson()

try:
    from xtermcolor import colorize
except:
    colorize = lambda x,rgb=None, ansi=None, bg=None, ansi_bg=None, fd=1: x

def get_key():
    '''
    This function tries to load the API key from some configuration files.
    It will try, in the order:
        - /etc/pysttrafik.conf
        - ~/.pysttrafik
    
    If the files aren't found or they don't contain the key attribute then
    None will be returned, otherwise, a string containing the key will be 
    returned.
    '''
    from configobj import ConfigObj
    import os
    from os.path import exists
    
    paths = ('/etc/pysttrafik.conf',
             "%s/.pysttrafik"% os.getenv("HOME"),
            )
    
    path = None
    for i in paths:
        if exists(i):
            path = i
            break
    try:
        config = ConfigObj(path)
        return config['key']
    except:
        return None

def gen_timetable_html(stops,datetime_obj):
    '''generates the HTML to a timetable
    takes the tram list (resulting from a call to board)
    and the time from the server'''
    
    r='<html><head><META http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body style="background-color:black; color:white;"><table>'
    r+='<tr><td></td><td>To</td><td>Track</td><td>Next</td></tr>'
    for i in stops:
        r+= i.toHtml(datetime_obj).encode('utf-8')
    r+='</table></body></html>'
    return r    


def to_datetime(date,time):
    '''Converts two string date and time into a datetime object
    
    date format YYYY-MM-DD
    time format HH:MM
    '''
    r= re.match(r'^([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})$',date)
    year = int(r.group(1))
    month = int(r.group(2))
    day = int(r.group(3))
    r= re.match(r'^([0-9]{1,2}):([0-9]{1,2})$',time)
    hour = int(r.group(1))
    minute = int(r.group(2))
    return datetime.datetime(year,month,day,hour,minute)

class Vasttrafik:
    def __init__(self,key,api="api.vasttrafik.se/bin/rest.exe/v1"):
        '''
        key is the API key that must be sent on every request to obtain a reply.
        Contact Västtrafik for details on how to obtain one.
        '''
        self.key = key
        self.api = api
        self.datetime_obj = None
        
    def request(self,service,param):
        url = "http://%s/%s?format=json&jsonpCallback=processJSON&authKey=%s&%s" % (self.api,service,self.key,param)
        
        try:
            f = urllib2.urlopen(url,timeout=10)
        except:
            f = urllib2.urlopen(url)
            
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
        a = self.request("location.name",urllib.urlencode({'input':user_input}))
        b = json.loads(a[13:-2]) #They return me some crap around the json
        c=b["LocationList"]['StopLocation']
        
        return [Stop(i) for i in c]
    def nearby(self,lat,lon,stops=10,dist=None):
        '''
        Returns the list of stops close to a certain location
        
        lat = latitude
        lon = longitude
        
        stops = maximum number of stops to return
        dist = maximum distance in meters
        '''
        params = 'originCoordLat=%s&originCoordLong=%s&maxNo=%d' % (str(lat),str(lon),stops)
        if dist != None:
            params += '&maxDist=%d' % dist
            
        b = json.loads(self.request('location.nearbystops',params)[13:-2])
        c=b["LocationList"]['StopLocation']
        
        return [Stop(i) for i in c]
    
    def board(self,id,direction=None,arrival=False,time_span=None,departures=2,datetime_obj=None):
        '''Returns an arrival/departure board for a given station'''
        
        
        if arrival:
            service='arrivalBoard'
        else:
            service='departureBoard'
        
        params = {}
        params['id']= str(id)
        params['maxDeparturesPerLine'] = str(departures)
        
        if direction != None:
            params['direction'] = direction
        #TODO arival and departures, datetime
        if time_span != None and time_span <=1439:
            params['timeSpan'] = str(time_span)
        
        b = json.loads(self.request(service,urllib.urlencode(params))[13:-2])
        if arrival:
            c=b['ArrivalBoard']['Arrival']
            self.datetime_obj = to_datetime(b['ArrivalBoard']['serverdate'],b['ArrivalBoard']['servertime'])
        else:
            c=b['DepartureBoard']['Departure']
            self.datetime_obj = to_datetime(b['DepartureBoard']['serverdate'],b['DepartureBoard']['servertime'])
        
        trams = [BoardItem(i) for i in c]
        
        #Group similar ones
        i = 0;
        while i < len(trams) -1:
            j = i+1
            while j< len(trams):
                if trams[i].join(trams[j]):
                    trams.pop(j)
                else:
                    j+=1
            i+=1
        
        #Sort by track
        trams.sort(key=lambda x: (x.track,x.datetime_obj[0]))
        return trams
    def trip(self,originCoord=None,originId=None,originCoordName=None,destCoord=None,destId=None,destCoordName=None,viaId=None,datetime_obj=None):
        '''
        originCoord = a tuple with origin coordinates (lat,lon)
        originId = stop id
        originCoordName = address
        
        destCoord
        destId
        destCoordName
        
        viaId = pass by a certain stop
        
        datetime_obj = search from this moment
        '''
        
        service='trip'
        params= {}
        
        if originCoord != None:
            params['originCoordLat'] = originCoord[0]
            params['originCoordLong'] = originCoord[1]
        elif originId != None:
            params['originId'] = originId
        elif originCoordName != None:
            params['originCoordName'] = originCoordName
        
        if destCoord != None:
            params['destCoordLat'] = destCoord[0]
            params['destCoordLong'] = destCoord[1]
        elif destId != None:
            params['destId'] = destId
        elif destCoordName != None:
            params['destCoordName'] = destCoordName
        
        if viaId != None:
            params['viaId'] = viaId
        
        if datetime_obj != None:
            params['date'] = '%04d-%02d-%02d' % (datetime_obj.year,datetime_obj.month,datetime_obj.day)
            params['time'] = '%02d:%02d' % (datetime_obj.hour,datetime_obj.minute)
        
        ###Request
        b = json.loads(self.request(service,urllib.urlencode(params))[13:-2])
        
        c = b['TripList']
        
        self.datetime_obj = to_datetime(c['serverdate'],c['servertime'])
        
        return [Trip(i) for i in c['Trip']]
        
class Trip(object):
    '''
    A trip contains a list of Legs (attribute legs).
    If the stops are directly connected the list will only
    have 1 element.
    
    If on a change the traveler must go from one Track to another,
    a Leg of veichle_type WALK will be between the other two Legs.
    '''
    def __init__(self,d):
        d = d['Leg']
        if isinstance(d,list):
            self.legs = [Leg(i) for i in d]
        else:
            self.legs = [Leg(d)]
        pass
    def toTerm(self):
        return self.toTxt(True)
    def toTxt(self,color=False):
        r=''
        for i in self.legs:
            r+=i.toTxt(color)+'\n'
        return r[:-1]
class LegHalf(object):
    def __init__(self,d):
        self.date = d['date']
        self.id = d['id']
        self.name = d['name']
        if 'routeIdx' in d:
            self.routeIdx = d['routeIdx']
        else:
            self.routeIdx = None
        self.time = d['time']
        
        if 'track' in d:
            self.track = d['track']
        else:
            self.track = None
        self.type = d['type']
        
        if 'rtDate' in d:
            self.date = d['rtDate']
        if 'rtTime' in d:
            self.time = d['rtTime']
        
        self.datetime_obj = to_datetime(self.date,self.time)
        
class Leg(object):
    '''
    a Leg is part of a Trip, and is performed on one veichle or by foot.
    
    it has an origin and a destination of type LegHalf
    '''
    def toTerm(self):
        '''
        Returns a pretty printed string representing the Leg of the trip.
        Escape codes to color the terminal are added.
        '''
        return self.toTxt(True)
    def toTxt(self,color=False):
        '''
        Returns a pretty printed string representing the Leg of the trip.
        '''
        return '%s %0*d:%0*d\t%s -> %s ' %(self.getName(color),2,self.origin.datetime_obj.hour,2,self.origin.datetime_obj.minute , self.origin.name, self.destination.name)
    def getName(self,color=False):
        '''Returns a nice version of the name
        If color is true, then 256-color escapes will be
        added to give the name the color of the line'''
        name = self.name
        name = name.replace(u'Spårvagn','')
        name = name.replace(u'Buss','')
        name += " "
        
        if self.direction !=None:
            name+=self.direction+ " "
        
        if self.wheelchair:
            name += u"♿ "
        if self.night:
            name += u"☾ "
        
        while len(name)<20:
            name=" "+name
        
        if not color:
            return name
    
        bgcolor = int('0x' + self.fgcolor[1:],16)
        fgcolor = int('0x' + self.bgcolor[1:],16)
        return colorize(name.encode('utf8'),fgcolor,bg=bgcolor).decode('utf8')
    def __init__(self,d):
        self._repr = d
        self.name = d['name']
        self.veichle_type = d['type']
        if 'id' in d:
            self.id = d['id']
        else:
            self.id = None
        
        self.origin = LegHalf(d['Origin'])
        self.destination = LegHalf(d['Destination'])
        
        #optionals
        self.direction = None
        self.stroke = None
        self.bgcolor = '#0000ff'
        self.fgcolor = '#ffffff'
        self.night = False
        self.booking = False
        
        self.wheelchair = 'accessibility' in d and d['accessibility'] == 'wheelChair'
        
        if 'track' in d:
            self.track = d['track']
        if 'rtDate' in d:
            self.rtdate = d['rtDate']
        if 'rtTime' in d:
            self.rttime = d['rtTime']
        if 'rtTrack' in d:
            self.track = d['rtTrack']
        if 'night' in d:
            self.night = True
        #TODO booking    
        if 'direction' in d:
            self.direction = d['direction']
        

        if 'bgColor' in d:
            self.bgcolor = d['bgColor']
        if 'stroke' in d:
            self.stroke = d['stroke']
        if 'fgColor' in d:
            self.fgcolor = d['fgColor']
        

class BoardItem(object):
    '''This represents one item of the panel at a stop
    has a bunch of attributes to represent the stop'''
    def join(self,o):
        '''Joins another stop into this one if possible
        Basically if there are 2 trams going at different times 
        they will be collapsed into a single one.
        Returns true if the other BoardItem has been joined.
        '''
        
        if o.name == self.name and o.stopid == self.stopid and o.direction == self.direction:
            self.datetime_obj+= o.datetime_obj
            return True
        return False
    def __repr__(self):
        repr(self._repr)
    def toTxt(self,servertime):
        return self.toTerm(servertime,color=false)
    def toHtml(self,servertime):
        delta = [ ((i - servertime).seconds / 60) for i in self.datetime_obj]
        delta.sort()
        
        name = self.getName()
        
        bus = '<td  style="background-color:%s; color:%s;" >%s</td>' % (self.fgcolor,self.bgcolor,name)
        direction = '<td>%s</td>' % self.direction
        track = '<td>%s</td>' % self.track
        delta = '<td>%s</td>' % ','.join(map(str, delta))
        
        return '<tr>%s%s%s%s</tr>' %(bus,direction,track,delta)
        
    def toTerm(self,servertime,color=True):
        '''Returns a string representing the BoardItem colorized using
        terminal escape codes.
        
        Servertime must be retrieved from the Vasttrafik class, and indicates
        the time on the server, it will be used to show the difference in
        minutes before the arrival.
        '''
        delta = [ ((i - servertime).seconds / 60) for i in self.datetime_obj]
        delta.sort()
        bus = self.getName(color)
        return '%s %0*d -> %s # %s' % (bus, 2, delta[0], self.direction, ','.join(map(str, delta)))
    def getName(self,color=False):
        '''Returns a nice version of the name
        If color is true, then 256-color escapes will be
        added to give the name the color of the line'''
        name = self.name
        name = name.replace(u'Spårvagn','')
        name = name.replace(u'Buss','')
        name += " "
        
        if self.wheelchair:
            name += u"♿ "
        if self.night:
            name += u"☾ "
        
        while len(name)<20:
            name=" "+name
        
        if not color:
            return name
    
        bgcolor = int('0x' + self.fgcolor[1:],16)
        fgcolor = int('0x' + self.bgcolor[1:],16)
        return colorize(name.encode('utf8'),fgcolor,bg=bgcolor).decode('utf8')
        
    def __init__(self,d):
        self._repr = d
        if not isinstance(d,dict):
            raise Exception("Invalid data")
        
        self.name = d['name']
        self.veichle_type = d['type']
        self.stop = d['stop']
        self.stopid = d['stopid']
        self.journeyid = d['journeyid']
        self.date = d['date']
        self.time = d['time']
        
        #TODO self.journeydetail = d['journeyDetailRef']
        
        #optionals
        self.track = None
        self.rtdate = None
        self.rttime = None
        self.direction = None
        self.stroke = None
        self.bgcolor = '#0000ff'
        self.fgcolor = '#ffffff'
        self.night = False
        self.booking = False
        
        if 'track' in d:
            self.track = d['track']
        if 'rtDate' in d:
            self.rtdate = d['rtDate']
        if 'rtTime' in d:
            self.rttime = d['rtTime']
        if 'rtTrack' in d:
            self.track = d['rtTrack']
        if 'night' in d:
            self.night = True
        #TODO booking    
        if 'direction' in d:
            self.direction = d['direction']
        self.wheelchair = 'accessibility' in d and d['accessibility'] == 'wheelChair'

        if 'bgColor' in d:
            self.bgcolor = d['bgColor']
        if 'stroke' in d:
            self.stroke = d['stroke']
        if 'fgColor' in d:
            self.fgcolor = d['fgColor']
        
        
        #Set the internal useful date representation
        if self.rtdate != None:
            date = self.rtdate
        else:
            date = self.date
        if self.rttime != None:
            time = self.rttime
        else:
            time = self.time
            
        self.datetime_obj = [to_datetime(date,time),]
    
class Stop(object):
    '''The object represents a stop
    
    it has attributes:
    id
    idx //might be None
    lon
    lat
    name
    '''
    def __init__(self,d):
        self.id = d['id']
        if 'idx' in d: 
            self.idx = d['idx'] 
        else: 
            self.idx = None
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
