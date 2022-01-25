from __future__ import print_function
from __future__ import absolute_import

import inspect
import numpy as np



class Settings:

    '''
    Reads from daq: int, float, str, bool, dicts
    Doesn't save: lists, objects
    '''
    
    


    def __init__(self, daq):
        # while appliation starts load old settings from file
        # save settings into daq
        self.filename="code/settings.cfg"
        self.daq=daq
        
        # read in all attr names and values from daq
        attr=inspect.getmembers(daq, lambda a:not(inspect.isroutine(a)))
        self.attributes={}
        for a, v in attr:
            if  (not a.startswith('__') and not a.endswith('__')) or (not a.startswith('_')):
                self.attributes[a]=[type(v), v]
        #print ("Loaded from DAQ: ",self.attributes)
        
        # TODO: if no settings.cfg create it and do once 
        # a saveSettings() to load stuff from daq.defaults
        
    def saveSettings(self):
        # save changed daq settings to file
        
        # write to file
        self.setfile=open(self.filename, "w")
        #help(self.attributes)
        try:
            items=self.attributes.items() # python3
        except:
            items=self.attributes.iteritems() # python2
        for attr, (tipe, value) in items:
            #if attr=="voltagerange":
            #    print ("save",attr, (tipe, value))
            if tipe!=dict and tipe !=list and tipe!=np.array:
                if tipe==str or tipe==int or tipe==float or tipe==bool:
                    self.setfile.write("%s %s\n" % (attr,getattr(self.daq, attr)))
                else:
                    #print("Error saving:", attr,getattr(self.daq, attr))
                    pass
            elif tipe==dict:
                # if dict
                try:
                    keys=value.keys() # python3
                except:
                    keys=value.iterkeys() # python2
                for entry in keys: # iterkeys
                    #if entry not in ["LowestPriority", "InheritPriority"]:
                        #print ("\n",attr, entry)   
                        self.setfile.write("%s.%s %s\n" % (attr, entry,getattr(self.daq, attr)[entry]))
            elif tipe==list:
                # these are data arrays which shouldn't be saved here
                pass
            else:
                print("Not know how to save:", attr,getattr(self.daq, attr))
        self.setfile.close()
        
    def convertType(self, value, tipe, verbose=False):
        if tipe==str:
            return str(value)
        elif tipe==int:
            return int(float(value))
        elif tipe==float:
            return float(value)
        elif tipe==bool:
            if type(value)==str:
                if value=="False":
                    return False
                else:
                    return True
            elif type(value)==int:
                if value==0:
                    return False
                else:
                    return True
            else:
                return bool(value)
        else:
            return value
            
    def loadSettings(self):
        self.setfile=open(self.filename, "r")
        for line in self.setfile:
            #print (line)
            n,v=line.replace("\n", "").split(" ")
            # todo change type of v
            if n=="channelEnabled":
                print ("load1",n, v, type(v))
            if "." in n:
                d,e=n.split(".")
                try:
                    #if d=="channelEnabled":
                    #    print ("load2",self.attributes[d][1][e], type(self.attributes[d][1][e]))
                    tipe=type(self.attributes[d][1][e])
                    #if d=="channelEnabled": print (tipe)
                except Exception as expc:
                    #if d=="channelEnabled": print (expc)
                    #if d=="channelEnabled": print ("Error",d,e, tipe)
                    tipe=str
                if not hasattr(self.daq, d):
                    setattr(self.daq, d, {})  
                getattr(self.daq, d)[e]=self.convertType(v, tipe)
                #if d=="channelEnabled":
                #    print ("load3",d,e, v, tipe, self.convertType(v, tipe, verbose=True), type(self.convertType(v, tipe, verbose=True)))
                #print (n,getattr(self.daq, d)[e])
            else:
                try:
                    tipe=self.attributes[n][0]
                except:
                    print ("Error",n, tipe)
                    tipe=str
                #if n=="voltagerange":
                #    print ("load4",n, v, tipe, self.convertType(v, tipe, verbose=True), type(self.convertType(v, tipe, verbose=True)))
                setattr(self.daq, n, self.convertType(v, tipe))
                #print (n,getattr(self.daq, n))
        self.setfile.close()
##########################################################################################

if __name__ == "__main__":

    # dummy daq
    names=["triggerenabled", 
            "measurementrunning",
            "measurementenabled",
            "threadIsStopped",
            "loopduration",
            "triggerchannel",
            "triggervoltage",
            "triggermode"
          ]
        # directories with entries A B C D
    dirs=["channelEnabled",
              "coupling",
              "voltagerange",
              "offset",
              "channelEnabled",
    
             ]
    entries=["A", "B", "C", "D"]
    
    class DAQ:
        blub=False            
        
    daq=DAQ()
    
    for name in names:
        setattr(daq, name, "1")
        
    for dyr in dirs:
        d={}
        for entry in entries:
            d[entry]="2"
        setattr(daq, dyr, d)
        
        
    s=Settings(daq)
    s.saveSettings()
    s.loadSettings()
    s.saveSettings()