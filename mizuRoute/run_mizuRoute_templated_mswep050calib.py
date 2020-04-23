# script to setup FUSE calibration of GRDC catchments
# Peter Uhe May 15 2019
# 
# Assumes catchment_obsforcings_toBC3.py script has been run to copy the elev_bands and catchment_obsforcing files for each catchment
# Also requires list of catchment ids to process (f_catchlist)

import os,glob,subprocess,sys,shutil,socket

# In BC4 use cdo from petepy conda environment:


##################################################################################
# Inputs from FUSE simulations:

# Define computer specific paths/variables
host=socket.gethostname()
# Blue Crystal Phase 3
if host[:7]=='newblue': 
	# Load cdo module
	exec(open('/newhome/pu17449/src/setup_scripts/module_python3_init').read())
	module('load','apps/cdo-1.9.3')

	# Paths
	inbase = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2/output'
	mizu_exe = '/newhome/pu17449/src/mizuRoute/route/bin/mizuRoute'
	control_template = '/newhome/pu17449/src/mizuRoute/route/settings/GBM-MERIT.control_template'
	outbase = '/newhome/pu17449/data/mizuRoute/output'
	controldir = '/newhome/pu17449/data/mizuRoute/control_files'
	logdir = '/newhome/pu17449/data/mizuRoute/logs'

	# qsub stuff
	qsub_script = '/newhome/pu17449/src/setup_scripts/mizuRoute/call_pythonscript.sh' 
	qsub_command = ['qsub','-v','CONTROL_FLIST,LOGDIR,NCPUS,MIZU_EXE',qsub_script]
	ncpus = 16
	nperjob = 9999

elif host[:8] == 'bc4login':
	# Blue Crystal Phase 4
	# Paths
	inbase = '/mnt/storage/scratch/pu17449/fuse/fuse_GBM_v2-2/output'
	mizu_exe = '/mnt/storage/home/pu17449/src/mizuRoute/route/bin/mizuRoute'
	control_template = '/mnt/storage/home/pu17449/src/mizuRoute/route/settings/GBM-MERIT.control_template'
	outbase = '/mnt/storage/scratch/pu17449/mizuRoute/output'
	controldir = '/mnt/storage/scratch/pu17449/mizuRoute/control_files'
	logdir = '/mnt/storage/scratch/pu17449/mizuRoute/logs'

	# qsub stuff
	qsub_script = '/mnt/storage/home/pu17449/src/setup_scripts/mizuRoute/call_pythonscript_bc4serial.sh'
	ncpus = 1
	nperjob = 3
	qsub_command = ['sbatch','--export','CONTROL_FLIST,LOGDIR,NCPUS,MIZU_EXE',qsub_script]


###################################################################################
# Export environment variables used by all QSUB commands
os.environ['NCPUS'] = str(ncpus)
os.environ['MIZU_EXE'] = mizu_exe
os.environ['LOGDIR'] = logdir

###################################################################################
# Mizurout choices for simulations

runlength = 34 # years to run (for checking complete output)

# List of decision IDS and calibration choices to loop over
# These need to correspond to FUSE simulations 
# FUSE simulations have the naming format: <setup-name>_<decision-id>_<calib-choice>
setup_name = 'GBM-tiled2-2'
fuse_decision_ids = [900,902,904]
#calib_choices = ['rundef','calibratedparams']
#calib_choices = ['MSWEPp5degcalibrated1','MSWEPp5degcalibrated2','MSWEPp5degcalibrated3']

calib_choices = ['MSWEPp5degcalibrateRand0001','MSWEPp5degcalibrateRand0002','MSWEPp5degcalibrateRand0003','MSWEPp5degcalibrateRand0004','MSWEPp5degcalibrateRand0005', 'MSWEPp5degcalibrateRand0006','MSWEPp5degcalibrateRand0007','MSWEPp5degcalibrateRand0008','MSWEPp5degcalibrateRand0009','MSWEPp5degcalibrateRand0010', 'MSWEPp5degcalibrateRand0011','MSWEPp5degcalibrateRand0012','MSWEPp5degcalibrateRand0013','MSWEPp5degcalibrateRand0014','MSWEPp5degcalibrateRand0015', 'MSWEPp5degcalibrateRand0016','MSWEPp5degcalibrateRand0017','MSWEPp5degcalibrateRand0018','MSWEPp5degcalibrateRand0019']

# User choice
override = True


##################################################################################
# Initialization

# initialise dictionary of input runs (name and input file)
input_runs = {}

# Initialize list of control files
sublist = []


##################################################################################
#
# Loop over decision ids and calib choices
for dec in fuse_decision_ids:
	for calib in calib_choices:
		sim_name = setup_name+'_'+str(dec)+'_'+calib+'_MSWEP2-2-050deg'

		# First do some preprocessing to remove extra dimension and select q_instnt variable
		# TODO: for large sets of runs, could move this command to the qsub script rather than here
		# 
		if calib == 'rundef':
			infile = os.path.join(inbase,sim_name+'_runs_def.nc')
			infile2 = os.path.join(inbase,sim_name+'_runs_def_qinst.nc')
		else:
			infile = os.path.join(inbase,sim_name+'_runs_pre_dist.nc')
			infile2 = os.path.join(inbase,sim_name+'_runs_pre_dist_qinst.nc')
		
		if os.path.exists(infile2):
			ret = 0
		elif os.path.exists(infile) and not os.path.exists(infile2):
			cdo_cmd = ['cdo','--reduce_dim','selvar,q_instnt',infile,infile2]
			print(cdo_cmd)
			ret = subprocess.call(cdo_cmd)
		else:
			print('Error, infile doesnt exist')
			ret = -1
		if ret == 0:
			input_runs[sim_name] = infile2
		else:
			print('Error running cdo command on input file!')


##################################################################################
#
# Loop over input files and set up mizuRoute simulation
for runname,inpath in input_runs.items():
		print(runname)

		if not os.path.exists(inpath):
			print('Error, input file doesnt exist',runname,inpath)
			continue

		outdir = os.path.join(outbase,runname)+'/'
		if not os.path.exists(outdir):
			os.mkdir(outdir)
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
		if override and os.path.exists(control_file):
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

		# submit nperjob simulations at a time
		if len(sublist)==nperjob:
			print('Submitting jobs',len(sublist))
			# First export environment variables used in the job
			os.environ['CONTROL_FLIST']=':'.join(sublist)
			print(os.environ['CONTROL_FLIST'])
			subprocess.call(qsub_command)
			# Reset submit list
			sublist = []

# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	os.environ['CONTROL_FLIST']=':'.join(sublist)
	print(os.environ['CONTROL_FLIST'])
	subprocess.call(qsub_command)
else:
	print('No more simulations to submit!')
