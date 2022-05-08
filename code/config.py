from __future__ import print_function
from __future__ import absolute_import

# Qt4 imports
try:
    from PyQt4 import QtGui, QtCore
    MyGui=QtGui
    qt=4
except ImportError as e:
    from PyQt5 import QtWidgets, QtCore, QtGui
    MyGui=QtWidgets
    qt=5


##########################################################################################


class configWidget(MyGui.QWidget):
    '''
    The layout of the config widget
    '''
    def __init__(self, parent, log, daq, settings):
        super(configWidget, self).__init__(parent)

        # copy geometry information from parent:
        self.left_minimum_size=parent.left_minimum_size
        self.right_width=parent.right_width
        self.right_tab_width=parent.right_tab_width
        self.right_tab_minimum_height=parent.right_tab_minimum_height
        self.window_position=parent.window_position
        self.window_size=parent.window_size

        config = MyGui.QTabWidget(self)
        config.setMinimumHeight(self.right_tab_minimum_height)
        config.setMinimumWidth(self.right_tab_width)
        config.setMaximumWidth(self.right_tab_width+25)
        trigger	= triggerConfigWidget(self, log, daq, settings)
        tab1	= channelConfigWidget(self, log, "A", daq, settings, trigger)
        tab2	= channelConfigWidget(self, log, "B", daq, settings, trigger)
        tab3	= channelConfigWidget(self, log, "C", daq, settings, trigger)
        tab4	= channelConfigWidget(self, log, "D", daq, settings, trigger)
        #trigger	= triggerConfigWidget(self, log, daq, settings)
        #tab6	= siggenConfigWidget(self, log, daq, settings)
        tab7	= measurementConfigWidget(self, log, daq, settings)
        display	=displayConfigWidget(self, log, daq, settings)
        #tab8	= settingsConfigWidget(self, log, daq, settings)
        config.addTab(tab1,"A")
        config.addTab(tab2,"B")
        config.addTab(tab3,"C")
        config.addTab(tab4,"D")
        config.addTab(trigger,"Trigger")
        #config.addTab(tab6,"Sig.Gen.")
        config.addTab(tab7,"Meas.")
        config.addTab(display,"Display")
        #config.addTab(tab8,"Sett.")
        #config.mainwindow = parent.parentWidget()

##########################################################################################


