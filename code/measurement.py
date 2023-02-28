from glob import glob
import numpy as np
import time, datetime, traceback

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

DEBUG=False

def gain(x):
   return 4.3820810269624345e-9*x**(0.50531132059975381*10)

class Measurement:

    def readDataFromFile(self, files):
        fullarray=[]
        i=0
        for f in files:
                try:
                    filearray=np.load(f)
                    for array in filearray:
                        fullarray.append(np.array(array))
                except IOError as e:
                    self.log.error( "Broken file %s (Seems to be still open)" %f)
                    
                i+=60*60 # one hour in seconds
            #break
        return np.array(fullarray)


    def getMeasurementTime(self):
        f=open(self.logfile)
        i=0
        NettoMeasurementtime_temp=0
        st=time.mktime(datetime.datetime.strptime(self.starttime, "%Y_%m_%d_%H_%M_%S").timetuple())
        for line in f:
            myline=line.replace("\n", "")
            ft=myline.split(":")[0].replace(" ","")
            try:
                ft=time.mktime(datetime.datetime.strptime(ft, "%Y_%m_%d_%H_%M_%S").timetuple())
            except ValueError as e:
                continue
                
            if ft<st:
                continue
                
            words=myline.split(" ")
            if "Measurement duration netto" in myline:
                NettoMeasurementtime_temp=float(words[6])
                self.NettoMeasurementtime=NettoMeasurementtime_temp
                break
            i+=1
        self.log.debug("Measurement time netto %f seconds" %self.NettoMeasurementtime)
        f.close()
        return True

    def findLogFile(self, directory="./", ending=".out"):
        files=glob(directory+"*"+ending)
        files=sorted(files)
        #print("Files:",files)
        st=time.mktime(datetime.datetime.strptime(self.starttime, "%Y_%m_%d_%H_%M_%S").timetuple())
                
        for fyle in files:
            #print "For", fyle
            ft= fyle.split("/")[-1].split(".")[0]
            #print("st ft fyle",self.starttime,ft, fyle)
            #self.log.error("Note: FT=%s"%ft)
            ft=time.mktime(datetime.datetime.strptime(ft, "%Y_%m_%d_%H_%M_%S").timetuple())
            if ft>st:
                #print("break", fyle)
                #print "Found", ft, st, fyle, self.starttime
                break
            logfile=fyle
        try:
            self.logfile=logfile
            self.log.debug("\t\tLogfile %s"%self.logfile)
        except:
            self.log.error("ERROR: Logfile not found")
        
        return self.logfile
    
    def findSettings(self):
        #print "start"
        f=open(self.logfile)
        i=0
        settings=""
        foundend=False
        st=time.mktime(datetime.datetime.strptime(self.starttime, "%Y_%m_%d_%H_%M_%S").timetuple())
        
        for line in f:
            # start
            myline=line.replace("\n", "")
            ft=myline.split(":")[0].replace(" ","")
            try:
                ft=time.mktime(datetime.datetime.strptime(ft, "%Y_%m_%d_%H_%M_%S").timetuple())
            except ValueError as e:
                continue
                
            if ft>st:
                continue
            #print (st, ft, line)
            
            
            if "Save times to file" in myline:
            #    if foundend:
            #        #print "stop2"
            #        break
                settings=""
                
            
            if "Measurement time:" in myline or \
                "Sampling" in myline or \
                "Samples" in myline or \
                "Capture duration" in myline or \
                "Captures" in myline or \
                "Channel" in myline or \
                "Trigger:" in myline:
                text=myline[22:]
                text=text.replace("DEBUG: ","")
                text=text.replace("INFO: ","")
                text=text.replace("MSG: ","")
                text=text.replace("\t","")
                text+="\n"
                settings+=text 
                #print settings
            #if "Measurement duration netto" in myline:
            #    foundend=True
                #print "stop1"
            i+=1
        f.close()
        #print "end"
        return settings

    def findComments(self):
        #print "findComments"
        f=open(self.logfile)
        i=0
        comments=""
        foundend=False
        st=time.mktime(datetime.datetime.strptime(self.starttime, "%Y_%m_%d_%H_%M_%S").timetuple())
        
        for line in f:
            myline=line.replace("\n", "")
            ft=myline.split(":")[0].replace(" ","")
            try:
                ft=time.mktime(datetime.datetime.strptime(ft, "%Y_%m_%d_%H_%M_%S").timetuple())
            except ValueError as e:
                continue
            
            
            if ft<st:
                continue
            #print (st, ">",ft)
            
            if "Rapid Block Mode set with" in myline:
                if foundend:
                    #print "XXX Stop settings 2"
                    break
                comments=""
            if "LMSG:" in myline:
                text=myline#[22:]
                text=text.replace("DEBUG: ","")
                text=text.replace("INFO: ","")
                text=text.replace("LMSG: ","")
                text=text.replace("MSG: ","")
                text+="\n"
                comments+=text
                #print comments
            if "Measurement duration netto" in myline:
                #print "XXX Stop settings 1"
                foundend=True
            i+=1
        f.close()
        #print "End Comments"
        return comments
            
