#!/cm/shared/languages/python-3.3.2/bin/python
# submit script for running lisflood runs in parallel
# Peter Uhe May 15 2019
# 

import os,subprocess,multiprocessing
import datetime
from convert_output_totiff import convert_to_tif_v2

def call_subproc(cmd,sim_name,logfile):
	print('command',cmd)
	print('log',logfile)
	ret = subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)
	# converts to tiff, relies on output being in folder relative to working directory
	convert_to_tif_v2(sim_name,sim_name)
	return ret
	

# Print start time 
print('Start:',datetime.datetime.now())

control_files = os.environ['CONTROL_FLIST'].split(':')
exefile = os.environ['EXEFILE']
# Work out number of concurrent processes to run, based on node size and number of processes per job
nodesize = int(os.environ['NODESIZE'])
jobsize = int(os.environ['OMP_NUM_THREADS'])
logdir = os.environ['LOGDIR']
numprocesses = int(nodesize/jobsize)

print('running simulations',len(control_files))
print(os.environ['CONTROL_FLIST'])
pool = multiprocessing.Pool(processes=numprocesses) # since node has 16 cores, and OMP_NUM_THREADS=2

for control_file in control_files:
	# Todo, could add check if this simulation has already been run
	fname = os.path.basename(control_file)
	sim_name =fname[:-4]
	logfile = os.path.join(logdir,sim_name+'.log')
	cmd = ['time',exefile,'-v',control_file]
	#ret = pool.apply_async(subprocess.call,cmd,{'stdout':open(logfile,'w') ,'stderr':subprocess.STDOUT})
	#subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)
	ret = pool.apply_async(call_subproc,[cmd,sim_name,logfile])
pool.close()
pool.join()

print(ret.get())
print('Finished:',datetime.datetime.now())
