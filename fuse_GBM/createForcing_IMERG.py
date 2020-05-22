# script to setup and submit FUSE gridded runs
# Peter Uhe Aug 21 2019
#

import os,glob,subprocess,sys,shutil
import datetime
import queue
import socket
from calendar import monthrange



setup_name = 'GBM-p1deg'
obsversion = 'IMERG-ERA5'
ssim = '2000-06-01'
esim = '2017-10-31'

###################################################################################

# Processing for imerg
# Take data for ERA5 from GBM-p1deg_MSWEP2-2-ERA5_input.nc, replace MSWEP with imerg
imerg_path = '/bp1store/geog-tropical/data/obs/IMERG/Final'
fuse_indir = '/work/pu17449/fuse/GBM-p1deg/input'
tmpdir     = '/work/pu17449/fuse/tmp'
old_input = os.path.join(fuse_indir,'GBM-p1deg_MSWEP2-2-ERA5_input.nc')

lonlatbox = '73,98,22,31.5'
years = range(2000,2018)
months = range(1,13)
startint = int(ssim[:4])*100+ int(ssim[5:7]) # e.g. 200606
endint = int(esim[:4])*100+ int(esim[5:7])

### Temporary files:
# Inputs for tas and pet (calculated from ERA5 and MSWEP2-2)
tmp1  = os.path.join(tmpdir,'GBM-p1deg_ERA5_200006-201710_inputs.nc')
# Concatenated precip files
fcat = os.path.join(tmpdir,'IMERG_cat_'+ssim+'_'+esim+'.nc')
# List of processed daily files to concatenate
dayfiles = []
ftmp2 = '' # initialise variable for temporary file

try:

	# Select tas and pet from MSWEP2-2 input file
	cdo_cmd = ['cdo','selvar,tas,pet','-seldate,'+ssim+','+esim,old_input,tmp1]
	if not os.path.exists(tmp1):
		print(' '.join(cdo_cmd))
		retval = subprocess.call(cdo_cmd)
		if not retval == 0:
			raise Exception('Error with cdo command')

	if not os.path.exists(fcat):
		#####
		# Loop over input files and process
		for year in years:
			for month in months:
				monint = year*100+month
				if monint <startint or monint>endint:
					continue # date is out of range
				ndays = monthrange(year,month)[1]
				for day in range(1,ndays+1):
					# Work out input file name and check if it exists
					daystr = str(year).zfill(4)+str(month).zfill(2)+str(day).zfill(2)
					fname = '3B-DAY.MS.MRG.3IMERG.'+daystr+'-S000000-E235959.V06.nc4'
					# Input file
					fin = os.path.join(imerg_path,fname)
					if not os.path.exists(fin):
						raise Exception('Error missing input file',fin)

					print(year,month,day)

					# Temporary files processed by cdo/nco
					ftmp2  = os.path.join(tmpdir,fname)
					ftmp3  = os.path.join(tmpdir,fname[:-4]+'_reorder.nc')

					######
					if not os.path.exists(ftmp2):
						cdo_cmd = ['cdo','-f','nc','invertlat','-sellonlatbox,'+lonlatbox,'-selvar,precipitationCal',fin,ftmp2]
						print(' '.join(cdo_cmd))
						retval = subprocess.call(cdo_cmd)
						if not retval==0:
							raise Exception('Error with CDO command')

						######
						#rename variables
						nco_cmd = ['ncrename','-v','precipitationCal,pr','-d','lat,latitude','-v','lat,latitude','-d','lon,longitude','-v','lon,longitude',ftmp2]
						print(' '.join(nco_cmd))
						retval = subprocess.call(nco_cmd)
						if not retval == 0:
							raise Exception('Error with NCO command')

						######
						# round longitude to nearest 0.1 degree
						nco_cmd = ['ncap2','-s','longitude = float(int(longitude*20)/20.0)',ftmp2]
						print(' '.join(nco_cmd))
						retval = subprocess.call(nco_cmd)
						if not retval == 0:
							raise Exception('Error with NCO command')

					######
					#reorder dimensions
					if not os.path.exists(ftmp3):
						nco_cmd = ['ncpdq','-a','time,latitude,longitude',ftmp2,ftmp3]
						print(' '.join(nco_cmd))
						retval = subprocess.call(nco_cmd)
						if not retval == 0:
							raise Exception('Error with NCO command')

					# Append file to list for concatenating
					dayfiles.append(ftmp3)
					# Remove ftmp2 files
					os.remove(ftmp2)

		################################################################################
		# concatenate daily files for precip
		cdo_cat = ['cdo','cat']+dayfiles+[fcat]
		print(' '.join(cdo_cat))
		retval = subprocess.call(cdo_cat)
		if not retval == 0:
			raise Exception('Error with cdo concatenate command')

	# Finally merge data together
	outfile = os.path.join(fuse_indir,'GBM-p1deg_'+obsversion+'_input.nc')
	if not os.path.exists(outfile):
		cdo_merge = ['cdo','merge',fcat,tmp1,outfile]
		print(' '.join(cdo_merge))
		retval = subprocess.call(cdo_merge)
		if not retval == 0:
			raise Exception('Error with cdo merge command')

except:
	print('Script failed, cleaning up!')
	raise
else:
	print('Finished')
finally:
	# Clean up temporary files
	if os.path.exists(tmp1):
		os.remove(tmp1)
	if os.path.exists(fcat):
		os.remove(fcat)
	if os.path.exists(ftmp2):
		os.remove(ftmp2)
	for f in dayfiles:
		if os.path.exists(f):
			os.remove(f)
