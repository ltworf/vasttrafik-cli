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
        trams= vast.board(stops[int(line)].id)
        f= open('/tmp/t.html','w')
        f.write(vasttrafik.gen_timetable_html(trams,vast.datetime_obj))
        f.close()
        print "\n\n\n\n\n\n\n\n\n"
        print "\t\t\t%s" % stops[int(line)].name
        for i in trams:
            print i.toTerm(vast.datetime_obj)
