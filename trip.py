#!/usr/bin/env python
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

from pysttrafik import Vasttrafik, gen_timetable_html, get_key
import readline
import sys
import datetime

key = get_key()
if key == None:
    print "No configuration"
    sys.exit(1)

vast = Vasttrafik(key)

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode emacs')
readline.set_completer_delims(" ")


def get_stop(prompt, preset=None):

    if preset:
        return vast.location(preset)[0]

    while True:
        line = raw_input(prompt)
        if len(line) == 0:
            return None

        stops = vast.location(line)

        for i in range(len(stops)):
            print "%d: %s" % (i, stops[i].name)
            if i > 8:
                break

        while True:
            line = raw_input('> ')
            try:
                return stops[int(line)]
            except:
                break


def get_time():
    line = raw_input('Insert time? [N/y]')
    if line != 'y':
        return datetime.datetime.now()
    hour = raw_input('Hour: ')
    minute = raw_input('Minutes: ')

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

    if len(sys.argv) == 1:
        time = get_time()

    print u'\t%s → %s\t Trips since: %s' % (orig.name, dest.name, str(time))
    for i in vast.trip(originId=orig.id, destId=dest.id, datetime_obj=time):
        print i.toTerm()
        print "========================="

main()
