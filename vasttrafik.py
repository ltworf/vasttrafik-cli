# -*- coding: utf-8 -*-
# coding=UTF-8
# pysttrafik
# Copyright (C) 2010  Salvo "LtWorf" Tomaselli
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
import json
import datetime
import re

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
        self.key = key
        self.api = api
        self.datetime_obj = None
        
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
    
    def board(self,id,direction=None,arrival=False,time_span=None,departures=2):
        '''Returns an arrival/departure board for a given station'''
        
        
        if arrival:
            service='arrivalBoard'
        else:
            service='departureBoard'
        
        params='id=%s&' % id
        
        if direction != None:
            params+='direction=%s&' % direction
        #TODO arival, timespan and departures
        b = json.loads(self.request(service,params)[13:-2])
        if arrival:
            c=b['ArrivalBoard']['Arrival']
        else:
            c=b['DepartureBoard']['Departure']
        
        self.datetime_obj = to_datetime(b['DepartureBoard']['serverdate'],b['DepartureBoard']['servertime'])
        return [BoardItem(i) for i in c]
            
class BoardItem(object):
    '''This represents one item of the panel at a stop
    has a bunch of attributes to represent the stop'''
    def __repr__(self):
        repr(self._repr)
    def toTxt(self,servertime):
        '''
        Prints a string representation of the table item,
        
        servertime is a datetime object obtained from the Vasttrafik class '''
        
        delta = (self.datetime_obj - servertime)
        delta = delta.seconds / 60
        
        return '%s -> %s (%s) -> %d' % (self.name,self.direction, self.track,delta)
    def toTerm(self,servertime):
        delta = (self.datetime_obj - servertime)
        delta = delta.seconds / 60
        try:
            from colorama import init
            from colorama import Fore, Back, Style
        except:
            return self.toTxt(servertime)
        init()
        
        '''
        Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
        Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
        Style: DIM, NORMAL, BRIGHT, RESET_ALL
        '''
        
        #For some reason actually they have to be swapped...
        bg = {'#dcd135':Fore.YELLOW,'#00abe5':Fore.BLUE,'#ffffff':Fore.WHITE,'#0e629b':Back.BLUE}
        fg = {'#14823c':Back.GREEN,'#eb1923':Back.RED,'#cd1432':Back.RED,'#008228':Back.GREEN,'#336699':Back.BLUE,'#872387':Back.RED,'#004b85':Back.BLUE,'#7d4313':Back.RED,'#b4e16e':Back.GREEN,'#fee6c2':Back.WHITE,'#ffffff':Back.WHITE,'#000000':Back.BLACK,'#102d64':Back.BLACK,'#00A5DC':Back.BLUE,'#fff014':Back.YELLOW,'#6ec8dc':Back.CYAN,'#fa8719':Back.MAGENTA}
        
        bus = ''
        
        if self.bgcolor in bg:
            bus+=bg[self.bgcolor]
        else:
            print "bg: ",self.bgcolor
        if self.fgcolor in fg:
            bus+=fg[self.fgcolor]
        else:
            print "fg: ", self.fgcolor
        
        bus+=self.name
        bus+=Style.RESET_ALL
        
        return '%s -> %s (%s) -> %d' % (bus, self.direction ,self.track,delta)
        
        
        
        
    def __init__(self,d):
        self._repr = d
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
        self.bgcolor = None
        self.fgcolor = None
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
        #TODO booking night    
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
            
        self.datetime_obj = to_datetime(date,time)
    
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