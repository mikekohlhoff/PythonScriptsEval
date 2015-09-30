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

class MatplotlibWidgetWL(QGraphicsView):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)
        self.canvas.ax.set_title('Series of Averages', fontsize=12)
        self.canvas.fig.patch.set_alpha(0)
        self.canvas.fig.tight_layout()
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.mpl_toolbar.pan()
        params = {
                  'legend.fontsize': 12,
                  'xtick.labelsize': 12,
                  'ytick.labelsize': 12,
                  'legend.handletextpad': .5,
                  'figure.autolayout': True,
                }
        plt.rcParams.update(params)
        self.data = []
        self.distmeshsurf = 1.
        self.setlegend = False
        if sys.platform == 'darwin':
            self.filePath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.filePath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'

    pickedValReady = pyqtSignal(object)
    
    def onclick(self, event):
        if event.button == 3:
            self.pickedValReady.emit(event.xdata)

    def addTrace(self):
        # average traces saved as (paramter, surface, surface err, field, field err)
        datapath = QFileDialog.getOpenFileNames(self, 'Select Avgerage Trace File', self.filePath, '(*.txt)')
        if not datapath: return
        for i in range(len(datapath)):
            self.data = loadtxt(str(datapath[i]), skiprows=2)
        self.filePath = os.path.dirname(str(datapath[0]))

    def kRange(self, n, ml):
        '''Stark states in parabolic quantum number k(n_1-n_2), {k}=-(n-|m_l|-1)...(n-|m_l|-1),
        (n-|m_l|) elements, elements the same for m_l=0, +/-2 where maxkmax states have pure m_l=0
        character, these two states are 'missing' at the edge of the manifold for m_l=+/-2'''
        kRange = [i for i in range(-(n-abs(ml)-1),(n-abs(ml)),2)]
        return kRange

    def StarkEnergy(self, n, ml, k, F):
        # Hartree in wavenumbers, Rydberg constant in cm^-1
        # Rydberg constant for Hydrogen != R_inf
        rh = 109677.583 
        hartree = 2*rh
        Eau = (-(1./(2*n**2)) + 1.5*n*k*F - (n**4)/16.0*(17*n**2 - 3*k**2 - 9*ml**2 + 19)*F**2 + \
              3/32*n**7*k*(23*n**2 - k**2 + 11*ml**2 + 39)*F**3 - \
              (n**10)/1024.0*(5487*n**4 + 35182*n**2 - 1134*ml**2*k**2 + \
              1806*n**2*k**2 - 3402*n**2*ml**2 - 3093*k**4 - 549*ml**4 + \
              5754*k**2 - 8622*ml**2 + 16211)*F**4)*hartree
        return Eau

    def plotSpectrum(self, n, ml02j32flag, ml1j32flag, ml02j12flag, ml1j12flag, trace, d, volt, offset, smooth, smoothwin, smoothpol):
        if len(self.data) < 1: return
        # get curent xy limits
        xlim1, xlim2 = self.canvas.ax.get_xlim()
        ylim1, ylim2 = self.canvas.ax.get_ylim()
        self.canvas.ax.clear()
        self.distmeshsurf = d
        # build Stark manifold from expansion for energies in E-field
        # from http://physics.nist.gov/asd
        Lalphaj32 = -82259.2850014 #121.5668237310
        Lalphaj12 =  -82258.919113 #121.5673644609
        rh = 109677.583
        c = 299792458
        # in eV
        h = 4.135667662E-15
        # Electric field in V/cm to atomic units E_h/ea_0.
        #http://physics.nist.gov/cgi-bin/cuu/Value?auefld 
        Fau = (100*volt/(5.142206E11))/d
        # energies converted to nm
        # account for fine splitting due to spin-orbit coupling
        # if not, from expansion: en = (2*10**7)/(self.StarkEnergy(n, 2, k, Fau) - self.StarkEnergy(2, 0, 1, Fau)) + offset
        kml02 = self.kRange(n, 0)
        kml1 = self.kRange(n, 1)
        if ml02j32flag:
            ml02j32 = [0]*len(kml02)
            for i in range(len(kml02)):
                ml02j32[i] = (2*10**7)/(self.StarkEnergy(n, 2, kml02[i], Fau) - (-rh-Lalphaj32)) + offset
        if ml1j32flag:
            ml1j32 = [0]*len(kml1)
            for i in range(len(kml1)):
                ml1j32[i] = (2*10**7)/(self.StarkEnergy(n, 1, kml1[i], Fau) - (-rh-Lalphaj32)) + offset
        if ml02j12flag:
            ml02j12 = [0]*len(kml02)
            for i in range(len(kml02)):
                ml02j12[i] = (2*10**7)/(self.StarkEnergy(n, 2, kml02[i], Fau) -  (-rh-Lalphaj12)) + offset
        if ml1j12flag:
            ml1j12 = [0]*len(kml1)
            for i in range(len(kml1)):
                ml1j12[i] = (2*10**7)/(self.StarkEnergy(n, 1, kml1[i], Fau) -  (-rh-Lalphaj12)) + offset

        if trace:
            argy = self.data[:,3]/max(self.data[:,3])
        else:
            argy = self.data[:,1]/max(self.data[:,1])
        if smooth:
            argx = savitzky_golay(self.data[:,0], smoothwin, smoothpol)
            argy = savitzky_golay(argy, smoothwin, smoothpol)
        else:
            argx = self.data[:,0]

        self.canvas.ax.plot(argx, argy, color='k', linewidth=1.5) 

        if ml02j32flag:
            xx = [ml02j32, ml02j32]
            yy = [[-0.02]*len(ml02j32), [1.02]*len(ml02j32)]
            self.canvas.ax.plot(xx,yy, 'b', linewidth=1.2)
            for i in range(len(ml02j32)):
                self.canvas.ax.text(ml02j32[i], 1.06, str(kml02[i]), horizontalalignment='center', \
                verticalalignment='center',color='b',fontsize=8)
        if ml1j32flag:
            xx = [ml1j32, ml1j32]
            yy = [[-0.02]*len(ml1j32), [1.02]*len(ml1j32)]
            self.canvas.ax.plot(xx,yy, 'b--', linewidth=1.2)
            for i in range(len(ml1j32)):
                self.canvas.ax.text(ml1j32[i], 1.06, str(kml1[i]), horizontalalignment='center', \
                verticalalignment='center',color='b',fontsize=8)
        if ml02j12flag:
            xx = [ml02j12, ml02j12]
            yy = [[-0.02]*len(ml02j12), [1.02]*len(ml02j12)]
            self.canvas.ax.plot(xx,yy, 'r', linewidth=1.2)
            for i in range(len(ml02j12)):
                self.canvas.ax.text(ml02j12[i], 1.06, str(kml02[i]), horizontalalignment='center', \
                verticalalignment='center',color='r',fontsize=8)
        if ml1j12flag:
            xx = [ml1j12, ml1j12]
            yy = [[-0.02]*len(ml1j12), [1.02]*len(ml1j12)]
            self.canvas.ax.plot(xx,yy, 'r--', linewidth=1.2)
            for i in range(len(ml1j12)):
                self.canvas.ax.text(ml1j12[i], 1.06, str(kml1[i]), horizontalalignment='center', \
                verticalalignment='center',color='r',fontsize=8)

        if self.setlegend:
            self.legendobj = self.canvas.ax.legend(['ml=2', 'ml=1', 'ml=0'],loc="upper left",  bbox_to_anchor = [.02,0.98], fontsize=12)
        self.setLegend(self.setlegend)
        self.canvas.ax.set_xlabel("Fundamental Wavelength (nm)")
        self.canvas.ax.set_title('Stark Manifold for n= ' + str(n), fontsize=12)
        if xlim1 == 0.0 and xlim2 == 1.0:
            xlim1 = min(argx)
            xlim2 = max(argx)
            ylim1 = 0
            ylim2 = 1.1
        self.canvas.ax.set_ylim(ymin=ylim1, ymax=ylim2)
        self.canvas.ax.set_xlim(xmin=xlim1, xmax=xlim2)
        self.canvas.draw()

    def setLegend(self, setlegend):
        self.setlegend = setlegend
        if hasattr(self, 'legendobj'):
            self.legendobj.set_visible(self.setlegend)
            self.canvas.draw()
     
    def clearDisplay(self):
        self.canvas.ax.clear()
        self.canvas.ax.set_title("", fontsize=12)
        self.data = []
        self.canvas.draw()