class channelConfigWidget(MyGui.QWidget):
    '''
    The master of the channel config widgets
    '''
    def __init__(self, parent, log, channel, daq, settings, trigger):
        super(channelConfigWidget, self).__init__(parent)
        self.log=log
        self.channel=channel
        self.daq=daq
        self.settings=settings
        self.trigger=trigger
        
        wrapperLayout = MyGui.QVBoxLayout(self)
        grid=MyGui.QGridLayout()

        labelVoltage = MyGui.QLabel()
        labelVoltage.setText("Voltage Range")
        self.chooseVoltage = MyGui.QComboBox(self)
        
        defaultRange=self.daq.voltagerange[self.channel]
        for entry in self.daq.ps.CHANNEL_RANGE:
            self.chooseVoltage.addItem(entry["rangeStr"])
            if defaultRange==entry["rangeV"]:
                defaultStr=entry["rangeStr"]
        index = self.chooseVoltage.findText(defaultStr, QtCore.Qt.MatchFixedString)
        if index >= 0:
             self.chooseVoltage.setCurrentIndex(index)        
        self.chooseVoltage.currentIndexChanged.connect(self.enable)

        labelCoupling = MyGui.QLabel()
        labelCoupling.setText("Coupling")
        self.chooseCoupling = MyGui.QComboBox(self)
        default=self.daq.coupling[self.channel]
        #self.log.error(str(default))
        for value in self.daq.ps.CHANNEL_COUPLINGS:
            self.chooseCoupling.addItem(value)
        index = self.chooseCoupling.findText(default, QtCore.Qt.MatchFixedString)
        if index>=0:
            self.chooseCoupling.setCurrentIndex(index)
        self.chooseCoupling.currentIndexChanged.connect(self.enable)

        labelOffset = MyGui.QLabel()
        labelOffset.setText("Offset [mV]")
        self.chooseOffset = MyGui.QLineEdit()
        default=int(self.daq.offset[self.channel]*1000)
        if qt==4:
        	self.chooseOffset.setValidator(MyGui.QIntValidator(-20000,20000)) # min max stellenzahl nach komma
        else:
        	self.chooseOffset.setValidator(QtGui.QIntValidator(-20000,20000))
        self.chooseOffset.setText(str(default))
        self.chooseOffset.textChanged.connect(self.enable)
        
        labelMaxOffset = MyGui.QLabel()
        labelMaxOffset.setText("Max.Offset [mV]")
        self.maxOffset = MyGui.QLabel()
        self.maxOffset.setText(str(int(self.daq.maxOffset(self.channel))))
        #Palette= QtGui.QPalette()
        #Palette.setColor(QtGui.QPalette.Text, QtCore.Qt.gray)
        #self.maxOffset.setPalette(Palette)
        #self.maxOffset.setReadOnly(True)
        labelHintOffset = MyGui.QLabel()
        labelHintOffset.setText("Inaccurate amplitude if offset \nabove/below Voltage Range!")


        c=0
        grid.addWidget(labelVoltage,          c,0) # y, x
        grid.addWidget(self.chooseVoltage,    c,1) # y, x
        c+=1
        grid.addWidget(labelCoupling,         c,0) # y, x
        grid.addWidget(self.chooseCoupling,   c,1) # y, x
        c+=1
        grid.addWidget(labelOffset,           c,0) # y, x
        grid.addWidget(self.chooseOffset,     c,1) # y, x
        c+=1
        grid.addWidget(labelMaxOffset,           c,0) # y, x
        grid.addWidget(self.maxOffset,     c,1) # y, x
        c+=1
        grid.addWidget(labelHintOffset,     c,1) # y, x
        #self.setLayout(layout)
        
        wrapperLayout.addLayout(grid)
        wrapperLayout.addStretch()

        # "off sets offset in Volt; do not use, not fully implemented in analysis yet!", logit=False)


    def enable(self):
        '''
        read all chosen settings
        set settings at device
        '''

        voltageString = str(self.chooseVoltage.currentText())
        for entry in self.daq.ps.CHANNEL_RANGE:
            if voltageString==entry["rangeStr"]:
                voltagerange=entry["rangeV"]
                self.daq.voltagerange[self.channel]=voltagerange
                

# TODO: channel A and B are hard coded as PMT and temperature here and in daq

        coupling=str(self.chooseCoupling.currentText())
        self.daq.coupling[self.channel] = coupling.replace("\r","")# TODO hier scheint kein \r in coupling zu sein

        offset = str(self.chooseOffset.text())
        try:
            self.daq.offset[self.channel]=float(offset)/1000
        except ValueError as e:
            #self.log.error("Could not convert string to float %s"%offset)
            self.daq.offset[self.channel]=0
            #self.chooseOffset.setText("0")

        if voltagerange!=self.daq.voltagerange[self.channel]:
            self.log.error("Required Voltage range not available: %f\n"+\
                           "Chose %f instead"%(voltagerange, self.daq.voltagerange))
        
        # update trigger minimum
        self.trigger.minVoltage.setText(str(self.daq.suggestedMinVoltage())) # after all other settings have been done!!
        self.maxOffset.setText(str(int(self.daq.maxOffset(self.channel))))# after all other settings have been done!!
        
        self.settings.saveSettings()



##########################################################################################

