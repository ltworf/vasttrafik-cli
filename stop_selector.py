
from PyQt4.QtCore import QString
from PyQt4.QtGui import QFrame
from PyQt4 import QtCore

from pysttrafik import Vasttrafik
from key import get_key
from selgui import Ui_Frame

class StopSelectorWidget(QFrame):
    
    selected = QtCore.pyqtSignal(name='selected')
    
    
    def __init__(self):
        super(StopSelectorWidget, self).__init__()
        
        #Initialize the frame and components
        self.ui = Ui_Frame()
        self.ui.setupUi(self)
        self.listWidget = self.ui.listWidget
        self.lineEdit = self.ui.lineEdit
        
        #Initialize the events
        QtCore.QObject.connect(self.lineEdit,QtCore.SIGNAL("textEdited(QString)"),self.changed)
        QtCore.QObject.connect(self.listWidget,QtCore.SIGNAL("activated(QModelIndex)"),self.selectedItem)
        QtCore.QObject.connect(self.ui.clearbtn,QtCore.SIGNAL("clicked()"),self.clear)
        
        #Initialize the internal status
        self.clear()
        
        
        #Initialize vasttrafik object 
        self.vast = Vasttrafik(get_key())
        
    def setStop(self,stop):
        self.stop = stop
        self.stopId = stop.id
        self.lineEdit.setText(stop.name)
    
    def clear(self):
        self.lineEdit.clear()
        self.listWidget.clear()
        self.listWidget.hide()
        self.stopId = None
        self.stop = None
        
    def selectedItem(self,item):
        r = self.listWidget.currentRow()
        s = self.stops[r]
        
        self.stopId = s.id
        self.stop = s
        self.selected.emit()
        
        self.lineEdit.setText(s.name)
        self.listWidget.hide()
        
    def changed(self,text):
        if self.stop != None:
            self.clear()
            self.lineEdit.setText(text)
            return 
            
        self.ui.listWidget.clear()
        if len(text) < 3:
            self.ui.listWidget.show()
            return
        text = unicode(text).encode('utf8')
        stops = self.vast.location(text)
        
        self.stops=stops
        
        for i in stops:
            qs=QString(i.name.encode('utf-8'))
            self.listWidget.addItem(i.name)
        if len(stops) == 1:
            self.selectedItem(self.listWidget.item(0))