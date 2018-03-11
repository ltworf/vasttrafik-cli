# pysttrafik
# Copyright (C) 2012-2017 Salvo "LtWorf" Tomaselli
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

import urllib.request
import urllib.parse
import datetime
import json
import re
from typing import Dict, List, Optional, NamedTuple

from ntupledict import from_dict, convert

try:
    from xtermcolor import colorize
except:
    colorize = lambda x, rgb=None, ansi=None, bg=None, ansi_bg=None, fd=1: x


class Stop(NamedTuple):

    '''
    The object represents a stop
    '''

    id: str
    lon: float
    lat: float
    name: str
    idx: Optional[str] = None

    def __str__(self):
        return self.name


Stops = List[Stop]


def _get_token(key: str) -> str:
    url = "https://api.vasttrafik.se:443/token"
    req = urllib.request.Request(url)
    req.data = b'grant_type=client_credentials'
    req.headers['Authorization'] = 'Basic ' + key
    r = b''
    with urllib.request.urlopen(req) as f:
        while True:
            l = f.read()
            if len(l) == 0:
                break
            r += l
    answer = r.decode('ascii')
    return json.loads(answer)['access_token']


def get_key() -> Optional[str]:
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
             "%s/.pysttrafik" % os.getenv("HOME"),
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


def gen_timetable_html(stops, datetime_obj) -> str:
    '''generates the HTML to a timetable
    takes the tram list (resulting from a call to board)
    and the time from the server'''

    r = '<html><head><META http-equiv="Content-Type" content="text/html; charset=UTF-8"></head><body style="background-color:black; color:white;"><table>'
    r += '<tr><td></td><td>To</td><td>Track</td><td>Next</td></tr>'
    for i in stops:
        r += i.toHtml(datetime_obj)
    r += '</table></body></html>'
    return r


def to_datetime(date: str, time: str) -> datetime.datetime:
    '''Converts two string date and time into a datetime object

    date format YYYY-MM-DD
    time format HH:MM
    '''
    r = re.match(r'^([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})$', date)
    year = int(r.group(1))
    month = int(r.group(2))
    day = int(r.group(3))
    r = re.match(r'^([0-9]{1,2}):([0-9]{1,2})$', time)
    hour = int(r.group(1))
    minute = int(r.group(2))
    return datetime.datetime(year, month, day, hour, minute)


class Vasttrafik:

    def __init__(self, key: str, api: str = "api.vasttrafik.se/bin/rest.exe/v2") -> None:
        '''
        key is the API key that must be sent on every request to obtain a reply.
        you can obtain one at api.vasttrafik.se, but it will be activated the
        night after registration.
        '''
        self.key = key
        self.api = api
        self.datetime_obj = None

    def _request(self, service, param):
        token = _get_token(self.key)

        url = "https://%s/%s?format=json&%s" % (
            self.api, service, param)
        req = urllib.request.Request(url)
        req.headers['Authorization'] = 'Bearer ' + token
        r = b''
        with urllib.request.urlopen(req) as f:
            while True:
                l = f.read()
                if len(l) == 0:
                    break
                r += l

        if r.strip().startswith(b'Invalid authKey'):
            raise Exception('Invalid authKey')

        return json.loads(r.decode('utf8'))

    def location(self, user_input) -> Stops:
        '''Returns a list of Stop objects, completing from the user input'''
        a = self._request(
            "location.name", urllib.parse.urlencode({'input': user_input}))
        c = a["LocationList"]['StopLocation']

        if isinstance(c, dict):
            c = [c]
        return convert(c, Stops)

    def nearby(self, lat: float, lon: float, stops: int = 10, dist: Optional[int] = None) -> Stops:
        '''
        Returns the list of stops close to a certain location

        lat = latitude
        lon = longitude

        stops = maximum number of stops to return
        dist = maximum distance in meters
        '''
        params = 'originCoordLat=%s&originCoordLong=%s&maxNo=%d' % (
            str(lat), str(lon), stops)
        if dist != None:
            params += '&maxDist=%d' % dist

        b = self._request('location.nearbystops', params)
        c = b["LocationList"]['StopLocation']

        return convert(c, Stops)

    def board(self, id, direction=None, arrival=False, time_span=None, departures=2, datetime_obj=None) -> List['BoardItem']:
        '''Returns an arrival/departure board for a given station'''

        if arrival:
            service = 'arrivalBoard'
        else:
            service = 'departureBoard'

        params = {}
        params['id'] = str(id)
        params['maxDeparturesPerLine'] = str(departures)

        if direction != None:
            params['direction'] = direction
        # TODO arival and departures, datetime
        if time_span != None and time_span <= 1439:
            params['timeSpan'] = str(time_span)
        if datetime_obj is not None:
            params['date'] = '%04d-%02d-%02d' % (
                datetime_obj.year, datetime_obj.month, datetime_obj.day)
            params['time'] = '%02d:%02d' % (
                datetime_obj.hour, datetime_obj.minute)

        b = self._request(service, urllib.parse.urlencode(params))
        if arrival:
            c = b['ArrivalBoard']['Arrival']
            self.datetime_obj = to_datetime(
                b['ArrivalBoard']['serverdate'], b['ArrivalBoard']['servertime'])
        else:
            c = b['DepartureBoard']['Departure']
            self.datetime_obj = to_datetime(
                b['DepartureBoard']['serverdate'], b['DepartureBoard']['servertime'])

        if not isinstance(c, list):
            c = [c]

        trams = [BoardItem(i) for i in c]

        # Group similar ones
        i = 0
        while i < len(trams) - 1:
            j = i + 1
            while j < len(trams):
                if trams[i].join(trams[j]):
                    trams.pop(j)
                else:
                    j += 1
            i += 1

        # Sort by track
        trams.sort(key=lambda x: (x.track, x.datetime_obj[0]))
        return trams

    def trip(self, originCoord=None, originId=None, originCoordName=None, destCoord=None, destId=None, destCoordName=None, viaId=None, datetime_obj=None) -> List['Trip']:
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

        service = 'trip'
        params = {}

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
            params['date'] = '%04d-%02d-%02d' % (
                datetime_obj.year, datetime_obj.month, datetime_obj.day)
            params['time'] = '%02d:%02d' % (
                datetime_obj.hour, datetime_obj.minute)

        # Request
        b = self._request(service, urllib.parse.urlencode(params))
        c = b['TripList']

        self.datetime_obj = to_datetime(c['serverdate'], c['servertime'])

        return [Trip(i) for i in c['Trip']]


