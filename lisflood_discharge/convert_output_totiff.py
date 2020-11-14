# Python script, calls gdal_translate for each output file to convert to tiff
import os,glob,subprocess
from concurrent.futures import ProcessPoolExecutor
from osgeo import gdal

# Converts an ascii file to geotiff and deletes original file if successful
def convert_single(f,f_tif):
	if not os.path.exists(f_tif):
		print('Converting to tiff:',f)
		cmd = ['gdal_translate','-of','GTiff','-ot','Float32','-co','COMPRESS=DEFLATE',f,f_tif]
		try:
			outputstr = subprocess.check_output(cmd) # check_output raises error if the commnand fails
			if os.path.exists(f_tif): # Double check the file was created
				os.remove(f)
			return 0
		except Exception as e:
			print('Error converting',e)
			return -1

def convert_to_tif(fpattern):
	print('converting to tiff:',fpattern)
	for f in glob.glob(fpattern):
		print(f)
		if f[-4:] != '.tif':
			dirname,fname = f.split('/')
			start,end = fname.split('.')
			f_tif = os.path.join(dirname,start+'-'+end+'.tif')
			convert_single(f,f_tif)

def convert_to_tif_v2(folder,sim_name,exts=['wd','wdfp','elev','dem','inittm','max','maxtm','mxe','totaltm']):
	if os.path.exists(folder):
		print('converting to tiff:',folder)
	else:
		print('Error, folder doesnt exist:',folder)
		return
	# First check if simuation is finished (use '.max' file as a flag)
	maxfile = os.path.join(folder,sim_name+'.max')
	if os.path.exists(maxfile):
		for ext in exts:
			for f in glob.glob(os.path.join(folder,sim_name+'*.'+ext)):
				start = f.split('.'+ext)[0]
				f_tif = start+'-'+ext+'.tif'
				convert_single(f,f_tif)

# convert_to_tif_v3 uses parallel processing
def convert_to_tif_v3(folder,sim_name,exts=['wd','wdfp','elev','dem','inittm','max','maxtm','mxe','totaltm','Fwidth','Qx','Qy','Qcx','Qcy'],jobsize=1):
	if os.path.exists(folder):
		print('Converting results to tiff:',folder)
	else:
		print('Error, folder doesnt exist:',folder)
		return
	# First check if simuation is finished (use '.max' file as a flag)
	maxfile = os.path.join(folder,sim_name+'.max')
	maxtif  = os.path.join(folder,sim_name+'-max.tif')
	if os.path.exists(maxfile) or os.path.exists(maxtif):
		with ProcessPoolExecutor(max_workers=jobsize) as pool:
			for ext in exts:
				fpattern = os.path.join(folder,sim_name+'*.'+ext)
				print('debug: converting',fpattern)
				for f in glob.glob(fpattern):
					start = f.split('.'+ext)[0]
					f_tif = start+'-'+ext+'.tif'
					pool.submit(convert_single,f,f_tif)

# convert_to_tif_v4 uses parallel processing, combines timeseries into single multiband file
def convert_to_tif_v4(folder,sim_name,exts=['wd','wdfp','elev','dem','inittm','max','maxtm','mxe','totaltm','Fwidth','Qx','Qy','Qcx','Qcy'],jobsize=1):
	if os.path.exists(folder):
		print('Converting results to tiff:',folder)
	else:
		print('Error, folder doesnt exist:',folder)
		return
	# First check if simuation is finished (use '.max' file as a flag)
	maxfile = os.path.join(folder,sim_name+'.max')
	maxtif  = os.path.join(folder,sim_name+'-max.tif')
	if os.path.exists(maxfile) or os.path.exists(maxtif):
		with ProcessPoolExecutor(max_workers=jobsize) as pool:
			for ext in exts:
				flist = []
				fpattern = os.path.join(folder,sim_name+'*.'+ext)
				print('debug: converting',fpattern)
				for f in glob.glob(fpattern):
					start = f.split('.'+ext)[0]
					f_tif = start+'-'+ext+'.tif'
					pool.submit(convert_single,f,f_tif)
					flist.append(f_tif)
		# now merge files, following answer from:
		# https://gis.stackexchange.com/questions/223910/using-rasterio-or-gdal-to-stack-multiple-bands-without-using-subprocess-commands
		for ext in exts:
			flist = sorted(glob.glob(os.path.join(folder,sim_name+'*-'+ext+'.tif')))
			if len(flist)>1:
				tmpfile = '/vsimem/'+sim_name+'-timeseries-'+ext+'.vrt'
				ts_file1 = os.path.join(folder,sim_name+'-timeseries-'+ext+'.tif')
				outds = gdal.BuildVRT(tmpfile, flist, separate=True)
				outds = gdal.Translate(ts_file1, outds,creationOptions=['COMPRESS=DEFLATE'])
				# Clean up individual files
				print('created',ts_file1)
				print('cleaning up',flist)
				for f in flist:
					os.remove(f)