#########################################################################################################

    def __init__(self,
                         starttime,
                         #logfile,
                         label="",
                         directory="./data/",
                         #temp=None,
                         newNumpySave=True,
                         otempmin=False,
                         tempLabels=["1 (Room)", "2", "3", "4"],
                         log=None,
                         tag="",
                         starttimelinux=0,
                ):
        self.log=log
        self.tempLabels=tempLabels
        self.starttime=starttime
        self.label=label
        self.directory=directory
        self.log.info("MEAS: Load Measurement: %s"%self.label)
        self.newNumpySave=newNumpySave
        self.logfile=None

        # find log file
        try:
            #if DEBUG: print "\tSearch log file ..."
            self.findLogFile(directory=self.directory)
        except Exception as e:
            self.log.error("MEAS: Error: Log file not found: %s"%str(e))
            

        # the following is needed to get the measurement time
        if self.logfile!=None:
        
            # find comments
            #if DEBUG: print "\tFind comments ..."
            self.comments=""
            self.comments+=self.findComments()

            self.settings=self.findSettings()
            
            #if DEBUG: print "\tFind netto measurement time ..."
            # find netto measurement time
            try:
                self.getMeasurementTime()
            except:
                self.NettoMeasurementtime=1
                
           



        #if DEBUG: print "\tLoad amplitudes ..."
        files=glob(directory+starttime+tag+"*"+"_amp*") # this should give only one file, thus only data of the last hour
        #if files==[]: print "\t\tError amp"+label,directory+starttime+"*"+"_amp*" 
        #else: 
        #    if DEBUG: print "\t\tFile number:", len(files)
        self.amplitudes=self.readDataFromFile(sorted(files))
        
        #if DEBUG: print "\tLoad noise amplitudes ..."
        files=glob(directory+starttime+tag+"*"+"_namp*")
        #if files==[]: print "\t\tError namp"+label,directory+starttime+"*"+"_namp*" 
        #else: 
        #    if DEBUG: print "\t\tFile number:", len(files)
        self.namplitudes=self.readDataFromFile(sorted(files))
        
        #if DEBUG: print "\tLoad areas ..."
        try:
            files=glob(directory+starttime+tag+"*"+"area.*")
            #if files==[]: print "\t\tError area"+label
            self.areas=self.readDataFromFile(sorted(files))
        except:
            #print "\t\tError loading area"
            pass

        #if DEBUG: print "\tLoad rates ..."
        files=glob(directory+starttime+tag+"*"+"rate*")
        #if DEBUG: print "\t\tLoad from x files:",len(files)
        #if len(files)==0: print "\t\tError rate"+label
        self.rates=self.readDataFromFile(sorted(files))
        
        #if DEBUG: print "\tLoad temps ..."
        files=glob(directory+starttime+tag+"*"+"temp*")
        #if len(files)==0: print "\t\tError temp"+label
        self.temps=self.readDataFromFile(sorted(files))
        
        #if DEBUG: print "\tLoad ChC ..."
        files=glob(directory+starttime+tag+"*"+"chC*")
        #if len(files)==0: print "\t\tError ChC"+label
        self.chC=self.readDataFromFile(sorted(files))
            
        #if DEBUG: print "\tLoad cpu ..."
        files=glob(directory+starttime+tag+"*"+"cpu*")
        self.cpu=self.readDataFromFile(sorted(files))
        
        try:
            #if DEBUG: print "\tLoad HV ..."
            files=glob(directory+starttime+tag+"*"+"HV.*")
            #if len(files)==0: print "\t\tError HV"+label
            self.HVs=self.readDataFromFile(sorted(files))
        except Exception as e:
            print("Couldnt load HV %s"%e)

        #if DEBUG: print "\tLoad times ..."
        files=glob(directory+starttime+tag+"*"+"_times.*")
        #if len(files)==0: print "\t\tError time"+label
        self.times=self.readDataFromFile(sorted(files))
        
        #if DEBUG: print "\tLoad fft ..."
        files=glob(directory+starttime+tag+"*"+"fft*")
        #if len(files)==0: print "\t\tError fft"+label
        self.fft=self.readDataFromFile(sorted(files))
        
        #if DEBUG: print "\tLoad noise fft ..."
        files=glob(directory+starttime+tag+"*"+"nfreq*")
        #if len(files)==0: print "\t\tError nfreq"+label
        self.nfreq=self.readDataFromFile(sorted(files))

        ##################
        
        self.hour=int(self.starttime.split("_")[3])
        mini=int(self.starttime.split("_")[4])
        self.starthourmin=self.hour+float(mini)/60
        self.day=int(self.starttime.split("_")[2])


        # get data
        self.hours=self.times/3600
        self.hours+=self.starthourmin

        if self.temps!=[]:
            self.temptimes=np.array(self.temps[:,0])
            #self.temptimes-=self.temptimes[0]
            self.temptimes/=3600
            self.temptimes+=self.starthourmin
            self.temp1=np.array(self.temps[:,1])
            self.temp2=np.array(self.temps[:,2])
            self.temp3=np.array(self.temps[:,3])
            self.temp4=np.array(self.temps[:,4])

        if self.cpu != []:
            cputime=self.cpu[:,0]
            #cputime-=cputime[0]
            cputime/=3600
            self.cputime=cputime+self.starthourmin
            self.memory=self.cpu[:,1]
            self.cpu1=self.cpu[:,2]
            self.cpu2=self.cpu[:,3]
            try:
                self.cpu3=self.cpu[:,4]
                self.cpu4=self.cpu[:,5]
            except:
                pass
            # the laptop has only 2 cpu kernels
            # the linux desktop has 4 cpu kernels

        if self.HVs!=[]:
            self.gain=gain(np.mean(self.HVs))
        else:
            self.gain=gain(1097)


        # ---------------------------------------------------------
        # HV log            

        self.saveHV=False
        # hv log
        try:
            fyles=glob("/data/obertacke/luminescence/picogui/hv/log/*.csv")
            fyles=sorted(fyles)
            fyle=fyles[-1]
            self.log.debug("Meas: HV: Use file %s"%fyle)
            data=np.loadtxt(fyle, delimiter=",")
            hours=int(tag[1:])
            md=3600 # usual 3600
            hvstart=(hours*md)+starttimelinux
            hvend=((hours+1)*md)+starttimelinux
            self.log.debug("Meas: HV: start-/endtime %d %d hours %d"%(hvstart, hvend, hours))
            self.log.debug("Meas: starttime %s %f"%(starttime,starttimelinux))
            hvtimes=data[:,0]

            if len(hvtimes)==0:
                raise Exception("No HV values in this log")
            
            cut1=hvtimes>hvstart
            cut2=hvtimes<hvend
            cut=cut1&cut2
            self.hvtimes=hvtimes[cut]
            self.hvvalues=data[:,1]
            self.hvvalues=self.hvvalues[cut]

            if len(self.hvtimes)==0:
                raise Exception("No HV values in this time frame")
            else:
                self.log.debug("Meas: %d HV values in this time frame"%len(self.hvtimes))
                
            self.hvtimes-=hvstart
            self.hvtimes/=3600 # first devide than add starthourmin
            self.hvtimes+=self.starthourmin + (float(hours)*md/3600)

            self.saveHV=True
        except Exception as e:
            e2=str(traceback.print_exc())
            self.log.error(e2)
            self.log.error(str(e))
            self.saveHV=False


        # --------------------------------------------------------
        self.saveFW=False
        # fw log
        try:
            fyles=glob("/data/obertacke/luminescence/picogui/filterwheel/log/*.csv")
            fyles=sorted(fyles)
            fyle=fyles[-1]
            self.log.debug("Meas: FW: Use file %s"%fyle)
            data=np.loadtxt(fyle, delimiter=",")
            hours=int(tag[1:])
            md=3600
            fwstart=hours*md+starttimelinux
            fwend=(hours+1)*md+starttimelinux
            self.log.debug("Meas: FW: start-/endtime %d %d hours %d"%(fwstart, fwend, hours))
            self.log.debug("Meas: starttime %s %f"%(starttime,starttimelinux))
            fwtimes=data[:,0]

            if len(fwtimes)==0:
                raise Exception("No Filterwheel values in this log")

            cut1=fwtimes>fwstart
            cut2=fwtimes<fwend
            cut=cut1&cut2
            self.fwtimes=fwtimes[cut]
            self.fwvalues=data[:,1]
            self.fwvalues=self.fwvalues[cut]

            if len(self.fwtimes)==0:
                raise Exception("No Filterwheel values in this time frame")
            else:
                self.log.debug("Meas: %d FW values in this time frame"%len(self.fwtimes))

            self.fwtimes-=fwstart
            self.fwtimes/=3600
            self.fwtimes+=self.starthourmin +  (float(hours)*md/3600)
            

            self.saveFW=True
        except Exception as e:
            e2=str(traceback.print_exc())
            self.log.error(e2)
            self.log.error(str(e))
            self.saveFW=False

        # ---------------------------------------------------------
        self.log.debug( "MEAS: Measurement %s loaded\n"% self.label)
        
        
