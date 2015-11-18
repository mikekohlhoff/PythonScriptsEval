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
        self.btn_defaultRydSeries.clicked.connect(lambda: self.RydSeriesGraph.plotWLScan(self.inp_laserOffset.value()))
        self.chk_defaultSet.clicked.connect(lambda: self.RydSeriesGraph.defaultSet(self.chk_defaultSet.isChecked()))
        # plot WL scan from file
        self.RydSeriesGraph.plotWLScan(self.inp_laserOffset.value())

        # Stark Scan Display
        self.btn_addTraceWL.clicked.connect(self.addTraceStark)
        self.btn_clearWL.clicked.connect(self.WLScanGraph.clearDisplay)
        self.btn_saveDistance.clicked.connect(self.saveDistance)
        self.chk_smoothStark.clicked.connect(self.setWLSmooth)
        self.chk_normaliseStark.clicked.connect(self.setStarkManifold)
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
        self.btn_singleTracesSaveFig.clicked.connect(self.SingleTracesGraph.saveFigure)
        
        # Avg Trace Display
        self.btn_avgTraceSave.clicked.connect(lambda: self.AvgTraceGraph.saveTrace(self.scanModeSelect.currentText()))
        self.btn_avgTraceSaveFig.clicked.connect(self.AvgTraceGraph.saveFigure)
        self.inp_avgTraceSetTitle.editingFinished.connect(lambda: self.AvgTraceGraph.setTitle(self.inp_avgTraceSetTitle.text()))
        self.inp_avgTraceSetTitle.setText('Set Title of Average Traces')

        # Matrix 2D tab
        self.btn_addMatrix.clicked.connect(self.addMatrixData)
        self.plotModeMatrix.currentIndexChanged.connect(self.plotMatrixRaw)
        self.chk_smoothMatrix.clicked.connect(self.setMatrixSmooth)
        self.chk_normaliseMatrix.clicked.connect(self.plotMatrixRaw)
        self.inp_smoothWinMatrix.editingFinished.connect(self.setMatrixSmooth)
        self.inp_smoothPolMatrix.editingFinished.connect(self.setMatrixSmooth)
        self.inp_selectTraceMatrix.valueChanged.connect(self.setPriorSelection)
        self.dataModeMatrix.currentIndexChanged.connect(self.plotMatrixData)
        self.chkboxmatrix = [self.chk_matrixtrace1, self.chk_matrixtrace2, self.chk_matrixtrace3, \
                           self.chk_matrixtrace4, self.chk_matrixtrace5, self.chk_matrixtrace6]
        self.chk_matrixtrace1.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace2.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace3.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace4.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace5.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace6.clicked.connect(self.traceSelectionMatrix)
        self.inp_matrixSetTitle.editingFinished.connect(lambda: self.MatrixGraphData.setTitle(self.inp_matrixSetTitle.text()))
        self.btn_matrixSaveFigure.clicked.connect(lambda: self.MatrixGraphData.saveFigure())
        self.chk_matrixErrorBars.clicked.connect(self.plotMatrixData)
        self.btn_traceok.clicked.connect(self.confirmTraceSelection)
        self.chk_baselineMatrix.clicked.connect(self.plotMatrixRaw)
        self.inp_baselineleft.valueChanged.connect(self.baselineValueMatrixChanged)
        self.inp_baselineright.valueChanged.connect(self.baselineValueMatrixChanged)
        self.btn_matrixCalculate.clicked.connect(self.calculateMatrixData)
        self.MatrixGraphData.plotAgain.connect(self.plotMatrixData)

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
        self.MatrixGraphRaw.distmeshsurf = lastval
        self.MatrixGraphData.distmeshsurf = lastval
        self.inp_dSurfMesh.setValue(lastval)
        self.out_fieldDist.setText(str(lastval))
        self.out_fieldDistVel.setText(str(lastval))
        self.textWLDiff.setText('dWL to zero field: \n -0.0265nm')
        self.inp_laserOffset.setValue(-0.2)
        self.out_datastatus.setText('No Data Processed')
        self.out_datastatus.setStyleSheet("background-color: red;")
        if sys.platform == 'darwin':
            self.savepath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2015'
        else:
            self.savepath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data\\2015'
        self.setWindowTitle('RSE Data Evaluation')
        self.setFixedSize(1006, 644)
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
            self.tabWidget_Modi.setCurrentIndex(3)

    # Matrix Data Display
    def addMatrixData(self):
        self.MatrixGraphRaw.clearDisplay()
        self.MatrixGraphData.clearData()
        [r, c] = self.MatrixGraphRaw.addTrace()
        self.baselinematrixmax = r
        self.maxnotraces = c
        self.out_tracenum.setText(str(c))
        self.inp_selectTraceMatrix.setMaximum(c)
        self.inp_baselineright.setValue(r)
        self.inp_baselineleft.setValue(r-5)
        # set check boxes for traces
        for i in range(len(self.MatrixGraphRaw.chkboxlist)):
            self.chkboxmatrix[i].setChecked(self.MatrixGraphRaw.chkboxlist[i])
        self.out_avgstatus.setText('Incomplete')
        self.out_avgstatus.setStyleSheet("background-color: red;")
        self.out_datastatus.setText('No Data Processed')
        self.out_datastatus.setStyleSheet("background-color: red;")
        self.plotMatrixRaw()

    def setPriorSelection(self):
        chkconf = self.MatrixGraphRaw.traceselect[self.inp_selectTraceMatrix.value()-1]
        # set trace selection if previous chosen
        if len(chkconf) > 0:
            for i in range(len(chkconf)):
                self.chkboxmatrix[i].setChecked(chkconf[i])
                self.MatrixGraphRaw.chkboxlist[i] = chkconf[i]
        else:
            for i in range(len(self.MatrixGraphRaw.data)):
                self.chkboxmatrix[i].setChecked(True)
        self.traceSelectionMatrix()

    def plotMatrixRaw(self):
        self.MatrixGraphRaw.plot(self.plotModeMatrix.currentText(), self.chk_normaliseMatrix.isChecked(), \
        self.inp_selectTraceMatrix.value(), self.chk_baselineMatrix.isChecked(), self.inp_baselineleft.value(), self.inp_baselineright.value())
        self.plotMatrixData()

    def plotMatrixData(self):
        if not(len(self.MatrixGraphRaw.data)) > 0: return
        plotdata = self.MatrixGraphRaw.getPlotData()
        datastruct = self.MatrixGraphRaw.datastructure[0]
        self.MatrixGraphData.plot(self.dataModeMatrix.currentText(), plotdata, datastruct, self.inp_selectTraceMatrix.value(), \
        self.MatrixGraphRaw.chkboxlist, self.chk_smoothMatrix.isChecked(), self.inp_smoothWinMatrix.value(), self.inp_smoothPolMatrix.value(), \
        self.chk_normaliseMatrix.isChecked(), self.plotModeMatrix.currentText(), self.chk_matrixErrorBars.isChecked(), \
        self.chk_baselineMatrix.isChecked(), self.inp_baselineleft.value(), self.inp_baselineright.value())
        
    def calculateMatrixData(self):
        if not(all(len(i)>0 for i in self.MatrixGraphRaw.traceselect)):
            QtGui.QMessageBox.warning(self, 'Data Processing Error', "Averaging of traces not complete.", QtGui.QMessageBox.Ok)
            return
        self.MatrixGraphData.calculateAllData(self.out_datastatus, self.MatrixGraphRaw.data, self.inp_baselineleft.value(), \
        self.inp_baselineright.value(), self.MatrixGraphRaw.datastructure[0], self.MatrixGraphRaw.traceselect, \
        self.inp_swinDerivative.value(), self.inp_spolDerivative.value())

    def setMatrixSmooth(self):
        if self.inp_smoothWinMatrix.value() <= self.inp_smoothPolMatrix.value():
            self.inp_smoothWinMatrix.setValue(self.inp_smoothPolMatrix.value()+1)
        if self.inp_smoothWinMatrix.value()%2 == 0:
            self.inp_smoothWinMatrix.setValue(self.inp_smoothWinMatrix.value()+1)
        self.plotMatrixData()
     
    def traceSelectionMatrix(self):
        for i in range(len(self.chkboxmatrix)):
            self.MatrixGraphRaw.chkboxlist[i] = self.chkboxmatrix[i].isChecked()
        self.plotMatrixRaw()

    def confirmTraceSelection(self):
        if not(len(self.MatrixGraphRaw.data)) > 0: return
        self.MatrixGraphRaw.traceselect[self.inp_selectTraceMatrix.value()-1] = [False, False, False, False, False, False]
        for i in range(len(self.MatrixGraphRaw.chkboxlist)):
            self.MatrixGraphRaw.traceselect[self.inp_selectTraceMatrix.value()-1][i] = self.MatrixGraphRaw.chkboxlist[i]
        if all(len(i)>0 for i in self.MatrixGraphRaw.traceselect):
            self.out_avgstatus.setText('Complete')
            self.out_avgstatus.setStyleSheet("background-color: green;")
            self.out_datastatus.setText('Data Ready')
            self.out_datastatus.setStyleSheet("background-color: yellow;")

    def baselineValueMatrixChanged(self):
        if not(self.inp_baselineleft.hasFocus()) and not(self.inp_baselineright.hasFocus()): return
        if self.inp_baselineright.value() > self.baselinematrixmax:
            self.inp_baselineright.setValue(self.baselinematrixmax)
            return
        if self.inp_baselineleft.value() >= self.inp_baselineright.value():
            self.inp_baselineleft.setValue(self.inp_baselineright.value()-1)
        self.plotMatrixRaw()

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
        self.inp_wlSmoothPol.value(), self.chk_normaliseStark.isChecked())

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
