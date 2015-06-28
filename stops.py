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

key = get_key()
if key == None:
    print "No configuration"
    sys.exit(1)

vast = Vasttrafik(key)

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode emacs')
readline.set_completer_delims(" ")

stops = []

while True:
    line = raw_input('> ')
    if len(line) == 0:
        sys.exit(0)
    elif not line.isdigit():
        stops = vast.location(line)
        for i in range(len(stops)):
            print "%d: %s" % (i, stops[i].name)
            if i > 8:
                break
    else:
        try:
            trams = vast.board(
                stops[int(line)].id, time_span=120, departures=4)
        except:
            print "Error"
            sys.exit(1)
        prev_track = None

        f = open('/tmp/t.html', 'w')
        f.write(gen_timetable_html(trams, vast.datetime_obj))
        f.close()
        print "\n\n\n\n\n\n\n\n\n"
        print "\t\t%s, Time: %s\n" % (stops[int(line)].name, vast.datetime_obj)
        for i in trams:

            if prev_track != i.track:
                print "   == Track %s ==" % i.track
            prev_track = i.track
            print i.toTerm(vast.datetime_obj)
