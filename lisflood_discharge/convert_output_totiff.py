# Python script, calls gdal_translate for each output file to convert to tiff
import os,glob,subprocess

def convert_to_tif(fpattern):
	print('converting to tiff:',fpattern)
	for f in glob.glob(fpattern):
		print(f)
		if f[-4:] != '.tif':
			dirname,fname = f.split('/')
			start,end = fname.split('.') 
			f_tif = os.path.join(dirname,start+'-'+end+'.tif')
			print(f_tif)
			cmd = ['gdal_translate','-of','GTiff','-ot','Float32','-co','COMPRESS=DEFLATE',f,f_tif]
			if not os.path.exists(f_tif):
				ret = subprocess.call(cmd)
				if ret==0:
					os.remove(f)

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
				#print(f,f_tif)
				cmd = ['gdal_translate','-of','GTiff','-ot','Float32','-co','COMPRESS=DEFLATE',f,f_tif]
				if not os.path.exists(f_tif):
					ret = subprocess.call(cmd)
					if ret==0 and os.path.exists(f_tif):
						os.remove(f)

# test case
#convert_to_tif_v2('/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/GBM-tiled2-2_904_calibrateRand0001_NorESM1-HAPPI_All-Hist_run018_EWEMBI_2012','GBM-tiled2-2_904_calibrateRand0001_NorESM1-HAPPI_All-Hist_run018_EWEMBI_2012')

# test case 2:
for outdir in glob.glob('/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/GBM-tiled2-2_904_calibrateRand0001_*'):
	sim_name = os.path.basename(outdir)
	convert_to_tif_v2(outdir,sim_name)
