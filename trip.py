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

from vasttrafik import Vasttrafik, get_key

key = get_key()
if key is None:
    print("No configuration")
    sys.exit(1)

vast = Vasttrafik(key)

def save_completion(name: str) -> None:
    """
    Saves the name of the stop in the completion file
    """
    cachedir = '%s/.cache/' % os.getenv("HOME")

    # Do nothing if cachedir is not there
    if not os.path.exists(cachedir):
        return

    # Read file or presume empty
    path = cachedir + 'vasttrafik-cli-stops'
    if os.path.exists(path):
        with open(path, 'rt') as f:
            lines = [i.strip() for i in f]
    else:
        lines = []

    # Trim up to the part completion can manage
    for char in ' ,':
        if char in name:
            name = name.split(char, 1)[0]
    # Only lower
    name = name.lower()

    # Do nothing if completion is there already
    if name in lines:
        return

    # Append new stop to completion
    lines.append(name)

    # Remove old completions, if necessary
    if len(lines) > 100:
        lines.pop(0)

    # Write the file again
    with open(path, 'wt') as f:
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


def main():
    orig = sys.argv[1] if len(sys.argv) > 2 else None
    dest = sys.argv[2] if len(sys.argv) > 2 else None

    orig = get_stop('FROM: > ', orig)
    dest = get_stop('TO: > ', dest)

    if orig == None or dest == None:
        return

    time = get_time(len(sys.argv) == 3)

    print('\t%s → %s\t Trips since: %s' % (orig.name, dest.name, str(time)))
    for i in vast.trip(originId=orig.id, destId=dest.id, datetime_obj=time):
        print(i.toTerm())
        print("=========================")

if __name__ == '__main__':
    main()
