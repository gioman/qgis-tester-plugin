# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from PyQt4 import uic, QtGui, QtCore
from report import *
import traceback
import sys
from qgistester.reportdialog import ReportDialog
from utils import execute

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), 'testerwidget.ui'))

class TesterWidget(BASE, WIDGET):

    def __init__(self, toolbar):
        QtGui.QWidget.__init__(self)
        self.setupUi(self)

        self.toolbar = toolbar

        self.btnCancel.clicked.connect(self.cancelTesting)
        self.btnTestOk.clicked.connect(self.testPasses)
        self.btnTestFailed.clicked.connect(self.testFails)
        self.btnSkip.clicked.connect(self.skipTest)
        self.btnNextStep.clicked.connect(self.runNextStep)

    def setTests(self, tests):
        self.tests = tests
        for t in tests:
            item = QtGui.QListWidgetItem("%s: %s" % (t.group.upper(), t.name))
            self.listTests.addItem(item)

    currentTestResult = None
    currentTest = 0;
    def startTesting(self):
        self.currentTest = 0
        self.report = Report()
        for i, test in enumerate(self.tests):
            item = self.listTests.item(i)
            item.setForeground(QtCore.Qt.black)
            item.setBackground(QtCore.Qt.white)

        self.runNextTest()

    currentTestStep = 0
    def runNextTest(self):
        if self.currentTestResult:
            self.report.addTestResult(self.currentTestResult)
        if self.currentTest < len(self.tests):
            self.listTests.scrollToItem(self.listTests.item(self.currentTest),
                                        QtGui.QAbstractItemView.EnsureVisible)
            self.currentTestResult = TestResult(self.tests[self.currentTest])
            item = self.listTests.item(self.currentTest)
            item.setBackground(QtCore.Qt.cyan)
            self.currentTestStep = 0
            self.runNextStep()
        else:
            self.toolbar.setVisible(False)
            dlg = ReportDialog(self.report)
            dlg.exec_()

    def runNextStep(self):
        test = self.tests[self.currentTest]
        desc, function, isVerifyStep = test.steps[self.currentTestStep]
        self.btnSkip.setEnabled(True)
        self.btnCancel.setEnabled(True)
        if os.path.exists(desc):
            with open(desc) as f:
                html = "".join(f.readlines())
            self.webView.setHtml(html, QtCore.QUrl.fromUserInput(desc))
        else:
            self.webView.setHtml(desc)
        QtCore.QCoreApplication.processEvents()
        if self.currentTestStep == len(test.steps) - 1:
            if function is not None:
                self.btnTestOk.setEnabled(False)
                self.btnTestFailed.setEnabled(False)
                self.btnNextStep.setEnabled(False)
                self.btnSkip.setEnabled(False)
                self.btnCancel.setEnabled(False)
                self.webView.setEnabled(False)
                QtCore.QCoreApplication.processEvents()
                try:
                    execute(function)
                    self.testPasses()
                except:
                    self.testFails(traceback.format_exc())
            else:
                self.btnTestOk.setEnabled(True)
                self.btnTestOk.setText("Test passes")
                self.btnTestFailed.setEnabled(True)
                self.btnTestFailed.setText("Test fails")
                self.webView.setEnabled(True)
                self.btnNextStep.setEnabled(False)
        else:
            if function is not None:
                self.btnTestOk.setEnabled(False)
                self.btnTestFailed.setEnabled(False)
                self.btnNextStep.setEnabled(False)
                self.btnSkip.setEnabled(False)
                self.btnCancel.setEnabled(False)
                self.webView.setEnabled(False)
                QtCore.QCoreApplication.processEvents()
                try:
                    execute(function)
                    self.currentTestStep += 1
                    self.runNextStep()
                except:
                    self.testFails(traceback.format_exc())
            else:
                self.currentTestStep += 1
                self.webView.setEnabled(True)
                self.btnNextStep.setEnabled(not isVerifyStep)
                if isVerifyStep:
                    self.btnTestOk.setEnabled(True)
                    self.btnTestOk.setText("Step passes")
                    self.btnTestFailed.setEnabled(True)
                    self.btnTestFailed.setText("Step fails")
                else:
                    self.btnTestOk.setEnabled(False)
                    self.btnTestFailed.setEnabled(False)

    def testPasses(self):
        test = self.tests[self.currentTest]
        if self.btnTestOk.isEnabled() and self.btnTestOk.text() == "Step passes":
            self.runNextStep()
        else:
            item = self.listTests.item(self.currentTest)
            item.setBackground(QtCore.Qt.white)
            item.setForeground(QtCore.Qt.green)
            try:
                test = self.tests[self.currentTest]
                test.cleanup()
                self.currentTestResult.passed()
            except:
                item.setForeground(QtCore.Qt.red)
                self.currentTestResult.failed("Test cleanup", traceback.format_exc())

            self.currentTest +=1
            self.runNextTest()


    def testFails(self, msg = ""):
        item = self.listTests.item(self.currentTest)
        item.setBackground(QtCore.Qt.white)
        item.setForeground(QtCore.Qt.red)
        test = self.tests[self.currentTest]
        if self.btnTestOk.isEnabled() and self.btnTestOk.text() == "Step passes":
            desc = test.steps[self.currentTestStep - 1][0]
        else:
            desc = test.steps[self.currentTestStep][0]
        self.currentTestResult.failed(desc, msg)
        try:
            test.cleanup()
        except:
            pass
        self.currentTest +=1
        self.runNextTest()

    def skipTest(self):
        item = self.listTests.item(self.currentTest)
        item.setBackground(QtCore.Qt.white)
        item.setForeground(QtCore.Qt.gray)
        try:
            test = self.tests[self.currentTest]
            test.cleanup()
        except:
            item.setForeground(QtCore.Qt.red)
        self.currentTest +=1
        self.currentTestResult.skipped()

        self.runNextTest()

    def cancelTesting(self):
        self.toolbar.setVisible(False)





