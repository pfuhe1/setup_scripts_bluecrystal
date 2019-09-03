# script to setup FUSE calibration of GRDC catchments
# Peter Uhe May 15 2019
# 
# Assumes catchment_obsforcings_toBC3.py script has been run to copy the elev_bands and catchment_obsforcing files for each catchment
# Also requires list of catchment ids to process (f_catchlist)

import os,glob,subprocess,sys,shutil
exec(open('/newhome/pu17449/src/setup_scripts/module_python3_init').read())
module('load','apps/cdo-1.9.3')


##################################################################################
# Inputs from FUSE simulations:

runlength = 34 # years to run (for checking complete output)
inbase = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2/output'

# List of decision IDS and calibration choices to loop over
# These need to correspond to FUSE simulations 
# FUSE simulations have the naming format: <setup-name>_<decision-id>_<calib-choice>
setup_name = 'GBM-tiled2-2'
fuse_decision_ids = [904]
calib_choices = ['calibrateRand0001']
#calib_choices = ['calibrated1','calibrated2','calibrated3', 'calibrateRand0001','calibrateRand0002','calibrateRand0003','calibrateRand0004','calibrateRand0005', 'calibrateRand0006','calibrateRand0007','calibrateRand0008','calibrateRand0009','calibrateRand0010', 'calibrateRand0011','calibrateRand0012','calibrateRand0013','calibrateRand0014','calibrateRand0015', 'calibrateRand0016','calibrateRand0017','calibrateRand0018','calibrateRand0019']

# initialise dictionary of input runs (name and input file)
input_runs = {}

##################################################################################
# Mizuroute configuration and paths

outbase = '/newhome/pu17449/data/mizuRoute/output'
controldir = '/newhome/pu17449/data/mizuRoute/control_files'
logdir = '/newhome/pu17449/data/mizuRoute/logs'

# Control files: use template then modify OUTDIR,INDIR,FIN,OUTNAME
control_template = '/newhome/pu17449/src/mizuRoute/route/settings/GBM-MERIT.control_template_gcms'

qsub_script = '/newhome/pu17449/src/setup_scripts/mizuRoute/call_pythonscript.sh' # use this one so we can load python3 module before calling python

# User choice
override = True

# Initialize list of control files
sublist = []


##################################################################################
#
# Loop over decision ids and calib choices
for dec in fuse_decision_ids:
	for calib in calib_choices:
		sim_name0 = setup_name+'_'+str(dec)+'_'+calib
		
		# Get all gcms
		inpaths = glob.glob(os.path.join(inbase,sim_name0+'_*_*_*_EWEMBI_runs_*.nc'))
		for infile in inpaths:

			# First do some preprocessing to remove extra dimension and select q_instnt variable
			# TODO: for large sets of runs, could move this command to the qsub script rather than here
			# 
			fname = os.path.basename(infile)
			if fname[-8:]=='qinst.nc': # skip the qinst files
				continue
			sim_name = fname.split('_runs_')[0]
			infile2 = infile[:-3]+'_qinst.nc'
			print(sim_name,infile,infile2)
			if os.path.exists(infile2):
				ret = 0
			elif os.path.exists(infile) and not os.path.exists(infile2):
				cdo_cmd = ['cdo','--reduce_dim','selvar,q_instnt',infile,infile2]
				print(cdo_cmd)
				ret = subprocess.call(cdo_cmd)
			else:
				print('Error, infile doesnt exist')
			if ret == 0:
				input_runs[sim_name] = infile2
			else:
				print('Error running cdo command on input file!')


##################################################################################
#
# Loop over input files and set up mizuRoute simulation
for runname,inpath in input_runs.items():
		print(runname)
		expt = runname.split('_')[4]
		if expt == 'All-Hist':
			start = '2006-01-01'
			end   = '2015-12-31'
		elif expt == 'Plus15-Future' or expt == 'Plus20-Future':
			start = '2106-01-01'
			end   = '2115-12-31'
		else:
			raise Exception('Cant process start/end dates for expt:',expt)

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
			sed_expr += 's#<START>#'+start+'#g; '
			sed_expr += 's#<END>#'+end+'#g; '
			sed_expr += 's#<OUTNAME>#'+outname+'#g'
			print(sed_expr)
			cmd = ['sed','-i','-e',sed_expr ,control_file]
			subprocess.call(cmd)
		
		# add fm_file to sublist
		sublist.append(control_file)

# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	os.environ['CONTROL_FLIST']=':'.join(sublist)
	print(os.environ['CONTROL_FLIST'])
	subprocess.call(['qsub','-v','CONTROL_FLIST',qsub_script])
else:
	print('No more simulations to submit!')
