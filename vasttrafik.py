# vasttrafik-cli
# Copyright (C) 2012-2023 Salvo "LtWorf" Tomaselli
#
# vasttrafik-cli is free software: you can redistribute it and/or modify
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

from dataclasses import dataclass, field
import urllib.request
import urllib.parse
import datetime
from enum import Enum
import json
import re
from time import time
from typing import Dict, List, Optional, NamedTuple, Union
from pathlib import Path

from wcwidth import wcswidth as ulen  # type: ignore
from typedload import load, dump
from xtermcolor import colorize  # type: ignore


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

@dataclass
class Token:
    expires_in: int
    access_token: str

    def expired(self) -> bool:
        return self.expires_in < time()


def to_datetime(date: str, time: str) -> datetime.datetime:
    '''Converts two string date and time into a datetime object

    date format YYYY-MM-DD
    time format HH:MM
    '''
    r = re.match(r'^([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})$', date)
    if r is None:
        raise Exception(f'Incorrect format: {date}')
    year = int(r.group(1))
    month = int(r.group(2))
    day = int(r.group(3))
    r = re.match(r'^([0-9]{1,2}):([0-9]{1,2})$', time)
    if r is None:
        raise Exception(f'Incorrect format: {time}')
    hour = int(r.group(1))
    minute = int(r.group(2))
    return datetime.datetime(year, month, day, hour, minute)


class Vasttrafik:

    def __init__(self, key: str, tokenfile: Path, api: str = "api.vasttrafik.se/bin/rest.exe/v2") -> None:
        '''
        key is the API key that must be sent on every request to obtain a reply.
        you can obtain one at api.vasttrafik.se, but it will be activated the
        night after registration.
        '''
        self.key = key
        self.api = api
        self.datetime_obj: Optional[datetime.datetime] = None
        self._tokenfile = tokenfile
        self._token: Optional[Token] = None

    def _get_token(self) -> Token:
        # Attempt to get cached token
        if self._token is None and self._tokenfile.exists():
            with self._tokenfile.open('rt') as f:
                self._token = load(json.load(f), Token)

        # If there is a token but it's expired, null it
        if self._token and self._token.expired():
            self._token = None

        if self._token is None:
            self._token = self._renew_token()

            with self._tokenfile.open('wt') as f:
                json.dump(dump(self._token), f)
        return self._token

    def _renew_token(self) -> Token:
        url = f'https://api.vasttrafik.se:443/token'
        req = urllib.request.Request(url)
        req.data = b'grant_type=client_credentials'
        req.headers['Authorization'] = 'Basic ' + self.key
        with urllib.request.urlopen(req) as f:
            r = load(json.load(f), Token)
        r.expires_in += int(time())
        return r

    def _request(self, service, param):
        token = self._get_token().access_token

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
        return load(c, Stops)

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
        if dist is not None:
            params += '&maxDist=%d' % dist

        b = self._request('location.nearbystops', params)
        c = b["LocationList"]['StopLocation']

        return load(c, Stops)

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

        trams = load(c, List[BoardItem])

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

    def trip(self, originCoord=None, originId=None, originCoordName=None, destCoord=None, destId=None, destCoordName=None, viaId=None, datetime_obj=None) -> 'Trips':
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

        return load(c['Trip'], Trips)


class LegHalf(NamedTuple):
    date: str
    id: str
    name: str
    time: str
    type: str
    track: str = ''
    routeIdx: Optional[str] = None
    rtDate: Optional[str] = None
    rtTime: Optional[str] = None

    @property
    def datetime_obj(self):
        d = self.rtDate if self.rtDate else self.date
        t = self.rtTime if self.rtTime else self.time
        return to_datetime(d, t)


class VehicleType(Enum):
    ST = 'ST'
    TRAM = 'TRAM'
    BUS = 'BUS'
    WALK = 'WALK'
    BOAT = 'BOAT'
    VAS = 'VAS'
    REG = 'REG'
    TAXI = 'TAXI'

    @property
    def symbol(self) -> str:
        s = {
            self.REG: '🚅',
            self.VAS: '🚆',
            self.TRAM: '🚋',
            self.BUS: '🚌',
            self.WALK: '🚶',
            self.BOAT: '⛴',
            self.ST: ' ',
            self.TAXI: '🚕',
        }
        return s[self]  # type: ignore