class Trip(object):

    '''
    A trip contains a list of Legs (attribute legs).
    If the stops are directly connected the list will only
    have 1 element.

    If on a change the traveler must go from one Track to another,
    a Leg of vehicle_type WALK will be between the other two Legs.
    '''

    def __init__(self, d) -> None:
        d = d['Leg']
        if isinstance(d, list):
            self.legs = [Leg(i) for i in d]
        else:
            self.legs = [Leg(d)]
        pass

    def toTerm(self):
        return self.toTxt(True)

    def toTxt(self, color=False):
        r = ''
        for i in self.legs:
            r += i.toTxt(color) + '\n'
        return r[:-1]


class LegHalf(NamedTuple):
    date: str
    id: str
    name: str
    time: str
    track: str
    type: str
    routeIdx: Optional[str] = None
    rtDate: Optional[str] = None
    rtTime: Optional[str] = None

    @property
    def datetime_obj(self):
        d = self.rtDate if self.rtDate else self.date
        t = self.rtTime if self.rtTime else self.time
        return to_datetime(d, t)


class Leg(object):

    '''
    a Leg is part of a Trip, and is performed on one vehicle or by foot.
    '''

    def toTerm(self):
        '''
        Returns a pretty printed string representing the Leg of the trip.
        Escape codes to color the terminal are added.
        '''
        return self.toTxt(True)

    def toTxt(self, color=False):
        '''
        Returns a pretty printed string representing the Leg of the trip.
        '''
        return '%s %0*d:%0*d\t%0*d:%0*d\t%s -> %s ' % (
            self.getName(color),
            2,
            self.origin.datetime_obj.hour,
            2,
            self.origin.datetime_obj.minute,
            2,
            self.destination.datetime_obj.hour,
            2,
            self.destination.datetime_obj.minute,
            self.origin.name,
            self.destination.name
        )

    def getName(self, color=False):
        '''Returns a nice version of the name
        If color is true, then 256-color escapes will be
        added to give the name the color of the line'''
        name = self.name
        name = name.replace(u'Spårvagn', '')
        name = name.replace(u'Buss', '')
        name += " "

        if self.direction != None:
            name += self.direction + " "

        if self.wheelchair:
            name += u"♿ "
        if self.night:
            name += u"☾ "

        while len(name) < 20:
            name = " " + name

        if not color:
            return name

        bgcolor = int('0x' + self.fgcolor[1:], 16)
        fgcolor = int('0x' + self.bgcolor[1:], 16)
        return colorize(name, fgcolor, bg=bgcolor)

    def __init__(self, d):
        self._repr = d
        self.name = d['name']
        self.vehicle_type = d['type']
        self.id = d.get('id')

        self.origin = convert(d['Origin'], LegHalf)
        self.destination = convert(d['Destination'], LegHalf)

        # optionals
        self.booking = False
        # TODO booking


        if 'track' in d:
            self.track = d['track']
        if 'rtDate' in d:
            self.rtdate = d['rtDate']
        if 'rtTime' in d:
            self.rttime = d['rtTime']
        if 'rtTrack' in d:
            self.track = d['rtTrack']
        self.night = 'night' in d
        self.wheelchair = d.get('accessibility') == 'wheelChair'
        self.direction = d.get('direction')
        self.bgcolor = d.get('bgColor', '#0000ff')
        self.fgcolor = d.get('fgColor', '#ffffff')
        self.stroke = d.get('stroke')


