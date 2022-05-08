# the picoscope functions I need, based on ps6000.py which is itself based on picobase

from __future__ import print_function
from __future__ import absolute_import


try:
    from PyQt4.QtCore import QThread
except ImportError as e:
    from PyQt5.QtCore import QThread

import traceback, os,inspect
#from . import ps6000
from .picoscope import picoscope
from .log import log
import time, sys
import numpy as np
import subprocess, psutil


##########################################################################################

MINIMALLOOPDURATION=1000 # milliseconds

class myPicoScope(QThread):
    '''
    the daq should run independently of the gui in background
    therefore it is started as a new thread
    '''

    def __init__(self, log,hygro=None,directory="./", connect=True):
        '''
        initialize and prepare
        '''
        QThread.__init__(self)

        self.log=log
        self.log.info("Initalize PicoScope class")

        self._directory=directory

        self.ps=None
        self._connect=connect
        
        self.hygro=hygro
        

        self.setDefault() # only pre-set not really set on the device
        self.out=None

    def open(self):
        '''
        start the connection to the device
        if connect = False a fake device modus is started
        '''

        
        self.log.info("Open PicoScope (%s) " % str(self._connect))
        try:
            #self.ps = ps6000.PS6000(connect=self._connect)
            self.ps=picoscope()
            if self._connect:
                self.ps.open()
                self.log.info("Found the following picoscope:")
                s=self.ps.getAllUnitInfo()
                self.log.info(s)
            else:
                self.log.info("Test device only")
            return True
        except Exception as e:
            if "image not found" in str(e):
                self.log.error( "ERROR: Libraries not found. Please export the path")
                print("$ export DYLD_FALLBACK_LIBRARY_PATH=/Applications/PicoScope6.app/Contents/Resources/lib/\n")
            elif "PICO_NOT_FOUND" in str(e): 
                self.log.error("Couldn't find Picoscope. Is it attached? If not start with option -t. ")
            else:
                print (traceback.print_exc())
                self.log.error(str(traceback.print_exc()))
            return False
        return True

    def close(self):
        if self._connect:
            self.ps.close()
            self.ps=None
        self.log.info("Picoscope closed. Good night!")

    def __del__(self):
        self.wait()

    def setDefault(self):
        '''
        only required at the first start of this app
        but: nice list of all used variables
        warning: some might be deprecated / not used any more
        '''
        self.amplitudes=[]
        self.blocktimes=[]
        self.rate=[]
        self.channelB=[]
        self.channelC=[]
        self.channelD=[]
        self.indices=[]
        self.areas=[]
        self.temperatures=[]
        self.cpu=[]
        
        #################
        
        #self.measurementrunning=False
        self.triggerenabled=False
        #self.measurementenabled=False

        self._threadIsStopped=False

        self.loopduration=MINIMALLOOPDURATION
        
        # set defaults for all values required in the interactive mode
        self.coupling={"A":"DC", "B":"DC", "C":"DC", "D":"DC"}
        self.voltagerange={"A":0.05, "B":0.05, "C":0.05, "D":0.05}
        self.offset={"A":0., "B":0., "C":0., "D":0.}
        self.channelEnabled={"A":True, "B":False, "C":False, "D":False}
        # set trigger
        self.triggerchannel="A"
        self.triggervoltage=0.
        self.triggermode="Falling"
        self.triggerdelay=0
        self.triggertimeout=10000
        self.triggerenabled=False
        # set rapid block measurements
        self.mchannel="A"
        self.numberofblocks=0
        self.samplefreq=1e9
        self.nosamples=300
        self.nopretriggersamples=0.1
        self.measurementduration=0 # min
        self.captures=300
        self.sleeptime=0.001
        self.nowaveforms=3
        self.simpleAmp=True
        #self.getTriggerInfo=False
        # temperature measuremnt
        self.measureTemp=False
        # signal generator
        self.sigoffsetVoltage=0
        self.pkToPk=2 # microvolts
        self.waveType="Square"
        self.sigfrequency=1E3
        self.sigGenEnabled=False
        #
        self.doCalcFFT=False
        self.measureCPU=False
        self.showArea=False
        self.plotMeas=False
        # 
        self.saveMeasurement=False
        #
        self.led=False
        self.source = "None"
        self.pmt = 6
        self.szint = "None"
        self.dist = ""
        self.water="None"
        self.degased=False
        #
        self.saveHVWfm=False
        self.calcCtimes=False
        self.selectNoise=False
        self.calcInvAmps=False
        self.calcCrosses=False
        self.calcDTimes=False
        #
        # display
        self.xticks=5
        # TODO link all defaults with gui!!