class Leg(NamedTuple):

    '''
    a Leg is part of a Trip, and is performed on one vehicle or by foot.
    '''

    name: str
    type: VehicleType
    Origin: LegHalf
    Destination: LegHalf
    # TODO booking
    accessibility: str = ''
    sname: Optional[str] = None
    track: Optional[str] = None
    rtDate: Optional[str] = None
    rtTime: Optional[str] = None
    rtTrack: Optional[str] = None
    direction: Optional[str] = None
    stroke: Optional[str] = None
    id: Optional[str] = None
    bgColor: str = '#0000ff'
    fgColor: str = '#ffffff'
    night: bool = False

    @property
    def wheelchair(self) -> bool:
        return self.accessibility == 'wheelChair'

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
            self.Origin.datetime_obj.hour,
            2,
            self.Origin.datetime_obj.minute,
            2,
            self.Destination.datetime_obj.hour,
            2,
            self.Destination.datetime_obj.minute,
            self.Origin.name,
            self.Destination.name
        )

    def getName(self, color=False):
        '''Returns a nice version of the name
        If color is true, then 256-color escapes will be
        added to give the name the color of the line'''
        if self.sname:
            name = self.sname + ' '
        else:
            name = self.name + ' '

        if self.direction is not None:
            name += self.direction + ' '

        if len(name) > 29:
            name = name[:29] + ' '

        if self.wheelchair:
            name += '♿ '
        if self.night:
            name += '☾ '

        name += self.type.symbol

        while ulen(name) < 33:
            name = ' ' + name

        if not color:
            return name

        fgcolor = int('0x' + self.fgColor[1:], 16)
        bgcolor = int('0x' + self.bgColor[1:], 16)
        return colorize(name, fgcolor, bg=bgcolor)


Legs = List[Leg]


class Trip(NamedTuple):

    '''
    A trip contains a list of Legs (attribute legs).
    If the stops are directly connected the list will only
    have 1 element.

    If on a change the traveler must go from one Track to another,
    a Leg of vehicle_type WALK will be between the other two Legs.
    '''
    Leg: Union[Leg,Legs]

    @property
    def legs(self) -> Legs:
        if isinstance(self.Leg, Leg):
            return [self.Leg]
        return self.Leg

    def toTerm(self):
        return self.toTxt(True)

    def toTxt(self, color=False):
        if self.legs:
            return '\n'.join(i.toTxt(color) for i in self.legs)
        return ''


Trips = List[Trip]


class Accessibility(Enum):
    WHEEL_CHAIR = 'wheelChair'
    NONE = None

    @property
    def symbol(self):
        if self == self.WHEEL_CHAIR:
            return '♿'
        return ''


@dataclass
class BoardItem:

    '''
    This represents one item of the panel at a stop
    has a bunch of attributes to represent the stop
    '''
    name: str
    sname: str

    vehicle_type: VehicleType = field(metadata={'name': 'type'})
    stop: str
    stopid: str
    direction: Optional[str]

    _time: str = field(metadata={'name': 'time'})
    _date: str = field(metadata={'name': 'date'})
    _track: str = field(metadata={'name': 'track'})
    _rtdate: Optional[str] = field(metadata={'name': 'rtDate'}, default=None)
    _rttime: Optional[str] = field(metadata={'name': 'rtTime'}, default=None)
    _rttrack: Optional[str] = field(metadata={'name': 'rtTrack'}, default=None)

    accessibility: Accessibility = Accessibility.NONE
    night: Optional[str] = None

    datetime_obj: List[datetime.datetime] = field(init=False)

    #stroke: Optional[str] = None
    bgcolor: str = field(default='#000000', metadata={'name': 'bgColor'})
    fgcolor: str = field(default='#ffffff', metadata={'name': 'fgColor'})

    @property
    def date(self) -> str:
        return self._rtdate if self._rtdate else self._date

    @property
    def time(self) -> str:
        return self._rttime if self._rttime else self._time

    @property
    def track(self) -> str:
        return self._rttrack if self._rttrack else self._track

    def __post_init__(self):
        self.datetime_obj = [to_datetime(self.date, self.time)]

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

    def toTxt(self, servertime):
        return self.toTerm(servertime, color=False)

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
        name = self.sname + ' '

        name += self.accessibility.symbol
        name += self.vehicle_type.symbol

        if self.night:
            name += u"☾ "

        while ulen(name) < 20:
            name = " " + name

        if not color:
            return name

        fgcolor = int('0x' + self.fgcolor[1:], 16)
        bgcolor = int('0x' + self.bgcolor[1:], 16)
        return colorize(name, fgcolor, bg=bgcolor)

