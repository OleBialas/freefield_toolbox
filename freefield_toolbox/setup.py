'''
Functions and classes for working with the freefield dome and arc.
'''

import numpy as np
import slab
import win32com.client
import csv
import numpy as np
import os
import time

# thoughts on the software architecture:
# Ideally, ZB, RX8, and RP2 are internal variables that the user never needs to use directly (but we can if needed). We would not need a freefield class for this, because there can never be more than one instance anyway.
# set_device function should be called in the beginning to choose arc or dome. Internal variables _calibration_filter and _speakertable are set accordingly. Other functions should not need to read the _device variable.
# provide functions for reading (or waiting for!) response from button box, flashlight, and headtracker


# internal variables here:
#TODO: Einheitliche Namen!
#TODO: Feedback from functions
#TODO: function to "unset" channels
_procs = dict(RX8_1=None, RX8_2=None, RP2=None, ZBus=None) # dict might be better because you can call objects with a string
_setup = None
_calibration_filter = None
_speakertable = None
_location_ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def initialize_setup(setup='arc'):
	'''
	Set the freefield setup to use (arc or dome).
	'''
	global _setup, _calibration_file, _calibration_filter, _speakertable
	if setup == 'arc':
		_setup = 'arc'
		calibration_file = os.path.join(_location_,'calibration_filter_arc.npy')
		table_file = os.path.join(_location_,'speakertable_arc.csv')
	elif setup == 'dome':
		_setup = 'dome'
		calibration_file = os.path.join(_location_,'calibration_filter_dome.npy')
		table_file = os.path.join(_location_,'speakertable_dome.csv')
	else:
		raise ValueError("Unknown device! Use 'arc' or 'dome'.")

	_speakertable = _read_table(table_file)
	_calibration_filter =  "load filter here"#slab.Filter.load(_calibration_file)

def initialize_devices(rcx_RX8_1=None, rcx_RX8_2=None, rcx_RP2=None, ZBus=False):
	'''
	Initialize the ZBus, RX8s, and RP2.
	'''
	global _procs
	if not _setup:
		raise ValueError("Please set device to 'arc' or 'dome' before initialization!")

	if rcx_RX8_1 is not None:
		_procs["RX8_1"] = _initialize_processor("RX8", rcx_RX8_1, 1)
	if rcx_RX8_2 is not None:
		_procs["RX8_2"] = _initialize_processor("RX8", rcx_RX8_2, 2)
	if rcx_RP2 is not None:
		_procs["RP2"] = _initialize_processor("RP2", rcx_RP2, 1)
	if ZBus:
		_procs["ZBus"] = _initialize_zbus()

def set(variable, value, proc='RX8s'):
	'''
	Set a variable on a processor to a value. Setting will silently fail if
	variable does not exist in the rco file. The function will use SetTagVal
	or WriteTagV correctly, depending on whether len(value) == 1 or is > 1.
	proc can be 'RX81', 'RX82', 'RP2', 'RX8s' or 'all'. 'RX8s' sends the value to
	all RX8 processors.
	Example:
	set('stimdur', 90, proc='RX8s')
	'''
	if proc.lower()=="rx8s":
		procs=["RX8_1", "RX8_2"]
	elif proc=="all":
		procs=["RX8_1", "RX8_2", "RP2"]
	elif proc=="RX8_1" or proc=="RX8_2" or proc=="RP2":
		procs=[proc]
	else:
		raise ValueError(proc+' is an improper value for proc. Possible values are: "all", "RX8s", "RX8_1", "RX8_2 or "RP2"')
	for p in procs:
		if type(value) == list or type(value) == np.ndarray:
			if not _procs[p]._oleobj_.InvokeTypes(15, 0x0, 1, (3, 0), ((8, 0), (3, 0), (0x2005, 0)), variable, 0, value):
				raise ValueError("writing to tag %s on %s failed!"%(variable, p))
			else:
				print("writing data to tag %s on %s..."%(variable, p))
		else:
			if not _procs[p].SetTagVal(variable, value):
				raise ValueError("writing to tag %s on %s failed!"%(variable, p))
			else:
				print("setting value of tag %s on %s to %s..."%(variable, p, value))