#########################################################################################################
        
    def plotVetoCheck(self, 
                      xlabeltime=6, 
                      figname=None, 
                      borders1=None,
                      borders2=None,
                      borders3=None,
                      borders4=None,
                      borders5=None,
                      borders6=None,
                      borders7=None,
                      cutValue=None,
                      axvlines=None,
                      rateCut=False,
                      dir="",
                      enabledChannels={"A":True, "B":False, "C":False, "D":False},
                      measTemp=False,
                      measCPU= False,
                     ):
        

        
        
        if len(self.rates)==0:
            self.log.error("No data taken")
            return

        
        #----------------------------------------------------------------------
        # Pre process data


        # rate
        if enabledChannels["A"]:
            meanAmp=[]
            allcounts=[]
            counts=[]
            for capture in self.amplitudes:
                    allcounts.append(len(capture))
                    capture=-np.array(capture)*1000
                    if cutValue!=None:
                        #print len(amps), np.mean(amps)
                        cut=capture>cutValue
                        capture=capture[cut]
                    counts.append(len(capture))
                    meanAmp.append(np.mean(capture))
            self.meanAmp=meanAmp
        
            N2=100
            if len(self.meanAmp) < N2*10: 
                N2 = max(10,len(self.meanAmp)/10)
                self.log.info("MEAS: Corrected N2 to %d"% N2)
            runningmean2=np.convolve(self.meanAmp, np.ones((N2,))/N2, mode='same')
            runninghours=self.hours
            runninghours=runninghours[int(0.5*N2):-int(0.5*N2)]
            ampM=runningmean2[int(0.5*N2):-int(0.5*N2)]
            
                
            # running mean of rate
            if rateCut==False:
                rates=self.rates
            else:
                # Rate anders berechnen
                times=np.array(allcounts)/self.rates
                rates=np.array(counts)/times
                self.ratesCut=rates
            
            N1=100
            if len(rates) < N1*10: 
                N1 = max(10,len(self.meanAmp)/10)
                self.log.info("MEAS: Corrected N1 to %d"%N1)
            runningmean=np.convolve(rates, np.ones((N1,))/N1, mode='same')
            runningmeanx=self.hours
            runningmeanx=runningmeanx[int(0.5*N1):-int(0.5*N1)]
            rateM=runningmean[int(0.5*N1):-int(0.5*N1)]
            self.RMRate=rateM
            self.RMTime=runningmeanx

        # noise
        if enabledChannels["D"]:
            # running mean of amp pmt and amp noise
            meanNoiseAmp=[]
            medianNoiseAmp=[]
            
            for capture in self.namplitudes:
                    
                    meanNoiseAmp.append(np.mean(capture))
                    medianNoiseAmp.append(np.median(capture))
            self.meanNoiseAmp=-np.array(meanNoiseAmp)*1000
            self.medianNoiseAmp=-np.array(medianNoiseAmp)*1000
            if self.meanNoiseAmp!=[]:
                runningmean3=np.convolve(self.meanNoiseAmp, np.ones((N2,))/N2, mode='same')
                ampMN=runningmean3[int(0.5*N2):-int(0.5*N2)]
        #----------------------------------------------------------------------
        # initialise plot
        
        fig=plt.figure(figsize=(10,10))
        subplotnumber=10
        i=11 # required to get the plots at the correct position, should be always 11

        # switch off channels
        if not enabledChannels["A"]: subplotnumber-=2
        if not enabledChannels["D"]: subplotnumber-=1
        if not measTemp: subplotnumber-=2
        if not enabledChannels["C"]:  subplotnumber-=1 
        if not enabledChannels["B"]:  subplotnumber-=1
        if not measCPU: subplotnumber-=1
        if not self.saveHV: subplotnumber-=1

        # produce subplots ------------------
        if enabledChannels["A"]: 
            # rate
            axis = fig.add_subplot(subplotnumber*100+i); i+=1 # 1 zeile, 1 spalte, 1. plot
            # ch A mean amp
            ax6=fig.add_subplot(subplotnumber*100+i); i+=1
        # temperature
        if measTemp: 
            ax2=fig.add_subplot(subplotnumber*100+i); i+=1
            ax8=fig.add_subplot(subplotnumber*100+i); i+=1
        # room light
        if enabledChannels["C"]: ax3=fig.add_subplot(subplotnumber*100+i); i+=1
        # HV
        if enabledChannels["B"]: ax4=fig.add_subplot(subplotnumber*100+i); i+=1
        # Noise
        if enabledChannels["D"]: ax5=fig.add_subplot(subplotnumber*100+i); i+=1
        # cpu
        if measCPU: ax7=fig.add_subplot(subplotnumber*100+i); i+=1
        # hv
        if self.saveHV: ax9 = fig.add_subplot(subplotnumber*100+i); i+=1
        # filterwheel
        if self.saveFW: ax10 = fig.add_subplot(subplotnumber*100+i); i+=1

        # collect axes -----------------
        axes=[]
        if enabledChannels["A"]: 
            axes.append(axis)
            axes.append(ax6)
        if measTemp:  
            axes.append(ax2)
            axes.append(ax8)
        if enabledChannels["C"]: axes.append(ax3)
        if enabledChannels["B"]: axes.append(ax4)
        if enabledChannels["D"]: axes.append(ax5)
        if measCPU:  axes.append(ax7)
        if self.saveHV: axes.append(ax9)
        if self.saveFW: axes.append(ax10)
        # ----------------
        # fill data into axes

        if enabledChannels["A"]:
            axis.plot(self.hours, rates, "b",linewidth=1., alpha=0.8, label="Rate per Capture")
            axis.plot(runningmeanx, rateM, "k",linewidth=2., label="Running Mean N=%d"%N1)

            ax6.plot(self.hours, self.meanAmp, label="PMT")
            if cutValue==None:
                text=""
            else:
                text="Cut %d" %cutValue
            ax6.plot(runninghours, ampM, "k",linewidth=2., label="Running Mean N=%d %s"%(N2, text))
        
        if measTemp: 
            try:
                ax8.plot(self.temptimes, self.temp1,label=self.tempLabels[0], color="blue", alpha=0.7) # room temperature, plot separately
                if max(self.temp2)<50: # broken sensor gives values > 4000
                    ax2.plot(self.temptimes, self.temp2,label=self.tempLabels[1], color="green", alpha=0.7) # sensor broken ?
                if max(self.temp3)<50:
                    ax2.plot(self.temptimes, self.temp3,label=self.tempLabels[2], color="cyan", alpha=0.7)
                if max(self.temp4)<50:
                    ax2.plot(self.temptimes, self.temp4,label=self.tempLabels[3], color="mediumslateblue", alpha=0.7) # sensor broken
            except Exception as e: 
                #print e
                pass
        
        if enabledChannels["C"]:
            try:
                ax3.plot(self.hours, self.chC, label="Light")
            except: pass

        if enabledChannels["B"]: 
            try:
                cB=[]
                for capture in self.HVs:
                    cB.append(np.mean(capture))
                #print ("HV",np.mean(cB))
                channelB=np.array(cB)

                ax4.plot(self.hours, channelB)
            except: pass

        if enabledChannels["D"]:
            if self.meanNoiseAmp!=[]:
                ax5.plot(self.hours, self.meanNoiseAmp, label="Antenna")
                ax5.plot(runninghours, ampMN, "k",linewidth=2., label="Running Mean N=%d"%N2)
        
        if measCPU:  
            try:
                ax7.plot(self.cputime, self.cpu1, label="CPU 1", color="blue", alpha=0.7)
                ax7.plot(self.cputime, self.cpu2, label="CPU 2", color="green", alpha=0.7)
                try:
                    ax7.plot(self.cputime, self.cpu3, label="CPU 3", color="cyan", alpha=0.7)
                    ax7.plot(self.cputime, self.cpu4, label="CPU 4", color="mediumslateblue", alpha=0.7)
                except:
                    pass
                ax7.plot(self.cputime, self.memory,label="Memory", color="black", linewidth=2, alpha=0.7)
            except:
                pass  

        if self.saveHV:
            ax9.plot(self.hvtimes, self.hvvalues, label="HV")      
        if self.saveFW:
            ax10.plot(self.fwtimes, self.fwvalues, label="FW")      
        # set y labels ----------
        if enabledChannels["A"]:
            axis.set_ylabel("Rate / Hz", fontsize=11)
            ax6.set_ylabel("<Ampl.> / mV", fontsize=10)
        if measTemp: 
            ax2.set_ylabel(r"Temp. / $^{\circ}$C", fontsize=10)
            ax8.set_ylabel(r"Temp. / $^{\circ}$C", fontsize=10)
        if enabledChannels["C"]: ax3.set_ylabel(r"Room light / V", fontsize=10)
        if enabledChannels["B"]: ax4.set_ylabel("HV / V", fontsize=11)
        if enabledChannels["D"]: ax5.set_ylabel("<Ampl.> / mV", fontsize=10)
        if measCPU:  ax7.set_ylabel("PC / %", fontsize=11)
        if self.saveHV: ax9.set_ylabel("HV / V", fontsize=11)
        if self.saveFW: ax10.set_ylabel("Position / steps", fontsize=10)

        # set title
        axes[0].text(0.95, 1.05, 
            "Started at %s"% (self.starttime),
            #fontsize=fs_small, 
            color="Black",style="italic",
            transform=axis.transAxes, 
            verticalalignment='bottom',
            horizontalalignment="right",
            )
        # set x label
        axes[-1].set_xlabel("Day of month / Hour of Day", fontsize=15)

        # adjust quantity of x lables
        #try:
        #    xloc = matplotlib.pyplot.MaxNLocator(6)
        #    axis.set_major_locator(xloc) # 'AxesSubplot' object has no attribute 'set_major_locator'
        #except Exception as e:
        #    self.log.debug("MEAS: xloc did not work: %s"%str(e))
        # nicer human readable ticks with hour and decimals
        labels=axis.get_xticks().tolist()
        ticks=np.arange(int(labels[0]), int(labels[-1])+xlabeltime, xlabeltime)
        l1=ticks%24
        l2=np.float32(np.float64(ticks)/24)+self.day
        labels=[]
        labels_empty=[]
        try:
            for i in range(len(ticks)):
                labels.append("%d/%.1f" %(l2[i],l1[i]))
                labels_empty.append(" ")
        except: pass

        # apply to all axes -------------
        i=1
        for ax in axes:
            if axvlines!=None:
                for axv in axvlines:
                    ax.axvline(axv, color="black")
            
            ax.grid(True)
            #if i==3:
            #    continue
            ax.set_xticks(list(ticks))
            ax.set_xticklabels(list(labels_empty)) # otherwise try: ax1.xaxis.set_ticklabels([])

            ax.set_xlim(min(self.hours),max(self.hours))
            #ax.set_xlim(4,10)
            i+=1
        axes[-1].set_xticklabels(list(labels))

        # format y ticks -----------------------------
        if enabledChannels["B"]: ax4.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

        # set y limits ----------------------
        if enabledChannels["A"]: 
            if borders1!=None:
                axis.set_ylim(borders1[0],borders1[1])
            if borders6!=None:
                ax6.set_ylim(borders6[0],borders6[1])
        if measTemp:
            if borders2!=None:
                ax2.set_ylim(borders2[0],borders2[1])
        if enabledChannels["C"]:
            if borders3!=None:
                ax3.set_ylim(borders3[0],borders3[1])
        if enabledChannels["B"]: 
            if borders4!=None:
                ax4.set_ylim(borders4[0],borders4[1])
        if enabledChannels["D"]: 
            if borders5!=None:
                ax5.set_ylim(borders5[0],borders5[1])            
        if measCPU:  
            if borders7!=None:
                ax7.set_ylim(borders7[0],borders7[1])
                
        # set legends ---------------
        if measTemp: 
            ax2.legend(loc="best",ncol=3, prop={"size":6})
            ax8.legend(loc="best",ncol=3, prop={"size":6})
        if enabledChannels["A"]:  
            axis.legend(loc="best",ncol=3, prop={"size":6})
            ax6.legend(loc="best",ncol=3, prop={"size":6})
        if enabledChannels["D"]:  ax5.legend(loc="best",ncol=3, prop={"size":6})
        if measCPU:  ax7.legend(loc="best",ncol=3, prop={"size":6})

        # save ----------------------------------
        #plt.show()
        if figname!=None:
            fig.savefig(dir+"Veto_"+figname.replace(" ","_")+".png", bbox_inches='tight')
            fig.clear(); plt.clf(); plt.close(fig);
            
            
