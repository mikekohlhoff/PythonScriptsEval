from PyQt4.QtCore import *
from PyQt4.QtGui import *

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import math
from pylab import *
import os
from Smoothing import *
import numpy as np

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6,10))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetOverview(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.ax.set_title('Series of Averages', fontsize=12)
        self.canvas.fig.patch.set_alpha(0)
        params = {
                  'legend.fontsize': 12,
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'legend.handletextpad': .5,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        
        self.datafield = []
        self.dataheader = []
        self.plotmode = 'Surface'
        self.scanmode = 'Voltage'
        self.setScanMode(self.scanmode)
        self.smooth = False
        self.smoothwin = 5
        self.smoothpol = 3
        # load colormap
        self.cmap = plt.cm.coolwarm
        self.setlegend = True

        if sys.platform == 'darwin':
            self.filePath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.filePath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'
    
    def receiveTrace(self, data, title):
        self.datafield.append(data)
        self.dataheader.append(title)
        self.plotTraces()

    def addTrace(self):
        # average traces saved as (paramter, surface, surface err, field, field err)
        datapath = QFileDialog.getOpenFileNames(self, 'Select Avgerage Trace File', self.filePath, '(*.txt)')
        if not datapath: return
        for i in range(len(datapath)):
            self.datafield.append(loadtxt(str(datapath[i])))
            self.dataheader.append(os.path.basename(str(datapath[i])))
        
        self.plotTraces()
        self.filePath = os.path.dirname(str(datapath[0]))

    def smoothParamChanged(self, smooth, smoothwin, smoothpol):
        self.smooth = smooth
        self.smoothwin = smoothwin
        self.smoothpol = smoothpol
        self.plotTraces()
    
    def plotTraces(self):
        if len(self.datafield) < 1: return
        color = iter(self.cmap(np.linspace(0,1,len(self.dataheader))))
        self.canvas.ax.clear()
        for i in range(len(self.dataheader)):
            data = self.datafield[i]
            c = next(color)

            errsurf = data[:,2]
            errfield = data[:,4]

            if self.smooth:
                argx = savitzky_golay(data[:,0], self.smoothwin, self.smoothpol)
                argsurf = savitzky_golay(data[:,1], self.smoothwin, self.smoothpol)
                argfield = savitzky_golay(data[:,3], self.smoothwin, self.smoothpol)

            else:
                argx = data[:,0]
                argsurf = data[:,1]
                argfield = data[:,3]

            if self.plotmode == 'Surface':
                self.canvas.ax.plot(argx, argsurf, color=c, linewidth=1.5, label=self.dataheader[i]) 
                self.canvas.ax.errorbar(argx, argsurf, yerr=errsurf, fmt='none', elinewidth=1.5, \
                capsize=2, capthick=0.5, ecolor=c)
            elif self.plotmode == 'Field':
                self.canvas.ax.plot(argx, argfield, color=c, linewidth=1.5, label=self.dataheader[i])
                self.canvas.ax.errorbar(argx, argfield, yerr=errfield, fmt='none', elinewidth=1.5, \
                capsize=2, capthick=0.5, ecolor=c)
            elif self.plotmode == 'Both':
                self.canvas.ax.plot(argx, argsurf, color=c, linewidth=1.5, label=self.dataheader[i]) 
                self.canvas.ax.errorbar(argx, argsurf, yerr=errsurf, fmt='none', elinewidth=1.5, \
                capsize=2, capthick=0.5, ecolor=c)
                self.canvas.ax.plot(argx, argfield, color=c, linewidth=1.5) 
                self.canvas.ax.errorbar(argx, argfield, yerr=errfield, fmt='none', elinewidth=1.5, \
                capsize=2, capthick=0.5, ecolor=c)
        
        self.legendobj = self.canvas.ax.legend(loc="upper left",  bbox_to_anchor = [.02,0.98], fontsize=12)
        self.setLegend(self.setlegend)
        self.canvas.ax.set_ylim(ymin=-0.04)
        axmaxx = max(data[:,0])*1.04
        self.canvas.ax.set_xlim(xmax=axmaxx)
        self.canvas.fig.tight_layout()
        self.canvas.draw()

    def clearDisplay(self):
        self.canvas.ax.clear()
        self.canvas.ax.set_title("", fontsize=12)
        self.canvas.draw()
        self.plotrefs = []
        self.datafield = []
        self.dataheader = []
        self.canvas.draw()

    def setLegend(self, setlegend):
        self.setlegend = setlegend
        if hasattr(self, 'legendobj'):
            self.legendobj.set_visible(self.setlegend)
            self.canvas.draw()
        
    def setScanMode(self, text):
        self.scanmode = str(text)
        if text == 'Voltage':
            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
        elif text == 'Wavelength':
            self.canvas.ax.set_xlabel("Wavelength (nm)", fontsize=12)
        elif text == 'Delay':
            self.canvas.ax.set_xlabel("Delay (mus)", fontsize=12)
        self.canvas.draw()
        
    def setPlotMode(self, text):
        self.plotmode = text
        self.plotTraces()
        
    def setTitle(self, text):
        self.canvas.ax.set_title(text, fontsize=12)
        self.canvas.draw()
        
    def setAxisTitle(self, text):
        self.canvas.ax.set_xlabel(text, fontsize=12)
        self.canvas.draw()
        
    def saveTrace(self):
        if len(self.datafield) < 1: return
        savedata = np.array([]).reshape(max(np.shape(self.datafield[0])),0)
        for i in range(len(self.datafield)):
            data = self.datafield[i]
            savedata = np.hstack((savedata,np.vstack(data[:,0])))
            if self.plotmode == 'Surface':
                savedata = np.hstack((savedata,np.vstack(data[:,1])))
                savedata = np.hstack((savedata,np.vstack(data[:,2])))
            elif self.plotmode == 'Field':
                savedata = np.hstack((savedata,np.vstack(data[:,3])))
                savedata = np.hstack((savedata,np.vstack(data[:,4])))
            elif self.plotmode == 'Both':
                savedata = np.hstack((savedata,np.vstack(data[:,1])))
                savedata = np.hstack((savedata,np.vstack(data[:,2])))
                savedata = np.hstack((savedata,np.vstack(data[:,3])))
                savedata = np.hstack((savedata,np.vstack(data[:,4])))

        savepath = QFileDialog.getSaveFileName(self, 'Save Traces to File', self.filePath, '(*.txt)')
        if not savepath: return
        if 'Voltage' in self.scanmode:
            fmtIn = '%.3f'
        elif 'Wavelength' in self.scanmode:
            # smallest step .00025nm
            fmtIn = '%.5f'
        elif 'Delay' in self.scanmode:
            fmtIn = '%.11f'
            
        headertext = ''
        for i in range(len(self.dataheader)):
            headertext += self.dataheader[i] + ', '
        headertext += '\n'
        if self.plotmode == 'Surface':
            headertext += (str(self.scanmode) + '\t' + 'SurfIon' + '\t' + 'SurfErr')*len(self.dataheader)
        elif self.plotmode == 'Field':
            headertext += (str(self.scanmode) + '\t' + 'FieldIon' + '\t' + 'FieldErr')*len(self.dataheader)
        elif self.plotmode == 'Both':
            headertext += (str(self.scanmode) + '\t' + 'SurfIon' + '\t' + 'SurfErr' + '\t' + 'FieldIon' + '\t' + 'FieldErr')*len(self.dataheader)
        np.savetxt(str(savepath), savedata, fmt=fmtIn, delimiter='\t', newline='\n', header=headertext)

    def saveFigure(self):
        savepath = QFileDialog.getSaveFileName(self, 'Save Image to File', self.filePath, 'Image Files(*.pdf *.png)')
        if not savepath: return
        self.canvas.fig.savefig(str(savepath))
     
