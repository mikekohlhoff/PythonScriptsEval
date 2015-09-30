from PyQt4.QtCore import *
from PyQt4.QtGui import *

from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
import math
from pylab import *
import os
from Smoothing import *

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6.5,5))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetAvgTrace(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.ax.set_title('Average of Single Traces', fontsize=12)
        self.canvas.fig.patch.set_alpha(0)
        params = {
                  'legend.fontsize': 12,
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'legend.handletextpad': .5,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        if sys.platform == 'darwin':
            self.savepath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.savepath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'

    def plotAvgTrace(self, xlabeltext, plotdata, plotchkbox):
        if plotchkbox.count(True) == 0:
            self.clearDisplay()
            return

        fieldtraces = []
        surftraces = []
        
        for i in range(len(plotdata)):
            if plotchkbox[i]:
                # get maximum for normalisation from smoothed traced (window=5,order=3)
                data = plotdata[i]
                fieldtraces.append(data[:,1]/max(savitzky_golay(data[:,1], 5, 3)))
                surftraces.append(data[:,3]/max(savitzky_golay(data[:,1], 5, 3)))

        argx = data[:,0]
        # standard error of the mean
        fieldavg = np.mean(np.vstack(fieldtraces), axis=0)
        fieldavgerr = np.std(np.vstack(fieldtraces), axis=0)/plotchkbox.count(True)
        surfavg = np.mean(np.vstack(surftraces), axis=0)
        surfavgerr = np.std(np.vstack(surftraces), axis=0)/plotchkbox.count(True)

        altgreen = '#66AA55'
        altblack = '#2A2A2A'
        
        self.canvas.ax.clear()
        self.canvas.ax.plot(argx, fieldavg, color=altblack, label='Field Signal', linewidth=1.5)
        self.canvas.ax.errorbar(argx, fieldavg, yerr=fieldavgerr, fmt='none', ecolor=altblack, elinewidth=1.5, capsize=2, capthick=0.5)
        self.canvas.ax.plot(argx, surfavg, color=altgreen, label='Surface Signal', linewidth=1.5)
        self.canvas.ax.errorbar(argx, surfavg, yerr=surfavgerr, fmt='none', ecolor=altgreen, elinewidth=1.5, capsize=2, capthick=0.5)

        if xlabeltext == 'Voltage':
            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
        elif xlabeltext == 'Wavelength':
            self.canvas.ax.set_xlabel("Wavelength (nm)", fontsize=12)
        elif xlabeltext == 'Delay':
            self.canvas.ax.set_xlabel("Delay (mus)", fontsize=12)

        self.canvas.ax.set_title('Average of Single Traces', fontsize=12)
        self.canvas.ax.legend(loc="upper left", bbox_to_anchor = [.022,0.98], fontsize=12)
        axminy = -0.04
        self.canvas.ax.set_ylim(ymin=axminy)
        axmaxx = max(data[:,0])*1.04
        self.canvas.ax.set_xlim(xmax=axmaxx)

        self.canvas.fig.tight_layout()
        self.canvas.draw()
        
        self.savedata = np.hstack((np.vstack(argx), np.vstack(surfavg), np.vstack(surfavgerr), np.vstack(fieldavg), np.vstack(fieldavgerr)))

    def saveTrace(self, scanparam):
        savepath = QFileDialog.getSaveFileName(self, 'Save Average Trace to File', self.savepath, '(*.txt)')
        if not savepath: return
        self.savepath = os.path.dirname(str(savepath))
        if 'Voltage' in scanparam:
            fmtIn = '%.3f'
        elif 'Wavelength' in scanparam:
            # smallest step .00025nm
            fmtIn = '%.5f'
        elif 'Delay' in scanparam:
            fmtIn = '%.11f'
        np.savetxt(str(savepath), self.savedata, fmt=fmtIn, delimiter='\t', newline='\n')

    def saveFigure(self):
        savepath = QFileDialog.getSaveFileName(self, 'Save Image to File', self.savepath, 'Image Files(*.pdf *.png)')
        if not savepath: return
        self.savepath = os.path.dirname(str(savepath))
        self.canvas.fig.savefig(str(savepath))
        
    def clearDisplay(self):
        self.canvas.ax.clear()
        self.canvas.ax.set_title("Average of Single Traces", fontsize=12)
        self.canvas.draw()
        
    def setTitle(self, text):
        self.canvas.ax.set_title(text, fontsize=12)
        self.canvas.draw()
