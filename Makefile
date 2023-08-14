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

all:
	@echo Nothing to do

.PHONY: install
install:
	#Install py files
	install -d $${DESTDIR:-/}/usr/share/vasttrafik-cli
	install stops.py $${DESTDIR:-/}/usr/share/vasttrafik-cli
	install trip.py $${DESTDIR:-/}/usr/share/vasttrafik-cli
	install -m644 vasttrafik.py $${DESTDIR:-/}/usr/share/vasttrafik-cli
	#Install links
	install -d $${DESTDIR:-/}/usr/bin/
	ln -fs "../share/vasttrafik-cli/stops.py" $${DESTDIR:-/}/usr/bin/stops
	ln -fs "../share/vasttrafik-cli/trip.py" $${DESTDIR:-/}/usr/bin/trip
	#Install conf
	install -m644 -D conf/vasttrafik-cli.conf $${DESTDIR:-/}/etc/vasttrafik-cli.conf
	#Install other files
	install -m644 -D README.md $${DESTDIR:-/}/usr/share/doc/vasttrafik-cli/README.md
	install -m644 -D man/stops.1 $${DESTDIR:-/}/usr/share/man/man1/stops.1
	install -m644 -D man/trip.1 $${DESTDIR:-/}/usr/share/man/man1/trip.1
	install -m644 -D completion/trip $${DESTDIR:-/}/usr/share/bash-completion/completions/trip
	install -m644 -D completion/stops $${DESTDIR:-/}/usr/share/bash-completion/completions/stops

.PHONY: clean
clean:
	$(RM) -r deb-pkg
	$(RM) -r __pycache__
	$(RM) -r *~
	$(RM) -r .mypy_cache/

.PHONY: dist
dist: clean
	cd ..; tar -czvvf vasttrafik-cli.tar.gz \
		vasttrafik-cli/conf/ \
		vasttrafik-cli/CHANGELOG \
		vasttrafik-cli/COPYING \
		vasttrafik-cli/completion \
		vasttrafik-cli/Makefile \
		vasttrafik-cli/man \
		vasttrafik-cli/vasttrafik.py \
		vasttrafik-cli/mypy.conf \
		vasttrafik-cli/README.md \
		vasttrafik-cli/screenshot.png \
		vasttrafik-cli/stops.py \
		vasttrafik-cli/trip.py
	mv ../vasttrafik-cli.tar.gz vasttrafik-cli_`head -1 CHANGELOG`.orig.tar.gz
	gpg --detach-sign -a *.orig.tar.gz

deb-pkg: dist
	mv vasttrafik-cli_`head -1 CHANGELOG`.orig.tar.gz* /tmp
	cd /tmp; tar -xf vasttrafik-cli_*.orig.tar.gz
	cp -r debian /tmp/vasttrafik-cli/
	cd /tmp/vasttrafik-cli/; dpkg-buildpackage --changes-option=-S
	mkdir deb-pkg
	mv /tmp/vasttrafik-cli_* deb-pkg
	$(RM) -r /tmp/vasttrafik-cli

.PHONY: mypy
mypy:
	mypy --config-file mypy.conf trip.py vasttrafik.py

.PHONY: test
test: mypy
