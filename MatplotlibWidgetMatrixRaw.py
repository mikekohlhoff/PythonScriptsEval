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

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
from matplotlib.colors import colorConverter
import matplotlib.patches as patches

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6,10))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetMatrixRaw(QGraphicsView):
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
            self.filePath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.filePath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'
        
        self.chkboxlist = [False, False, False, False, False, False]
        self.colors = ['k','b','r','g', 'c', 'm']

    loadedfile = pyqtSignal(object, int)

    def addTrace(self):
        # average traces saved as (paramter, surface, surface err, field, field err)
        datapath = QFileDialog.getOpenFileNames(self, 'Select Avgerage Trace File', self.filePath, '(*.txt)')
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

    def plot(self, plotmode, normalise, tracenum, baseline, baseleft, baseright):
        if len(self.data) < 1: return
        self.canvas.ax.clear()
        if tracenum > (self.datastructure[0][1]): return
        tracenum -= 1
        # expected data structure (volt, delay, gate1/field, errgate1, gate2/surf, errgate2)
        for i in range(len(self.data)):
            if self.chkboxlist[i]:
                data = self.data[i]
                r = self.datastructure[i][0]
                c = self.datastructure[i][1]

                j = tracenum
                argxvolt = data[j*r:(j+1)*r,0]/self.distmeshsurf
                labelstr = i+1
                argysurf = data[j*r:(j+1)*r,4]
                argyfield = data[j*r:(j+1)*r,2]

                if normalise:
                    argysurf = argysurf/max(savitzky_golay(argyfield, 5, 3))
                    argyfield = argyfield/max(savitzky_golay(argyfield, 5, 3))
                
                c = self.colors[i]
                if plotmode == 'Surface':
                    self.canvas.ax.plot(argxvolt, argysurf, color=c, label=labelstr, linewidth=1.2)
                elif plotmode == 'Field':
                    self.canvas.ax.plot(argxvolt, argyfield, color=c, label=labelstr, linewidth=1.2)
                else:
                    self.canvas.ax.plot(argxvolt, argysurf, color=c, label=labelstr, linewidth=1.2)
                    self.canvas.ax.plot(argxvolt, argyfield, color=c, linewidth=1.2)
                
                self.legendobj = self.canvas.ax.legend(loc="upper left",  bbox_to_anchor = [.02,0.98], fontsize=8)
                self.canvas.ax.set_xlabel("Extraction Field (V/cm)")
                self.canvas.ax.set_title('Single Traces', fontsize=12)
                self.canvas.ax.set_xlim(xmin=0, xmax=max(argxvolt)*1.04)

                if baseline:
                    # overlay for baseline correction
                    y0, y1 = self.canvas.ax.get_ylim()
                    if argxvolt[-1] < argxvolt[0]:
                        argxvolt = argxvolt[::-1]
                    width = abs(argxvolt[baseright-1] - argxvolt[baseleft-1])
                    self.canvas.ax.add_patch(patches.Rectangle((argxvolt[baseleft-1], y0), width, y1-y0, fc='k', alpha=0.1))

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
        self.chkboxlist = [False, False, False, False, False, False]
        self.traceselect = []
        self.canvas.draw()    
    
    def saveFigure(self):
        savepath = QFileDialog.getSaveFileName(self, 'Save Image to File', self.filePath, 'Image Files(*.pdf *.png)')
        if not savepath: return
        self.canvas.fig.savefig(str(savepath))

    def setTitle(self, text):
        self.canvas.ax.set_title(text, fontsize=12)
        self.canvas.draw()

