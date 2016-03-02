from __future__ import division
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

all_data = pd.read_csv('ASR_Output.csv', index_col=0)
state_times = pd.read_csv('/Users/admin/Desktop/Safer_ASR/callout_state_times.csv')

all_data = all_data[all_data['Callout Time'] >= 0][all_data['State Time'] >= 0]

all_data['delta_t'] = all_data['Callout Time'] - all_data['State Time']
all_data['abs_delta_t'] = abs(all_data['Callout Time'] - all_data['State Time'])

good_calls = all_data.query('abs_delta_t <= 3')

g1 = good_calls.query('Subject <= 10')
g1['Group'] = 1
g2 = good_calls.query('Subject > 10')
g2['Group'] = 2

g1s = state_times.query('Subject <= 10')
g1s['Group'] = 1
g2s = state_times.query('Subject > 10')
g2s['Group'] = 2

state_times = pd.concat([g1s, g2s])
good_calls = pd.concat([g1, g2])

good_calls = good_calls.rename(columns={"Callout Value": "Callout"})


sns.boxplot(x='Trial', y='delta_t', hue='Group', data=good_calls)
plt.savefig('Box_by_Trial.pdf')
plt.close('all')
good_calls = good_calls.sort_values(by = ['Callout'])

sns.boxplot(x='Callout', y='delta_t', hue='Group', data=good_calls)
plt.savefig('Box_by_callout.pdf')
plt.close('all')

good_calls['Trial'] -= 2
df = good_calls
df = df.query('Trial>0')

m = df.groupby(('Group', 'Trial')).mean().reset_index()
s = df.groupby(('Group', 'Trial')).sem().reset_index()

f, ax = plt.subplots()
ax.errorbar(m.query('Group == 1').Trial,
			m.query('Group == 1').abs_delta_t,
			yerr=s.query('Group == 1').abs_delta_t,
			color='r', label='Group 1')
ax.errorbar(m.query('Group == 2').Trial,
			m.query('Group == 2').abs_delta_t,
			yerr=s.query('Group == 2').abs_delta_t,
			color='b', label='Group 2')
plt.legend()
plt.margins(0.05)
plt.show()

plt.close('all')

state_count = state_times.groupby(('Group', 'Trial')).count().reset_index()
call_count = good_calls.groupby(('Group', 'Trial')).count().reset_index()
percent = (call_count.delta_t/state_count.Time).dropna()
pd.merge(state_count, call_count,on=['Group','Trial'], how='left')
state_count['Percent'] = call_count['delta_t']/state_count['Time']
state_count.groupby('Group').Percent.agg(["mean", "sem"])

df = state_count

m = df.groupby(('Group', 'Trial')).mean().reset_index()
s = df.groupby(('Group', 'Trial')).sem().reset_index()

f, ax = plt.subplots()
ax.errorbar(m.query('Group == 1').Trial,
			m.query('Group == 1').Percent,
			yerr=s.query('Group == 1').Percent,
			color='r', label='Group 1')
ax.errorbar(m.query('Group == 2').Trial,
			m.query('Group == 2').Percent,
			yerr=s.query('Group == 2').Percent,
			color='b', label='Group 2')
plt.legend()
plt.margins(0.05)
plt.show()