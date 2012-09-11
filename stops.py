#!/usr/bin/env python

import vasttrafik
import readline
import sys
import os
from configobj import ConfigObj

try:
    config = ConfigObj("%s/.pysttrafik"% os.getenv("HOME"))
    key = config['key']
except:
    print "No configuration"
    sys.exit(1)

vast = vasttrafik.Vasttrafik(key)

readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode emacs')
readline.set_completer_delims(" ")

stops=[]

while True:
    line = raw_input('> ')
    if len(line)==0:
        sys.exit(0)
    elif not line.isdigit():
        stops = vast.location(line)
        for i in range(len(stops)):
            print "%d: %s" % (i,stops[i].name)
            if i>8:
                break
    else:
        trams = vast.board(stops[int(line)].id,time_span=120)
        prev_track=None
        
        f= open('/tmp/t.html','w')
        f.write(vasttrafik.gen_timetable_html(trams,vast.datetime_obj))
        f.close()
        print "\n\n\n\n\n\n\n\n\n"
        print "\t\t%s, Time: %s\n" % (stops[int(line)].name,vast.datetime_obj)
        for i in trams:
            
            if prev_track != i.track:
                print "   == Track %s ==" % i.track
            prev_track = i.track
            print i.toTerm(vast.datetime_obj)
