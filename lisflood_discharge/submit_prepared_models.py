# submit_prepared_models.py
# Requrires first running script preparing the lisflood simulations, then submits these to a HPC queue
# Previous script run would be e.g. lisflood_setup_inputs_obs_v2.py
# The lfdir is then copied from PC to this server
# E.g. 
# rsync -ruv --exclude '*.tif' --exclude='*.wd*' --exclude='*.elev' <lfdir> bp1-login01b.acrc.bris.ac.uk:/work/pu17449/lisflood/
#
# Peter Uhe
# 2020/01/30
# 

# Load modules
import os,sys,glob,subprocess,socket

hostname = socket.gethostname()

# Parameters for this domain
###############################################################################################

#regname = 'rectclip-manndepth'
#regname = 'rectclip-maskfpbank'
regname  = 'rectlarger-maskbank'
resname  = '9sd8'
clipname = regname+'_'+resname

startmon = 4 # april (1)
endmon = 10 # october (31)
ntimes = None


sublist = []


# Specify directories/paths
###############################################################################################
# Blue crystal3
if hostname[:7]=='newblue':
	# Lisflood simulation directories
	lfdir = '/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_'+clipname
	lf_dischargedir = os.path.join(lfdir,'dischargeobs')
	lf_pardir = os.path.join(lfdir,'parfilesobs')
	logdir = '/newhome/pu17449/data/lisflood/logs'

	# Qsub file for HPC queue
	qsub_script = '/newhome/pu17449/src/setup_scripts/lisflood_discharge/call_pythonscript_v2.sh'
	control_script = '/newhome/pu17449/src/setup_scripts/lisflood_discharge/qsub_multiproc.py'
	exe_file = '/newhome/pu17449/src/pfu_d8subgrid/lisflood_double_rect_r688'
	ncpus = 16 # number of processors per job
	jobsize = 4 # number of processors per simulation
	simsperjob = 30 # Number of simulations to submit per job

# Blue Pebble:
elif hostname[:9]=='bp1-login':
	# Lisflood simulation directories
	lfdir = '/work/pu17449/lisflood/lisfloodfp_'+clipname
	lf_dischargedir = os.path.join(lfdir,'dischargeobs')
	lf_pardir = os.path.join(lfdir,'parfilesobs')
	resultdir = os.path.join(lfdir,'results')
	# Qsub file for HPC queue
	qsub_script = '/home/pu17449/src/setup_scripts/lisflood_discharge/call_pythonscript_bp.sh'
	control_script = '/home/pu17449/src/setup_scripts/lisflood_discharge/qsub_multiproc_v3.py'
	exe_file = '/home/pu17449/bin/lisflood_double_rect_r688'
	#exe_file = '/home/pu17449/bin/lisflood_double_rect_trunk-r647'
	ncpus = 4 # (node size is 24) # number of processors per job
	jobsize = 4 # number of processors per simulation
	simsperjob = 1
	logdir = '/work/pu17449/lisflood/logs'


# Create logdir
if not os.path.exists(logdir):
	os.mkdir(logdir)

# Export common environment variables
os.environ['LISFLOOD_DIR'] = lfdir
os.environ['EXE_FILE'] = exe_file
os.environ['LOGDIR'] = logdir
os.environ['RESULTDIR'] = resultdir
os.environ['CONTROL_SCRIPT'] = control_script

# check output bci file (only one needed to describe the discharge points of the network)
f_bci = os.path.join(lf_dischargedir,clipname+'.bci')
if os.path.exists(f_bci):
	print('bcifile:',f_bci)
else:
	raise Exception('Error, bci file missing',f_bci)



###############################################################################################
# Main script: Loop over discharge files and write out discharge values
#
#fpattern = os.path.join(lfdir,'GBM-tiled2-2_904_calibrated*')
fpattern = os.path.join(lf_pardir,'GBM-tiled2-2_904_calibrated*')
print(fpattern)
for fpar in glob.glob(fpattern):
#	runname = os.path.basename(outdir)
	runname = os.path.basename(fpar)[:-4]
	outdir = os.path.join(resultdir,runname)
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	year = int(runname[-4:])
	print(runname,year)
	f_bdy = os.path.join(lf_dischargedir,runname+'.bdy')
	f_par = os.path.join(lf_pardir,runname+'.par')

	maxtif = os.path.join(outdir,runname+'-max.tif') # Only generated after the run is finished
	if os.path.exists(maxtif):
		print('Result already exists, skipping')
		continue

	if not os.path.exists(f_bdy) or not os.path.exists(f_par):
		print('Error, boundary or par file doesnt exist')
		continue

	# add par to sublist
	sublist.append(f_par)

	if len(sublist)>=simsperjob:
		print('Submitting jobs',len(sublist))
		# Set list of control files
		os.environ['CONTROL_FLIST']=':'.join(sublist)
		print(os.environ['CONTROL_FLIST'])
		# Submit to queue
		qsub_cmd = ['qsub','-l','select=1:ncpus='+str(ncpus)+':ompthreads='+str(jobsize)+':mem=12gb','-v','CONTROL_FLIST,EXE_FILE,LOGDIR,CONTROL_SCRIPT,LISFLOOD_DIR,RESULTDIR',qsub_script]
		print(' '.join(qsub_cmd))
		subprocess.call(qsub_cmd)
		# reset sublist 
		sublist = []

# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	# Set list of control files
	os.environ['CONTROL_FLIST']=':'.join(sublist)
	print(os.environ['CONTROL_FLIST'])
	# Submit to queue
	qsub_cmd = ['qsub','-l','select=1:ncpus='+str(ncpus)+':ompthreads='+str(jobsize)+':mem=12gb','-v','CONTROL_FLIST,EXE_FILE,LOGDIR,CONTROL_SCRIPT,LISFLOOD_DIR,RESULTDIR',qsub_script]
	print(' '.join(qsub_cmd))
	subprocess.call(qsub_cmd)
	#subprocess.call([qsub_script])
else:
	print('No more simulations to submit!')