def calc_recurrence(flist,fout,depth_thresh,tmpdir='/run/user/335970'):
	print('Calculating recurrence for',len(flist),' files')
	for i,f in enumerate(flist):
		sumfile = os.path.join(tmpdir,'sum_'+str(i)+'.tif')
		if i==0:
			gdal_cmd = ['gdal_calc.py','--calc','A>'+str(depth_thresh),'--format','GTiff','--type','Float32','-A',f,'--A_band','1','--outfile',sumfile]
			print(' '.join(gdal_cmd))
			outstr = subprocess.check_output(gdal_cmd)
		else:
			gdal_cmd = ['gdal_calc.py','--calc','(A>'+str(depth_thresh)+')+B','--format','GTiff','--type','Float32','-A',f,'--A_band','1','-B',last_sumfile,'--B_band','1','--co','COMPRESS=NONE','--outfile',sumfile]
			print(' '.join(gdal_cmd))
			outstr = subprocess.check_output(gdal_cmd)
			# Clean up old sumfile
			os.remove(last_sumfile)
		last_sumfile = sumfile

	# Finally convert to recurrence
	gdal_cmd = ['gdal_calc.py','--calc','A*100/'+str(len(flist)),'--format','GTiff','--type','Float32','-A',sumfile,'--A_band','1','--co','COMPRESS=DEFLATE','--outfile',fout]
	print(' '.join(gdal_cmd))
	outstr = subprocess.check_output(gdal_cmd)
	os.remove(sumfile)

if __name__=='__main__':
	# test case
	#convert_to_tif_v2('/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/GBM-tiled2-2_904_calibrateRand0001_NorESM1-HAPPI_All-Hist_run018_EWEMBI_2012','GBM-tiled2-2_904_calibrateRand0001_NorESM1-HAPPI_All-Hist_run018_EWEMBI_2012')
	#basedir = '/home/pu17449/work/lisflood/lisfloodfp_rectclip-manndepth_9sd8/results'
	#basedir = '/work/pu17449/lisflood/lisfloodfp_rectlarger-maskbank_9sd8/results'
	#basedir = '/work/pu17449/lisflood/lisfloodfp_rectlarger-chansolverMSWEP_slopev2fix_9sd8/results'
	basedir = '/work/pu17449/lisflood/lisfloodfp_rectlarger-chansolverMSWEP_2020-07-13_3sd8/results'
	# test case 2:
	#for outdir in glob.glob(basedir+'/*'):
	#	sim_name = os.path.basename(outdir)
	#	convert_to_tif_v3(outdir,sim_name,jobsize=4)

	# test single one:
	#convert_to_tif_v4('/work/pu17449/lisflood/lisfloodfp_rectlarger-maskbankMSWEP_9sd8/results/GBM-p1deg_904_MSWEP2-2-ERA5-calibrated3_MSWEP2-2-ERA5_2010','GBM-p1deg_904_MSWEP2-2-ERA5-calibrated3_MSWEP2-2-ERA5_2010')
	convert_to_tif_v4('/work/pu17449/lisflood/lisfloodfp_bangladesh-bnksmooth-chansolverMSWEP_2020-11-02_9sd8/results/GBM-p1deg_900_MSWEP2-2-ERA5-calibrated1_MSWEP2-2-ERA5_1980','GBM-p1deg_900_MSWEP2-2-ERA5-calibrated1_MSWEP2-2-ERA5_1980')

	# Test  calc_recurrence
	#maxfiles = glob.glob(os.path.join(basedir,'*900*','*-max.tif'))
	#depth_thresh = 0.5
	#frecurrence = os.path.join(basedir,'recurrence_MSWEP-2020-07-13_'+str(depth_thresh)+'m.tif')
	#calc_recurrence(maxfiles,frecurrence,depth_thresh)
