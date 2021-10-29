#!/usr/bin/env python3
# vasttrafik-cli
# Copyright (C) 2012-2021 Salvo "LtWorf" Tomaselli
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

import sys
import datetime
import os
from typing import Optional
from pathlib import Path

from vasttrafik import Vasttrafik


CONFIGDIR = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
CACHEDIR = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))


def init() -> None:
    '''
    Create expected files and directories
    '''
    if not CACHEDIR.exists():
        CACHEDIR.mkdir(parents=True)


def get_key() -> str:
    '''
    This function tries to load the API key from some configuration files.
    It will try, in the order:
        - /etc/vasttrafik-cli.conf
        - ~/.vasttrafik-cli

    If the files aren't found or they don't contain the key attribute then
    None will be returned, otherwise, a string containing the key will be
    returned.
    '''
    from configobj import ConfigObj  # type: ignore

    paths = (
        Path.home() / '.vasttrafik-cli',
        CONFIGDIR / 'vasttrafik-cli.conf',
        Path('/etc/vasttrafik-cli.conf'),
    )

    path = None
    for i in paths:
        if i.exists():
            path = i
            break
    if path is None:
        raise Exception('No configuration file found')
    config = ConfigObj(str(path))
    return config['key']


key = get_key()
vast = Vasttrafik(key, CACHEDIR / 'vasttrafik-cli-token')


def save_completion(name: str) -> None:
    """
    Saves the name of the stop in the completion file
    """
    # Trim up to the part completion can manage
    for char in ' ,':
        if char in name:
            name = name.split(char, 1)[0]
    # Only lower
    name = name.lower()

    # Read file or presume empty
    path = CACHEDIR / 'vasttrafik-cli-stops'
    if path.exists():
        with path.open('rt') as f:
            lines = [i.strip() for i in f]
    else:
        lines = []

    # Do nothing if completion is there already
    if name in lines:
        return

    # Append new stop to completion
    lines.append(name)

    # Remove old completions, if necessary
    if len(lines) > 100:
        lines.pop(0)

    # Write the file again
    with path.open('wt') as f:
        f.write('\n'.join(lines))


def get_stop(prompt, preset=None):
    if preset:
        r = vast.location(preset)
        save_completion(r[0].name)
        return r[0]

    while True:
        try:
            line = input(prompt)
        except (KeyboardInterrupt, EOFError):
            sys.exit(0)
        if not line:
            return None

        stops = vast.location(line)

        for i in range(len(stops)):
            print("%d: %s" % (i, stops[i].name))
            if i > 8:
                break

        while True:
            try:
                line = input('> ')
            except (KeyboardInterrupt, EOFError):
                sys.exit(0)
            try:
                save_completion(stops[int(line)].name)
                return stops[int(line)]
            except:
                break


def get_time(default):
    if default:
        return datetime.datetime.now()

    try:
        line = input('Insert time? [N/y]')
    except KeyboardInterrupt:
        sys.exit(0)
    except EOFError:
        line = ''
    if line != 'y':
        return datetime.datetime.now()

    try:
        hour = input('Hour: ')
        minute = input('Minutes: ')
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

    now = datetime.datetime.now()
    r = now.replace(minute=int(minute), hour=int(hour))

    if (r - now).total_seconds() < 0:
        # Must increment one day
        r += datetime.timedelta(days=1)
    return r


def tripmain():
    if len(sys.argv) > 3:
        sys.exit('Invalid number of parameters')
    orig = sys.argv[1] if len(sys.argv) == 3 else None
    dest = sys.argv[2] if len(sys.argv) == 3 else None

    origstop = get_stop('FROM: > ', orig)
    deststop = get_stop('TO: > ', dest)

    if origstop is None or deststop is None:
        return

    time = get_time(len(sys.argv) == 3)

    print('\t%s → %s\t Trips since: %s' % (origstop.name, deststop.name, str(time)))
    for i in vast.trip(originId=origstop.id, destId=deststop.id, datetime_obj=time):
        print(i.toTerm())
        print("=========================")


def stopsmain():
    if len(sys.argv) > 2:
        sys.exit('Invalid number of parameters')
    preset = sys.argv[1] if len(sys.argv) == 2 else ''
    stop = get_stop('> ', preset)
    trams = vast.board(stop.id, time_span=120, departures=4)

    print("\t\t%s, Time: %s\n" % (stop.name, vast.datetime_obj))
    prev_track = None
    for i in trams:
        if prev_track != i.track:
            print("   == Track %s ==" % i.track)
        prev_track = i.track
        print(i.toTerm(vast.datetime_obj))


if __name__ == '__main__':

    init()

    cmdname = Path(sys.argv[0]).name
    if cmdname.startswith('trip'):
        tripmain()
    elif cmdname.startswith('stops'):
        stopsmain()