##########################################################################################

    def setChannel(self, channel, disable=False):
    
        '''
        wrapper function to manage the channel properties of the picoscope
        '''

        if disable:
            self.channelEnabled[channel]=False
        else:
            self.channelEnabled[channel]=True

        if self._connect:

            VRange=self.ps.setChannel(channel=channel,
                                      coupling=self.coupling[channel],
                                      VRange=self.voltagerange[channel],
                                      VOffset=self.offset[channel],
                                      enabled=self.channelEnabled[channel],
                                      )
            self.voltagerange[channel]=VRange
        self.out.info("Channel %s, Mode %s, Voltage %fV, Offset %fV, Enabled %d" % (channel,
                                                                        self.coupling[channel],
                                                                        self.voltagerange[channel],
                                                                        self.offset[channel],
                                                                        int(self.channelEnabled[channel]),
                                                                        ))

##########################################################################################
    def setTrigger(self, disable=False):
    
        '''
        wrapper function to manage the trigger settings of the picoscope
        the trigger works on 1 channel
        There are some thresholds below which the trigger does not function well dependent
        on the channel range setting
        '''

        if disable:
            self.triggerenabled=False
        else:
            self.triggerenabled=True

        if self._connect:
        
            # ensure channel is enabled
            self.setChannel(self.triggerchannel)

            ret=self.ps.setSimpleTrigger(self.triggerchannel,
                                    threshold_V=self.triggervoltage,
                                    direction=self.triggermode,
                                    delay=self.triggerdelay,
                                    timeout_ms=self.triggertimeout,
                                    enabled=self.triggerenabled)
        else:
            ret=True

        if ret:
            self.out.info("Trigger: Channel %s, " %  (self.triggerchannel) +\
                          "Voltage %fV, " % (self.triggervoltage) +\
                          "Shape %s, "% (self.triggermode) +\
                          "Delay %f, "% (self.triggerdelay) +\
                          "Timeout %f, "% (self.triggertimeout) +\
                          "enabled %d" % (self.triggerenabled))
        else:
            self.out.error("WARNING: Setting trigger failed!")


##########################################################################################
    def setSignalGenerator(self, disable=False):
    
        '''
        alpha version
        not in use currently
        not shown in GUI
        '''

        if disable:
            sigoffsetVoltage=0
            pkToPk=0
            self.siggenenabled=False
        else:
            sigoffsetVoltage=self.sigoffsetVoltage
            pkToPk=self.pkToPk
            self.siggenenabled=True

        waveType=self.waveType
        frequency=self.sigfrequency
        shots=1
        triggerType="Rising"
        triggerSource="None"
            
        if self._connect:
            self.ps.setSigGenBuiltInSimple(
                                   offsetVoltage=sigoffsetVoltage,
                                   pkToPk=pkToPk,
                                   waveType=waveType,
                                   frequency=frequency,
                                   shots=shots,
                                   triggerType=triggerType,
                                   triggerSource=triggerSource
                                   )

        else:
            pass
            # TODO
        self.log.info(r"Signal Generator: Offset: %d $\mu V$"%sigoffsetVoltage+\
                        r"PeakToPeak: %d $\mu V$" % pkToPk +\
                        "WaveType: %s" % waveType+\
                        "Frequency: %e Hz" % frequency +\
                        "Enabled: %d" % self.siggenenabled
                        )

