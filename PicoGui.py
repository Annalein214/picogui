## #! /usr/bin/env python
## #! /usr/bin/env python2
# You have to execute this script to start the application

# the application is compatible with Windows, Linux and Mac OS
# as well as QT4 and QT5
# as well as python2 and python3

# python 2 vs 3 compatible stuff
from __future__ import print_function
from __future__ import absolute_import

# standard stuff
import sys, os
from optparse import OptionParser
from code.helpers import green, nc, red, yellow, lila, pink, blue

# qt stuff
print ()
try:
    from PyQt4 import QtGui
    print("INFO: Running on PyQT4")
    MyGui=QtGui
except ImportError as e:
    print("WARNING: PyQT4 not found")

    try:
        from PyQt5 import QtWidgets
        print("INFO: Running on PyQT5")
        MyGui=QtWidgets
    except ImportError as e:
        print(red,"ERROR: PyQt5 not found.", nc)
        print(lila,"Did you try to start python2 instead of python3 or vise versa?", nc)

# my stuff
from code.gui import ApplicationWindow

#from code.window import MainWindow

from code.log import log
from code.daq import myPicoScope
from code.settings import Settings
# external hardware
from code.temperature.hygrosens import Hygrosens # temperature sensor
from code.lightsensor.photodiode import Photodiode


# picoscope

##########################################################################################

def main(opts, log, connect):

    # initialization function:
    # - tests and initializes the temperature sensor hygrosens
    # - starts and tests the picoscopes
    # - loads the recent settings
    # - starts GUI
    # - starts the Application
    
    #print(connect)
    
    # initialize important external hardware
    if connect: 
        # temperature sensor: hygrosens
        hygro=Hygrosens(log)
        if hygro.online==False:
            hygro=None
            print("Hygrosense temperature sensor not found, turned off")
        # photodiode via arduino
        diode = Photodiode(log)
        if diode.online==False:
            diode=None
            print("Arduino light sensor not found, turned off")
    else:
        hygro=None
        diode=None
        
    
    scope=myPicoScope( log=log, 
                       hygro=hygro,
                       directory=opts.directory, 
                       connect=connect,
                       diode=diode,
                      )
    ret=scope.open()
      
    settings=Settings(scope)
    try:
        settings.loadSettings()
    except :#FileNotFoundError as e:
        log.error("No Settings found. Set up anew")
        settings.saveSettings() # only required if there is no settings.cfg
        settings.loadSettings()
    

    if ret==True and opts.konsole==False:

        app = MyGui.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(True)

        # Set up the GUI part
        gui=ApplicationWindow(scope, log, opts, settings)
        gui.show()
        log.debug("Window is set up")

        sys.exit(app.exec_())
        # here nothing is executed anymore
    elif opts.konsole==True and ret==True:
        log.info("Starting in Konsole Mode. Directly starting data taking.")
        scope._threadIsStopped=False
        scope.startRapidMeasurement()
        scope.close()
        log.endLogging()


##########################################################################################

if __name__ == '__main__':

    # This function has only the most basic functions which have to be initialized / tested
    # at the very beginning:
    # - command line options
    # - logging directory
    # - start logging
    # - start main initialization function

    #print("Arguments:"+" ".join(sys.argv))

    usage="""

            %prog [options]

            This program is dedicated for use with PicoScope  6404B and Luminescence Measurements.

            -d : directory to store data. All Files will be stored in ./data if not otherwise set.
            -t : don't use an actual picoscope but fakedata for testing, does not work for all functions!

            """
    parser = OptionParser(usage=usage)
    parser.add_option("-t","--test", action="store_true",dest="test", help="Do not connect to device.", default=False)
    parser.add_option("-d","--dir",dest="directory", help="Directory to store data", default=False)
    parser.add_option("-k", "--konsole", action="store_true", dest="konsole", help="Start from terminal without GUI", default=False)
    opts, args = parser.parse_args()

    # wether to really connect to the picoscope or only simulate
    if opts.test:
        connect=False
    else:
        connect=True

    # set and check directories
    if not opts.directory:
        opts.directory="./data/" # also works on windows
    opts.directory=opts.directory.replace(" ", "")

    if opts.directory[-1]!="/":
        opts.directory+="/"

    if not os.path.exists(opts.directory):
        print(red,"ERROR: Directory not found: %s"%opts.directory, nc)
        print(lila,"Please do $mkdir data$ in this directory or start with the -d option.", nc)
        quit()

    # start logging, set logging level
    log=log(save=True, level="info", directory=opts.directory)
    log.debug("Arguments:"+" ".join(sys.argv))
    log.info("Connect:%s"%str(connect))

    # make it so!
    main(opts, log, connect)

##########################################################################################

'''
TODO
####

- ask what to save!

plotvetocheck reparieren, temperatur aussen getrennt anzeigen

Temperatursensor bei zu geringen Temperaturen spinnt

Testen:
---

Gute TODO:
- Statt Spektrum optional: Plots fuer Licht, Temperatur, Noiselevel (siehe veto)

######

sehr optional:

PicoGui
    - Optional pro kanal bestimmen, was gemessen wird (mean, pulseanalysis, rate) und angezeigt wird
    

Wartung
    - direkt alle Daten in ein Objekt speichern und dieses Objekt dann stuendlich abspeichern.
    -NEIN: so kann man einzelnes nicht gebrauchtes unterdruecken
    - ggf in Display option zum speichern machen

Signalgenerator 
    - genau verstehen was freq bedeutet
    - loeschen: white noise, sinc, dcvoltage, 
    - wie invertieren
    - wie breite und frequenz unabhaengig justieren
    
- Trigger times
    - test new struct and mail resulting "m" to hitesh

##########################################################################################

Version 1:

Neu in Version 2: 
- Version mit der Sarah Piepers Arbeit entstand.

Neu in Version 3:
- switch between PE und Amplitude im laufenden Programm
- PE corrected with gain
- Auswertung am Ende
- daten und bild in ordner speichern
- datenbank
- starten ohne GUI moeglich. Es wird ausgefuehrt, was in settings.cfg hinterlegt ist.

Neu in Version 4: 
- Verbesserung des Startvorgangs (PicoGui)
- Neue Variable dtimes: zeiten zwischen 1. und allen weiteren Pulsen in einem capture
- Wenn "nicht speichern" loesche das provisorisch angelegte Verzeichnis in /data/ und damit das zugehoerige .out file
- Ein Vorschlag fuer das jeweils passende minimum an Triggerschwelle wird angezeigt.
- Bug dass plotten manchmal nicht geht beseitigt??
- Trenne Meas. und Display options
- Bug dass kein Noise mehr angezeigt wird beseitigt??
- Verbessertes Layout in Plots (xticks, Textinfos der Rate / HV)
'''