class triggerConfigWidget(MyGui.QWidget):
    '''
    trigger tab widget
    '''
    def __init__(self, parent, log, daq, settings):
        super(triggerConfigWidget, self).__init__(parent)
        self.log=log
        self.daq=daq
        self.settings=settings

        wrapperLayout = MyGui.QVBoxLayout(self)
        grid=MyGui.QGridLayout()

        #self.enabled=MyGui.QCheckBox("Enabled")
        #self.enabled.setChecked(False)
        #self.enabled.stateChanged.connect(self.enable)

        labelChannel = MyGui.QLabel()
        labelChannel.setText("Channel")
        self.chooseChannel = MyGui.QComboBox(self)
        defaultChannel=self.daq.triggerchannel
        for entry in ["A","B", "C", "D"]:
            self.chooseChannel.addItem(entry)
        #self.chooseChannel.model().item(2).setEnabled(False) 
        index = self.chooseChannel.findText(defaultChannel, QtCore.Qt.MatchFixedString)
        if index >= 0: self.chooseChannel.setCurrentIndex(index)
        self.chooseChannel.currentIndexChanged.connect(self.enable)
        
        labelMinVoltage = MyGui.QLabel()
        labelMinVoltage.setText("Min. Voltage [mV]")
        #self.minVoltage = MyGui.QLabel()
        #self.minVoltage.setText(str(self.daq.suggestedMinVoltage()))
        self.minVoltage = MyGui.QLabel()
        self.minVoltage.setText(str(self.daq.suggestedMinVoltage()))
        #self.minVoltage.setReadOnly(True)
        #Palette= QtGui.QPalette()
        #Palette.setColor(QtGui.QPalette.Text, QtCore.Qt.gray)
        #self.minVoltage.setPalette(Palette)
        
        labelMode = MyGui.QLabel()
        labelMode.setText("Mode")
        self.chooseMode = MyGui.QComboBox(self)
        default=self.daq.triggermode
        for entry in ["Falling","Rising"]:
            self.chooseMode.addItem(entry)
        index = self.chooseMode.findText(default, QtCore.Qt.MatchFixedString)
        if index >= 0: self.chooseMode.setCurrentIndex(index)
        self.chooseMode.currentIndexChanged.connect(self.enable)
        
        labelVoltage = MyGui.QLabel()
        labelVoltage.setText("Voltage [mV]  ")
        self.chooseVoltage = MyGui.QLineEdit()
        default=self.daq.triggervoltage
        self.chooseVoltage.setText(str(int(default*1000)))
        if qt==4:
        	self.chooseVoltage.setValidator(MyGui.QIntValidator(-20000,20000)) # min max stellenzahl nach komma
        else:
        	self.chooseVoltage.setValidator(QtGui.QIntValidator(-20000,20000))
        self.chooseVoltage.textChanged.connect(self.enable)

        labelDelay = MyGui.QLabel()
        labelDelay.setText("Delay [Sampling Interval]")
        self.chooseDelay = MyGui.QLineEdit()
        default=self.daq.triggerdelay
        self.chooseDelay.setText(str(int(default)))
        if qt==4:
        	self.chooseDelay.setValidator(MyGui.QIntValidator(-1000000,1000000)) # min max stellenzahl nach komma
        else:
        	self.chooseDelay.setValidator(QtGui.QIntValidator(-1000000,1000000))
        self.chooseDelay.textChanged.connect(self.enable)

        labelHintDelay = MyGui.QLabel()
        labelHintDelay.setText("Note: + will shift trigger to left. Default \nat 0 is a 10% shift to right. Make sure you \ndon't choose a value larger than 10% \notherwise the waveform is shifted out \nof the analysis window.")

        c=0
        grid.addWidget(labelChannel,          c,0) # y, x
        grid.addWidget(self.chooseChannel,    c,1) # y, x
        c+=1
        grid.addWidget(labelMinVoltage,          c,0) # y, x
        grid.addWidget(self.minVoltage,    c,1) # y, x        
        c+=1
        grid.addWidget(labelVoltage,          c,0) # y, x
        grid.addWidget(self.chooseVoltage,    c,1) # y, x
        c+=1
        grid.addWidget(labelMode,             c,0) # y, x
        grid.addWidget(self.chooseMode,       c,1) # y, x
        c+=1
        grid.addWidget(labelDelay,            c,0) # y, x
        grid.addWidget(self.chooseDelay,      c,1) # y, x
        c+=1
        grid.addWidget(labelHintDelay,            c,1)
        

        wrapperLayout.addLayout(grid)
        wrapperLayout.addStretch()


    def enable(self):
        '''
        read all chosen settings
        '''

        self.daq.triggerchannel = str(self.chooseChannel.currentText())
        self.daq.triggermode = str(self.chooseMode.currentText())
        self.daq.triggerdelay = 0 # TODO
        self.daq.triggertimeout =10000 # TODO

        
        triggervoltage = str(self.chooseVoltage.text())
        if triggervoltage=="-":# no wired effect when starting to type a negative number
            triggervoltage=0
        try:
            self.daq.triggervoltage=float(triggervoltage)/1000
        except ValueError as e:
            #self.log.error("Could not convert string to float %s"%triggervoltage)
            self.daq.triggervoltage=0
            #self.chooseVoltage.setText("0")
        
        delay = str(self.chooseDelay.text())
        if delay=="-":# no wired effect when starting to type a negative number
            delay=0
        try:
            self.daq.triggerdelay=int(float(delay))
        except ValueError as e:
            #self.log.error("Could not convert string to int %s"%delay)
            self.daq.triggerdelay=0
            #self.chooseVoltage.setText("0")
            
        self.minVoltage.setText(str(self.daq.suggestedMinVoltage())) # after all other settings have been done!!
            
        self.settings.saveSettings()

