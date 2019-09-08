#!/cm/shared/languages/python-3.3.2/bin/python
# submit script for running lisflood runs in parallel
# Peter Uhe May 15 2019
# 

import os,subprocess,multiprocessing
import datetime
from convert_output_totiff import convert_to_tif_v2

def call_subproc(cmd,sim_name,logfile):
	ret = subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)
	# converts to tiff, relies on output being in folder relative to working directory
	convert_to_tif_v2(sim_name,sim_name)
	return ret
	

# Print start time 
print('Start:',datetime.datetime.now())

control_files = os.environ['CONTROL_FLIST'].split(':')
print('running simulations',len(control_files))
print(os.environ['CONTROL_FLIST'])
pool = multiprocessing.Pool(processes=2) # since node has 16 cores, and OMP_NUM_THREADS=8

exefile = '/newhome/pu17449/src/pfu_d8subgrid/lisflood_double_rect_constchanwidth'

for control_file in control_files:
	# Todo, could add check if this simulation has already been run
	fname = os.path.basename(control_file)
	sim_name =fname[:-4]
	logfile = os.path.join('/newhome/pu17449/data/lisflood/logs/'+sim_name+'.log')
	cmd = ['time',exefile,'-v',control_file]
	print('command',cmd)
	print('log',logfile)
	#ret = pool.apply_async(subprocess.call,cmd,{'stdout':open(logfile,'w') ,'stderr':subprocess.STDOUT})
	#subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)
	ret = pool.apply_async(call_subproc,[cmd,sim_name,logfile])
pool.close()
pool.join()

print(ret.get())
print('Finished:',datetime.datetime.now())