def get(variable, proc, n_samples=1):
	'''
	Get the value of a variable from a processor. Returns None if variable
	does not exist in the rco file. [Can we get single items and arrays automatically?]
	proc can be 'RX81', 'RX82', or 'RP2'.
	Example:
	get('playing', proc='RX81')
	'''
	if n_samples >1:
		value = np.asarray(_procs[proc].ReadTagV(variable, 0, n_samples))
	else:
		value = _procs[proc].GetTagVal(variable)
	return value

def halt(proc="all"):
	'''
	Halt specified processor. If "all" (default), halt all processors
	'''
	if proc=="all":
		for p,n in zip(_procs.values(), _procs.keys()):
			if p.Halt():
				print("Halting "+n)
	else:
		if _procs[proc].Halt():
			print("Halting "+proc)
	pass

def trigger(trig='zBusA', proc=None):
	'''
	Send a trigger. Options are "soft", "zBusA" and "zBusB". For using
	the software trigger a processor must be specified. For using
	zBus triggers, the zBus must be initialized first.
	'''
	if 'soft' in trig.lower():
		if not proc:
			raise ValueError('Proc needs to be specified for SoftTrig!')
		if _procs[proc].SoftTrg(1):
			print("sending software trigger to "+proc)
	elif "zbus" in trig.lower() and not _procs["ZBus"]:
		raise ValueError('ZBus needs to be initialized first!')
	elif trig.lower()=="zbusa":
		if _procs["ZBus"].zBusTrigA(0, 0, 20):
			print("sending trigger via ZBus-A")
	elif trig.lower()=="zbusb":
		if _procs["ZBus"].zBusTrigB(0, 0, 20):
			print("sending trigger via ZBus-B")
	else:
		raise ValueError("Unknown trigger type! Must be 'soft', 'zBusA' or 'zBusB'!")

def wait_to_finish_playing(proc="all", tagname="playback"):
	'''
	Busy wait as long as sound is played from the processors. The .rco file must
	contain a tag that has the value 1 while sound is being played and 0
	otherwise. By default, this tag is refered to as "playback".
	'''
	if proc=="all":
		while any(get(variable=tagname, n_samples=1, proc=p) for proc in _procs.keys()):
			time.sleep(0.01)
	else:
		while get(variable=tagname, n_samples=1, proc=proc):
			time.sleep(0.01)

def get_speaker_from_direction(azimuth=0, elevation=0):
	'''
	Returns the channel and processor that the speaker at a given azimuth
	and elevation is attached to.
	'''
	table = filter_table(azimuth=[str(azimuth)], elevation=[str(elevation)])
	proc = table["proc"]
	channel = table["index"]
	return int(channel[0]), proc[0]

def get_speaker_position(number, proc=None):
	"""
	return azimuth or azimuth and elevation (for dome and arc respectively) for
	a given speaker. The speaker can be defined by the ongoing number, or
	by index numer & processor.
	"""
	if _setup == "arc": #only return azimuth
		if proc is not None:
			table=filter_table(index=[str(number)], proc=[proc])
		else:
			table=filter_table(ongoing=[str(number)])
		return float(table["azimuth"][0])
	elif _setup == "dome": #return azimuth and elevation
		if proc is not None:
			table=filter_table(index=[str(number)], proc=[proc])
		else:
			table=filter_table(ongoing=[str(number)])
		return float(table["azimuth"][0]), float(table["elevation"][0])

def get_speaker_from_number(number):
	table = filter_table(ongoing=[str(number)])
	proc = table["proc"]
	channel = table["index"]
	return int(channel[0]), proc[0]

# other functions to access the freefield table here
def _read_table(fname):
	handle = open(fname, encoding="utf8")
	reader = csv.reader(handle)
	headers = reader.__next__()
	table = {}
	for h in headers:
		table[h] = []
	for row in reader:
		for h, v in zip(headers, row):
			table[h].append(v)
	return table