##########################################################################################

class siggenConfigWidget(MyGui.QWidget):
    '''
    signal generator tab widget
    '''
    def __init__(self, parent, log, daq, settings):
        super(siggenConfigWidget, self).__init__(parent)
        self.log=log
        self.daq=daq
        self.settings=settings

        layout=MyGui.QGridLayout()
        '''
        self.sigoffsetVoltage=0
        self.pkToPk=2 # microvolts
        self.waveType="Square"
        self.sigfrequency=1E3
        '''

        labelOffset = MyGui.QLabel()
        labelOffset.setText("Offset in mV")
        self.chooseOffset = MyGui.QLineEdit()
        self.chooseOffset.setText("0")
        self.chooseOffset.textChanged.connect(self.enable)
        # TODO read setDefault value and set it here

        labelP2P = MyGui.QLabel()
        labelP2P.setText("Peak 2 Peak in mV")
        self.chooseP2P = MyGui.QLineEdit()
        self.chooseP2P.setText("0")
        self.chooseP2P.textChanged.connect(self.enable)
        # TODO read setDefault value and set it here

        labelFreq = MyGui.QLabel()
        labelFreq.setText("Frequency in Hz")
        self.chooseFreq = MyGui.QLineEdit()
        self.chooseFreq.setText("0")
        #self.chooseFreq.setValidator(MyGui.QFloatValidator(0,20000000, 3))
        self.chooseFreq.textChanged.connect(self.enable)
        # TODO read setDefault value and set it here

        labelType = MyGui.QLabel()
        labelType.setText("Channel")
        self.chooseType = MyGui.QComboBox(self)
        for entry in list(self.daq.ps.WAVE_TYPES):
            self.chooseType.addItem(entry)
        self.chooseType.currentIndexChanged.connect(self.enable)
        
        self.sigGenEnabled=MyGui.QCheckBox("Enable signal generator")
        self.sigGenEnabled.setChecked(False)
        self.sigGenEnabled.stateChanged.connect(self.enable)
        # TODO read setDefault value and set it here

        c=0
        layout.addWidget(labelOffset,          c,0) # y, x
        layout.addWidget(self.chooseOffset,    c,1) # y, x
        c+=1
        layout.addWidget(labelP2P,              c,0) # y, x
        layout.addWidget(self.chooseP2P,        c,1) # y, x
        c+=1
        layout.addWidget(labelFreq,             c,0) # y, x
        layout.addWidget(self.chooseFreq,       c,1) # y, x
        c+=1
        layout.addWidget(labelType,            c,0) # y, x
        layout.addWidget(self.chooseType,      c,1) # y, x
        c+=1
        layout.addWidget(self.sigGenEnabled,        c,0) # y, x

        self.setLayout(layout)


    def enable(self):
        '''
        read all chosen settings
        '''

        offset = str(self.chooseOffset.text())
        if offset=="-":# no wired effect when starting to type a negative number
            offset=0
        try:
            self.daq.sigoffsetVoltage=float(offset)/1000 # mV-> V
        except ValueError as e:
            #self.log.error("Could not convert string to float %s"%offset)
            self.daq.sigoffsetVoltage=0
            self.chooseOffset.setText("0")
            
        p2p = str(self.chooseP2P.text())
        if p2p=="-":# no wired effect when starting to type a negative number
            p2p=0
        try:
            self.daq.pkToPk=float(p2p)/1000 # mV-> V
        except ValueError as e:
            #self.log.error("Could not convert string to float %s"%p2p)
            self.daq.pkToPk=0
            self.chooseP2P.setText("0")
        
        freq = str(self.chooseFreq.text())
        try:
            self.daq.sigfrequency=float(freq)
        except ValueError as e:
            #self.log.error("Could not convert string to float %s"%freq)
            self.daq.sigfrequency=0
            self.chooseFreq.setText("0")

        self.daq.waveType = str(self.chooseType.currentText())
                
        try:
            if self.sigGenEnabled.isChecked():
                self.log.info("Enable Signal Generator")
                self.daq.setSignalGenerator(disable=False)
                self.daq.sigGenEnabled=True
            elif not self.sigGenEnabled.isChecked() and self.daq.sigGenEnabled:
                self.log.info("Disable Signal Generator")
                self.daq.setSignalGenerator(disable=True)
                self.daq.sigGenEnabled=False
        except Exception as e:
            print(e)
            
        self.settings.saveSettings()
		
