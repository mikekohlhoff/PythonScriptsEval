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
import matplotlib.patches as patches
import colormaps as cmaps
import math
from pylab import *
import os
from Smoothing import *
import copy
import time
import scipy.integrate as integrate

from scipy import signal

import numpy  as np
import numpy.random as rand

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6.5,5))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class PanOnlyToolbar(NavigationToolbar):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ("Pan", )]

    def __init__(self, *args, **kwargs):
        super(PanOnlyToolbar, self).__init__(*args, **kwargs)
        self.layout().takeAt(1)  #or more than 1 if you have more buttons
        
class MatplotlibWidgetGrapheneData(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.fig.patch.set_alpha(0)
        params = {
                  'legend.fontsize': 12,
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'legend.handletextpad': .5,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        self.main_frame = QWidget()
        self.toolbar = PanOnlyToolbar(self.canvas, self.main_frame)
        self.vbl.addWidget(self.toolbar)
        if sys.platform == 'darwin':
            self.savepath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2016'
        else:
            self.savepath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2016'
        self.savepathavgtrace = self.savepath
        self.cmap = plt.get_cmap('bone')
        self.cmapright = 0.84
        
        # distance valve surface for velocity calculation
        self.dist = 0.46

    plotAgain = pyqtSignal()
    
    def plot(self, mode, datain, datastructure, tracein, chkbox, smooth, smoothwin, smoothpol, \
             errbar, baseline, bl, br, foffsurf, surfbias, baselinefield, fieldleft, fieldright, \
             fofffield, bconstsurf, bconstfield, smoothwinfield, smoothpolfield, peaksurf, kernelsurf, \
             peakfield, kernelfield, allchecked, intleft, intright, dwin, dpol, errcomb, randy, derivativeindex):
                  
        if chkbox.count(True) == 0: return
        r = datastructure[0]
        c = datastructure[1]
        
        # operating on new list changes old list
        datain = copy.deepcopy(datain)
        self.canvas.ax.clear()
         
        if tracein > c: return
        
        # tracenum -= 1 for array indexing
        if not(allchecked): traces = range(tracein-1,tracein)
        else: traces = range(c)
        
        # correct single traces as in raw-graph and average data sets per delay
        # if all traces are checked, calculate average for all delays
        if not(self.allprocessed):
            
            allsurfdelays = []
            self.velocities = []
        
            for t in traces:
                tracenum = t
                surftraces = []
                # for error calculation without spike removal and smooth
                surftracesraw = []
                errtraces = []
                
                for i in range(len(datain)):
                    data = datain[i]
                    j = tracenum
                    argysurf = data[j*r:(j+1)*r,4]
                    errysurf = data[j*r:(j+1)*r,5]
                    argyfield = data[j*r:(j+1)*r,2]
                    argx = data[j*r:(j+1)*r,0]
                    
                    # revert data direction
                    if argx[-1] < argx[0]:
                        # dependent on incremental direction in scan
                        argx = argx[::-1]
                        argysurf = argysurf[::-1]
                        argyfield = argyfield[::-1]
                        errysurf = errysurf[::-1]
                    
                    # field signal processing
                    if baselinefield:
                        # substract from averaged data window
                        boff = np.mean(argyfield[fieldleft-1:fieldright])
                        argyfield -= boff
                    if bconstfield:
                        # subtract constant
                        argyfield -= fofffield
                    if peakfield:
                        # median filter for noise removal
                        argyfield = signal.medfilt(argyfield, kernelfield)
                        
                    # surface signal processing
                    if baseline:
                        # substract from averaged data window
                        boff =  np.mean(argysurf[bl-1:br])
                        argysurf -= boff
                    if bconstsurf:
                        # subtract constant
                        argysurf -= foffsurf
                    # use unfiltered traces for error calculation    
                    argysurfraw = copy.deepcopy(argysurf)
                    if peaksurf:
                        argysurf = signal.medfilt(argysurf, kernelsurf)
                    
                    # normalise to field signal
                    fieldsmooth = savitzky_golay(argyfield, smoothwinfield, smoothpolfield)                
                    argysurf = argysurf/max(fieldsmooth)
                    argysurfraw = argysurfraw/max(fieldsmooth)
                    errysurf = errysurf/max(fieldsmooth)
                    
                    surftraces.append(argysurf)
                    surftracesraw.append(argysurfraw)
                    errtraces.append(errysurf)
                    
                # correct (negative) extraction voltage for (positive) surf bias to get field values
                argx = (argx + surfbias)/self.distmeshsurf
                 
                # average traces per velocity
                # standard error of the mean as relative error
                surfavg = np.mean(np.vstack(surftraces), axis=0)
                # error calculation
                surfavgerr = self.averageErr(surftracesraw, errtraces, errcomb, chkbox.count(True))

                if smooth:
                    argx = savitzky_golay(argx, smoothwin, smoothpol)
                    surfavg = savitzky_golay(surfavg, smoothwin, smoothpol)
                
                # append all velocity traces
                self.velocities.append(self.dist/data[j*r,1])
                allsurfdelays.append(np.hstack((np.vstack(argx), np.vstack(surfavg), np.vstack(surfavgerr))))
                             
                self.fmtIn = '%.3f'
                self.savevel = self.dist/data[j*r,1]
                self.savedata = np.hstack((np.vstack(argx), np.vstack(surfavg), np.vstack(surfavgerr), np.vstack(self.savevel*np.ones(len(argx)))))
                
            self.allsurfdelays = np.asarray(allsurfdelays)
            if allchecked: self.allprocessed = True
            self.integratexmax = len(argx)
   
            self.canvas.ax.plot(argx, surfavg, color='k', linewidth=1.5)
            if errbar:
                self.canvas.ax.errorbar(argx, surfavg, yerr=surfavgerr, fmt='None', ecolor='k', elinewidth=1.5, capsize=2, capthick=0.5)
    
            self.canvas.ax.set_xlabel("Extraction Field (V/cm)", fontsize=12)
            self.canvas.ax.set_ylabel("Surface Signal", fontsize=12)
            self.canvas.ax.set_title('Average of single veloctiy surface traces', fontsize=12)
            self.canvas.ax.set_xlim(xmin=0, xmax=max(argx)*1.04)
            self.canvas.ax.axhline(lw=1, c='k', ls='-')
            self.canvas.fig.tight_layout()
            self.canvas.draw()
        
        if not(self.allprocessed): return
        if mode == 'All Traces':
            self.canvas.ax.clear()
            color=iter(self.cmap(np.linspace(0,self.cmapright,np.shape(self.allsurfdelays)[0])))
            for i in range(np.shape(self.allsurfdelays)[0]):
                x = self.allsurfdelays[i][:,0]
                y = self.allsurfdelays[i][:,1]
                c = next(color)
                # plot without erros for better visibility
                self.canvas.ax.plot(x, y, color=c, linewidth=1.5)
            
            self.canvas.ax.axhline(lw=1, c='k', ls='-')
            # overlay integration area    
            y0, y1 = self.canvas.ax.get_ylim()
            width = abs(x[intright-1] - x[intleft-1])
            altred = '#EE3333'
            self.canvas.ax.add_patch(patches.Rectangle((x[intleft-1], y0), width, y1-y0, ec='w',fc='m', hatch='\\', alpha=0.14))
            self.canvas.ax.axvline(x=x[derivativeindex-1], ymin=-10, ymax=10, lw=2, c='k', ls=':')
            self.canvas.ax.set_xlabel("Extraction Field (V/cm)", fontsize=12)
            self.canvas.ax.set_ylabel("Surface signal", fontsize=12)
            self.canvas.ax.set_title('Average of all velocity traces', fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()
        
        if not(self.dataCalculated): self.calculateData(intleft, intright, dwin, dpol, randy, derivativeindex)
        if mode == 'Integral All':
            if not(allchecked): return
            dist = 0.46

            vel = self.integrals[:,0]
            y = self.integrals[:,1]
            yerr = self.integrals[:,2]
          
            self.canvas.ax.plot(vel, y, color='k', lw=1, ls='--')
            self.canvas.ax.scatter(vel, y, s=26, c='k')
            if errbar:
                self.canvas.ax.errorbar(vel, y, yerr=yerr, fmt='None', ecolor='k', elinewidth=1.5, capsize=2, capthick=1)

            self.canvas.ax.set_xlabel("Velocity (m/s)", fontsize=12)
            self.canvas.ax.set_ylabel('Integrated Surface Traces (arb)', fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()
            self.savedata = self.integrals
            self.fmtIn = '%.3f'
            
        if mode == 'Derivative':
            # derivative of trace for single velocity
            x = self.derivatives[tracein-1][:,0]
            y = self.derivatives[tracein-1][:,1]
            # plot without erros for better visibility
            if smooth:
                y = savitzky_golay(y, smoothwin, smoothpol)
            self.canvas.ax.plot(x, y, color='b', linewidth=2)
      
            self.canvas.ax.plot(x, y, c='k', linewidth=1.5)
            self.canvas.ax.set_xlabel("Extraction Field (V/cm)", fontsize=12)
            self.canvas.ax.set_ylabel("Derivative of Surface signal", fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()
            
        if mode == 'All Derivatives':    
            color=iter(self.cmap(np.linspace(0,self.cmapright,np.shape(self.derivatives)[0])))
            for i in range(np.shape(self.derivatives)[0]):
                x = self.derivatives[i][:,0]
                y = self.derivatives[i][:,1]
                c = next(color)
                # plot without erros for better visibility
                if smooth:
                    y = savitzky_golay(y, smoothwin, smoothpol)
                self.canvas.ax.plot(x, y, color=c, linewidth=1.5)
      
            self.canvas.ax.plot(x, y, c='k', linewidth=1.5)
            self.canvas.ax.set_xlabel("Extraction Field (V/cm)", fontsize=12)
            self.canvas.ax.set_ylabel("Derivative of Surface signal", fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()
    
    def averageErr(self, ytraces, errtraces, errmode, num):
        if errmode and num > 1:
            # combine errors from data sets
            # errors recorded as standard dev from averaging single scope traces
            # 're-calculate' as standard error
            ac = np.sqrt(1)
            if num == 2:
                err = self.combineBins(ytraces[0], ytraces[1], errtraces[0]/ac, errtraces[1]/ac)
            elif num == 3:
                mean1 = np.mean(np.vstack(ytraces[0:2]), axis=0)
                err1 = self.combineBins(ytraces[0], ytraces[1], errtraces[0]/ac, errtraces[1]/ac)
                err = self.combineBins(mean1, ytraces[2], err1, errtraces[2]/ac)
        else:
            # std deviation not error for averaging of traces, need for later randy approach 
            err = np.std(np.vstack(ytraces), axis=0)
            #err = np.sqrt(np.sum(np.array(errtraces)**2, axis=0))
        return err
    
    def combineBins(self, ma, mb, ea, eb):
        # assume 10 averages per data point
        return np.sqrt(9/38.*ea**2 + 9/38.*eb**2 + 100*(ma-mb)**2/7600)
    
    def calculateData(self, intleft, intright, dwin, dpol, randy, derivindex):
        self.integrals = np.zeros((np.shape(self.allsurfdelays)[0], 3), dtype=np.float)
        
        # Calculate integrals
        for i in range(np.shape(self.allsurfdelays)[0]):
            x = self.allsurfdelays[i][:,0]
            surfy = self.allsurfdelays[i][:,1]
            surferr = self.allsurfdelays[i][:,2]
           
            argx = self.velocities[i]
            # trapez rule
            dydx = np.trapz(surfy[intleft-1:intright], x=x[intleft-1:intright])
            if randy:
                # Monte Carlo error sampling  
                dydx, stdvrand = self.trapzErr(x[intleft-1:intright], surfy[intleft-1:intright], surferr[intleft-1:intright])
                derr = stdvrand
            else:
                # TODO stdv vs std error_sqrt
                derr = np.sum(surferr[intleft-1:intright]*4)
            
            self.integrals[i,:] = np.hstack((argx, dydx, derr))
        
        # calculate derivative
        derivatives = []
        
        for i in range(np.shape(self.allsurfdelays)[0]):
            x = self.allsurfdelays[i][:derivindex,0]
            surfy = self.allsurfdelays[i][:derivindex,1]
            
            # order 1 calculates derivative instead of smooth
            dy = savitzky_golay(surfy, dwin, dpol, 1)
            
            derivatives.append(np.hstack((np.vstack(x), np.vstack(dy))))
        
        self.derivatives = np.asarray(derivatives)

        self.dataCalculated = True

    def trapzErr(self, x, y, err, nit=1000):
        areas = np.zeros(nit)
        n = len(x)
        for i in xrange(nit):
            rand_x = rand.normal(size=n)*4 + x
            rand_y = rand.normal(size=n) * err + y
            areas[i] = np.trapz(rand_y, x=rand_x)
            
        return np.mean(areas), np.std(areas)
        
    def clearData(self):
        self.allsurfdelays = []
        
    def clearIntData(self):
        self.integrals = []
        self.derivatives = []
        self.dataCalculated = False

    def saveAvgTrace(self):
        if self.allprocessed: return
        filename = 'v=' + str(int(self.savevel)) + 'ms'
        savepath = QFileDialog.getSaveFileName(self, 'Save Avg Trace to File for ' + filename, self.savepathavgtrace, '(*.txt)')
        if not savepath: return
        self.savepathavgtrace = os.path.dirname(str(savepath))
        np.savetxt(str(savepath), self.savedata, fmt=self.fmtIn, delimiter='\t', newline='\n')

    def saveTrace(self, scanparam):
        if scanparam == 'All Traces' or scanparam == 'Derivative' or scanparam == 'All Derivatives': return
        savepath = QFileDialog.getSaveFileName(self, 'Save ' + scanparam + ' to File', self.savepath, '(*.txt)')
        if not savepath: return
        self.savepath = os.path.dirname(str(savepath))
        np.savetxt(str(savepath), self.savedata, fmt=self.fmtIn, delimiter='\t', newline='\n')

    def saveFigure(self):
        savepath = QFileDialog.getSaveFileName(self, 'Save Image to File', self.savepath, 'Image Files(*.pdf *.png)')
        if not savepath: return
        self.savepath = os.path.dirname(str(savepath))
        self.canvas.fig.savefig(str(savepath))
        
    def setTitle(self, text):
        self.canvas.ax.set_title(text, fontsize=12)
        self.canvas.draw()








