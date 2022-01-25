from __future__ import print_function
from __future__ import absolute_import

try:
    from PyQt4 import QtGui, QtCore
    MyGui=QtGui
    qt=4
except ImportError as e:
    from PyQt5 import QtWidgets, QtCore
    MyGui=QtWidgets
    qt=5

from code.graph import plotWidget
from .config import configWidget

import time

class ApplicationWindow(MyGui.QMainWindow):
    def __init__(self, daq, log, opts, settings):
        MyGui.QMainWindow.__init__(self)

        # preparations
        self.log  = log
        self.daq = daq
        self.opts=opts # currently not used, but might be useful to get sys.argv here
        self.settings=settings
        
        # geometry
        self.left_minimum_size=(550,500)
        self.right_width=450
        self.right_tab_width=self.right_width-30 # not smaller than 30
        self.right_tab_minimum_height=200
        self.window_position=(100,100)
        self.window_size=(self.left_minimum_size[0]+self.right_width+50, max(self.left_minimum_size[1], self.right_tab_minimum_height)+50) # x, y


        # window size
        desktop = MyGui.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        screen_x = screen_size.x() + screen_size.width()
        screen_y = screen_size.y() + screen_size.height()
        self.log.info("Screen with size %i x %i px detected" %(screen_x,screen_y))
        self.log.info("Window minimum size is %d x %d px"%self.window_size)

        if self.window_size[1]>screen_y or self.window_size[0]>screen_x:
            self.log.error("Window is too big for screen!!")

        self.setGeometry(self.window_position[0], self.window_position[1], self.window_size[0], self.window_size[1])

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("PicoGui")

        self.file_menu = MyGui.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = MyGui.QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.main_widget = CentralWidget(self, log, daq, settings)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.statusBar().showMessage("All hail matplotlib!", 2000)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.daq.close()
        self.log.endLogging()
        self.fileQuit()

##########################################################################################