def filter_table(**kwargs):
	"""
	Read table and filter for keyword arguments. Only accepts lists of strings.
	TODO: should result in an error instead of returning empty lists.
	"""
	table=_speakertable
	if len(kwargs)==0:
		raise ValueError("Need a keyword to filter table!")
	for title, values in kwargs.items():
		tmp = {}
		for key in _speakertable:
			tmp[key] = []
		for value in values:
			pos = np.where(np.asanyarray(table[title]) == value)[0]
			for j in pos:
				for key in table.keys():
					tmp[key].append(table[key][j])
		table = tmp

	return table

def set_signal_and_speaker(signal=None, speaker_number=0, apply_calibration=True):
	'''
	Upload a signal to the correct RX8 (signal on the other one stays the same)
	and channel. If apply_calibration=True, apply the speaker's inverse filter
	before upoading.
	'''
	if apply_calibration:
		signal = _calibration_filter.channel(speaker_number).apply(signal)
	set(variable='chan', value=speaker_number, proc='RX81')
	set(variable='chan', value=speaker_number-24, proc='RX82')
	# TODO: this assumes higher chan numbers are on RX82 - might not be true for dome?

# functions implementing complete procedures
def calibrate():
	'''
	Calibrate all speakers in the array by presenting a sound from each one,
	recording, computing inverse filters, and saving the calibration file.
	'''
	slab.Signal.set_default_samplerate(48828.125)
	sig = slab.Sound.chirp(duration=10000, from_freq=100, to_freq=None, kind='quadratic')
	initialize(rcx_file_name_RX8_1='calibration_RX8.rco', rcx_file_name_RX8_2='calibration_RX8.rco', rcx_file_name_RP2='calibration_RP2.rco')
	input('Set up microphone. Press any key to start calibration...')
	set(variable='signal', value=sig, proc='RX8s')
	recording = numpy.zeros((sig.nsamples,48))
	for speaker in range(48):
		set(variable='chan', value=speaker+1, proc='RX8s')
		for i in range(10):
			trigger() # zBusA by default
			wait_to_finish_playing()
			if i == 0: # first iteration
				rec = get(variable='recording', proc='RP2')
			else:
				rec = rec + get(variable='recording', proc='RP2')
		recording[:,speaker] = rec / 10 # averaging
	recording = slab.Sound(recording) # make a multi-channel sound objects
	#filt = # make inverse filter
	# rename old filter file, if it exists, by appending current date
	filt.save(_calibration_file) # save filter file to 'calibration_arc.npy' or dome.

def _initialize_processor(device_type, rcx_file, index, connection="GB"):

	try:
		RP = win32com.client.Dispatch('RPco.X')
	except win32com.client.pythoncom.com_error as e:
		print("Error:", e)
		return -1

	if device_type == "RP2":
		if RP.ConnectRP2(connection, index):
			print("Connected to RP2")
	elif device_type == "RX8":
		if RP.ConnectRX8(connection, index):
			print("Connected to RX8")
	else:
		print("Error: unknown device type!")
		return -1

	if not RP.ClearCOF():
		print("ClearCOF failed")
		return -1

	if RP.LoadCOF(rcx_file):
		print("Circuit {0} loaded".format(rcx_file))
	else:
		print("Failed to load {0}".format(rcx_file))
		return -1

	if RP.Run():
		print("Circuit running")
	else:
		print("Failed to run {0}".format(rcx_file))
		return -1

	return RP

def _initialize_zbus(connection="GB"):

	try:
		ZB = win32com.client.Dispatch('ZBUS.x')
	except win32com.client.pythoncom.com_error as e:
		print("Error:", e)
		return -1
	print("Successfully initialized ZBus")

	if ZB.ConnectZBUS(connection):
		print("Connected to ZBUS")
	else:
		print("failed to connect to ZBUS")

	return ZB