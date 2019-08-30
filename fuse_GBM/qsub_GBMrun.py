#!/cm/shared/languages/python-3.3.2/bin/python
# submit script for FUSE calibration of GRDC catchments
# Peter Uhe Aug 21 2019
# 

# call this script from 'setup_grdc_catch_best73.py which creates a qsub job to submit to the HPC queue
# This script is actually called from 'call_pythonscript.sh' (which is needed to load the python module before calling the script)

import os,glob,subprocess,sys,shutil,multiprocessing
import datetime

def call_subproc(cmd,logfile):
	subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)

# Print start time 
print(datetime.datetime.now())
# First load modules needed 
# python2
#execfile('/cm/local/apps/environment-modules/3.2.6//Modules/3.2.6/init/python')
# python3
#exec(open('/cm/local/apps/environment-modules/3.2.6//Modules/3.2.6/init/python').read())
exec(open('/newhome/pu17449/src/setup_scripts/module_python3_init').read())
module('load','languages/intel-compiler-16-u2')
module('load','libraries/intel_builds/netcdf-4.3')
module('load','libraries/intel_builds/hdf5-1.8.12')
module('list')

#fm_files = sys.argv[1:]
fm_files = os.environ['FM_FLIST'].split(':')
logdir = os.environ['LOGDIR']
print('running simulations',len(fm_files))
print(os.environ['FM_FLIST'])
pool = multiprocessing.Pool(processes=16)

for fm_file in fm_files:
	# Todo, could add check if this simulation has already been run
	fname = os.path.basename(fm_file)
	settingsdir = os.path.dirname(fm_file)
	sim_name = fname[3:-4]
	# Sim name has format FUSEsetup_FUSEdecison_FUSEcalib_<GCM-runstring>
#	setup,dec,calib = sim_name.split('_')
	tmp = sim_name.split('_')
	setup = tmp[0]
	calib = tmp[2]
	calib_file = '_'.join(tmp[:3])+'.nc'
#	calib_file = sim_name+'.nc' # Calib file is in output directory
	logfile = os.path.join(logdir,sim_name+'.log')
	if calib == 'rundef':
		cmd = ['time','/newhome/pu17449/src/fuse/bin/fuse.exe',fm_file,setup,'run_def']
	else:
		cmd = ['time','/newhome/pu17449/src/fuse/bin/fuse.exe',fm_file,setup,'run_pre_dist',calib_file]
	print('command',cmd)
	print('log',logfile)
	#ret = pool.apply_async(subprocess.call,cmd,{'stdout':open(logfile,'w') ,'stderr':subprocess.STDOUT})
	#subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)
	ret = pool.apply_async(call_subproc,[cmd,logfile])
pool.close()
pool.join()

#print(ret.get())