##########################################################################################

    def run(self):
        '''
        wrapper function for startRapidMeasurement()
        it requires to have this name, for the parallelization of the GUI and the 
        picoscope readout
        logging in special out file instead of log file!
        '''
        self.log.debug("Daq run")
        self.startRapidMeasurement()


    def startRapidMeasurement(self):
        '''
        set up, control, trigger readout within the rapid mode of PicoScope
        '''
        self.log.debug("Daq startRapidMeasurement")
        
        # custom log per run
        self.starttime=time.time() # required to time the measurement duration
        st=self.formatTimeforLog(self.starttime)
        self._directory=self._directory.replace("\r", "")
        self.saveDirectory=self._directory+"/"+str(st)+"/"
        if not os.path.exists(self.saveDirectory):
            os.mkdir(self.saveDirectory)
        self.out=log(save=True, level="debug", directory=self.saveDirectory, end="out")
        self.out.info("Main log file: %s"%self.log.filename)
        self.out.debug("Daq startRapidMeasurement")

        # --------------------
        # preparation
        
        # ensure at least one channel is enabled
        oneChannelSet=False
        for a in ["A", "B", "C", "D"]:
            if self.channelEnabled[a]==True:
                oneChannelSet=True
        if not oneChannelSet:
            self.out.error("At least one Channel must be set for the measurement to start")
            return
        # enable required channels
        print (self._connect)
        if self._connect:
            self.setChannel("A", disable=(not self.channelEnabled["A"]))
            self.setChannel("B", disable=(not self.channelEnabled["B"]))
            self.setChannel("C", disable=(not self.channelEnabled["C"]))
            self.setChannel("D", disable=(not self.channelEnabled["D"]))
        
        # enable triggering
        if self._connect:
            self.setTrigger()

        # configure measurement variables
        if self._connect:
            # TODO choose yourself, currently hard coded
            self.res = self.ps.setSamplingFrequency(self.samplefreq, self.nosamples) # sample frequency, number of samples
        else:
            self.res=[1250000000,3000000000]
        self.sampleRate = self.res[0]
        self.interval=1./self.res[0]
        if self._connect:
            self.samples_per_segment = self.ps.memorySegments(self.captures) # number of memory segments must be equal or larger than self.captures!
            if self.samples_per_segment<self.nosamples:
                self.out.error( "Reduce sample number per capture to maximum number")
                self.nosamples=self.samples_per_segment
        else:
            self.samples_per_segment=0
        self.blockduration=self.interval*self.nosamples*self.captures
        if self._connect:
            self.ps.setNoOfCaptures(self.captures)
        if self.simpleAmp==False:
            self.nopretriggersamples=0.0
        else:
            self.nopretriggersamples=0.1

        # --------------------
        # log settings
        self.out.info("Rapid Block Mode set with")
        self.out.info("\tNo of Blocks: %d" % (self.numberofblocks))
        self.out.info("\tMeasurement time: %f" % (self.measurementduration))
        self.out.info("\tSampling  %f MHz\n\tInterval %fns"%(self.res[0]/1E6, self.interval*1e9))
        self.out.info("\tSamples %d samples (Max: %d)"%(self.nosamples,self.samples_per_segment))
        self.out.info("\tCapture duration %fns (Max: %ens)"%(self.interval*self.nosamples*1e9, self.res[1]*1./self.res[0]*1e9 ))
        self.out.info("\tCaptures %d"% self.captures)
        self.out.info("\tBlock duration w/o deadtime %ens" % (self.blockduration*1.e9))
        self.out.info("\tPretrigger Sample Fraction %f"% self.nopretriggersamples)
        self.out.info("\tSleep Time %fs"% self.sleeptime)
        self.out.info("\tMaximal Signal rate %e Hz"%(self.captures/(self.blockduration)))
        self.out.info("\tSimpleAmp %d"%int(self.simpleAmp))
        self.out.info("\tStarttime %s"%(str(st)))
        

        # --------------------
        # loop
        
        # set variables which are collected / adjusted in the loop
        
        self.startexecutiontime=time.time() # required to time the measurement duration       

        self.loopduration=MINIMALLOOPDURATION
        self.noSaves=0 # has to be reset when startexecutiontime is reset
        self.measurementtime=[] # required to calculate the rate
        self.blocktimes=[] # times for datas (will be saved)
        self.amplitudes=[] # amplitudes to be saved
        self.waveforms=[]
        self.channelB=[]
        self.channelC=[]
        if self.selectNoise: 
            self.selectedWaveforms=[]
            self.calcInvAmps=True
            self.calcCrosses=True
        if self.calcInvAmps: 
            self.invAmps=[]
        self.HVWfm=[]
        if self.calcCrosses:
            self.crosses=[]
        self.HVstd=[]
        self.xfreq=[]
        self.ctimes=[]
        # noise
        self.noiseAmps=[]
        #self.noiseWfm=[]
        self.noiseFreq=[]
        #
        if self.doCalcFFT: self.frequencies=[]
        self.areas=[]
        #self.areas2=[]
        self.indices=[]
        self.rate=[] # rates to be saved
        endBlock=time.time() # required for the first loop
        self.lastSaved=endBlock
        #
        self.lastTempSaved=endBlock
        self.temperatures=[]
        #
        self.lastCPUSaved=endBlock
        self.cpu=[]
        self.absTimes=[]
        if self.calcDTimes: self.dtimes=[]
        i=0 # block nbr

        while not self._threadIsStopped:

            # info about loop progress:
            if self.numberofblocks!=0:
                self.progress=float(i)/(self.numberofblocks)*100
                sys.stdout.write("\r \t %.2f %%" % (self.progress) ); sys.stdout.flush()
            elif self.measurementduration!=0:
                self.progress=float(endBlock-self.startexecutiontime)/(self.measurementduration*60)*100
                sys.stdout.write("\r \t %.2f %%" % (self.progress) ); sys.stdout.flush()
            else:
                # since the measurement is reset every hour use this value for the progress bar
                self.progress=float(endBlock-self.startexecutiontime)/(60*60)*100
                sys.stdout.write("\r \t %.2f %%" % (self.progress) ); sys.stdout.flush()

            if i>0:
                # adjust to a more useful value matching the actual execution duration
                self.loopduration=max(MINIMALLOOPDURATION,(time.time()-startBlock)*2*1000)            

            # block
            startBlock=time.time() # record measurement time -> needs to be directly before the block
            if self._connect:
                self.ps.runBlock(pretrig=self.nopretriggersamples)
                #print ("run")
                while(self.ps.isReady() == False):
                    time.sleep(self.sleeptime)
            else:
                # produce fake data
                # TODO
                #filenbr=np.random.randint(1,11)
                #rawdata=np.loadtxt("./code/fakedata/%d.txt" % filenbr)
                #rawdata=rawdata.flatten()
                #dataraw=[]

                #l=max(1,len(rawdata)-self.nosamples-1)
                #for c in range(self.captures):
                #    startwaveform=np.random.randint(0,l)
                #    waveform=rawdata[startwaveform:(startwaveform+self.nosamples)]
                #    dataraw.append(waveform)
                #data=np.array(dataraw)
                pass
                time.sleep(0.5)
            endBlock=time.time() # record measurement time -> needs to be directly after the block
            self.measurementtime.append(endBlock-startBlock) # measurement duration of this block
            
            # --------------------
            
            if self._connect:
                # get data from enabled channels                
                
                dataV=self.ps.getDataVBulk()
                data=dataV[0]
                dataB=dataV[1]
                dataC=dataV[2]
                dataD=dataV[3]

                
            ############################################################
            # analyse data
            
            #print ("Analyse")
            
            if self.channelEnabled["A"]==True and self._connect:
                self.blocktimes.append(endBlock-self.startexecutiontime)

                
                # calc amplitude and get some waveforms
                amps, freq, invAmps =self.amplitudeFromCaptures(data, self.simpleAmp)
                self.amplitudes.append(np.array(amps))
                if self.calcInvAmps: self.invAmps.append(np.array(invAmps))
                signals=amps
                
                # prepare waveforms for saving
                rand=np.random.randint(len(data), size=self.nowaveforms)
                wfms=data[rand]
                self.savedCaptures=wfms
                self.waveforms.extend(wfms)
                
                # save fft
                if self.doCalcFFT: self.frequencies.append(freq)
                
                # calc area
                ars=self.areaFromCaptures(data, self.simpleAmp)
                self.areas.append(np.array(ars))
                #self.areas2.append(np.array(ars2))
                
                # calc rate
                self.rate.append(float(len(signals))/max((endBlock-startBlock),0.001))
                self.absTimes.append((endBlock-startBlock))
                
                if self.calcCrosses:
                    crosses=self.thresholdCrosses( data)
                    self.crosses.append(crosses)
                    
                if self.calcDTimes:
                    self.dtimes.append(self.getDtimes(data))
                                    
                if self.selectNoise:
                    # special code to find noise sources
                    amps=(-np.array(amps)*1000)
                    areas=(-np.array(ars)*1000*1e9)
                    invAmps=(-np.array(invAmps)*1000) 

                    cut1=amps>10
                    cut2=amps<50
                    cut3=amps<areas*(40./300)
                    cut4=invAmps<1
                    cut5=crosses<2
                
                    cut=cut1 & cut2
                    cut=cut & cut3
                    cut=cut & cut4
                    cut=cut & cut5
                
                    selectedWaveforms=data[cut]
                    if len(selectedWaveforms)>self.nowaveforms:
                        rand=np.random.randint(len(selectedWaveforms), size=self.nowaveforms)
                        selectedWaveforms=selectedWaveforms[rand]
                    
                    self.selectedWaveforms.extend(selectedWaveforms)
                
            ############################################################
            
            if self.channelEnabled["D"]==True and self._connect:
                # calc amplitude and get some waveforms
                amps, freq, invAmp=self.amplitudeFromCaptures(dataD, noise=True)
                self.noiseAmps.append(np.array(amps))
                #self.noiseWfm.extend(savedCaptures)
                #self.savedNoise=savedCaptures
                self.noiseFreq.append(freq)

                # prepare waveforms for saving
                rand=np.random.randint(len(dataD), size=self.nowaveforms)
                wfms=dataD[rand]
                self.savedNoise=wfms
                
            ############################################################

            if self.channelEnabled["C"]==True and self._connect:
                self.channelC.append(np.mean(dataC))
                
            ############################################################

            if self.channelEnabled["B"]==True and self._connect:
            
                hv, std=self.getHVMean(dataB)
                
                self.channelB.append(hv)
                self.HVstd.append(std)
                
                if self.saveHVWfm==True:
                    rand=np.random.randint(len(dataB), size=self.nowaveforms)
                    HVWfm=dataB[rand]
                    self.HVWfm.extend(HVWfm)
                #print( np.mean(dataB))
                
            ############################################################
                
            if self.measureTemp and endBlock-self.lastTempSaved > (10) and self._connect and self.hygro!=None:

                try:
                    a=[endBlock-self.startexecutiontime]
                    t=self.hygro.readDevice()
                    a.extend(list(t))
                    #self.out.debug("Temperatures measured after %f seconds: %f %f %f %f" % \
                    #(a[0], a[1], a[2], a[3], a[4]))
                    self.temperatures.append(np.array(a))
                    self.lastTempSaved=endBlock
                except Exception as e:
                    print (traceback.print_exc())
                    self.out.error("Cannot read temperature %s"%e)
                # check timing precision
                if self.calcCtimes:
                    ctimes=[]
                    #self.out.debug("Check timing precision")
                    for i in range(50):
                        startctime=time.time()
                        time.sleep(self.sleeptime)
                        endctime=time.time()
                        ctimes.append(endctime-startctime)
                    self.ctimes.append(np.array(ctimes))
                
            ############################################################
            if self.measureCPU and endBlock-self.lastCPUSaved > (10) and self._connect:
                a=[endBlock-self.startexecutiontime]
                a.append(psutil.virtual_memory().percent)
                a.extend(list(psutil.cpu_percent(percpu=True)))
                self.cpu.append(np.array(a))
                self.lastCPUSaved=endBlock
            
            ############################################################
            # save stuff after one hour
            #print("end")
            if endBlock-self.lastSaved > (60*60) and self._connect:
                self.out.info("Save data after %f seconds" % (endBlock-self.startexecutiontime))
                self.saveAll()
                self.lastSaved=endBlock
                self.saveMeasurement=True
                
            
                
            ############################################################
            # stop the loop:
            i+=1
            if self.numberofblocks >0 and i>=self.numberofblocks:
                self.saveAll()
                self.lastSaved=endBlock
                self.saveMeasurement=True
                break
            elif self.measurementduration!=0 and ((self.measurementduration*60)<(endBlock-self.startexecutiontime)):
                self.saveAll()
                self.lastSaved=endBlock
                self.saveMeasurement=True
                break
        ############################################################
        # end loop
        

        self.out.info("Measurement duration netto: %.2e sec" % (sum(self.measurementtime)))
        self.out.info("Mean measurement time per block: %.2e sec" % (sum(self.measurementtime)/i))
        recordedTimePerBlock=self.nosamples * self.captures*self.interval # seconds
        noRecordPerBlock=(sum(self.measurementtime)/i)-recordedTimePerBlock
        if self.captures>1:
            noTriggerTimeBetweenCapture=noRecordPerBlock/(self.captures-1)
        else:
            noTriggerTimeBetweenCapture=0
        self.out.info("Mean time without trigger + dead time between captures: %.2e ns" % (noTriggerTimeBetweenCapture*1.e9))

        self.loopduration=MINIMALLOOPDURATION # reset
        
        # saving the run is handled in gui.stopMeasurement
        

