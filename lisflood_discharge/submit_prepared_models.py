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
import os,sys,glob,subprocess

# Parameters for this domain
###############################################################################################
# extent xmin, xmax, ymin, ymax
extent = [89.03,89.95,24.5,26]
extentstr = str(extent)[1:-1]
res = 0.0025 # in degrees
ds_buffer = 0.1 # buffer around each reach to set the downstream boundary

# Give this domain a name
regname = 'rectclip'
resname = '9sd8'
clipname = regname+'_'+resname

# Domain to use
#xbound = [89,90]
#ybound = [24.5,26]

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
	# Qsub file for HPC queue
	qsub_script = '/newhome/pu17449/src/setup_scripts/lisflood_discharge/call_pythonscript_v2.sh'
	exe_file = '/newhome/pu17449/src/pfu_d8subgrid/lisflood_double_rect_r688'
	nodesize = 16 # number of processors per node
	jobsize = 4 # number of processors per simulation

# Blue Pebble:
elif hostname[:9]=='bp1-login':
	# Lisflood simulation directories
	lfdir = '/work/pu17449/lisflood/lisfloodfp_'+clipname
	lf_dischargedir = os.path.join(lfdir,'dischargeobs')
	lf_pardir = os.path.join(lfdir,'parfilesobs')
	# Qsub file for HPC queue
	qsub_script = '/home/pu17449/src/setup_scripts/lisflood_discharge/call_pythonscript_v2.sh'
	nodesize = 24 # number of processors per node
	jobsize = 4 # number of processors per simulation
	logdir = '/work/pu17449/lisflood/logs'

# Create logdir
if not os.path.exists(logdir):
	os.mkdir(logdir)

# Export common environment variables
os.environ['OMP_NUM_THREADS'] = jobsize
os.environ['EXE_FILE'] = exe_file
os.environ['NODESIZE'] = nodesize
os.environ['LOGDIR'] = logdir

# check output bci file (only one needed to describe the discharge points of the network)
f_bci = os.path.join(lf_dischargedir,clipname+'.bci')
if os.path.exists(f_bci):
	print('bcifile:',f_bci)
else:
	raise Exception('Error, bci file missing',f_bci)



###############################################################################################
# Main script: Loop over discharge files and write out discharge values
#
fpattern = os.path.join(lfdir,'GBM-tiled2-2_904_calibrated?')
for resultdir in glob.glob(fpattern):
	runname = os.path.basename(rundir)
	year = int(runname[-4:])
	print(runname,year)
	f_bdy = os.path.join(lf_dischargedir,runname+'.bdy')
	f_par = os.path.join(lf_pardir,runname+'.par')

	maxtif = os.path.join(resultdir,runname+'-max.tif') # Only generated after the run is finished
	if os.path.exists(maxtif):
		print('Result already exists, skipping')
		continue

	if not os.path.exists(f_bdy) or not os.path.exists(f_par):
		print('Error, boundary or par file doesnt exist')
		continue

	# add par to sublist
	sublist.append(f_par)

	if len(sublist)>=30:
		print('Submitting jobs',len(sublist))
		# Set list of control files
		os.environ['CONTROL_FLIST']=':'.join(sublist)
		print(os.environ['CONTROL_FLIST'])
		# Submit to queue
		subprocess.call(['qsub','-v','CONTROL_FLIST,OMP_NUM_THREADS,EXE_FILE,NODESIZE,LOGDIR',qsub_script])
		# reset sublist 
		sublist = []

# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	# Set list of control files
	os.environ['CONTROL_FLIST']=':'.join(sublist)
	print(os.environ['CONTROL_FLIST'])
	# Submit to queue
	subprocess.call(['qsub','-v','CONTROL_FLIST,OMP_NUM_THREADS,EXE_FILE,NODESIZE,LOGDIR',qsub_script])
	#subprocess.call([qsub_script])
else:
	print('No more simulations to submit!')