class BoardItem(object):

    '''This represents one item of the panel at a stop
    has a bunch of attributes to represent the stop'''

    def join(self, o: 'BoardItem') -> bool:
        '''Joins another stop into this one if possible
        Basically if there are 2 trams going at different times
        they will be collapsed into a single one.
        Returns true if the other BoardItem has been joined.
        '''

        if o.name == self.name and o.stopid == self.stopid and o.direction == self.direction:
            self.datetime_obj += o.datetime_obj
            return True
        return False

    def __repr__(self):
        repr(self._repr)

    def toTxt(self, servertime):
        return self.toTerm(servertime, color=false)

    def toHtml(self, servertime):
        delta = [((i - servertime).seconds // 60) for i in self.datetime_obj]
        delta.sort()

        name = self.getName()

        bus = '<td  style="background-color:%s; color:%s;" >%s</td>' % (
            self.fgcolor, self.bgcolor, name)
        direction = '<td>%s</td>' % self.direction
        track = '<td>%s</td>' % self.track
        delta = '<td>%s</td>' % ','.join(map(str, delta))

        return '<tr>%s%s%s%s</tr>' % (bus, direction, track, delta)

    def toTerm(self, servertime, color=True):
        '''Returns a string representing the BoardItem colorized using
        terminal escape codes.

        Servertime must be retrieved from the Vasttrafik class, and indicates
        the time on the server, it will be used to show the difference in
        minutes before the arrival.
        '''
        bus = self.getName(color)
        delta = self.departures(servertime)
        return '%s %0*d -> %s # %s' % (bus, 2, delta[0], self.direction, ','.join(map(str, delta)))

    def departures(self, servertime) -> List[int]:
        delta = [((i - servertime).seconds // 60) for i in self.datetime_obj]
        delta.sort()
        return delta

    def getName(self, color=False):
        '''Returns a nice version of the name
        If color is true, then 256-color escapes will be
        added to give the name the color of the line'''
        name = self.name
        name = name.replace(u'Spårvagn', '')
        name = name.replace(u'Buss', '')
        name += " "

        if self.wheelchair:
            name += u"♿ "
        if self.night:
            name += u"☾ "

        while len(name) < 20:
            name = " " + name

        if not color:
            return name

        bgcolor = int('0x' + self.fgcolor[1:], 16)
        fgcolor = int('0x' + self.bgcolor[1:], 16)
        return colorize(name, fgcolor, bg=bgcolor)

    def __init__(self, d) -> None:
        self._repr = d
        if not isinstance(d, dict):
            raise Exception("Invalid data")

        self.name = d['name']
        self.vehicle_type = d['type']
        self.stop = d['stop']
        self.stopid = d['stopid']
        self.journeyid = d['journeyid']
        self.date = d['date']
        self.time = d['time']
        self.sname = d.get('sname', '')

        # TODO self.journeydetail = d['journeyDetailRef']

        # optionals
        self.booking = False
        self.night = 'night' in d

        self.track = d.get('track')
        self.rtdate = d.get('rtDate')
        self.rttime = d.get('rtTime')
        if 'rtTrack' in d:
            self.track = d['rtTrack']
        # TODO booking
        self.direction = d.get('direction')
        self.wheelchair = d.get('accessibility') == 'wheelChair'

        self.bgcolor = d.get('bgColor', '#0000ff')
        self.stroke = d.get('stroke')
        self.fgcolor = d.get('fgColor', '#ffffff')

        # Set the internal useful date representation
        if self.rtdate != None:
            date = self.rtdate
        else:
            date = self.date
        if self.rttime != None:
            time = self.rttime
        else:
            time = self.time

        self.datetime_obj = [to_datetime(date, time), ]