#########################################################################################################


    def getTimefromRun(self,Subrunnumber=390-(60), subruns=390, srduration=10.*60):
        days=int(srduration*Subrunnumber/(60*60*24)) # rounds down
        day=self.day+days
        hours= srduration*Subrunnumber/(60*60)
        hour=self.starthourmin+hours-days*24
        if hour>24:
            hour-=24
            day+=1
        minutes=hour-int(hour)
        minutes=int(minutes*60)
        hour=int(hour)

        #print "Day, hour of day, minute of hour:",day, hour, minutes
        
        
######################################################################################################

    def areaSpectrum(self, 
                     figname=None,
                     cutValue=None, # cut on amplitude -mV
                     borders=(-1,40),
                     bins=128,
                     xborders=None,
                     log=True,
                     dir="",
                    ):      
        # Areas


        s=self
        
        if len(self.rates)==0:
            self.log.error("No data taken")
            return
        ##################################

        fig = plt.figure(figsize=(6,4),dpi=100)
        ax1 = fig.add_subplot(111)
        
        binning=[ i*float((borders[1]-borders[0]))/bins+borders[0] for i in range(bins+1)]
        binwidth=binning[1]-binning[0]
        binning=np.array(binning)
        bincenters = (binning[1:]+binning[:-1])/2
        X = np.array([binning[:-1],binning[1:]]).T.flatten()  

        i=0
        amps=s.areas
        amps= amps.flatten()
        amps=-np.array(amps)/50./(1.602*1e-19)/self.gain
        x=-np.array(s.amplitudes.flatten())*1000

        histvals, binedges = np.histogram(amps, bins=binning)
        histvals=np.float64(histvals)
        histvals/=s.NettoMeasurementtime # counts -> rate * binwidth
        histvals/=binwidth # rate / bin

        Y = np.array([histvals,histvals]).T.flatten()    
        ax1.plot(X,Y, linewidth=2.,label=s.label)
        self.histAreaX=binedges
        self.histAreaY=histvals

        if cutValue!=None:
            amps=amps[x>cutValue]
            histvals, binedges = np.histogram(amps, bins=binning)
            histvals=np.float64(histvals)
            histvals/=s.NettoMeasurementtime # counts -> rate * binwidth
            histvals/=binwidth # rate / bin
            Y = np.array([histvals,histvals]).T.flatten()    
            ax1.plot(X,Y, linewidth=2.,label="Cut Amplitude >%fmV" % cutValue)
            self.histCutAreaX=binedges
            self.histCutAreaY=histvals
        i+=1
        #if i>0: break

        ax1.grid(True)
        ax1.set_ylabel("Rate in Hz", fontsize=15)
        ax1.legend(bbox_to_anchor=(0, 1.02,1, 0.102),loc=3,ncol=1,mode="expand",borderaxespad=0., prop={'size':15})
        if log: ax1.set_yscale("log", nonposy="clip")
        if xborders!=None:
            ax1.set_xlim(xborders[0],xborders[1])
        else:
            ax1.set_xlim(borders[0],borders[1])
        ax1.set_xlabel("Photoelectrons", fontsize=15)

        #plt.show()
        if figname!=None:
                        fig.savefig(dir+"Area_"+figname.replace(" ","_")+".png", bbox_inches='tight'); fig.clear(); plt.clf(); plt.close(fig);

