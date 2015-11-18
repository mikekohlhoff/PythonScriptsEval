from PyQt4.QtCore import *
from PyQt4.QtGui import *

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
import math
from pylab import *
from matplotlib.ticker import FuncFormatter
import os

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6.5,5))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetRydSeries(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.ax.set_title('Rydberg Series', fontsize=12)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.fig.patch.set_alpha(0)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        params = {
                  'legend.fontsize': 12,
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'legend.handletextpad': .5,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.mpl_toolbar.pan()
        self.clearflag = False
        self.defaultloaded = False
        self.filePath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike'
    
    pickedValReady = pyqtSignal(object)
    
    def defaultSet(self, bool):
        self.defaultloaded = bool
    
    def plotWLScan(self,laseroffset):
        '''display complete WL scan and Rydberg series on top'''
        dataField = loadtxt('FullWavelengthScanField.txt')
        dataSurface = loadtxt('FullWavelengthScanSurface.txt')
        argYField = dataField[:,1]/max(dataField[:,1])
        argYSurface = dataSurface[:,1]/max(dataSurface[:,1])
        self.canvas.ax.clear()
        self.canvas.ax.plot(dataField[:,0], argYField, 'k', label="Field Signal", linewidth=1.5)
        self.canvas.ax.plot(dataSurface[:,0], argYSurface, 'g', label="Surface Signal", linewidth=1.5)
        self.canvas.ax.set_xlabel("Fundamental Wavelength (nm)", fontsize=12)
        self.canvas.ax.set_title('Rydberg Series', fontsize=12)
        self.canvas.ax.legend(loc="upper right",  bbox_to_anchor = [.98,0.86], fontsize=12)
        self.canvas.ax.set_ylim([-0.02,1.12])
        self.plotRydSeries(laseroffset)
        self.canvas.fig.tight_layout()
        self.canvas.draw()
        self.defaultloaded = True

    def addTrace(self):
        datapath = QFileDialog.getOpenFileName(self, 'Select WL Scan File', self.filePath, '(*.txt)')
        if not datapath: return
        self.filePath = os.path.dirname(str(datapath))
        if len(datapath) < 1: return
        data = loadtxt(str(datapath))
        argY = data[:,1]/max(data[:,1])
        if self.defaultloaded:
            self.canvas.ax.plot(data[:,0], argY, 'r', label="Field Signal", linewidth=1.5)
        else:
            self.canvas.ax.plot(data[:,0], argY, 'k', label="Field Signal", linewidth=1.5)
        self.canvas.draw()
        

    def clearDisplay(self):
        self.canvas.ax.cla()
        self.canvas.draw()
        self.clearflag = True
        self.defaultloaded = False

    def onclick(self, event):
        if event.button == 3:
            self.pickedValReady.emit(event.xdata)

    def plotRydSeries(self, laseroffset):
        # Rydberg constant for Hydrogen
        rh = 109677.583
        nRange = np.arange(15, 71)
        j32offset = 0.091 # 1/64*alpha^2*Ryd
        rydEn = (2.*10**7)/(rh*(0.25 - (1./nRange**2)) - j32offset) + laseroffset
        if not(self.clearflag):
            if hasattr(self, 'rydlines') and len(self.canvas.ax.lines) > 0:
                for i in range(np.size(self.rydlines)):
                    self.canvas.ax.lines.remove(self.rydlines[i])
            if hasattr(self, 'rydlabels') and len(self.canvas.ax.texts) > 0:
                 for i in range(np.size(self.rydlines)):
                    self.rydlabels[i].remove()
        xx = (rydEn, rydEn)
        yy = (np.ones(np.size(rydEn))*-0.02,np.ones(np.size(rydEn))*1.02)
        self.rydlines = self.canvas.ax.plot(xx,yy,linewidth=1,color='b')
        labels = nRange.astype(str)
        self.rydlabels = {}       
        for i in range(np.size(labels)):
            self.rydlabels[i] = self.canvas.ax.text(rydEn[i], 1.06, labels[i],
        horizontalalignment='center',verticalalignment='center',color='b',fontsize=12)
        self.canvas.draw()
        self.clearflag = False