##########################################################################################
    def getHVMean(self, data):
        hv=[]
        std=[]
        for capture in data:
            hv.append(np.mean(capture))
            std.append(np.std(capture))
        return np.array(hv), np.array(std)
                
                
    def thresholdCrosses(self, data):
        crosses=[]
    
        for waveform in data:
            thresh=waveform>=self.triggervoltage
            step=waveform<self.triggervoltage
            cut=thresh[1:]&step[:-1]
            crosses.append(sum(cut))
        return np.array(crosses)
        
    def getDtimes(self, data):
        timedifferences=[]
        for waveform in data:
            belowTrigger= waveform < self.triggervoltage
            belowTrigger=belowTrigger[1:] # reduce size to match following arrays
            if sum(belowTrigger)>0:
                slope=waveform[1:]-waveform[:-1]
                negativeSlope=slope<0
                slopeAndBelowTrigger=(belowTrigger & negativeSlope)
                # clean in a way that only one True per pulse is left
                single=slopeAndBelowTrigger[:-1] & np.invert( slopeAndBelowTrigger[1:])
                t=np.arange(0,len(single),1)*self.interval
                times=t[single]
                dtimes=times-times[0]
                timedifferences.extend(list(dtimes))
        return np.array(timedifferences)
    
    def amplitudeFromCaptures(self, data, simpleAmp=True, noise=False, negativePulse=True):
    
        if noise:
            simpleAmp=True
        
        #savedCaptures=[]
        amplitudes=[]
        ind=[]
        freq=[]
        invAmps=[]
        
        # get only one amplitude per capture
        if simpleAmp:
            for waveform in data:
                if negativePulse:
                    amplitudes.append(np.min(waveform))
                    if not noise and self.calcInvAmps:
                        invAmps.append(np.max(waveform))
                else:
                    amplitudes.append(np.max(waveform)) # change min / max for negative / positive pulses
                    if not noise and self.calcInvAmps:
                        invAmps.append(np.min(waveform))
                if self.doCalcFFT or noise:
                    freq=self.calcFFT(waveform)
                #if len(savedCaptures)<self.nowaveforms:
                #        savedCaptures.append(np.array(waveform))
        ###### NOT TESTED FOR A LONG TIME!!! 
        else: 
            # get several amplitudes per capture
            for capture in data:
                indices=np.arange(0,len(capture),1)
                underthresold=capture<self.triggervoltage
                indices=indices[underthresold]
                skipuntil=0
                for i in indices:
                    if i>skipuntil:
                        waveform=capture[max(0,i-50):min(i+50,len(capture)-1)]
                        ind.append(i)
                        if negativePulse:
                            amplitudes.append(np.min(waveform))
                        else:
                            amplitudes.append(np.max(waveform)) # change min / max for negative / positive pulses
                        if self.doCalcFFT or noise:
                            freq=self.calcFFT(waveform)
                        #if len(savedCaptures)<self.nowaveforms:
                        #    waveform=capture[max(0,i-100):min(i+300,len(capture)-1)]
                        #    savedCaptures.append(np.array(waveform))
                        skipuntil=i+500 # TODO
                    else:
                        continue
            self.indices.append(np.array(ind))
            # TODO: indices as return and not directly saved
        #########
        
        return amplitudes, freq, invAmps

    def areaFromCaptures(self, data, simpleAmp=True, negativePulse=True):
        # get only one amplitude per capture
        areas=[]
        ind=[]
        areas2=[]
        
        if self.triggerchannel=="A":

            if simpleAmp:
                # find baseline
                i_debug=0
                for waveform in data:
                    ### old
                    if 1:
                        #baseline=capture[0: int(len(capture)*0.05)]
                        #baseline=np.median(baseline)
                        baseline=0
                        indices=np.arange(0,len(waveform),1)
                        if negativePulse:
                            underthresold=waveform<self.triggervoltage
                        else:
                            underthresold=waveform>self.triggervoltage # change from < to > for negative / positive pulses
                        indices=indices[underthresold]
                        area=waveform[underthresold]-baseline
                        area*=self.interval
                        areas.append(sum(area))
                        
                        # V3
                        #diff=(waveform[1:]-waveform[:-1])
                        #intg=np.cumsum(diff)
                        #area=intg-baseline
                        #area*=self.interval
                        #areas2.append(sum(area))
                    else:
                        # this version gives strange spe peak, but nice pedastal, previous version seems much more stable
                        # spoke with John from Mainz about this algo
                        #preTriggerSamples=int(len(waveform)*0.09)
                        #baselineSamples=waveform[0:preTriggerSamples]
                        #baseline=np.median(baselineSamples)
                        baseline=0
                        #if i_debug<5: print("Pretrigger",preTriggerSamples, baseline, baselineSamples)
                        
                        area=waveform[0:int(len(waveform)*0.5)]-baseline # any sinus noise should add up to zero
                        area*=self.interval
                        area=sum(area)
                        if i_debug<5: print("area", area)
                        areas.append(area)


                        i_debug+=1
                    
            else:
                self.out.error("SimpleAmp = False is not implemented for Areas!")
                areas=[0]
        else:
            if simpleAmp:
                # find baseline
                for waveform in data:
                    # V1:
                    #baseline=capture[0: int(len(capture)*0.05)]
                    #baseline=np.median(baseline)
                    #area=waveform-baseline
                    # V2:
                    baseline=0
                    area=waveform-baseline
                    # V3:
                    #baseline=0
                    #diff=(waveform[1:]-waveform[:-1])
                    #intg=np.cumsum(diff)
                    #area=intg-baseline
                    # V4: 
                    # nur von Triggerzeitpunkt bis unter 10% runter integrieren, vorher V3 anwenden
                    # V5: 
                    # obiges ggf auch fuer TriggerchannelA? Ja weil sonst gilt diese Kalibration fuer oben ja nicht!!!
                    
                    ###### common
                    
                    area*=self.interval
                    areas.append(sum(area))
            else:
                self.out.error("SimpleAmp = False is not implemented for Areas!")
                areas=[0]   
        return np.array(areas)
        
        
    def calcFFT(self, waveform):
        # fft
        Y = np.fft.fft(waveform)
        # correct for mirroring at the end
        N = len(Y)/2+1
        # leakage effect
        hann = np.hanning(len(waveform))
        Yhann = np.fft.fft(hann*waveform)
        freq=2*np.abs(Yhann[:N])/N
        
        
        if self.xfreq==[]:
            # x values
            dt = 500 * self.interval
            fa = 1.0/dt # scan frequency
            X = np.linspace(0, fa/2, N, endpoint=True)
            self.xfreq=X
        return np.array(freq)
