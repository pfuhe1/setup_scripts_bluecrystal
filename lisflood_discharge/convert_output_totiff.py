# Python script, calls gdal_translate for each output file to convert to tiff
import os,glob,subprocess
from concurrent.futures import ProcessPoolExecutor

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
def convert_to_tif_v3(folder,sim_name,exts=['wd','wdfp','elev','dem','inittm','max','maxtm','mxe','totaltm'],jobsize=1):
	if os.path.exists(folder):
		print('Converting results to tiff:',folder)
	else:
		print('Error, folder doesnt exist:',folder)
		return
	# First check if simuation is finished (use '.max' file as a flag)
	maxfile = os.path.join(folder,sim_name+'.max')
	if os.path.exists(maxfile):
		with ProcessPoolExecutor(max_workers=jobsize) as pool:
			for ext in exts:
				for f in glob.glob(os.path.join(folder,sim_name+'*.'+ext)):
					start = f.split('.'+ext)[0]
					f_tif = start+'-'+ext+'.tif'
					pool.submit(convert_single,f,f_tif)


if __name__=='__main__':
	# test case
	#convert_to_tif_v2('/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/GBM-tiled2-2_904_calibrateRand0001_NorESM1-HAPPI_All-Hist_run018_EWEMBI_2012','GBM-tiled2-2_904_calibrateRand0001_NorESM1-HAPPI_All-Hist_run018_EWEMBI_2012')
	basedir = '/home/pu17449/work/lisflood/lisfloodfp_rectclip_9sd4/results'
	# test case 2:
	for outdir in glob.glob(basedir+'/*'):
		sim_name = os.path.basename(outdir)
		convert_to_tif_v2(outdir,sim_name)