##########################################################################################

class measurementConfigWidget(MyGui.QWidget):
    '''
    The master of the channel config widgets
    '''
    def __init__(self, parent, log, daq, settings):
        super(measurementConfigWidget, self).__init__(parent)
        self.log=log
        self.daq=daq
        self.settings=settings
        
        wrapperLayout = MyGui.QVBoxLayout(self)
        grid=MyGui.QGridLayout()
        
        default=bool(self.daq.channelEnabled["A"])
        #self.log.error(str(default))
        self.PMTEnabled=MyGui.QCheckBox("Ch. A (PMT)")
        self.PMTEnabled.setChecked(default)
        self.PMTEnabled.stateChanged.connect(self.enable)
        
        default=bool(self.daq.channelEnabled["B"])
        #self.log.error(str(default))
        self.HVEnabled=MyGui.QCheckBox("Ch. B (HV)")
        self.HVEnabled.setChecked(default)
        self.HVEnabled.stateChanged.connect(self.enable)
        
        default=bool(self.daq.channelEnabled["C"])
        #self.log.error(str(default))
        self.chCEnabled=MyGui.QCheckBox("Ch. C (Light)")
        self.chCEnabled.setChecked(default)
        self.chCEnabled.stateChanged.connect(self.enable)
        
        default=bool(self.daq.channelEnabled["D"])
        #self.log.error(str(default))
        self.chDEnabled=MyGui.QCheckBox("Ch. D (Antenna)")
        self.chDEnabled.setChecked(default)
        self.chDEnabled.stateChanged.connect(self.enable)
        
        default=self.daq.measureTemp
        self.tempEnabled=MyGui.QCheckBox("Temperature")
        self.tempEnabled.setChecked(default)
        self.tempEnabled.stateChanged.connect(self.enable)
        
        default=self.daq.measureCPU
        self.cpuEnabled=MyGui.QCheckBox("CPU / Memory")
        self.cpuEnabled.setChecked(default)
        self.cpuEnabled.stateChanged.connect(self.enable)
        
        labelFreq = MyGui.QLabel()
        labelFreq.setText("Sampling frequency")
        self.chooseFreq = MyGui.QLineEdit()
        #if qt==4:
        # 	self.chooseFreq.setValidator(MyGui.QIntValidator(0,1064448)) # min max stellenzahl nach komma
        #else:
        # 	self.chooseFreq.setValidator(QtGui.QIntValidator(0,1064448))
        self.chooseFreq.setText("%e" % self.daq.samplefreq)
        self.chooseFreq.textChanged.connect(self.enable)

        labelSample = MyGui.QLabel()
        labelSample.setText("Number of samples")
        self.chooseSample = MyGui.QLineEdit()
        if qt==4:
        	self.chooseSample.setValidator(MyGui.QIntValidator(0,1064448)) # min max stellenzahl nach komma
        else:
        	self.chooseSample.setValidator(QtGui.QIntValidator(0,1064448))
        self.chooseSample.setText(str(int(self.daq.nosamples)))
        self.chooseSample.textChanged.connect(self.enable)

        labelCaptures = MyGui.QLabel()
        labelCaptures.setText("Number of captures")
        self.chooseCaptures = MyGui.QLineEdit()
        if qt==4:
        	self.chooseCaptures.setValidator(MyGui.QIntValidator(0,100000)) # min max stellenzahl nach komma
        else:
        	self.chooseCaptures.setValidator(QtGui.QIntValidator(0,100000))
        self.chooseCaptures.setText(str(int(self.daq.captures)))
        self.chooseCaptures.textChanged.connect(self.enable)
        
        #verticalLine =  MyGui.QFrame()
        #verticalLine.setFrameStyle(MyGui.QFrame.HLine)
        #verticalLine.setSizePolicy(MyGui.QSizePolicy.Minimum,QSizePolicy.Expanding)
        labelAdj= MyGui.QLabel()
        labelAdj.setText("Switch on / off:")


        
        self.fftEnabled=MyGui.QCheckBox("FFT")
        self.fftEnabled.setChecked(bool(self.daq.doCalcFFT))
        self.fftEnabled.stateChanged.connect(self.enable)


        c=0
        grid.addWidget(labelFreq,           c,0) # y, x
        grid.addWidget(self.chooseFreq,     c,1) # y, x
        c+=1
        grid.addWidget(labelSample,           c,0) # y, x
        grid.addWidget(self.chooseSample,     c,1) # y, x
        c+=1
        grid.addWidget(labelCaptures,         c,0) # y, x
        grid.addWidget(self.chooseCaptures,   c,1) # y, x
        c+=1
        grid.addWidget(labelAdj,             c,0) # y, x
        c+=1
        grid.addWidget(self.PMTEnabled,        c,0) # y, x
        grid.addWidget(self.tempEnabled,        c,1) # y, x
        c+=1
        grid.addWidget(self.HVEnabled,        c,0) # y, x
        grid.addWidget(self.fftEnabled,        c,1) # y, x
        c+=1
        grid.addWidget(self.chCEnabled,        c,0) # y, x
        grid.addWidget(self.cpuEnabled,        c,1) # y, x
        c+=1
        grid.addWidget(self.chDEnabled,        c,0) # y, x
        #c+=1
        #grid.addWidget(verticalLine,             c,0) # y, x
        
        c+=1

        wrapperLayout.addLayout(grid)
        wrapperLayout.addStretch()


    def enable(self):
        '''
        read all chosen settings
        '''


        nosamples = str(self.chooseSample.text())
        try:
            self.daq.nosamples=int(nosamples)
        except ValueError as e:
            #self.log.error("Could not convert string to int %s"% nosamples)
            self.daq.nosamples=0


        captures = str(self.chooseCaptures.text())
        try:
            self.daq.captures=int(captures)
        except ValueError as e:
            #self.log.error("Could not convert string to int %s"%captures)
            self.daq.captures=0
            
        
        freq = str(self.chooseFreq.text())
        try:
            self.daq.samplefreq=int(float(freq))
        except ValueError as e:
            #self.log.error("Could not convert string to int %s"%freq)
            self.daq.samplefreq=1.e9

        self.daq.channelEnabled["A"] = self.PMTEnabled.isChecked()
        self.daq.channelEnabled["B"] = self.HVEnabled.isChecked()
        self.daq.channelEnabled["C"] = self.chCEnabled.isChecked()
        self.daq.channelEnabled["D"] = self.chDEnabled.isChecked()
        self.daq.doCalcFFT = self.fftEnabled.isChecked()
        self.daq.measureTemp=self.tempEnabled.isChecked()
        self.daq.measureCPU=self.cpuEnabled.isChecked()
             
        
        self.settings.saveSettings()
        
        