##########################################################################################
    def monitorToHV(self,monitor):
        return 3000.*monitor/5.
        
    def suggestedMinVoltage(self):
        voltagerange=self.voltagerange[self.triggerchannel]
        try:
            return self.ps.MINTRIGGER[voltagerange]
        except Exception as e: 
            return -float(voltagerange)*1000/10
        
    def maxOffset(self, channel):
        voltagerange=self.voltagerange[channel]
        coupling=self.coupling[channel]
        self.log.info("%s %f %s %d %d %d" % (channel, voltagerange, 
                                            coupling, self.ps.MAXOFFSETDC[voltagerange], 
                                            self.ps.MAXOFFSETAC[voltagerange], coupling=="DC50"))
        if coupling=="DC50":
            return self.ps.MAXOFFSETDC[voltagerange]
        else:
            return self.ps.MAXOFFSETAC[voltagerange]
    
    def plotMeasurement(self):
        from .measurement import Measurement
        
        t=self.formatTimeforLog(self.starttime)
        
        meas=Measurement(starttime=t,  
                  directory=self.saveDirectory,
                  label=t,
                  log=self.out,
                  tag="_%03d"%int(self.noSaves),
                  starttimelinux=self.starttime,
                  )
                  
        meas.plotVetoCheck(
                  xlabeltime=0.5,
                  figname=str(t)+"_%03d"%int(self.noSaves),
                  dir=self.saveDirectory,
                  enabledChannels=self.channelEnabled,
                  measTemp=self.measureTemp,
                  measCPU=  self.measureCPU,
                  )
                  
        #meas.areaSpectrum(figname=t,
        #             borders=(-self.voltagerange["A"]*1000+self.offset["A"]*1000,
        #                     self.voltagerange["A"]*1000+self.offset["A"]*1000),
        #             bins=128,
        #             dir=directory,
        #            )    
        meas.amplSpectrum(figname=str(t)+"_%03d"%int(self.noSaves),
                     borders=(-self.voltagerange["A"]*1000+self.offset["A"]*1000,
                             self.voltagerange["A"]*1000+self.offset["A"]*1000),
                     bins=128,
                     dir=self.saveDirectory,
                    )

    def saveAll(self):
    
        self.save("absTimes", self.absTimes); self.absTimes=[]
        self.save("times", self.blocktimes); self.blocktimes=[]
        if self.calcCtimes: self.save("ctimes",self.ctimes); self.ctimes=[]
        if self.channelEnabled["A"]:
            try:
                self.save("amp", self.amplitudes); self.amplitudes=[]
                self.save("area", self.areas); self.areas=[]
                #self.save("area2", self.areas2); self.areas2=[]
                self.save("rate", self.rate); self.rate=[]
                self.save("wfm", self.waveforms); self.waveforms=[]
                if self.calcDTimes: self.save("dtimes", self.dtimes); self.dtimes=[]
                if self.selectNoise: self.save("swfm", self.selectedWaveforms); self.selectedWaveforms=[]
                if self.calcInvAmps: self.save("invA", self.invAmps); self.invAmps=[]
                if self.calcCrosses: self.save("crosses", self.crosses); self.crosses=[]
            except Exception as e:
                self.out.error("Couldnt save channel A")
                self.out.error(str(traceback.print_exc()))
        if self.channelEnabled["D"]:
            try:
                self.save("namp", self.noiseAmps); self.noiseAmps=[]
                #self.save("nwfm", self.noiseWfm); self.noiseWfm=[]
                if self.doCalcFFT:
                    freq=[self.xfreq]
                    for f in self.frequencies:
                        freq.append(np.array(f))
                    freq=np.array(freq)
                    self.save("nfreq", freq)
            except Exception as e:
                self.out.error("Couldnt save channel D")
                self.out.error(str(traceback.print_exc()))
        if self.measureTemp: 
            self.save("temp", self.temperatures); self.temperatures=[]
        if self.measureCPU:
            self.save("cpu", self.cpu); self.cpu=[]
        if self.doCalcFFT:
            try:
                freq=[self.xfreq]
                for f in self.frequencies:
                    freq.append(np.array(f))
                freq=np.array(freq)
                self.save("fft", freq)
                self.frequencies=[]
            except Exception as e:
                self.out.error("Couldnt save channel A frequencies")
                self.out.error(str(traceback.print_exc()))
        if self.channelEnabled["C"]:
            self.save("chC", self.channelC); self.channelC=[]
        if self.channelEnabled["B"]:
            try:
                self.channelB=self.monitorToHV(np.array(self.channelB))
                self.save("HV", self.channelB); self.channelB=[]
                self.save("HVstd", self.HVstd); self.HVstd=[]
            except Exception as e:
                self.out.error("Couldnt save channel B")
                self.out.error(str(traceback.print_exc()))
            if self.saveHVWfm==True:
                self.save("HVwfm", self.HVWfm); self.HVWfm=[]
        if not self.simpleAmp: 
            self.save("ind", self.indices); self.indices=[]
            
        try:
            if self.plotMeas: 
                self.plotMeasurement()
                self.log.info("Plotted the Measurement")
        except Exception as e:
            self.out.error("Plotting Measurement didnt work: %s" % e)
            self.out.error(str(traceback.print_exc()))
        
        self.noSaves+=1
        self.xfreq=[]
                    
    def formatTimeforLog(self, t): # input given by time.time()
        s=time.localtime(float(t))
        return "%4d_%02d_%02d_%02d_%02d_%02d" % (s.tm_year,s.tm_mon,s.tm_mday,s.tm_hour,s.tm_min,s.tm_sec)


    def save(self, name, values):
        t=self.formatTimeforLog(self.starttime)
        #self._directory=self._directory.replace("\r", "")
        #directory=self._directory+"/"+str(t)+"/"
        if not os.path.exists(self.saveDirectory):
            os.mkdir(self.saveDirectory)
        filename="%s/%s_%03d_%s" % (self.saveDirectory, str(t), int(self.noSaves), str(name))
        self.out.info("Save %s to file %s"%(name, filename))
        #np.savetxt(filename, values)
        np.save(filename, values)
        return True
        
        '''
        currently saving:
        - absTimes: absolute times of new runs
        - amp: amplitudes of channel a
        - area: area of channel a
        - cpu: cpu cores and memory information
        - HV: HV mean value per run
        - HVstd: HV std value per run
        - invA
        
        TODO: combine HV / HVstd
        '''
        
    def deleteDir(self):
        self.log.info("Deleting directory %s" % self.saveDirectory)

        try:
            if os.path.isfile(self.out.filename):
                os.remove(self.out.filename)
            if os.path.exists(self.saveDirectory):
                os.rmdir(self.saveDirectory)
        except Exception as e:
            if os.path.exists(self.saveDirectory):
                self.log.error("Deleting of directory %s didn't work." % os.path.exists(self.saveDirectory))
