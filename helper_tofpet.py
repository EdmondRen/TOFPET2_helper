import numpy as np
import ROOT


from collections.abc import Sequence


import configparser
import os.path
import re
from sys import stdout,stderr
import bitarray
import math, pprint, argparse, time
from functools import reduce

import joblib
import scipy
from scipy import ndimage, signal, interpolate
import csv
from pylab import *

from petsysbuild.petsys import tofpet2b, tofpet2c, fe_power, daqd, config




mpl_colors = np.array([ROOT.kAzure+4,
ROOT.kOrange-3,
ROOT.kTeal+4,
ROOT.kPink-1,
ROOT.kViolet-7,
ROOT.kRed-1,
ROOT.kMagenta-9,
ROOT.kGray+1,
ROOT.kYellow+1,
ROOT.kCyan+1,
ROOT.kAzure+4+1,
ROOT.kOrange-3+1,
ROOT.kTeal+4+1,
ROOT.kPink-1+1,
ROOT.kViolet-7+1,
ROOT.kRed-1+1,
ROOT.kMagenta-9+1,
ROOT.kGray+1+1,
ROOT.kYellow+1+1,
ROOT.kCyan+1+1], dtype=np.int16)
mpl_colors32 = np.array(mpl_colors, dtype=np.int32)



class mpl_colors_cls(Sequence):
    mpl_colors = np.array([ROOT.kAzure+4,
ROOT.kOrange-3,
ROOT.kTeal+4,
ROOT.kPink-1,
ROOT.kViolet-7,
ROOT.kRed-1,
ROOT.kMagenta-9,
ROOT.kGray+1,
ROOT.kYellow+1,
ROOT.kCyan+1,
ROOT.kAzure+4+1,
ROOT.kOrange-3+1,
ROOT.kTeal+4+1,
ROOT.kPink-1+1,
ROOT.kViolet-7+1,
ROOT.kRed-1+1,
ROOT.kMagenta-9+1,
ROOT.kGray+1+1,
ROOT.kYellow+1+1,
ROOT.kCyan+1+1], dtype=np.int16)
    def __init__(self):
        super().__init__()
    def __getitem__(self, i):
        return int(self.mpl_colors[i%len(self.mpl_colors)])
    def __len__(self):
        return len(self.mpl_colors)
    

def decomp_channelID(channelIDabs):
    portID, slaveID, chipID, channelID = channelIDabs>>17, channelIDabs>>12 & 0b11111, channelIDabs>>6 & 0b111111, channelIDabs & 0b111111
    return portID, slaveID, chipID, channelID        
	
