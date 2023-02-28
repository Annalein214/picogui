# picogui
Python GUI for the Picoscope and some other hardware using the PicoSDK and implemented in Python. 

This program was written in order to measure the rate PMT pulses, i.e. small pulses at low rate, as accurately as possible over long times. Some further measurement devices, of which the data is of interest at the same time-axis, is added into the program, i.e. light sensor, HV, temperature, movement and position of motors. Thus, a diverse set of measurement devices is already supported and could be adjusted for similar needs.

A similar program exists which controls a probe via a km long cable using RS458. In that probe a RedPitaya is the mainboard and also reading out a PMT. Additional hardware (read out by the RedPitaya) were Raspberry py Zero IR Cameras, Motors, observation of the charge of low temperature batteries, temperature sensors, gyro sensor or a light flasher plus customized camera. This program is not yet on GIT. If interested, please contact me.


# Functionality

## Oscilloscope

All Picoscope functions are implemented in the code. Most of them are also available in the GUI, i.e. 
- settings of channels: Range, Offset of Range, Coupling
- settings of trigger: Channel, Voltage, Rising/Falling, Delay
- sampling: Frequency, Samples, Captures (for rapid mode)
- trigger modes: normal (not in GUI) and rapid block mode (minimal deadtime < 1us)

Live display / GUI functions
- set a measurement duration after which the scope is automatically stopped
- measure endless 
- adjust how many waveforms are saved 
- calculate and show max amplitude spectrum 
- calculate and show PMT charge spectrum 
- enter log entries any time into your measurement log
- show slow data as numbers e.g. temperature, HV, rate, Light Sensor
- FFT support buggy but worked at some time
- hourly plots which show data over time (i.e. rate, mean amplitude, temperature, HV etc)

## Other devices

TBD or see below

# Prerequisits

The software runs on Linux, Mac, Windows (some versions might not be supported, because the programm was only sometimes used at the one or other OS).

- python 2 or 3 (2 deprecated)
- PyQT4 or 5 (4 deprecated)
- pyseriel (for further hardware)

Picoscope 3xxx (MSO) or 6xxx, change to others should be straight forward. 
Further possible hardware, see below.

# Usage

Create a folder named "data" in the top folder. In Terminal start the program with 

$ pythonX PicoGui.py

Make sure you check the output in the terminal for errors as well as the general log of the device and the measurement log (in the measurement folder). Manual log messages are marked with "LMSG" in the logs. For every measurement a new folder is created, however they are not automatically deleted, if the measurement is not stored. 

This software is made for rate measurements. Therefore I recommend to measure the rate accuracy first. 
Set the captures in a way that each block of triggers takes at least 1 sec, i.e. Number_of_Captures >= Real_Rate_in_Hz. 
Then use a signal generator and record the rate in relation to the set rate at the generator. My experience is an increase to 5% under-estimation of rate which is then very stable up to at least 100kHz. 

# Further hardware

## CPU / Memory 

The observation of CPU / Memory usage was implemented at a time. Probably it is broken now.

## Temperature

Can be readout and integrated into the program as slow data. Live output is the latest measurement, no graph. However, in the hourly plot a graph is shown. 

## Filterwheel: 

A motor is driven by an Arduino and its position read out with an Encoder. The motor turns a wheel with optical filters in it beneath a PMT. So the position of the filters needs to be accurately adjusted. 
Currently this is an independent program which requires independent setup, see this file.


## HV: 

High voltage can be run either in parallel or also read out by this programm (channel B).
If separate programm, the results can still be added into the overview files.
If using channel B, the data is shown live in Figure 3. 

## Light sensor

Channel C, only voltage is given as number in live mode. In plots the graph is shown. 

## Motor 

Motor encoder values can be read out and given for same time-axis



