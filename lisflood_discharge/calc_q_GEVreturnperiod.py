# lisflood_setup_inputs_obs_v2.py
# Takes input from mizuRoute discharge, river network information and produces lisflood boundary conditions
# Requires running first lisflood_discharge_inputs_qgis.py to produce shapefiles (streamnet)
# Requires running first 077_main_lowres_v3_shiftregion.py (lisflood files)
# Output of these script is then copied from PC to this server
#
# Peter Uhe
# 2020/01/28
#

# Load modules
import os,sys,glob,pickle,shutil,socket
import numpy as np
from netCDF4 import Dataset,num2date
from osgeo import ogr
import csv
import datetime
from write_bdy_bci import write_bdy, write_bci_v2
import subprocess
from scipy.stats import genextreme

import warnings
warnings.filterwarnings("error")

###############################################################################################
# Main script: Loop over discharge files
# First calculate yearly maximum discharge using cdo
# Then load that data into a big array
#
host = socket.gethostname()
if host[:7] == 'newblue':
	# Input dir for discharge
	mizuroute_outdir = '/newhome/pu17449/data/mizuRoute/output'
	runname = 'GBM_EWEMBI'
	fpattern = os.path.join(mizuroute_outdir,'GBM-tiled2-2_90?_calibrated?','q_*.nc')
	# Template file to use for output
	template = os.path.join(mizuroute_outdir,'template.nc')
elif host[:3]=='bp1':
	mizuroute_outdir = '/work/pu17449/mizuRoute/output/'
	runname = 'GBM-p1deg_MSWEP2-2-ERA5'
	fpattern = os.path.join(mizuroute_outdir,'GBM-p1deg_90?_MSWEP2-2-ERA5-calibrated?_MSWEP2-2-ERA5','q_*.nc')
	# Template file to use for output
	template = os.path.join(mizuroute_outdir,'template.nc')



percentiles = np.array([50,80,90,95,99]) # percentile assumed for bankfull flow
nreaches = 3527

#fpattern = os.path.join(mizuroute_outdir,'GBM-tiled2-2_904_calibrateRand0001_'+model+'_*_EWEMBI/q_*.nc')
# Folder for processing/ temporary files
yrmax_dir = os.path.join(mizuroute_outdir,'yrmax_data')

files = glob.glob(fpattern)
fulldata = np.zeros([len(files),nreaches]) # river segment
for i,f_discharge in enumerate(files):
	#f_discharge = '/home/pu17449/data2/mizuRoute/merithydro/q_GBM_MERIT-Hydro_1988-1-1.nc'
	fname = os.path.basename(f_discharge)
	print(fname)
	runname = fname[2:-7]
	outdir  = os.path.join(yrmax_dir,runname)
	maxfile = os.path.join(outdir,fname[:-3]+'_yrmax.nc')
	if os.path.exists(maxfile):
		print('Result already exists, skipping')
		#continue
	else:
		if not os.path.exists(outdir):
			os.makedirs(outdir)
			cdo_cmd = ['cdo','yearmax','-selvar,IRFroutedRunoff',f_discharge,maxfile]
			print(' '.join(cdo_cmd))
			ret = subprocess.call(cdo_cmd)
			if not ret==0:
				raise Exception('Error with cdo command')
	with Dataset(maxfile,'r') as f:
		fulldata[i,:] = f.variables['IRFroutedRunoff'][0,:]

# Calclate GEV fit and return periods for each river segment
retperiod_q = np.zeros([len(percentiles),nreaches])
minshape = -0.3
for reach in range(nreaches):
	qvals = fulldata[:,reach]
	try:
		c,loc,scale = genextreme.fit(qvals,-0.01)
		tmp = genextreme.ppf(percentiles/100.,c,loc,scale)
#		if min(tmp)<0.:
#			print('Warning, trying negative shape')
#			c,loc,scale = genextreme.fit(qvals,-0.01)
#			tmp = genextreme.ppf(percentiles/100.,c,loc,scale)
	except Exception as e:
		print('error fitting',reach,qvals)
		# try with different shape parameter guess
		c,loc,scale= genextreme.fit(qvals,0.0)
		tmp = genextreme.ppf(percentiles/100.,c,loc,scale)
	retperiod_q[:,reach] = tmp
	if tmp.min()<0 or tmp.max()>5*qvals.max():
		#print('debug: reach,fit',reach,c,loc,scale)
		#print('qvals',qvals.min(),np.median(qvals),qvals.max())
		#print('fitted vals',tmp)
		c,loc,scale= genextreme.fit(qvals,f0=minshape)
		tmp = genextreme.ppf(percentiles/100.,c,loc,scale)
		#print('fitted vals, shape='+str(minshape),tmp)
		if tmp.min()<0 or tmp.max()>5*qvals.max():
			# can't seem to get the fit right, raise Exception
			raise Exception('Error cant get fit working')
	elif c<minshape:
		print('Debug, low shape',c)
		print('qvals',qvals.min(),np.median(qvals),qvals.max())
		print('fitted vals',tmp)
	retperiod_q[:,reach] = tmp

# Now calculate bankfull from 50th percentile (e.g. 2 year return period flow)
#bankfull = np.percentile(fulldata,percentile,axis=0)

# Now write out bankfull to netcdf file, based on template
for p,percentile in enumerate(percentiles):
	bankfull_file = os.path.join(mizuroute_outdir,'q_bankfull_'+runname+'_GEVfit'+str(percentile)+'ile.nc')
	shutil.copy(template,bankfull_file)
	with Dataset(bankfull_file,'a') as f:
		f.variables['IRFroutedRunoff'][0,:] = retperiod_q[p,:]
