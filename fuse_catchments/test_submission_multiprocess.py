#!/usr/bin/python
# PBS batch resources
#PBS -l mem=16000mb
#PBS -l nodes=1:ppn=16 
#PBS -l walltime=12:00:00
#PBS -j oe
##!/cm/shared/languages/python-3.3.2/bin/python
# submit script for FUSE calibration of GRDC catchments
# Peter Uhe May 15 2019
# 

# call this script from 'setup_grdc_catch_best73.py

import os,glob,subprocess,sys,shutil,multiprocessing
import datetime

logfile = 'test_hello.log'
# Print start time 
print(datetime.datetime.now())
# First load modules needed

#fm_files = sys.argv[1:]
pool = multiprocessing.Pool(processes=1)

cmd = ['echo','hello_test']
print('command',cmd)
print('log',logfile)
ret = pool.apply_async(subprocess.call,cmd,{'stdout':open(logfile,'w') ,'stderr':subprocess.STDOUT})
pool.close()
pool.join()

print(ret.get())
