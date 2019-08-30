# script to setup FUSE calibration of GRDC catchments
# Peter Uhe May 15 2019
# 
# Assumes catchment_obsforcings_toBC3.py script has been run to copy the elev_bands and catchment_obsforcing files for each catchment
# Also requires list of catchment ids to process (f_catchlist)

import os,glob,subprocess,sys,shutil


runlength = 34 # years to run (for checking complete output)

outbase = '/newhome/pu17449/data/mizuRoute/output'

# dictionary of input runs (name and input runoff)
input_runs = {}
input_runs['rundef_900']='/newhome/pu17449/data/fuse/fuse_GBM_v2-2/output/GBM-tiled2-2_900_runs_def_qinst.nc'
input_runs['calib_900']  ='/newhome/pu17449/data/fuse/fuse_GBM_v2-2/output/GBM-tiled2-2_900_runs_pre_dist_qinst.nc'
input_runs['rundef_snowredist_900'] = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2_redistr/output/GBM-tiled2-2_900_runs_def_snoredist_qinst.nc'
input_runs['calib_snowredist_900']  = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2_redistr/output/GBM-tiled2-2_900_runs_pre_dist_snoredist_qinst.nc'

# User choice
fuse_decision_id = 900
override = True

# Control files: use template then modify OUTDIR,INDIR,FIN,OUTNAME
control_template = '/newhome/pu17449/src/mizuRoute/route/settings/GBM-MERIT.control_template'
controldir = '/newhome/pu17449/data/mizuRoute/control_files'
logdir = '/newhome/pu17449/data/mizuRoute/logs'


qsub_script = '/newhome/pu17449/src/setup_scripts/mizuRoute/call_pythonscript.sh' # use this one so we can load python3 module before calling python
sublist = []


for runname,inpath in input_runs.items():

		print(runname)

		if not os.path.exists(inpath):
			print('Error, input file doesnt exist',runname,inpath)
			continue

		outdir = os.path.join(outbase,runname)+'/'
		indir = os.path.dirname(inpath)+'/'
		fin   = os.path.basename(inpath)
		outname = 'q_'+runname
		
		control_file = os.path.join(controldir,'control_'+runname+'.txt')

		# Check if the calibration has already been run scucessfully
		outfiles = glob.glob(os.path.join(outdir,outname+'*.nc'))
		if len(outfiles) >= runlength and not override:
			print('Run',runname,'already completed, skipping')
			continue

		# copy template and modify
		if override:
			os.remove(control_file)
		if not os.path.exists(control_file):
			shutil.copy(control_template,control_file)
		sed_expr = 's#<OUTDIR>#'+outdir+'#g; '
		sed_expr += 's#<INDIR>#'+indir+'#g; '
		sed_expr += 's#<FIN>#'+fin+'#g; '
		sed_expr += 's#<OUTNAME>#'+outname+'#g'
		print(sed_expr)
		cmd = ['sed','-i','-e',sed_expr ,control_file]
		subprocess.call(cmd)
		
		# add fm_file to sublist
		sublist.append(control_file)

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
	os.environ['CONTROL_FLIST']=':'.join(sublist)
	print(os.environ['CONTROL_FLIST'])
	subprocess.call(['qsub','-v','CONTROL_FLIST',qsub_script])
else:
	print('No more simulations to submit!')
