from __future__ import division
import xml.etree.ElementTree as ET
import os
import re
import pandas as pd
import numpy as np
import time
import seaborn as sns
import matplotlib.pyplot as plt


subject_directory = '/Users/admin/Desktop/Safer_ASR/asr_logs'

subject_file_names = os.listdir(subject_directory)

state_times = pd.read_csv('/Users/admin/Desktop/Safer_ASR/callout_state_times.csv')

def natural_sort(l): 
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanum_key)

subject_file_names = natural_sort(subject_file_names)

def get_callout_value(callout):
	tens = ['zero', 'ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
	ones = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
	callout_value = 0
	for word in callout.split():
		if word in tens:
			callout_value += tens.index(word)*10
		if word in ones:
			callout_value += ones.index(word)
		if word == 'hundred':
			callout_value += 100

	return callout_value


output = [[0,0,0,0]]

for subject_name in subject_file_names:
	if 'DS' not in subject_name:
		trial = subject_name
		if 'speech' in trial:
			tree = ET.parse(subject_directory + '/' + trial)
			root = tree.getroot()
			utters=root.findall("./turn/user_input/")
			if len(utters) > 0:
				hyps = root.findall("./turn/user_input/utterance/")
				subject_id = trial[15]
				if trial[16] != '_':
					subject_id = trial[15:17]
				trial_id = trial[trial.index('trial') + 6]
				if trial[trial.index('trial') + 7] != '_':
					trial_id += trial[trial.index('trial') + 7]
				dsf_time = trial[-27:-4]
				trial_start = root[0].attrib['start']
				asr_time = [u.attrib['start'] for u in utters]
				for i , utterance in enumerate(hyps):
					callout = ''
					for w in utterance:
						callout += w.text + ' '
					time = (float(asr_time[i]) - float(trial_start))/1000
					call_value = get_callout_value(callout)
					newrow = [int(subject_id), int(trial_id), call_value, time]
					output.append(newrow)

			elif 'log' in trial:
				logname = trial
				log = open(subject_directory + subject_name + '/' + logname)
				starts = []
				for line in log.readlines():
					if 'ASR task Started' in line:
						starts.append(line[0:12])
				starts = starts[1:44:2]

cols = ['Subject', 'Trial', 'fuel_remaining', 
			'Callout_Time']
data = pd.DataFrame(output)
data = data.drop(0)
data.columns = cols



merge1 = pd.merge(state_times, data, how='left', 
	on=['Subject', 'Trial', 'fuel_remaining'])
merge1['delta_t'] = abs(merge1.Time - merge1.Callout_Time)

good_calls = merge1.query('delta_t <= 3')
good_calls = good_calls.reset_index()
good_calls['Callout Value'] = good_calls['fuel_remaining']
good_calls['Callout ID'] =  3000 + good_calls['fuel_remaining']
del good_calls['delta_t']

bad_calls = merge1.query('delta_t > 3')
bad_calls = bad_calls.reset_index()
bad_calls['Callout ID'] = 3000 + bad_calls['fuel_remaining']
bad_calls['Callout Value'] = bad_calls['fuel_remaining']
bad_calls['fuel_remaining'] = -1*np.ones(len(bad_calls))
bad_calls['Time'] = -1*np.ones(len(bad_calls))
del bad_calls['delta_t']

missed_calls = merge1.query('Callout_Time != Callout_Time')
missed_calls = missed_calls.reset_index()
missed_calls['Callout ID'] = np.zeros(len(missed_calls))
missed_calls['Callout Value'] = -1*np.ones(len(missed_calls))
missed_calls['Callout_Time'] = -1*np.ones(len(missed_calls))
del missed_calls['delta_t']

merge2 = pd.merge(state_times, data, how='right', 
	on=['Subject', 'Trial', 'fuel_remaining'])
merge2['rem'] = merge2['fuel_remaining']%5
if merge2.query('fuel_remaining > 100').empty:
	other_calls = merge2.query('rem !=0')
else: 
	print "Well...Shit"
other_calls = other_calls.reset_index()
other_calls['Callout ID'] = 3000 + other_calls['fuel_remaining']
other_calls['Callout Value'] = other_calls['fuel_remaining']
other_calls['fuel_remaining'] = -1*np.ones(len(other_calls))
other_calls['Time'] = -1*np.ones(len(other_calls))
del other_calls['rem']


final_out = pd.concat([good_calls, bad_calls, missed_calls, other_calls], ignore_index=True)
final_out = final_out.rename(columns={"fuel_remaining": "State Value", "Callout_Time": "Callout Time", "Time": "State Time"})
final_out = final_out.sort_values(by = ['Subject', 'Trial', 'State Time', 'Callout Time'])
final_out = final_out[['Subject', 'Trial', 'Callout ID', 'Callout Value', 'State Time', 'State Value']]

final_out.to_csv('ASR_Output.csv')

good_calls['delta_t'] = good_calls['Callout_Time'] - good_calls['Time'] 
g1 = good_calls.query('Subject <= 10')
g1['Group'] = 1
g2 = good_calls.query('Subject > 10')
g2['Group'] = 2

good_calls = pd.concat([g1, g2])
good_calls = good_calls.sort_values(by = ['fuel_remaining'])

sns.boxplot(x='fuel_remaining', y='delta_t', hue='Group', data=good_calls)
plt.show()