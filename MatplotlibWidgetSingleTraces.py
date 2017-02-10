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
import os
from Smoothing import *
import matplotlib.patches as patches

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6.5,5))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetSingleTraces(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.ax.set_title('Single Traces', fontsize=12)
        self.canvas.fig.patch.set_alpha(0)
        params = {
                  'legend.fontsize': 12,
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'legend.handletextpad': .5,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        self.plotrefs = []
        self.datafiles = []
        self.dataheader = []
        # default max avg traces: 6
        self.chkboxlist = [False, False, False, False, False, False]
        if sys.platform == 'darwin':
            self.filePath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data'
        else:
            self.filePath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data'
        self.colors = ['k','b','r','g', 'c', 'm']
        self.distmeshsurf = 1.
    
    loadedfile = pyqtSignal(object,object)
    
    def addTrace(self, xlabeltext, normalizeflag):
        # Reading of files assumes same format data files have been saved in 
        # RSDGUI.py (parameter, valueGate1, errGate1, valueGate2, 
        # errGate2) with (parameter, field signal, err, surface signal, err)
        datapath = QFileDialog.getOpenFileNames(self, 'Select WL Scan File', self.filePath, '(*.txt)')
        if not datapath: return
        
        for i in range(len(datapath)):
            self.dataheader.append(os.path.basename(str(datapath[i])))
            self.datafiles.append(loadtxt(str(datapath[i]),skiprows=2))
        self.chkboxlist = [False, False, False, False, False, False]
        for i in range(len(self.dataheader)):
            self.chkboxlist[i] = True
        self.loadedfile.emit(self.dataheader,self.chkboxlist)
        self.filePath = os.path.dirname(str(datapath[0]))
        return len(self.datafiles[0][:,0])

    def plotTraces(self, xlabeltext, normalizeflag, bleft, bright, surfbias):
        self.canvas.ax.clear()
        self.plotrefs = []
        for i in range(len(self.dataheader)):
            data = self.datafiles[i]
            if xlabeltext == 'Voltage':
                # extraction mesh negative
                argx = (data[:,0] + surfbias)/self.distmeshsurf
            else:
                argx = data[:,0]
            if normalizeflag:
                # get maximum for normalisation from smoothed field signal traced (window=5,order=3)
                fieldplotref = self.canvas.ax.plot(argx, data[:,1]/max(savitzky_golay(data[:,1], 5, 3)), \
                self.colors[i], label=str(i+1), linewidth=1.5)[0]
                surfplotref = self.canvas.ax.plot(argx, data[:,3]/max(savitzky_golay(data[:,1], 5, 3)), \
                self.colors[i], linewidth=1.5)[0]
            else:
                fieldplotref = self.canvas.ax.plot(argx, data[:,1], self.colors[i], label=str(i+1), linewidth=1.5)[0]
                surfplotref = self.canvas.ax.plot(argx, data[:,3], self.colors[i], linewidth=1.5)[0]
    
            self.plotrefs.append([fieldplotref,surfplotref])

        if xlabeltext == 'Voltage':
            self.canvas.ax.set_xlabel("Extraction Field (V/cm)", fontsize=12)
        elif xlabeltext == 'Wavelength':
            self.canvas.ax.set_xlabel("Wavelength (nm)", fontsize=12)
        elif xlabeltext == 'Delay':
            self.canvas.ax.set_xlabel("Delay (mus)", fontsize=12)

        self.canvas.ax.set_title('Single Traces', fontsize=12)
        self.canvas.ax.legend(loc="upper left",  bbox_to_anchor = [.02,0.98], fontsize=8)
        axmaxx = max(argx)*1.04
        self.canvas.ax.set_xlim(xmax=axmaxx)

        # overlay for baseline correction
        y0, y1 = self.canvas.ax.get_ylim()
        if argx[-1] < argx[0]:
            argx = argx[::-1]
        width = abs(argx[bright-1] - argx[bleft-1])
        self.canvas.ax.add_patch(patches.Rectangle((argx[bleft-1], y0), width, y1-y0, fc='k', alpha=0.1))
        self.canvas.ax.axhline(lw=1, c='k', ls='--')

        self.canvas.draw()


    def clearDisplay(self):
        self.canvas.ax.clear()
        self.canvas.ax.set_title("Single Traces", fontsize=12)
        self.canvas.draw()
        self.plotrefs = []
        self.datafiles = []
        self.dataheader = []

    def toggleVisibility(self):
        for i in range(len(self.plotrefs)):
            self.plotrefs[i][0].set_visible(self.chkboxlist[i])
            self.plotrefs[i][1].set_visible(self.chkboxlist[i])
        self.canvas.draw()

    def saveFigure(self):
        savepath = QFileDialog.getSaveFileName(self, 'Save Image to File', self.filePath, 'Image Files(*.pdf *.png)')
        if not savepath: return
        self.canvas.fig.savefig(str(savepath))
