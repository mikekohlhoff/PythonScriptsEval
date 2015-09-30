# -*- coding: utf-8 -*-
'''
Handle data evaluation exported from RSE/RSD gui
''' 

import time
from datetime import datetime
import os
import sys
import pickle
import math

# UI related
from PyQt4 import QtCore, QtGui, uic
ui_form = uic.loadUiType("dataevalgui.ui")[0]



class DataEvalGui(QtGui.QMainWindow, ui_form):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        # Rydberg Series display
        self.inp_laserOffset.valueChanged.connect(lambda: self.RydSeriesGraph.plotRydSeries(self.inp_laserOffset.value()))
        self.btn_clearRydSeries.clicked.connect(self.RydSeriesGraph.clearDisplay)
        self.RydSeriesGraph.pickedValReady.connect(self.updatePickedDisplayRydSeries)
        self.btn_addTraceRydSeries.clicked.connect(self.RydSeriesGraph.addTrace)
        # plot WL scan from file
        self.RydSeriesGraph.plotWLScan(self.inp_laserOffset.value())

        # Stark Scan Display
        self.btn_addTraceWL.clicked.connect(self.addTraceStark)
        self.btn_clearWL.clicked.connect(self.WLScanGraph.clearDisplay)
        self.btn_saveDistance.clicked.connect(self.saveDistance)
        self.chk_smoothStark.clicked.connect(self.setWLSmooth)
        self.inp_wlSmoothWin.editingFinished.connect(self.setWLSmooth)
        self.inp_wlSmoothPol.editingFinished.connect(self.setWLSmooth)
        self.inp_PQN.editingFinished.connect(self.setStarkManifold)
        self.chk_switchTrace.clicked.connect(self.setStarkManifold)
        self.inp_dSurfMesh.valueChanged.connect(self.setStarkManifold)
        self.inp_starkField.valueChanged.connect(self.setStarkManifold)
        self.inp_laserOffsetSplitting.valueChanged.connect(self.setStarkManifold)
        self.chk_displayml02j32.clicked.connect(self.setStarkManifold)
        self.chk_displayml1j32.clicked.connect(self.setStarkManifold)
        self.chk_displayml02j12.clicked.connect(self.setStarkManifold)
        self.chk_displayml1j12.clicked.connect(self.setStarkManifold)
        self.WLScanGraph.pickedValReady.connect(self.updatePickedDisplayStarkScan)
        self.chk_legendStark.clicked.connect(lambda: self.WLScanGraph.setLegend(self.chk_legendStark.isChecked()))

        # Single Traces Display
        self.btn_addSingleTraces.clicked.connect(lambda: self.chk_dispSingleTracesNormalise.setChecked(False))
        self.btn_addSingleTraces.clicked.connect(lambda: self.SingleTracesGraph.addTrace(self.scanModeSelect.currentText(),
        self.chk_dispSingleTracesNormalise.isChecked()))
        self.btn_addSingleTraces.clicked.connect(lambda: self.inp_avgTraceSetTitle.setText(''))
        self.btn_clearSingleTraces.clicked.connect(self.resetTraceChkboxes)
        self.btn_clearSingleTraces.clicked.connect(lambda: self.out_inpTraces.setText(''))
        self.SingleTracesGraph.loadedfile.connect(self.displayFileNames)
        self.chkboxrefs = [self.chk_dispSingleTrace1, self.chk_dispSingleTrace2, self.chk_dispSingleTrace3, \
                           self.chk_dispSingleTrace4, self.chk_dispSingleTrace5, self.chk_dispSingleTrace6]
        self.chk_dispSingleTrace1.clicked.connect(self.traceSelectionChanged)
        self.chk_dispSingleTrace2.clicked.connect(self.traceSelectionChanged)
        self.chk_dispSingleTrace3.clicked.connect(self.traceSelectionChanged)
        self.chk_dispSingleTrace4.clicked.connect(self.traceSelectionChanged)
        self.chk_dispSingleTrace5.clicked.connect(self.traceSelectionChanged)
        self.chk_dispSingleTrace6.clicked.connect(self.traceSelectionChanged)
        self.btn_addSingleTraces.clicked.connect(lambda: self.AvgTraceGraph.plotAvgTrace(self.scanModeSelect.currentText(),
                                                self.SingleTracesGraph.datafiles, self.SingleTracesGraph.chkboxlist))
        self.chk_dispSingleTracesNormalise.clicked.connect(self.plotNormTrace)
        self.btn_updateDistance.clicked.connect(self.updateDistance)

        # Avg Trace Display
        self.btn_avgTraceSave.clicked.connect(lambda: self.AvgTraceGraph.saveTrace(self.scanModeSelect.currentText()))
        self.btn_avgTraceSaveFig.clicked.connect(self.AvgTraceGraph.saveFigure)
        self.inp_avgTraceSetTitle.editingFinished.connect(lambda: self.AvgTraceGraph.setTitle(self.inp_avgTraceSetTitle.text()))
        self.inp_avgTraceSetTitle.setText('Set Title of Average Traces')

        # Overview Display
        self.btn_avgTraceSend.clicked.connect(self.sendTrace)
        self.inp_overviewSetTitle.editingFinished.connect(lambda: self.OverviewGraph.setTitle(self.inp_overviewSetTitle.text()))
        self.inp_overviewSetAxisTitle.editingFinished.connect(lambda: self.OverviewGraph.setAxisTitle(self.inp_overviewSetAxisTitle.text()))
        self.scanModeSelectOverview.currentIndexChanged.connect(lambda: self.OverviewGraph.setScanMode(self.scanModeSelectOverview.currentText()))
        self.plotModeSelectOverview.currentIndexChanged.connect(lambda: self.OverviewGraph.setPlotMode(self.plotModeSelectOverview.currentText()))
        self.chk_overviewSmooth.clicked.connect(self.setOverviewSmooth)
        self.inp_overviewSmoothWin.editingFinished.connect(self.setOverviewSmooth)
        self.inp_overviewSmoothPol.editingFinished.connect(self.setOverviewSmooth)
        self.btn_clearOverview.clicked.connect(self.OverviewGraph.clearDisplay)
        self.chk_setLegendOverview.clicked.connect(lambda: self.OverviewGraph.setLegend(self.chk_setLegendOverview.isChecked()))
        self.chk_normaliseOverview.clicked.connect(lambda: self.OverviewGraph.normaliseParamChanged(self.chk_normaliseOverview.isChecked()))
        self.btn_addOverview.clicked.connect(self.OverviewGraph.addTrace)
        self.btn_overviewSaveTrace.clicked.connect(self.OverviewGraph.saveTrace)
        self.btn_overviewSaveFigure.clicked.connect(self.OverviewGraph.saveFigure)

        # defaults
        file = open('meshsurfacedistance.pckl')
        lastval = pickle.load(file)
        file.close()
        self.distmeshsurf = lastval
        self.WLScanGraph.distmeshsurf = lastval
        self.SingleTracesGraph.distmeshsurf = lastval
        self.inp_dSurfMesh.setValue(lastval)
        self.out_fieldDist.setText(str(lastval))
        if sys.platform == 'darwin':
            self.savepath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.savepath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'
        self.setWindowTitle('RSE Data Evaluation')
        self.setFixedSize(992, 596)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.show()

    # Rydberg Series Display
    def updatePickedDisplayRydSeries(self, val):
        self.out_pickedWL.setText('{:3.5f}'.format(val))

    # Single Traces Display
    def traceSelectionChanged(self):
        if len(self.SingleTracesGraph.dataheader) < 1: return
        for i in range(len(self.SingleTracesGraph.chkboxlist)):
            self.SingleTracesGraph.chkboxlist[i] = self.chkboxrefs[i].isChecked()
        self.SingleTracesGraph.toggleVisibility()
        self.AvgTraceGraph.plotAvgTrace(self.scanModeSelect.currentText(), self.SingleTracesGraph.datafiles, self.SingleTracesGraph.chkboxlist)
    
    def plotNormTrace(self):
        self.SingleTracesGraph.plotTraces(self.scanModeSelect.currentText(), self.chk_dispSingleTracesNormalise.isChecked())
        self.SingleTracesGraph.toggleVisibility()

    def resetTraceChkboxes(self):
        for i in range(len(self.SingleTracesGraph.chkboxlist)):
            self.SingleTracesGraph.chkboxlist[i] = False
            self.chkboxrefs[i].setChecked(False)
        self.SingleTracesGraph.clearDisplay()

    def displayFileNames(self, filelist, chkboxlist):
        filenames = ''
        for i in range(len(filelist)):
            filenames = filenames + str(i+1) + ': ' + filelist[i] + '\n'
        self.out_inpTraces.setText(filenames)
        # set check boxes for traces
        for i in range(len(chkboxlist)):
            self.chkboxrefs[i].setChecked(chkboxlist[i])
    
    def updateDistance(self):
        file = open('meshsurfacedistance.pckl')
        lastval = pickle.load(file)
        file.close()
        self.distmeshsurf = lastval
        self.WLScanGraph.distmeshsurf = lastval
        self.out_fieldDist.setText(str(lastval))

    # Avg Trace Display
    def sendTrace(self):
        if hasattr(self.AvgTraceGraph, 'savedata'):
            if self.inp_avgTraceSetTitle.text() == '':
                tracename, ok = QtGui.QInputDialog.getText(self, 'Input Dialog', 'Enter trace name:')
                if ok:
                    self.inp_avgTraceSetTitle.setText(str(tracename))
                else: return
            self.OverviewGraph.receiveTrace(self.AvgTraceGraph.savedata, self.inp_avgTraceSetTitle.text())
            time.sleep(0.28)
            self.tabWidget_Modi.setCurrentIndex(2)

    # Overview Graph
    def setOverviewSmooth(self):
        if self.inp_overviewSmoothWin.value() <= self.inp_overviewSmoothPol.value():
            self.inp_overviewSmoothWin.setValue(self.inp_overviewSmoothPol.value()+1)
        if self.inp_overviewSmoothWin.value()%2 == 0:
            self.inp_overviewSmoothWin.setValue(self.inp_overviewSmoothWin.value()+1)
        self.OverviewGraph.smoothParamChanged(self.chk_overviewSmooth.isChecked(), self.inp_overviewSmoothWin.value(),
        self.inp_overviewSmoothPol.value())

    # Stark Scan graph
    def addTraceStark(self):
        self.WLScanGraph.addTrace()
        self.setStarkManifold()

    def setWLSmooth(self):
        if self.inp_wlSmoothWin.value() <= self.inp_wlSmoothPol.value():
            self.inp_wlSmoothWin.setValue(self.inp_wlSmoothPol.value()+1)
        if self.inp_wlSmoothWin.value()%2 == 0:
            self.inp_wlSmoothWin.setValue(self.inp_wlSmoothWin.value()+1)
        self.setStarkManifold()

    def setStarkManifold(self):
        self.WLScanGraph.plotSpectrum(self.inp_PQN.value(), self.chk_displayml02j32.isChecked(), self.chk_displayml1j32.isChecked(), \
        self.chk_displayml02j12.isChecked(), self.chk_displayml1j12.isChecked(), self.chk_switchTrace.isChecked(), self.inp_dSurfMesh.value(), \
        self.inp_starkField.value(), self.inp_laserOffsetSplitting.value(), self.chk_smoothStark.isChecked(), self.inp_wlSmoothWin.value(), \
        self.inp_wlSmoothPol.value())

    def updatePickedDisplayStarkScan(self, val):
        self.out_pickedStarkScan.setText('{:3.5f}'.format(val))

    def saveDistance(self):
        file = open('MeshSurfaceDistance.pckl', 'w')
        pickle.dump(self.WLScanGraph.distmeshsurf, file)
        file.close()
     
    def shutDownGui(self):
        self.blockSignals(True)

if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    myapp = DataEvalGui()
    app.exec_()
