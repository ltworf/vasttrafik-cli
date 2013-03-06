#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013  Salvo "LtWorf" Tomaselli
# 
# This  is free software: you can redistribute it and/or modify
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
from datetime import datetime
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import QBrush, QColor
from PyQt4.QtCore import QDateTime


from stop_selector import StopSelectorWidget
import gui
from pysttrafik import Vasttrafik
from key import get_key

class AppUI(QtGui.QMainWindow):
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = gui.Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.stop_selector = StopSelectorWidget()
        self.from_selector = StopSelectorWidget()
        self.to_selector = StopSelectorWidget()
        
        self.stopList = self.ui.stopList
        self.tripList = self.ui.tripList
        self.dateTimeEdit = self.ui.dateTimeEdit
        
        self.ui.tripFormLayout.addRow('From',self.from_selector)
        self.ui.tripFormLayout.addRow('To',self.to_selector)
        self.ui.stopLayout.addWidget(self.stop_selector)
        
        
        self.stopList.headerItem().setText(0,'')
        self.stopList.headerItem().setText(1,'')
        self.stopList.headerItem().setText(2,'Direction')
        self.stopList.headerItem().setText(3,'Minutes')
        
        self.tripList.setColumnCount(5)
        self.tripList.headerItem().setText(0,'Departure')
        self.tripList.headerItem().setText(1,'')
        self.tripList.headerItem().setText(2,'Track')
        self.tripList.headerItem().setText(3,'Destination')
        self.tripList.headerItem().setText(4,'Arrival')
        
        
        QtCore.QObject.connect(self.stop_selector,QtCore.SIGNAL("selected()"),self.boardselected)
        QtCore.QObject.connect(self.from_selector,QtCore.SIGNAL("selected()"),self.stopselected)
        QtCore.QObject.connect(self.to_selector,QtCore.SIGNAL("selected()"),self.stopselected)
        
        now=datetime.now()
        min_date_time = QDateTime(now.year,now.month,now.day,now.hour,now.minute)
        
        self.dateTimeEdit.setMinimumDateTime(min_date_time)
        #Initialize vasttrafik object 
        self.vast = Vasttrafik(get_key())
    def swapstops(self):
        if self.from_selector.stopId == None or self.to_selector.stopId == None:
            return
        
        orig = self.from_selector.stop
        dest = self.to_selector.stop
        
        self.from_selector.setStop(dest)
        self.to_selector.setStop(orig)
        
        self.stopselected()
        
    def boardselected(self):
        if self.stop_selector.stopId == None:
            return
        self.stopList.clear()
        
        trams = self.vast.board(self.stop_selector.stopId,time_span=120,departures=4)
        

        #Set content
        for i in trams:
            item = QtGui.QTreeWidgetItem()
            
            
            bc = QColor(
                int(i.bgcolor[1:3],16),
                int(i.bgcolor[3:5],16),
                int(i.bgcolor[5:7],16),
                )
            fc = QColor(
                int(i.fgcolor[1:3],16),
                int(i.fgcolor[3:5],16),
                int(i.fgcolor[5:7],16),
                )
            
            bbrush=QtGui.QBrush()
            fbrush=QtGui.QBrush()

            bbrush.setColor(fc)
            fbrush.setColor(bc)

            bbrush.setStyle(1)
            fbrush.setStyle(1)

            
            item.setBackground(0,bbrush)
            item.setForeground(0,fbrush)
            
            item.setText(0,i.getName().strip())
            item.setText(1,i.track)
            item.setText(2,i.direction)
            
            
            delta = [(q - self.vast.datetime_obj).seconds / 60 for q in i.datetime_obj]
            delta.sort()
            delta = [str(i) for i in delta]
            item.setText(3,', '.join(delta))
            
            self.stopList.addTopLevelItem(item)

        for i in range(4):
            self.stopList.resizeColumnToContents(i) #Must be done in order to avoid  too small columns
    
    
    def stopselected(self):
        if self.from_selector.stopId == None or self.to_selector.stopId == None:
            return
        d=self.dateTimeEdit.dateTime()
        date = d.date()
        time = d.time()
        
        d=datetime(date.year(),date.month(),date.day(),time.hour(),time.minute())
        
        trips=self.vast.trip(originId = self.from_selector.stopId, destId = self.to_selector.stopId,datetime_obj=d)
        
        
        self.tripList.clear()
        
        for trip in trips:
            item = QtGui.QTreeWidgetItem()
            for i in trip.legs:
                if i.origin.name == i.destination.name:
                    continue
                
                leg = QtGui.QTreeWidgetItem()
                
                bc = QColor(
                    int(i.bgcolor[1:3],16),
                    int(i.bgcolor[3:5],16),
                    int(i.bgcolor[5:7],16),
                    )
                fc = QColor(
                    int(i.fgcolor[1:3],16),
                    int(i.fgcolor[3:5],16),
                    int(i.fgcolor[5:7],16),
                    )
            
                bbrush=QtGui.QBrush()
                fbrush=QtGui.QBrush()

                bbrush.setColor(fc)
                fbrush.setColor(bc)

                bbrush.setStyle(1)
                fbrush.setStyle(1)

                leg.setBackground(1,bbrush)
                leg.setForeground(1,fbrush)
                
                leg.setText(0,'%02d:%02d' % (i.origin.datetime_obj.hour,i.origin.datetime_obj.minute))
                
                leg.setText(1,i.getName().strip())
                
                if i.origin.track !=None:
                    leg.setText(2,i.origin.track)
                leg.setText(3,i.destination.name)
                
                leg.setText(4,str(i.destination.datetime_obj.strftime('%H:%M')))
                
                item.addChild(leg)
            item.setText(0,'%02d:%02d' % (trip.legs[0].origin.datetime_obj.hour,trip.legs[0].origin.datetime_obj.minute))
            self.tripList.addTopLevelItem(item)
        
        self.tripList.expandAll()
            
        for i in range(4):
            self.tripList.resizeColumnToContents(i) #Must be done in order to avoid  too small columns
      
def main():
    app = QtGui.QApplication(sys.argv)
    
    MainWindow = AppUI()
    MainWindow.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
