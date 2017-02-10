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
import copy

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
from matplotlib.colors import colorConverter
import matplotlib.patches as patches

from scipy import signal

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6,10))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetGrapheneRaw2(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.fig.patch.set_alpha(0)
        self.canvas.fig.tight_layout()
        params = {
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        self.data = []
        self.distmeshsurf = 1.
        self.datastructure = []
        self.traceselect = []
        self.setlegend = False
        if sys.platform == 'darwin':
            self.filePath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2016'
        else:
            self.filePath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2016'
        
        self.chkboxlist = [False, False, False, False]
        self.colors = ['k','b','r','g', 'c', 'm']

    loadedfile = pyqtSignal(object, int)

    def addTrace(self):
        # average traces saved as (paramter, surface, surface err, field, field err)
        datapath = QFileDialog.getOpenFileNames(self, 'Select Matrix Trace File', self.filePath, '(*.txt)')
        if not datapath: return
        for i in range(len(datapath)):
            # read data block
            self.data.append(loadtxt(str(datapath[i]), skiprows=3))
            # read header to get data structure
            [r, c] = self.getDataStructure(datapath[i])
            self.datastructure.append([r, c])
            self.chkboxlist[i] = True
        
        self.traceselect = [[]]*c
        self.filePath = os.path.dirname(str(datapath[0]))
        return [r, c]

    def getDataStructure(self, datapath):
            f = open(datapath, 'r')
            s = f.readlines()[1]
            f.close()
            s = s[s.find(',')+2:-1]
            xi = s.find('x')
            r = s[0:xi]
            c = s[xi+1::]
            return [int(r), int(c)]

    def plot(self, plotmode, normalise, tracenum, baseline, baseleft, baseright, foffsurf, baselinefield, fieldleft, fieldright, fofffield, \
             smoothshow, smoothwin, smoothpol, bconstsurf, bconstfield, peaksurf, kernelsurf, peakfield, kernelfield):
        if len(self.data) < 1 or sum(self.chkboxlist < 1): return
        self.canvas.ax.clear()
        
        if tracenum > (self.datastructure[0][1]): return
        tracenum -= 1
        
        # expected data structure (volt, delay, gate1/field, errgate1, gate2/surf, errgate2)
        for i in range(len(self.data)):
            if self.chkboxlist[i]:   
                # operating on new list changes old list
                data = copy.deepcopy(self.data[i])
                r = self.datastructure[i][0]
                c = self.datastructure[i][1]

                j = tracenum
                argxvolt = data[j*r:(j+1)*r,0]/self.distmeshsurf
                labelstr = i+1
                argysurf = data[j*r:(j+1)*r,4]
                argyfield = data[j*r:(j+1)*r,2]

                # revert data direction
                if argxvolt[-1] < argxvolt[0]:
                    # dependent on incremental direction in scan
                    argxvolt = argxvolt[::-1]
                    argysurf = argysurf[::-1]
                    argyfield = argyfield[::-1]
                
                # field signal processing
                if baselinefield:
                    # substract from averaged data window
                    boff = np.mean(argyfield[fieldleft-1:fieldright])
                    argyfield -= boff
                if bconstfield:
                    # subtract constant
                    argyfield -= fofffield
                
                # median filter for noise removal
                if peakfield:
                    argyfield = signal.medfilt(argyfield, kernelfield)
                
                # surface signal processing
                if baseline:
                    # substract from averaged data window
                    boff = np.mean(argysurf[baseleft-1:baseright])
                    argysurf -= boff
                if bconstsurf:
                    # subtract constant
                    argysurf -= foffsurf
                
                if peaksurf:
                    argysurf = signal.medfilt(argysurf, kernelsurf)
                
                # normalistation to field signal
                fieldsmooth = savitzky_golay(argyfield, smoothwin, smoothpol)
                if normalise:
                    argysurf = argysurf/max(fieldsmooth)
                    argyfield = argyfield/max(fieldsmooth)
                
                col = self.colors[i]
                # overlay smooth traces onto transparent raw data
                if smoothshow: av = 0.5
                else: av=1
                if plotmode == 'Surface':
                    self.canvas.ax.plot(argxvolt, argysurf, color=col, label=labelstr, linewidth=1.5)
                elif plotmode == 'Field':
                    self.canvas.ax.plot(argxvolt, argyfield, color=col, label=labelstr, linewidth=1.5, alpha=av)
                else:
                    self.canvas.ax.plot(argxvolt, argysurf, color=col, label=labelstr, linewidth=1.5)
                    self.canvas.ax.plot(argxvolt, argyfield, color=col, linewidth=1.5, alpha=av)
                
                # plot smoothed traces
                if smoothshow and normalise:
                    if plotmode == 'Field':
                        self.canvas.ax.plot(argxvolt, fieldsmooth/max(fieldsmooth), color=col, linewidth=2.2)
                    elif plotmode == 'Both':
                        self.canvas.ax.plot(argxvolt, fieldsmooth/max(fieldsmooth), color=col, linewidth=2.2)
                elif smoothshow and not(normalise):
                    if plotmode == 'Field':
                        self.canvas.ax.plot(argxvolt, fieldsmooth, color=col, linewidth=2.2)
                    elif plotmode == 'Both':
                        self.canvas.ax.plot(argxvolt, fieldsmooth, color=col, linewidth=2.2)
                
                self.canvas.ax.set_xlim(xmin=0, xmax=max(argxvolt)*1.04)
                
            self.legendobj = self.canvas.ax.legend(loc="upper left",  bbox_to_anchor = [.02,0.98], fontsize=8)
            self.canvas.ax.set_xlabel("Extraction Field (V/cm)")
            self.canvas.ax.set_title('Single Traces', fontsize=12)
            

        if baseline and (plotmode == 'Surface' or plotmode == 'Both'):
            # overlay for baseline correction
            y0, y1 = self.canvas.ax.get_ylim()
            width = abs(argxvolt[baseright-1] - argxvolt[baseleft-1])
            self.canvas.ax.add_patch(patches.Rectangle((argxvolt[baseleft-1], y0), width, y1-y0, fc='g', alpha=0.14))
            
        if baselinefield and (plotmode == 'Field' or plotmode == 'Both'):
            # overlay for baseline correction
            y0, y1 = self.canvas.ax.get_ylim()
            width = abs(argxvolt[fieldright-1] - argxvolt[fieldleft-1])
            self.canvas.ax.add_patch(patches.Rectangle((argxvolt[fieldleft-1], y0), width, y1-y0, fc='c', alpha=0.14))

        self.canvas.ax.axhline(lw=1, c='k', ls='--')
        self.canvas.draw()

    def getPlotData(self):
        plotdata = []
        for i in range(len(self.chkboxlist)):          
            if self.chkboxlist[i]:
                data = self.data[i]
                plotdata.append(data)
        return plotdata
        
    def clearDisplay(self):
        self.canvas.ax.clear()
        self.canvas.ax.set_title("", fontsize=12)
        self.data = []
        self.datastructure = []
        self.chkboxlist = [False, False, False, False]
        self.traceselect = []
        self.canvas.draw()    

    def setTitle(self, text):
        self.canvas.ax.set_title(text, fontsize=12)
        self.canvas.draw()