class staircase:
	@staticmethod
	def take_staircase(args, channels=None):
		"""
		INPUT:
		args:class
			examples:
			class args:
				data_dir = "/mnt/sda2/tofpet_data/test_stand_init/"
				config = f"{data_dir}/config.ini"
				output = f"{data_dir}/disc_staircase_all_channels_temp_"
				dark_reads = 2 # Each counter period is 0.08s, 5 reads->0.4s
				disc_lsb_t1 = 55
				disc_lsb_t2 = 55
				disc_lsb_e = 48  # Default is 40		
		channels: list of channels or None
			Each "channel" is a tuple of (portID, slaveID, chipID, channelID)
			If not given, all channels will be measured
		"""
		# Some constant numbers
		# Counter period is set to 0b111 = 2^24 cycles
		COUNT_MAX = 1.0 * (2**24)
		BIAS_ON = True

		TriggerList = [ 
			(0,  "vth_t1", [0,0,0,0]),
			(1,  "vth_t2", [0,0,1,3]),
				(2,  "vth_e",  [3,2,2,2])
			]


		#######################
		# DAQ setup
		# Open daqd driver
		idaqd = daqd.Connection()
		idaqd.initializeSystem()
		CLK_FREQ = idaqd.getSystemFrequency()
		T = COUNT_MAX * (1 / CLK_FREQ)
		counter_sharing = 1
		print("* System CLK frequency: ",CLK_FREQ)

		# Get active Asics and Channels
		activeAsics = idaqd.getActiveAsics()
		activeChannels = [ (portID, slaveID, chipID, channelID) for channelID in range(64) for portID, slaveID, chipID in activeAsics ]

		# Apply configuration file
		systemConfig = config.ConfigFromFile(args.config, loadMask=config.LOAD_ALL^config.LOAD_QDCMODE_MAP)
		systemConfig.loadToHardware(idaqd, bias_enable=config.APPLY_BIAS_OFF)

		# Get Asic configurations
		asicsConfig = idaqd.getAsicsConfig()

		# Setup counter, discriminator LSB
		for (portID, slaveID, chipID), ac in list(asicsConfig.items()):
			if not ac: continue
			gc = ac.globalConfig
			
			if idaqd.getAsicSubtype(portID, slaveID, chipID) == "2B":
				COUNTER_SETTING = 0x4
			else:
				COUNTER_SETTING = 0b111

			# print(portID, slaveID, chipID, COUNTER_SETTING)
			gc.setValue("counter_en", 0b1)
			gc.setValue("counter_period", COUNTER_SETTING)
			gc.setValue("disc_lsb_t1", args.disc_lsb_t1)
			gc.setValue("disc_lsb_t2", args.disc_lsb_t2)
			gc.setValue("disc_lsb_e", args.disc_lsb_e)

			for cc in ac.channelConfig:
				cc.setValue("trigger_mode_1", 0)
				cc.setValue("counter_mode", 0x2) # Count valid events
				cc.setValue("trigger_b_latched", 0)

		# Get a list of channels to scan
		channels_masked=[]
		if channels is None:
			channels=activeChannels
		else:
			for ch in activeChannels:
				if ch not in channels:		
					channels_masked.append(ch)
					
		# ----------------------------------------------------
		# Measure  trigger rate w.r.t a trigger threshold
		# ----------------------------------------------------
		print(f"Scanning trigger rate w.r.t. different discriminators")

		if BIAS_ON:
			systemConfig.loadToHardware(idaqd, bias_enable=config.APPLY_BIAS_ON)
			print("Bias voltage turned ON!")

		data_save = {}
		for ind, trigger_type, trigger_mode_setting in TriggerList:

			stdout.write(f"  {trigger_type}"); stdout.flush()

			# Dictionary to hold the output
			outdata = {}
			for portID, slaveID, chipID, channelID in channels:
				outdata[(portID, slaveID, chipID, channelID)]={}
				for thresholdValue in range(0,62):
					outdata[(portID, slaveID, chipID, channelID)][thresholdValue]=[]

			# Set the unused channels to the highest threshold
			for portID, slaveID, chipID, channelID in channels_masked:
				systemConfig.mapAsicChannelThresholdToDAC((portID, slaveID, chipID, channelID), "vth_t1", 62)
				systemConfig.mapAsicChannelThresholdToDAC((portID, slaveID, chipID, channelID), "vth_t2", 62)
				systemConfig.mapAsicChannelThresholdToDAC((portID, slaveID, chipID, channelID), "vth_e", 62)

			# Scan threshold values
			for thresholdValue in range(0,62):
				for portID, slaveID, chipID, channelID in channels:
					cc = asicsConfig[(portID, slaveID, chipID)].channelConfig[channelID]

					dac_setting = systemConfig.mapAsicChannelThresholdToDAC((portID, slaveID, chipID, channelID), trigger_type, int(thresholdValue))

					cc.setValue(trigger_type, dac_setting) # Set threshold
					cc.setValue("trigger_mode_2_t", trigger_mode_setting[0])    # Set trigger to be single threshold on t1
					cc.setValue("trigger_mode_2_q", trigger_mode_setting[1])
					cc.setValue("trigger_mode_2_e", trigger_mode_setting[2])
					cc.setValue("trigger_mode_2_b", trigger_mode_setting[3])
					if ind==1:
						vth_t1_temp = systemConfig.mapAsicChannelThresholdToDAC((portID, slaveID, chipID, channelID), "vth_t1", 15)
						cc.setValue("vth_t1", vth_t1_temp) # For the scan of vth_t2, there is no t2 only trigger, need to set vth_t1 to a low value


				idaqd.setAsicsConfig(asicsConfig)
				time.sleep(1*T)
				next_read_start_time = time.time() + counter_sharing*T + 1E-3
				for n in range(args.dark_reads):
					s = next_read_start_time - time.time()
					if s > 0: time.sleep(s)
					next_read_start_time = time.time() + counter_sharing*T + 1E-3
					for portID, slaveID, chipID in activeAsics:
						vv = idaqd.read_mem_ctrl(portID, slaveID, 5, 24, 64*chipID, 64)
						for channelID, v in enumerate(vv):
							if (portID, slaveID, chipID, channelID) in channels:
								# Write out the number of triggers per second
								# -- v from vv is the counter value, divided by the max counter period T 
								v = v/T
								outdata[(portID, slaveID, chipID, channelID)][thresholdValue].append(v)


				stdout.write(".")
				stdout.flush()
				
			stdout.write("\n")
			data_save[trigger_type] = outdata


		if BIAS_ON:
			systemConfig.loadToHardware(idaqd, bias_enable=config.APPLY_BIAS_OFF)
			print("Bias voltage turned OFF!")	

		return data_save

	@staticmethod
	def find_threshold(thresholds, trigger_rate, target_npe, ):
		"""
		calculate the threshold at given rate

		INPUT:
		
		"""
		trigger_rate=np.array(trigger_rate)
		trigger_rate[trigger_rate<=0]=1e-10
		trigger_rate_diff = -scipy.ndimage.gaussian_filter(np.log10(trigger_rate), sigma=1.2, order=1)

		# Interpolate
		trigger_rate_curve = scipy.interpolate.interp1d(thresholds, trigger_rate_diff, kind="quadratic")
		thresholds_interp = np.linspace(thresholds[0], thresholds[-1], 512)
		rate_inter = trigger_rate_curve(thresholds_interp)
		# Find peaks
		peaks, prop = scipy.signal.find_peaks(rate_inter, 
												height = 0.1, prominence = 0.05)   
		if len(peaks)<2:
			raise Exception("Not enough peaks found, cannot set threshold")


		# Use the largest two peaks as first and second pe peak
		# inds_sort = np.argsort(prop["peak_heights"])
		# peaks_sorted = np.array(peaks)[inds_sort[::-1]]
		peaks_sorted = peaks

		baseline = 2*thresholds_interp[peaks_sorted[0]] - thresholds_interp[peaks_sorted[1]]
		amp_1pe = thresholds_interp[peaks_sorted[1]] - thresholds_interp[peaks_sorted[0]]


		# plot(thresholds_interp, rate_inter) 
		# axvline(baseline)
		# axvline(baseline+1.5*amp_1pe)
		return baseline + target_npe*amp_1pe

	@staticmethod
	def plot_staircase(data, channels = None, plot_all_channels=True, plot_legend=True):
		channels = data.keys() if channels is None else channels

		curve_save = {}
		channel_count=0
		for ch in channels:
			thresholds = list(data[ch].keys())
			trigger_rate = [np.mean(data[ch][th]) for th in data[ch].keys()]

			if np.max(trigger_rate[12:])>0 or plot_all_channels:

				plot(thresholds, trigger_rate, label = f"{ch}")
				channel_count+=1
				curve_save[ch] = [thresholds, trigger_rate]

		print(f"Found {channel_count} channels")
		yscale("log")
		xlabel("Trigger threshold [DAC unit]")
		ylabel("Rate [Hz]")
		gca().xaxis.set_minor_locator(plt.MultipleLocator(1))
		gca().xaxis.set_major_locator(plt.MultipleLocator(10))
		grid(which="major")
		grid(which="minor", alpha=0.4)
		if plot_legend: 
			legend(loc="best", fontsize=9)
		return curve_save

	@staticmethod
	def process_staircase(curve_save, channels, target_rate=None, target_npe=None, make_plot=False, label=""):
		channels_info= {}
		for ch in channels:
			channels_info[ch]={}
			thresholds, trigger_rate = curve_save[ch]
			# Find threshold at given rate
			if target_rate is not None:
				threshold_set = thresholds[np.argmax(np.array(trigger_rate)<target_rate)]
				channels_info[ch]["threshold"] = threshold_set

			# Find threshold at given number of photo-electrons (target_npe)
			elif target_npe is not None and  1<target_npe<20:
				threshold_npe = staircase.find_threshold(thresholds, trigger_rate, target_npe)
				threshold_set = int(round(threshold_npe))


			if threshold_set<=2:
				print("[Warning] threshold is less than 2 for channel", ch)
				threshold_set=10

			if threshold_set>62:
				print("[Warning] threshold is larger than 62 for channel", ch)
				threshold_set=62				

			if trigger_rate[thresholds.index(threshold_set)]>300e3 or trigger_rate[threshold_set]<20:
				print(f"[Warning] rate {trigger_rate[thresholds.index(threshold_set)]} Hz for channel", ch)

			channels_info[ch]["threshold"] = threshold_set

			plot(thresholds, trigger_rate)
			plot(threshold_set, trigger_rate[thresholds.index(threshold_set)], marker="*", markersize=10)
			title(label+f" {ch}")
			xlabel("Threshold")
			ylabel("Rate [Hz]")
			yscale("log")
			show()

		return channels_info


	@staticmethod
	def update_discriminator(filename, channel_info, verbose=False):
		threshold_row_map = {
		"vth_t1": 4,
		"vth_t2": 5,
		"vth_e": 6,
		}

		# Open the file
		with open(filename, 'r') as f:
			output = [f.readline()]
			for line in f:
				output.append(line)


		# Update the content
		for key in channel_info:
			info = channel_info[key]
			threshold_row = threshold_row_map[key]

			for ch in info:
				for iline in range(1, len(output)):
					line = output[iline]
					content = [int(ii) for ii in line.split("\t")]
					if tuple(content[:4])==ch:
						# Print only if the new value is different from the old one
						if content[threshold_row]!=info[ch]["threshold"]:
							print(key, ch, "threshold old", content[threshold_row], "threshold_new", info[ch]["threshold"])
						content[threshold_row] = info[ch]["threshold"]
						output[iline] = reduce(lambda x, y: str(x) + '\t' + str(y), content)+"\n"
						continue


		# Write the file
		os.rename(filename, filename+".backup")
		with open(filename, 'w', newline='') as f:
			f.writelines(output)