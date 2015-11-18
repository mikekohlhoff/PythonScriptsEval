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
import copy
import time
import scipy.integrate as integrate

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(6.5,5))
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)

class MatplotlibWidgetMatrixData(QGraphicsView):
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
        if sys.platform == 'darwin':
            self.savepath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.savepath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'
        self.cmap = plt.cm.Blues
        self.contourcmap = plt.cm.bone
        self.dataready = False

    plotAgain = pyqtSignal()
    
    def plot(self, mode, datain, datastructure, tracenum, chkbox, smooth, smoothwin, smoothpol, normalise, plotmode, errbar, baseline, bl, br):
        if chkbox.count(True) == 0: return
        r = datastructure[0]
        c = datastructure[1]
        
        # operating on new list changes old list
        datain = copy.deepcopy(datain)
        self.canvas.ax.clear()
        
        if mode == 'Average':
            if tracenum > c: return
            tracenum -= 1
            fieldtraces = []
            surftraces = []
            
            for i in range(len(datain)):
                data = datain[i]
                j = tracenum
                argysurf = data[j*r:(j+1)*r,4]
                argyfield = data[j*r:(j+1)*r,2]
                
                argx = data[j*r:(j+1)*r,0]/self.distmeshsurf
                if baseline:
                    # get baseline shift 
                    if argx[-1] < argx[0]:
                        # dependent on incremental direction in scan
                        argsb = argysurf[::-1]
                    else: argsb = argysurf
                    boff = np.mean(argsb[bl-1:br])
                    argysurf -= boff
                # normalise to field signal
                if normalise:
                    maxF = max(savitzky_golay(argyfield, 5, 3))
                    argysurf = argysurf/maxF
                    argyfield = argyfield/maxF

                fieldtraces.append(argyfield)
                surftraces.append(argysurf)

            argx = data[j*r:(j+1)*r,0]/self.distmeshsurf
            labelstr = str(data[j*r,1]*1E6)

            # standard error of the mean as relative error
            fieldavg = np.mean(np.vstack(fieldtraces), axis=0)
            fieldavgerr = (np.std(np.vstack(fieldtraces), axis=0)/chkbox.count(True))
            surfavg = np.mean(np.vstack(surftraces), axis=0)
            surfavgerr = (np.std(np.vstack(surftraces), axis=0)/chkbox.count(True))

            if smooth:
                argx = savitzky_golay(argx, smoothwin, smoothpol)
                surfavg = savitzky_golay(surfavg, smoothwin, smoothpol)
                fieldavg = savitzky_golay(fieldavg, smoothwin, smoothpol)

            if plotmode == 'Surface':
                self.canvas.ax.plot(argx, surfavg, color='g', label='Surface Signal', linewidth=1.5)
                if errbar:
                    self.canvas.ax.errorbar(argx, surfavg, yerr=surfavgerr, fmt='None', ecolor='g', elinewidth=1.5, capsize=2, capthick=0.5)
            elif plotmode == 'Field':
                self.canvas.ax.plot(argx, fieldavg, color='k', label='Field Signal', linewidth=1.5)
                if errbar:
                    self.canvas.ax.errorbar(argx, fieldavg, yerr=fieldavgerr, fmt='None', ecolor='k', elinewidth=1.5, capsize=2, capthick=0.5)
            else:
                self.canvas.ax.plot(argx, fieldavg, color='k', label='Field Signal', linewidth=1.5)
                self.canvas.ax.plot(argx, surfavg, color='g', label='Surface Signal', linewidth=1.5)
                if errbar:
                    self.canvas.ax.errorbar(argx, fieldavg, yerr=fieldavgerr, fmt='None', ecolor='k', elinewidth=1.5, capsize=2, capthick=0.5)
                    self.canvas.ax.errorbar(argx, surfavg, yerr=surfavgerr, fmt='None', ecolor='g', elinewidth=1.5, capsize=2, capthick=0.5)

            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
            self.canvas.ax.set_title('Average of Single Traces', fontsize=12)
            self.canvas.ax.legend(loc="upper left", bbox_to_anchor = [.022,0.98], fontsize=12)
            self.canvas.ax.set_xlim(xmin=0, xmax=max(argx)*1.04)
            self.canvas.ax.axhline(lw=1, c='k', ls='--')
            self.canvas.fig.tight_layout()
            self.canvas.draw()

        elif mode == 'All Traces':
            if not(self.dataready): return
            color=iter(self.cmap(np.linspace(0.3,1,len(self.singletraces))))
            for i in range(len(self.singletraces)):
                x = self.singletraces[i][:,0]
                y = self.singletraces[i][:,2]
                if smooth:
                    y = savitzky_golay(y, smoothwin, smoothpol)
                c = next(color)
                self.canvas.ax.plot(x, y, color=c, linewidth=1.5)
                
            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
            self.canvas.ax.set_ylabel("Normalised Surface signal", fontsize=12)
            self.canvas.ax.set_title('Average of Single Traces', fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()

        elif mode == 'Integral':
            if not(self.dataready): return
            dist = 0.46

            x = self.integrals[:,0]
            y = self.integrals[:,1]
            yerr = self.integrals[:,2]
            vels = (dist/x)*math.sin(math.radians(20))

            self.canvas.ax.plot(vels, y, color='k', lw=1, ls='--')
            self.canvas.ax.scatter(vels, y, s=26, c='k')
            if errbar:
                self.canvas.ax.errorbar(vels, y, yerr=yerr, fmt='None', ecolor='k', elinewidth=1.5, capsize=2, capthick=1)

            self.canvas.ax.set_xlabel("Velocity (m/s)", fontsize=12)
            self.canvas.ax.set_ylabel('Integrated Surface Traces (arb)', fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()

        elif mode == 'Derivative': 
            if not(self.dataready): return
            dist = 0.46
            color=iter(self.cmap(np.linspace(0.3,1,len(self.derivatives))))
            
            x = self.derivatives[tracenum-1][:,0]
            y = self.derivatives[tracenum-1][:,2]
            delay = self.derivatives[tracenum-1][0,1]
            label = '{:.0f}'.format(((dist/delay)*math.sin(math.radians(20)))) + '(m/s)'

            if smooth:
                y = savitzky_golay(y, smoothwin, smoothpol)
            self.canvas.ax.plot(x, y, c='k', linewidth=1.5, label=label)
            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
            self.canvas.ax.set_ylabel("Derivative of Surface signal", fontsize=12)
            self.canvas.ax.legend(loc="upper left", bbox_to_anchor = [.022,0.98], fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()

        elif mode == 'All Derivatives':
            if not(self.dataready): return
            color=iter(self.cmap(np.linspace(0.3,1,len(self.derivatives))))
            for i in range(len(self.derivatives)):
                x = self.derivatives[i][:,0]
                y = self.derivatives[i][:,2]
                if smooth:
                    y = savitzky_golay(y, smoothwin, smoothpol)
                c = next(color)
                self.canvas.ax.plot(x, y, color=c, linewidth=1.5)

            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
            self.canvas.ax.set_ylabel("Derivative Surface signal", fontsize=12)
            self.canvas.fig.tight_layout()
            self.canvas.draw()

        elif mode == 'Contour':
            if not(self.dataready): return
            dist = 0.46
            cmap = self.contourcmap

            V = self.contourdata[0]
            D = dist/self.contourdata[1]
            if smooth:
                Z = self.contourdata[3]
            else:
                Z = self.contourdata[2]
            
            self.canvas.ax.contourf(V,D,Z,50,cmap=cmap)

            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
            self.canvas.ax.set_ylabel("Velocity (m/s)", fontsize=12)
            self.canvas.ax.set_title("Surface Ionisation Signal", fontsize=12)

            self.canvas.draw()
            # show in imshow
            #self.canvas.ax.imshow(img, cmap = self.cmap, vmin=v[0], vmax=v[1],interpolation='spline36',filternorm=1)

        elif mode == 'Contour dSIP':
            if not(self.dataready): return
            dist = 0.46
            cmap = self.contourcmap

            V = self.contourderivative[0]
            D = dist/self.contourderivative[1]
            if smooth:
                Z = self.contourderivative[3]
            else:
                Z = self.contourderivative[2]
            
            self.canvas.ax.contourf(V,D,Z,50,cmap=cmap)

            self.canvas.ax.set_xlabel("Extraction Voltage (V)", fontsize=12)
            self.canvas.ax.set_ylabel("Velocity (m/s)", fontsize=12)
            self.canvas.ax.set_title("dSIP/dF", fontsize=12)

            self.canvas.draw()


    def calculateAllData(self, statusref, datain, bl, br, datastructure, traceselect, swin, spol):
        self.statusref = statusref
        statusref.setText('Calculating')

        # copy data over
        data = copy.deepcopy(datain)
        
        self.dataThread = DataProcessingThread(data, bl, br, datastructure[0], datastructure[1], traceselect, self.distmeshsurf, swin, spol)
        self.dataThread.dataReady.connect(self.processingFinished)
        self.dataThread.start()
        
    def processingFinished(self, traces, inttraces, derivtraces, contourdata, contourderivative):
        self.statusref.setText('Data Processed')
        self.statusref.setStyleSheet("background-color: green;")

        self.singletraces = traces
        self.integrals = inttraces
        self.derivatives = derivtraces
        self.contourdata = contourdata
        self.contourderivative = contourderivative
        self.dataready = True

        self.plotAgain.emit()

    def clearData(self):
        self.dataReady = False
        self.singletraces = []
        self.integrals = []
        self.derivatives = []
        self.contourdata = []

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
        
    def setTitle(self, text):
        self.canvas.ax.set_title(text, fontsize=12)
        self.canvas.draw()

class DataProcessingThread(QThread):
    def __init__(self, datain, bl, br, r, c, tselect, d, swin, spol):
        QThread.__init__(self)
        self.data = datain
        self.bl = bl
        self.br = br
        self.r = r
        self.c = c
        self.tselect = tselect
        self.distF = d

        if swin <= spol:
            swin = spol + 1
        if swin%2 == 0:
            swin = swin + 1
        self.swin = swin
        self.spol = spol

    dataReady = pyqtSignal(object, object, object, object, object)
    
    def __del__(self):
        self.wait()

    def run(self):

        traces = []
        # 1. baseline correct per trace
        # 2. normalise per trace
        # 3. average normalised and baseline corrected traces
        for j in range(self.c):
            # j = trace number
            
            surf = []
            field = []
            # number of traces per setting
            # choose traces from manual pre-processing
            tracecount = 0
            r = self.r
            for i in range(len(self.data)):
                if self.tselect[j][i]:
                    tracecount += 1

                    data = self.data[i]
                    ysurf = data[j*r:(j+1)*r,4]
                    yfield = data[j*r:(j+1)*r,2]
                    
                    argx1 = data[j*r:(j+1)*r,0]/self.distF
                    argx2 = data[j*r:(j+1)*r,1]
                        
                    # correct baseline shift in surface signal
                    if argx1[-1] < argx1[0]:
                        # dependent on incremental direction in scan
                        argsb = ysurf[::-1]
                    else: argsb = ysurf
                    boff = np.mean(argsb[self.bl-1:self.br])
                    ysurf -= boff

                    # normalise to maximum of field signal
                    maxF = max(savitzky_golay(yfield, 5, 3))
                    ysurf = ysurf/maxF

                surf.append(ysurf)
                field.append(yfield)
        
            # standard error of the mean
            surfavg = np.mean(np.vstack(surf), axis=0)
            surfavgerr = np.std(np.vstack(surf), axis=0)/tracecount
                
            # build list of argx2 traces
            traces.append(np.hstack((np.vstack(argx1), np.vstack(argx2), np.vstack(surfavg), np.vstack(surfavgerr))))
           
        # integrate surface profiles
        IntTraces = []
        dydx = []
        derr = []
        argx = []
        for i in range(len(traces)):
            data = traces[i]
            # trapez rule
            x = data[:,0]
            surf = data[:,2]
            err = data[:,3]
            if x[0] > x[-1]:
                x = np.flipud(x)
                surf = np.flipud(surf)
                err = np.flipud(err)

            dydx.append(np.trapz(surf, x=x))
            derr.append(np.sum(err))
            argx.append(data[:,1][0])

        IntTraces = np.hstack((np.vstack(argx), np.vstack(dydx), np.vstack(derr)))
        
        # calculate derivative
        DTraces = []
        xd = []
        for i in range(len(traces)):
            data = traces[i]
            argx1 = data[:,0]
            if argx1[0] < argx1[-1]:
                y = np.flipud(data[:,2])
            else:
                y = data[:,2]

            dy = savitzky_golay(y, self.swin, self.spol, 1)
            argx2 = data[:,1]
            DTraces.append(np.hstack((np.vstack(argx1), np.vstack(argx2), np.vstack(dy))))

            xd = np.append(xd, data[0,1])
            if i == 0:
                ZD = dy
                ZDS = savitzky_golay(dy, self.swin, self.spol)
            else:
                ZD = np.vstack((ZD, dy))
                ZDS = np.vstack((ZDS, savitzky_golay(dy, self.swin, self.spol)))

        xv = data[:,0]
        XV, XD = np.meshgrid(xv, xd)
        CDData = [XV, XD, ZD, ZDS]

        # calculate data for contour plotting of all traces
        xd = np.array([])
        for i in range(len(traces)):
            data = traces[i]
            xd = np.append(xd, data[0,1])
            if i == 0:
                Z = data[:,2]
                ZS = savitzky_golay(data[:,2], self.swin, self.spol)
            else:
                Z = np.vstack((Z, data[:,2]))
                ZS = np.vstack((ZS, savitzky_golay(data[:,2], self.swin, self.spol)))

        xv = data[:,0]
        XV, XD = np.meshgrid(xv, xd)
        CData = [XV, XD, Z, ZS]

        self.dataReady.emit(traces, IntTraces, DTraces, CData, CDData)
        self.quit()
        return
