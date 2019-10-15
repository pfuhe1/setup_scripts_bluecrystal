#!/cm/shared/languages/python-3.3.2/bin/python
# submit script for FUSE calibration of GRDC catchments
# Peter Uhe May 15 2019
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
print('running simulations',len(fm_files))
print(os.environ['FM_FLIST'])
pool = multiprocessing.Pool(processes=16)

for fm_file in fm_files:
	# Todo, could add check if this simulation has already been run
	fname = os.path.basename(fm_file)
	grdcid = fname.split('_')[2]
	sim_name = 'grdc_'+grdcid
	logfile = os.path.join('/newhome/pu17449/data/fuse/grdc_catchments/fuse_'+sim_name+'/logs/'+fname[3:-4]+'.log')
	cmd = ['time','/newhome/pu17449/src/fuse/bin/fuse.exe',fm_file,sim_name,'calib_sce']
	print('command',cmd)
	print('log',logfile)
	#ret = pool.apply_async(subprocess.call,cmd,{'stdout':open(logfile,'w') ,'stderr':subprocess.STDOUT})
	#subprocess.call(cmd,stdout=open(logfile,'w'),stderr=subprocess.STDOUT)
	ret = pool.apply_async(call_subproc,[cmd,logfile])
pool.close()
pool.join()

print(ret.get())
