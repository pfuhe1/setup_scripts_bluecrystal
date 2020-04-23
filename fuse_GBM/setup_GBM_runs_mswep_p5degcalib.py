# script to setup and submit FUSE gridded runs
# Peter Uhe Aug 21 2019
# 

import os,glob,subprocess,sys,shutil
import datetime
import queue
import socket



# User choice
# TODO: first call script to produce different calibration files. (src/fuse_processing/generate_param_maps.py
fuse_decision_ids = [900,902,904]
#calib_choices = ['rundef','calibratedparams']
#calib_choices = ['calibrated1','calibrated2','calibrated3',]
#calib_choices = ['MSWEPp5degcalibrated1','MSWEPp5degcalibrated2','MSWEPp5degcalibrated3']
calib_choices = ['MSWEPp5degcalibrateRand0001','MSWEPp5degcalibrateRand0002','MSWEPp5degcalibrateRand0003','MSWEPp5degcalibrateRand0004','MSWEPp5degcalibrateRand0005','MSWEPp5degcalibrateRand0006','MSWEPp5degcalibrateRand0007','MSWEPp5degcalibrateRand0008','MSWEPp5degcalibrateRand0009','MSWEPp5degcalibrateRand0010','MSWEPp5degcalibrateRand0011','MSWEPp5degcalibrateRand0012','MSWEPp5degcalibrateRand0013','MSWEPp5degcalibrateRand0014','MSWEPp5degcalibrateRand0015','MSWEPp5degcalibrateRand0016','MSWEPp5degcalibrateRand0017','MSWEPp5degcalibrateRand0018','MSWEPp5degcalibrateRand0019']
setup_name = 'GBM-tiled2-2'
ssim = '1980-01-01'
esim = '2013-12-31'

override = True

###################################################################################
# Define computer specific paths/variables
host=socket.gethostname()
if host[:7]=='newblue':
	# Blue Crystal Phase 3
	fm_template = '/newhome/pu17449/src/fuse_templates/fm_template_mswep_p5deg.txt'
	qsub_script = '/newhome/pu17449/src/setup_scripts/fuse_GBM/call_pythonscript.sh' 
	basedir = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2'
	qsub_command = ['qsub','-v','FM_FLIST,LOGDIR,NCPUS,FUSE_EXE',qsub_script]
	fuse_exe = '/newhome/pu17449/src/fuse/bin/fuse.exe'
	ncpus = 16
	nperjob = 9999
elif host[:8] == 'bc4login':
	fm_template = '/mnt/storage/home/pu17449/src/fuse_templates/fm_template_mswep_p5deg.txt'
	qsub_script = '/mnt/storage/home/pu17449/src/setup_scripts/fuse_GBM/call_pythonscript_bc4serial.sh'
	basedir = '/mnt/storage/home/pu17449/scratch/fuse/fuse_GBM_v2-2'
	ncpus = 1
	nperjob = 23
	fuse_exe =  '/mnt/storage/home/pu17449/src/fuse/bin/fuse.exe'
	qsub_command = ['sbatch','--export','FM_FLIST,LOGDIR,NCPUS,FUSE_EXE',qsub_script]


###################################################################################
# Fuse folder paths

settingsdir = os.path.join(basedir,'settings')
# Standard input is from EWEMBI. TODO for future runs with different forcings, use different folders
inputdir    = os.path.join(basedir,'input')
outputdir    = os.path.join(basedir,'output')
logdir    = os.path.join(basedir,'logs')
if not os.path.exists(logdir):
	os.mkdir(logdir)

###################################################################################
# Export environment variables used by all QSUB commands
os.environ['NCPUS'] = str(ncpus)
os.environ['FUSE_EXE'] = fuse_exe
os.environ['LOGDIR'] = logdir


###################################################################################
sublist = []
# Loop over runs to submit and add fm_file to sublist for submission
for dec in fuse_decision_ids:
	for calib in calib_choices:
		sim_name = setup_name+'_'+str(dec)+'_'+calib
		print(sim_name)
		
		if calib == 'rundef':
			out_file = os.path.join(outputdir,sim_name+'runs_def.nc')
		else:
			out_file = os.path.join(outputdir,sim_name+'runs_pre_dist.nc')

		# Check if this run has already been computed
		if not os.path.exists(out_file):

			fm_file = os.path.join(settingsdir,'fm_'+sim_name+'.txt')
		
			if os.path.exists(fm_file) and override:
				os.remove(fm_file)

			# copy fuse filemanager template and modify
			if not os.path.exists(fm_file):
				shutil.copy(fm_template,fm_file)
				sed_expr =  's#<settings_dir>#'+settingsdir+'#g; '
				sed_expr += 's#<input_dir>#'+inputdir+'#g; '
				sed_expr += 's#<output_dir>#'+outputdir+'#g; '
				sed_expr += 's#<decid>#'+str(dec)+'#g; '
				sed_expr += 's#<calibid>#'+calib+'#g; '
				sed_expr += 's#<s_sim>#'+ssim+'#g; '
				sed_expr += 's#<e_sim>#'+esim+'#g; '
				sed_expr += 's#<s_eval>#'+ssim+'#g; '
				sed_expr += 's#<e_eval>#'+esim+'#g'
				cmd = ['sed','-i','-e',sed_expr ,fm_file]
				print(cmd)
				subprocess.call(cmd)
		
			# add fm_file to sublist
			sublist.append(fm_file)

			# submit nperjob simulations at a time
			if len(sublist)==nperjob:
				print('Submitting jobs',len(sublist))
				# First export environment variables used in the job
				os.environ['FM_FLIST']=':'.join(sublist)
				print(os.environ['FM_FLIST'])
				subprocess.call(qsub_command)
				# Reset submit list
				sublist = []

		else:
			print('Output file already exists, skipping:',out_file)


# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	os.environ['FM_FLIST']=':'.join(sublist)
	print(os.environ['FM_FLIST'])
	# Submit to compute queue
	subprocess.call(qsub_command)
	#subprocess.call([qsub_script]) # call on login node for debugging
else:
	print('No more simulations to submit!')