class CentralWidget(MyGui.QWidget):
    '''
    The layout of the main window
    '''
    def __init__(self, parent, log, daq, settings):
        super(CentralWidget, self).__init__(parent)
        self.daq=daq
        if qt==4:
            self.connect(self.daq, QtCore.SIGNAL("finished()"), self.stopMeasurement)
        else:
            self.daq.finished.connect(self.stopMeasurement)
        self.log=log
        self.settings=settings

        # copy geometry information from parent:
        self.left_minimum_size=parent.left_minimum_size
        self.right_width=parent.right_width
        self.right_tab_width=parent.right_tab_width
        self.right_tab_minimum_height=parent.right_tab_minimum_height
        self.window_position=parent.window_position
        self.window_size=parent.window_size

        # main layout which will devided horizontally
        layout=MyGui.QHBoxLayout()

        # left side will comprise the plot
        left = MyGui.QGroupBox(self)
        left.setMinimumSize(self.left_minimum_size[0],self.left_minimum_size[1])
        # white background is nicer for the plot
        left.setStyleSheet("background-color: rgb(255, 255, 255)")
        # add the plot widget
        leftlayout=MyGui.QVBoxLayout()
        plot=plotWidget(self,log, daq)
        leftlayout.addWidget(plot)
        left.setLayout(leftlayout)

        # right side will comprise the config and buttons to start/stop the measurement
        right = MyGui.QGroupBox(self)
        right.setMinimumWidth(self.right_width)
        right.setMaximumWidth(self.right_width+50)

        # right side is devided into the to part (config) and bottom part (start/stop button)
        rightlayout=MyGui.QVBoxLayout()

        # the config widget is complicated therefore in another class
        config=configWidget(self, log, daq, settings)

        self.saveLog = MyGui.QLineEdit()
        # TODO evaluate as float which is within the range given by voltagerange
        #e2.setValidator(MyGui.QDoubleValidator(0.99,99.99,5)) # min max stellenzahl nach komma
        self.saveLog.setPlaceholderText("Press enter to save")
        # TODO read setDefault value and set it here
        self.saveLog.returnPressed.connect(self.saveLogger)

        self.progress = MyGui.QProgressBar(self)
        self.progress.setGeometry(200, 80, 250, 20)


        self.button = MyGui.QPushButton('Start', self)
        self.button.clicked.connect(self.startMeasurement)

        # put together the right part
        rightlayout.addWidget(config)
        rightlayout.addWidget(self.saveLog)
        rightlayout.addWidget(self.progress)
        rightlayout.addWidget(self.button)
        right.setLayout(rightlayout)

        # put together the central widget
        layout.addWidget(left)
        layout.addWidget(right)
        self.setLayout(layout)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_progressbar)
        self.timer.start(1000)

    def saveLogger(self):
        if self.daq.out!=None:
            log=self.daq.out
        else:
            log=self.log
        try:
            log.msg("LMSG:"+str(self.saveLog.text())) # used a string here which is easily searchable
        except:
            self.log.msg("LMSG:"+str(self.saveLog.text())) # used a string here which is easily searchable
        self.saveLog.setText("")
        #self.saveLog.setPlaceholderText("Text is saved!")
        #time.sleep(0.5)
        self.saveLog.setPlaceholderText("Log Message: Press enter to save")


    def update_progressbar(self):
        if self.daq.isRunning():
            self.progress.setValue(self.daq.progress)
        else:
            self.progress.setValue(0)

    def startMeasurement(self):
        if self.button.text()=="Start":
            if not self.daq.isRunning():
                    self.button.setText('Stop')
                    self.daq._threadIsStopped=False
                    self.daq.start()
                    self.log.debug("Measurement started.")
            else:
                self.log.error("Measurement is  running -> you cannot start it.")

        else:
            self.stopMeasurement()

    def stopMeasurement(self):
        # this is executed twice when stopping a run somehow!!

        self.log.debug("Stopping measurement...")

        if self.daq.isRunning():
            '''
             measurement is running -> Stop it
            '''
            self.daq._threadIsStopped=True # this stops the next loop
            while self.daq.isRunning():
                time.sleep(0.1)
            self.log.debug("Measurement stopped.")
            if self.daq.saveMeasurement:
                self.daq.saveAll()
                #self.daq.writeToDatenbank()
                self.daq.saveMeasurement=False
                self.out=None
            else:
                #self.askToSave()
                text, ok = MyGui.QInputDialog.getText(self, 'Do you want to save?', 
                                            'Do you want to save this measurement?\n'+
                                            'You can enter a last Logbook message here:')
                if ok:
                    self.daq.out.msg("LMSG:"+str(text))
                    self.daq.saveAll()
                    #self.daq.writeToDatenbank()
                    self.daq.saveMeasurement=False
                    self.daq.out=None
                else:
                    self.daq.deleteDir()
                    self.log.info("Measurement not saved.")
        if self.button.text()=="Stop":
            self.button.setText('Start')
            self.log.debug("Stop Measurement: Measurement button set to start.")
            
        
    '''
    def askToSave(self):
       print("Ask")
       msg = MyGui.QMessageBox()
       msg.setIcon(MyGui.QMessageBox.Information)

       msg.setText("Do you want to save this measurement?")
       #msg.setInformativeText("Do you want to save this measurement?")
       msg.setWindowTitle("Save?")
       #msg.setDetailedText("blub")
       msg.setStandardButtons(MyGui.QMessageBox.Ok | MyGui.QMessageBox.Cancel)
       msg.buttonClicked.connect(self.answerSave)
       retval = msg.exec_()
       print("value of pressed message box button:", retval)

    def answerSave(self,i):
       self.log.debug("Button pressed is:%s"%i.text() )
       if i.text()=="OK":
            self.daq.saveAll()
            # reset
            self.daq.saveMeasurement=False
    '''