######################################################################################################

    def amplSpectrum(self, 
                     figname=None,
                     cutValue=None, # cut on amplitude -mV
                     borders=(-10,90),
                     bins=128,
                     xborders=None,
                     log=True,
                     dir="",
                    ):      
        
        s=self
        
        if len(self.rates)==0:
            self.log.error("No data taken")
            return
        ##################################

        fig = plt.figure(figsize=(6,4),dpi=100)
        ax1 = fig.add_subplot(111)
        
        binning=[ i*float((borders[1]-borders[0]))/bins+borders[0] for i in range(bins+1)]
        binwidth=binning[1]-binning[0]
        binning=np.array(binning)
        bincenters = (binning[1:]+binning[:-1])/2
        X = np.array([binning[:-1],binning[1:]]).T.flatten()  

        i=0
        amps=s.amplitudes
        amps= amps.flatten()
        self.log.info("AmplSpectrum: self.amplitudes %d flattened %d" % (len(s.amplitudes), len(amps)))
        self.log.info("AmplSpectrum: min %f max %f mean %f" % (min(amps), max(amps), np.mean(amps)))
        # if original: min/max: -0.09, -0.006
        # if adjusted: min/max: +6, +90
        if np.mean(amps)<0: # probably not adjusted # TODO take it out once bug solved
            self.log.info("AmplSpectrum: Adjust amplitudes, seem to have not been adjusted before")
            amps=-np.array(amps)*1000
        self.log.info("AmplSpectrum: min %f max %f mean %f" % (min(amps), max(amps), np.mean(amps)))
        

        histvals, binedges = np.histogram(amps, bins=binning)
        histvals=np.float64(histvals)
        histvals/=s.NettoMeasurementtime # counts -> rate * binwidth
        histvals/=binwidth # rate / bin

        Y = np.array([histvals,histvals]).T.flatten()    
        ax1.plot(X,Y, linewidth=2.,label=s.label+"_"+figname[-3:])
        self.histAmpX=binedges
        self.histAmpY=histvals
        
        if cutValue!=None:
            ax1.axvline(cutValue, color="k", linewidth=1.)

        i+=1
        #if i>0: break

        ax1.grid(True)
        ax1.set_ylabel("Rate in Hz", fontsize=15)
        ax1.legend(bbox_to_anchor=(0, 1.02,1, 0.102),loc=3,ncol=1,mode="expand",borderaxespad=0., prop={'size':15})
        if log: 
            try: 
                ax1.set_yscale("log", nonposy="clip")
            except:
                ax1.set_yscale("log", nonpositive="clip")
        if xborders!=None:
            ax1.set_xlim(xborders[0],xborders[1])
        else:
            ax1.set_xlim(borders[0],borders[1])
        ax1.set_xlabel("Amplitude in mV", fontsize=15)

        #plt.show()
        if figname!=None:
                        fig.savefig(dir+"Amplitude_"+figname.replace(" ","_")+".png", bbox_inches='tight'); fig.clear(); plt.clf(); plt.close(fig);