##########################################################################################

        
class displayConfigWidget(MyGui.QWidget):
    '''
    The master of the channel config widgets
    '''
    def __init__(self, parent, log, daq, settings):
        super(displayConfigWidget, self).__init__(parent)
        self.log=log
        self.daq=daq
        self.settings=settings
        
        wrapperLayout = MyGui.QVBoxLayout(self)
        grid=MyGui.QGridLayout()
        
        
        default=self.daq.showArea
        self.showArea=MyGui.QCheckBox("Show Charge")
        self.showArea.setChecked(default)
        self.showArea.stateChanged.connect(self.enable)

        labelTime = MyGui.QLabel()
        labelTime.setText("Measurement time [min]")
        self.chooseTime = MyGui.QLineEdit()
        self.chooseTime.setText(str(float(self.daq.measurementduration))) # disabled
        self.chooseTime.textChanged.connect(self.enable)

        labelWaveforms = MyGui.QLabel()
        labelWaveforms.setText("Waveforms to show/save")
        self.chooseWaveforms = MyGui.QLineEdit()
        if qt==4:
        	self.chooseWaveforms.setValidator(MyGui.QIntValidator(0,1000)) # min max stellenzahl nach komma
        else:
        	self.chooseWaveforms.setValidator(QtGui.QIntValidator(0,1000)) # min max stellenzahl nach komma
        self.chooseWaveforms.setText(str(int(self.daq.nowaveforms)))
        self.chooseWaveforms.textChanged.connect(self.enable)
        
        labelXTicks = MyGui.QLabel()
        labelXTicks.setText("Xtick Nbr.")
        self.labelXTicks = MyGui.QLineEdit()
        if qt==4:
        	self.labelXTicks.setValidator(MyGui.QIntValidator(0,20)) # min max stellenzahl nach komma
        else:
        	self.labelXTicks.setValidator(QtGui.QIntValidator(0,20)) # min max stellenzahl nach komma
        self.labelXTicks.setText(str(int(self.daq.xticks))) # disabled
        self.labelXTicks.textChanged.connect(self.enable)
        
        

        c=0
        c+=1
        grid.addWidget(labelTime,             c,0) # y, x
        grid.addWidget(self.chooseTime,       c,1) # y, x
        c+=1
        grid.addWidget(labelWaveforms,        c,0) # y, x
        grid.addWidget(self.chooseWaveforms,  c,1) # y, x
        c+=1
        grid.addWidget(labelXTicks,        c,0) # y, x
        grid.addWidget(self.labelXTicks,  c,1) # y, x
        c+=1
        grid.addWidget(self.showArea,        c,0) # y, x
        c+=1
        
        wrapperLayout.addLayout(grid)
        wrapperLayout.addStretch()


    def enable(self):
        '''
        read all chosen settings
        '''

        measurementduration = str(self.chooseTime.text())
        try:
            self.daq.measurementduration=float(measurementduration)
        except ValueError as e:
            #self.log.error("Could not convert string to float %s"%measurementduration)
            self.daq.measurementduration=0
            #self.chooseTime.setText("0")
            
        nowaveforms = str(self.chooseWaveforms.text())
        try:
            self.daq.nowaveforms=int(nowaveforms)
        except ValueError as e:
            #self.log.error("Could not convert string to int %s"% nowaveforms)
            self.daq.nowaveforms=0
        
        xticks=str(self.labelXTicks.text())
        try:
            self.daq.xticks=int(xticks)
        except ValueError as e:
            #self.log.error("Could not convert string to int %s"% xticks)
            self.daq.xticks=5
        
        
        self.daq.showArea=self.showArea.isChecked()  
        
         
                     
        self.settings.saveSettings()

