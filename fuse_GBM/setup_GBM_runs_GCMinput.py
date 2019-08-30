# script to setup and submit FUSE gridded runs
# Peter Uhe Aug 21 2019
# 

import os,glob,subprocess,sys,shutil
import datetime
import queue



# User choice
# TODO: first call script to produce different calibration files. (src/fuse_processing/generate_param_maps.py
fuse_decision_ids = [900,902,904]
calib_choices = ['rundef','calibratedparams']
gcm_runs = ['NorESM1-HAPPI_Plus15-Future_run001_EWEMBI']
setup_name = 'GBM-tiled2-2'
#ssim = '1980-01-01'
#esim = '2013-12-31'
ssim = '2106-04-01'
esim = '2115-12-31'

override = True

# Define paths
fm_template = '/newhome/pu17449/src/fuse_templates/fm_template_gcms.txt'
#settingsdir = os.path.join(templatedir,'settings_dir')

#basedir = os.path.join('/newhome/pu17449/data/fuse',setup_name)
basedir = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2'
settingsdir = os.path.join(basedir,'settings')
# Standard input is from EWEMBI. TODO for future runs with different forcings, use different folders
inputdir    = os.path.join(basedir,'input')
outputdir    = os.path.join(basedir,'output')
logdir    = os.path.join(basedir,'logs')
if not os.path.exists(logdir):
	os.mkdir(logdir)

qsub_script = '/newhome/pu17449/src/setup_scripts/fuse_GBM/call_pythonscript.sh' # use this one so we can load python3 module before calling python
sublist = []

for dec in fuse_decision_ids:
	for calib in calib_choices:
		for gcm_id in gcm_runs:
			sim_name = setup_name+'_'+str(dec)+'_'+calib+'_'+gcm_id
			print(sim_name)

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
			sed_expr += 's#<gcmid>#'+gcm_id+'#g; '
			sed_expr += 's#<s_sim>#'+ssim+'#g; '
			sed_expr += 's#<e_sim>#'+esim+'#g; '
			sed_expr += 's#<s_eval>#'+ssim+'#g; '
			sed_expr += 's#<e_eval>#'+esim+'#g'
			cmd = ['sed','-i','-e',sed_expr ,fm_file]
			print(cmd)
			subprocess.call(cmd)
		
		# add fm_file to sublist
		sublist.append(fm_file)

		# submit 16 files at a time
#		if len(sublist)==16:
#			# Set list of fm files as environment variable
#			os.environ['FM_FLIST']=','.join(sublist)
#			subprocess.call(['qsub',qsub_script])
			# Reset submit list
#			sublist = []


# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	os.environ['FM_FLIST']=':'.join(sublist)
	os.environ['LOGDIR']=logdir
	print(os.environ['FM_FLIST'])
	# Submit to compute queue
	subprocess.call(['qsub','-v','FM_FLIST,LOGDIR',qsub_script])
	#subprocess.call([qsub_script]) # call on login node 
else:
	print('No more simulations to submit!')