##########################################################################################

    def writeToDatenbank(self):
        directory="./code/"
        filename=directory+"Datenbank.csv"
        if not os.path.isfile(filename) :
            first=True
        else:
            first=False
        
        if not first:
            datenbank=open(filename, "r")
            for line in datenbank:
                firstline=line
            datenbank.close()
        
        datenbank=open(filename, "a")
        ###
        if first: firstline="Starttime; "
        t=self.formatTimeforLog(self.starttime)
        settings="%s; " % t
        ss=[]
        dyc={}
        sfile=open("./code/settings.cfg")
        for line in sfile:
            firstword=line.split(" ")[0]
            if "_"!=firstword[0] and firstword not in ["loopduration", "saveMeasurement"]:
                ss.append(firstword)
                dyc[firstword]=line.split(" ")[1].replace("\n", "").replace("\r", "")
        sfile.close()
        ss=sorted(ss)
        
        if first: 
            for s in ss:
                firstline+=s+"; "
                settings+=dyc[s]+"; "
        else:
            for s in firstline.replace("\n", "").replace("\r", "").split("; "):
                if s=="": continue
                if s in dyc:
                    settings+=dyc[s]+"; "
                else:
                    self.log.error("Didnt found in Firstline of database .%s."% s)
                    settings+="-; "
            for s in ss:
                if s=="": continue
                if s not in firstline.replace("\n", "").replace("\r", "").split("; "):
                    settings+=dyc[s]+"; "
            
        
        
        if first: firstline+="LogMessages"
        logfile=open(self.out.filename)
        for line in logfile:
            if "LMSG:" in line:
                line=line.split("LMSG:")[1].replace("\n", "")
                settings+=line+", "
        #print (settings)
        logfile.close()
        
        settings+="\n"
        if first: firstline+="\n"
        self.log.debug(firstline)
        self.log.debug(settings)
        
        ###
        if first:  datenbank.write("%s\n" % (firstline))
        datenbank.write("%s\n" % (settings))
        datenbank.close()
        
        

        
        
        
        
        
        