##########################################################################################

class settingsConfigWidget(MyGui.QWidget):
    '''
    settings tab widget
    '''
    def __init__(self, parent, log, daq, settings):
        super(settingsConfigWidget, self).__init__(parent)
        self.log=log
        self.daq=daq
        self.settings=settings

        layout=MyGui.QGridLayout()

        #self.enabled=MyGui.QCheckBox("Enabled")
        #self.enabled.setChecked(False)
        #self.enabled.stateChanged.connect(self.enable)
        
        default=self.daq.led
        self.led=MyGui.QCheckBox("LED on")
        self.led.setChecked(default)
        self.led.stateChanged.connect(self.enable)
        
        labelSource = MyGui.QLabel()
        labelSource.setText("Source")
        self.chooseSource = MyGui.QComboBox(self)
        default=self.daq.source
        for entry in ["None", "Am241_stud","Am241_katrin", "Ba133","Sr90"]:
            self.chooseSource.addItem(entry)
        index = self.chooseSource.findText(default, QtCore.Qt.MatchFixedString)
        if index >= 0: self.chooseSource.setCurrentIndex(index)
        self.chooseSource.currentIndexChanged.connect(self.enable)
        
        labelPMT = MyGui.QLabel()
        labelPMT.setText("PMT")
        self.choosePMT = MyGui.QComboBox(self)
        default=str(self.daq.pmt)
        for entry in ["6","1","3"]:
            self.choosePMT.addItem(entry)
        index = self.choosePMT.findText(default, QtCore.Qt.MatchFixedString)
        if index >= 0: self.choosePMT.setCurrentIndex(index)
        self.choosePMT.currentIndexChanged.connect(self.enable)
        
        labelSzin = MyGui.QLabel()
        labelSzin.setText("Szintillator")
        self.chooseSzin = MyGui.QComboBox(self)
        default=self.daq.szint
        for entry in ["None","EJ212","EJ440","Uwe"]:
            self.chooseSzin.addItem(entry)
        index = self.chooseSzin.findText(default, QtCore.Qt.MatchFixedString)
        if index >= 0: self.chooseSzin.setCurrentIndex(index)
        self.chooseSzin.currentIndexChanged.connect(self.enable)
        
        labelWater = MyGui.QLabel()
        labelWater.setText("Water Quality")
        self.chooseWater = MyGui.QComboBox(self)
        default=self.daq.water
        for entry in ["None","Ultra-Purified", "De-Ionized", "Mineral", "Tab", "Contamined"]:
            self.chooseWater.addItem(entry)
        index = self.chooseWater.findText(default, QtCore.Qt.MatchFixedString)
        if index >= 0: self.chooseWater.setCurrentIndex(index)
        self.chooseWater.currentIndexChanged.connect(self.enable)
        
        default=self.daq.degased
        self.degased=MyGui.QCheckBox("Water is degased")
        self.degased.setChecked(default)
        self.degased.stateChanged.connect(self.enable)
        
        #labelDistance = MyGui.QLabel()
        #labelDistance.setText("Distance PMT to water / source")
        #self.chooseDistance = MyGui.QLineEdit()
        #self.chooseDistance.setText(str(self.daq.dist))
        #self.chooseDistance.textChanged.connect(self.enable)

        c=0
        layout.addWidget(labelSource,    c,0) # y, x
        layout.addWidget(self.chooseSource,    c,1) # y, x
        c+=1
        layout.addWidget(labelPMT,    c,0) # y, x
        layout.addWidget(self.choosePMT,    c,1) # y, x
        c+=1
        layout.addWidget(labelSzin,    c,0) # y, x
        layout.addWidget(self.chooseSzin,    c,1) # y, x
        c+=1
        layout.addWidget(labelWater,    c,0) # y, x
        layout.addWidget(self.chooseWater,    c,1) # y, x
        c+=1
        layout.addWidget(self.degased,    c,0) # y, x
        c+=1
        #layout.addWidget(labelDistance,    c,0) # y, x
        #layout.addWidget(self.chooseDistance,    c,1) # y, x
        #c+=1
        layout.addWidget(self.led,    c,0) # y, x
        
        c+=1
        wrapperLayout.addLayout(grid)
        wrapperLayout.addStretch()


    def enable(self):
        '''
        read all chosen settings
        '''
        self.daq.led=self.led.isChecked()   
        self.daq.source = str(self.chooseSource.currentText())
        self.daq.pmt = int(str(self.choosePMT.currentText()))
        self.daq.szint = str(self.chooseSzin.currentText())
        self.daq.water = str(self.chooseWater.currentText())
        #self.daq.dist = str(self.chooseDistance.text())
        self.daq.degased = self.degased.isChecked()
        
        self.settings.saveSettings()

##########################################################################################
