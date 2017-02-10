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
ui_form = uic.loadUiType("grapheneevalgui2.ui")[0]

class DataEvalGui(QtGui.QMainWindow, ui_form):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.alltraceschecked = False
        self.setupUi(self)
        self.initUI()

    def initUI(self):
        # Matrix 2D tab
        self.btn_addMatrix.clicked.connect(self.addMatrixData)
        self.plotModeMatrix.currentIndexChanged.connect(self.plotMatrixRaw)
        self.chk_smoothMatrixRaw.clicked.connect(self.plotMatrixRaw)
        self.inp_smoothWinMatrixRaw.editingFinished.connect(self.plotMatrixRaw)
        self.inp_smoothPolMatrixRaw.editingFinished.connect(self.plotMatrixRaw)
        self.chk_smoothMatrix.clicked.connect(self.plotMatrixData)
        self.chk_normaliseMatrix.clicked.connect(self.plotMatrixRaw)
        self.inp_smoothWinMatrix.editingFinished.connect(self.plotMatrixData)
        self.inp_smoothPolMatrix.editingFinished.connect(self.plotMatrixData)
        self.inp_selectTraceMatrix.valueChanged.connect(self.setPriorSelection)
        self.dataModeMatrix.currentIndexChanged.connect(self.plotMatrixData)
        self.chkboxmatrix = [self.chk_matrixtrace1, self.chk_matrixtrace2, self.chk_matrixtrace3, self.chk_matrixtrace4]
        self.chk_matrixtrace1.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace2.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace3.clicked.connect(self.traceSelectionMatrix)
        self.chk_matrixtrace4.clicked.connect(self.traceSelectionMatrix)
        self.inp_matrixSetTitle.editingFinished.connect(lambda: self.MatrixGraphData.setTitle(self.inp_matrixSetTitle.text()))
        self.btn_matrixSaveFigure.clicked.connect(lambda: self.MatrixGraphData.saveFigure())
        self.chk_matrixErrorBars.clicked.connect(self.plotMatrixData)
        self.chk_comberr.clicked.connect(self.plotMatrixData)
        self.btn_traceok.clicked.connect(self.confirmTraceSelection)
        self.chk_baselineMatrix.clicked.connect(self.plotMatrixRaw)
        self.chk_baselineMatrixField.clicked.connect(self.plotMatrixRaw)
        self.inp_baselineleft.valueChanged.connect(self.baselineValueMatrixChanged)
        self.inp_baselineright.valueChanged.connect(self.baselineValueMatrixChanged)
        self.inp_fixedoffsetsurf.valueChanged.connect(self.plotMatrixRaw)
        self.chk_baselineconstsurf.clicked.connect(self.plotMatrixRaw)
        self.inp_baselineleftfield.valueChanged.connect(self.baselineValueMatrixFieldChanged)
        self.inp_baselinerightfield.valueChanged.connect(self.baselineValueMatrixFieldChanged)
        self.inp_fixedoffsetfield.valueChanged.connect(self.plotMatrixRaw)
        self.chk_baselineconstfield.clicked.connect(self.plotMatrixRaw)
        self.MatrixGraphData.plotAgain.connect(self.plotMatrixData)
        self.btn_matrixSaveData.clicked.connect(lambda: self.MatrixGraphData.saveTrace(self.dataModeMatrix.currentText()))
        self.btn_traceokall.clicked.connect(self.setAllChecked)
        self.inp_surfbias.editingFinished.connect(self.plotMatrixData)
        self.chk_peakremovesurf.clicked.connect(self.plotMatrixRaw)
        self.inp_kernelsurf.editingFinished.connect(self.plotMatrixRaw)
        self.chk_peakremovefield.clicked.connect(self.plotMatrixRaw)
        self.inp_kernelfield.editingFinished.connect(self.plotMatrixRaw)
        self.inp_integrateleft.valueChanged.connect(self.integrateValueChanged)
        self.inp_integrateright.valueChanged.connect(self.integrateValueChanged)
        self.btn_recalculate.clicked.connect(self.resetAllVelData)
        self.inp_swinDerivative.valueChanged.connect(self.derivativeValueChanged)
        self.inp_spolDerivative.valueChanged.connect(self.derivativeValueChanged)
        self.inp_derivativeindex.valueChanged.connect(self.derivativeIndexChanged)
        self.btn_saveavgtrace.clicked.connect(lambda: self.MatrixGraphData.saveAvgTrace())
                
        # defaults
        file = open('meshsurfacedistance.pckl')
        lastval = pickle.load(file)
        file.close()
        self.distmeshsurf = lastval
        self.MatrixGraphRaw.distmeshsurf = lastval
        self.MatrixGraphData.distmeshsurf = lastval
        self.out_fieldDistVel.setText('{:.2f}'.format(lastval))
        self.out_avgstatus.setText('0/0 Traces Checked')
        self.out_datastatus.setText('No Data')
        self.out_datastatus.setStyleSheet("background-color: red;")
        self.dataModeMatrix.setEnabled(False)
        self.inp_integrateleft.setEnabled(False)
        self.inp_integrateright.setEnabled(False)
        self.MatrixGraphData.allprocessed = False
        self.MatrixGraphData.clearData()
        self.MatrixGraphData.clearIntData()
        if sys.platform == 'darwin':
            self.savepath = '/Users/TPSGroup/Documents/Experimental Data/Data Mike/Raw Data/2016'
        else:
            self.savepath = 'C:\\Users\\tpsgroup\\Desktop\\Documents\\Data Mike\\Raw Data##2016'
        self.setWindowTitle('RSE Graphene Data Evaluation')
        self.setFixedSize(1170, 736)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.show()

    # Matrix Data Display
    def addMatrixData(self):
        self.alltraceschecked = False
        self.MatrixGraphRaw.clearDisplay()
        self.MatrixGraphData.clearData()
        self.MatrixGraphData.clearIntData()
        [r, c] = self.MatrixGraphRaw.addTrace()
        self.baselinematrixmax = r
        self.maxnotraces = c
        self.out_tracenum.setText(str(c))
        self.inp_selectTraceMatrix.setMaximum(c)
        self.inp_baselineright.setValue(r)
        #self.inp_baselineleft.setValue(r-5)
        #self.inp_baselinerightfield.setValue(5)
        self.inp_baselineleftfield.setValue(1)
        # set check boxes for traces
        for i in range(len(self.MatrixGraphRaw.chkboxlist)):
            self.chkboxmatrix[i].setChecked(self.MatrixGraphRaw.chkboxlist[i])
        self.out_avgstatus.setText('0/' + str(self.MatrixGraphRaw.datastructure[0][1]) + ' Traces Checked')
        self.out_avgstatus.setStyleSheet("background-color: yellow;")
        self.out_datastatus.setText('Incomplete')
        self.out_datastatus.setStyleSheet("background-color: red;")
        self.dataModeMatrix.setEnabled(False)
        self.inp_integrateleft.setEnabled(False)
        self.inp_integrateright.setEnabled(False)
        self.inp_derivativeindex.setEnabled(False)
        self.MatrixGraphData.allprocessed = False
        self.plotMatrixRaw()

    def plotMatrixRaw(self):
        self.setMatrixRawSmooth()
        self.setKernelSize()
        self.MatrixGraphRaw.plot(self.plotModeMatrix.currentText(), self.chk_normaliseMatrix.isChecked(), self.inp_selectTraceMatrix.value(), \
        self.chk_baselineMatrix.isChecked(), self.inp_baselineleft.value(), self.inp_baselineright.value(), self.inp_fixedoffsetsurf.value(), \
        self.chk_baselineMatrixField.isChecked(),  self.inp_baselineleftfield.value(), self.inp_baselinerightfield.value(), self.inp_fixedoffsetfield.value(),\
        self.chk_smoothMatrixRaw.isChecked(), self.inp_smoothWinMatrixRaw.value(), self.inp_smoothPolMatrixRaw.value(), self.chk_baselineconstsurf.isChecked(), \
        self.chk_baselineconstfield.isChecked(), self.chk_peakremovesurf.isChecked(), self.inp_kernelsurf.value(), self.chk_peakremovefield.isChecked(), \
        self.inp_kernelfield.value())
        self.plotMatrixData()
        
    def plotMatrixData(self):
        # take selected raw traces and average in other widget
        if not(len(self.MatrixGraphRaw.data)) > 0: return
        plotdata = self.MatrixGraphRaw.getPlotData()
        datastruct = self.MatrixGraphRaw.datastructure[0]
        self.setMatrixRawSmooth()
        self.setMatrixSmooth()
        self.setKernelSize()
        self.MatrixGraphData.plot(self.dataModeMatrix.currentText(), plotdata, datastruct, self.inp_selectTraceMatrix.value(), \
        self.MatrixGraphRaw.chkboxlist, self.chk_smoothMatrix.isChecked(), self.inp_smoothWinMatrix.value(), self.inp_smoothPolMatrix.value(), \
        self.chk_matrixErrorBars.isChecked(), self.chk_baselineMatrix.isChecked(), self.inp_baselineleft.value(), self.inp_baselineright.value(), \
        self.inp_fixedoffsetsurf.value(), self.inp_surfbias.value(), self.chk_baselineMatrixField.isChecked(),  self.inp_baselineleftfield.value(), \
        self.inp_baselinerightfield.value(), self.inp_fixedoffsetfield.value(), self.chk_baselineconstsurf.isChecked(), self.chk_baselineconstfield.isChecked(), \
        self.inp_smoothWinMatrixRaw.value(), self.inp_smoothPolMatrixRaw.value(), self.chk_peakremovesurf.isChecked(), self.inp_kernelsurf.value(), \
        self.chk_peakremovefield.isChecked(), self.inp_kernelfield.value(), self.alltraceschecked, self.inp_integrateleft.value(), self.inp_integrateright.value(),
        self.inp_swinDerivative.value(), self.inp_spolDerivative.value(), self.chk_comberr.isChecked(), self.chk_randy.isChecked(), self.inp_derivativeindex.value())

    def resetAllVelData(self): 
        self.MatrixGraphData.clearIntData()
        self.plotMatrixData()
    
    def setMatrixSmooth(self):
        if self.inp_smoothWinMatrix.value() <= self.inp_smoothPolMatrix.value():
            self.inp_smoothWinMatrix.setValue(self.inp_smoothPolMatrix.value()+1)
        if self.inp_smoothWinMatrix.value()%2 == 0:
            self.inp_smoothWinMatrix.setValue(self.inp_smoothWinMatrix.value()+1)
     
    def setMatrixRawSmooth(self):
        if self.inp_smoothWinMatrixRaw.value() <= self.inp_smoothPolMatrixRaw.value():
            self.inp_smoothWinMatrixRaw.setValue(self.inp_smoothPolMatrixRaw.value()+1)
        if self.inp_smoothWinMatrixRaw.value()%2 == 0:
            self.inp_smoothWinMatrixRaw.setValue(self.inp_smoothWinMatrixRaw.value()+1)
    
    def setKernelSize(self): 
        if self.inp_kernelsurf.value()%2 == 0:
            self.inp_kernelsurf.setValue(self.inp_kernelsurf.value()+1)
        if self.inp_kernelfield.value()%2 == 0:
            self.inp_kernelfield.setValue(self.inp_kernelfield.value()+1)
            
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
            
    def traceSelectionMatrix(self):
        for i in range(len(self.chkboxmatrix)):
            self.MatrixGraphRaw.chkboxlist[i] = self.chkboxmatrix[i].isChecked()
        self.plotMatrixRaw()

    def confirmTraceSelection(self):
        if not(len(self.MatrixGraphRaw.data)) > 0: return
        self.MatrixGraphRaw.traceselect[self.inp_selectTraceMatrix.value()-1] = [False, False, False, False]
        for i in range(len(self.MatrixGraphRaw.chkboxlist)):
            self.MatrixGraphRaw.traceselect[self.inp_selectTraceMatrix.value()-1][i] = self.MatrixGraphRaw.chkboxlist[i]
        if all(len(i)>0 for i in self.MatrixGraphRaw.traceselect):
            self.out_avgstatus.setText('Complete')
            self.out_avgstatus.setStyleSheet("background-color: green;")
            self.out_datastatus.setText('Data Ready')
            self.out_datastatus.setStyleSheet("background-color: green;")
            self.alltraceschecked = True
            self.dataModeMatrix.setEnabled(True)
            self.inp_integrateleft.setEnabled(True)
            self.inp_integrateright.setEnabled(True)
            self.inp_derivativeindex.setEnabled(True)
            self.inp_integrateright.setValue(self.MatrixGraphData.integratexmax)
            self.inp_derivativeindex.setValue(self.MatrixGraphData.integratexmax)
            self.plotMatrixData()
        else:
            self.out_avgstatus.setText(str(len(filter(None, self.MatrixGraphRaw.traceselect))) + '/' + str(self.MatrixGraphRaw.datastructure[0][1]) + ' Traces Checked')
            
    def setAllChecked(self):
        for i in range(len(self.MatrixGraphRaw.traceselect)):
            self.MatrixGraphRaw.traceselect[i] = [True]*len(self.MatrixGraphRaw.data)    
        self.out_avgstatus.setText('Complete')
        self.out_avgstatus.setStyleSheet("background-color: green;")
        self.out_datastatus.setText('Data Ready')
        self.out_datastatus.setStyleSheet("background-color: green;")
        self.alltraceschecked = True
        self.dataModeMatrix.setEnabled(True)
        self.inp_integrateleft.setEnabled(True)
        self.inp_integrateright.setEnabled(True)
        self.inp_derivativeindex.setEnabled(True)
        self.inp_integrateright.setValue(self.MatrixGraphData.integratexmax)
        self.inp_derivativeindex.setValue(self.MatrixGraphData.integratexmax)
        self.plotMatrixData()
            
    def baselineValueMatrixChanged(self):
        if not(self.inp_baselineleft.hasFocus()) and not(self.inp_baselineright.hasFocus()): return
        if self.inp_baselineright.value() > self.baselinematrixmax:
            self.inp_baselineright.setValue(self.baselinematrixmax)
            return
        if self.inp_baselineleft.value() >= self.inp_baselineright.value():
            self.inp_baselineleft.setValue(self.inp_baselineright.value()-1)
        self.plotMatrixRaw()

    def baselineValueMatrixFieldChanged(self):
        if not(self.inp_baselineleftfield.hasFocus()) and not(self.inp_baselinerightfield.hasFocus()): return
        if self.inp_baselinerightfield.value() > self.baselinematrixmax:
            self.inp_baselinerightfield.setValue(self.baselinematrixmax)
            return
        if self.inp_baselineleftfield.value() >= self.inp_baselinerightfield.value():
            self.inp_baselineleftfield.setValue(self.inp_baselinerightfield.value()-1)
        self.plotMatrixRaw()
        
    def integrateValueChanged(self):
        if not(self.inp_integrateleft.hasFocus()) and not(self.inp_integrateright.hasFocus()): return
        if self.inp_integrateright.value() > self.MatrixGraphData.integratexmax:
            self.inp_integrateright.setValue(self.MatrixGraphData.integratexmax)
            return
        if self.inp_integrateleft.value() >= self.inp_integrateright.value():
            self.inp_integrateleft.setValue(self.inp_integrateright.value()-1)
        self.plotMatrixData()
            
    def derivativeValueChanged(self):
        if self.inp_swinDerivative.value() <= self.inp_spolDerivative.value():
            self.inp_swinDerivative.value().setValue(self.inp_spolDerivative+1)
        if self.inp_swinDerivative.value()%2 == 0:
            self.inp_swinDerivative.setValue(self.inp_swinDerivative.value()+1)
            
    def derivativeIndexChanged(self):
        if self.inp_derivativeindex.value() > self.MatrixGraphData.integratexmax:
            self.inp_derivativeindex.setValue(self.MatrixGraphData.integratexmax)
        self.plotMatrixData()
            
    def shutDownGui(self):
        self.blockSignals(True)


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    myapp = DataEvalGui()
    app.exec_()
