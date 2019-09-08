# lisflood_discharge_inputs_rectclip_gcms.py
#
# Peter Uhe
# Sep 5 2019
# 

# Load modules
import os,sys,glob,pickle,shutil
import numpy as np
from netCDF4 import Dataset,num2date
from osgeo import ogr
import csv
import datetime
from write_bdy_bci import write_bdy, write_bci
import subprocess

########################################################################################
# Function to calculate index of closest grid box, 
# Inputs are point latitude and longitude coordinates and grid latitude,longitude coordinates 
#
def find_closest_1d_v2(p_lat,p_lon,lat_coord,lon_coord):
	ny=lat_coord.shape[0]
	nx=lon_coord.shape[0]
	min_dist=100000000
	minx=-1
	miny=-1
	for j in range(ny):
		dist=(lat_coord[j]-p_lat)**2
		if dist<min_dist:
			miny=j
			min_dist=dist
	min_dist=100000000
	#print 'plon',p_lon
	for i in range(nx):
		dist= (np.abs(lon_coord[i]-p_lon)%360)**2
		if dist<min_dist:
			minx=i
			min_dist=dist
	return miny,minx

########################################################################################
# Function to calculate index of point, 
# Inputs are point latitude and longitude coordinates and list of latitude,longitude pairs 
#
def find_closest_list(p_lat,p_lon,lat_coord,lon_coord):
	ny=lat_coord.shape[0]
	nx=lon_coord.shape[0]
	min_dist=100000000
	minx=-1
	miny=-1
	for j in range(ny):
		dist=(lat_coord[j]-p_lat)**2 + (lon_coord[j]-p_lon)**2
		if dist<min_dist:
			miny=j
			min_dist=dist
	print('min dist',min_dist)
	return miny

########################################################################################
# Function to return true if point (xx,yy) is within bounds xbounds,ybounds 
def in_bounds(xx,yy,xbound,ybound):
	return xbound[0]<xx and xx<xbound[1] and ybound[0]<yy and yy<ybound[1]


########################################################################################
# Function to check if point is not in list (also ignores -1)
def point_notinlist(point,points_list):
	return (point!=-1 and point not in points_list)

########################################################################################
# Little function to format dates into a string nicely
def format_date(date):
	return date.strftime('%Y-%m-%d')



###############################################################################################		
# Start of main script
###############################################################################################
# Set up Shapefile reading driver
driver = ogr.GetDriverByName("ESRI Shapefile")

###############################################################################################
# Input/ Output

# Input dir for discharge
mizuroute_outdir = '/newhome/pu17449/data/mizuRoute/output'

# File, storing network attributes 
f_network        = '/newhome/pu17449/src/mizuRoute/route/ancillary_data/MERIT_mizuRoute_network_meta.nc'
# All points  (downstream outlet) in river network (needed identifying points outside selection)
f_all_downstream = '/newhome/pu17449/data/lisflood/ancil_data/strn_network_9sd8.out/strn_network_9sd8_downstream.shp'
# All upstream points in river network (use to match locations with IDs as upstream points are unique to a single river segment)
f_all_upstream = '/newhome/pu17449/data/lisflood/ancil_data/strn_network_9sd8.out/strn_network_9sd8_upstream.shp'

# parameter file template for lisflood 
f_par_template = '/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/077_template.par'

# Output dirs
lisflood_basedir = '/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest'
lisflood_dischargedir = '/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/discharge'
lisflood_pardir = '/newhome/pu17449/data/lisflood/ancil_data/lisfloodfp_d89s_RectTest/parfiles'

if not os.path.exists(lisflood_dischargedir):
	os.mkdir(lisflood_dischargedir)

if not os.path.exists(lisflood_pardir):
	os.mkdir(lisflood_pardir)

# output bci file (only one needed to describe the discharge points of the network)
f_bci = os.path.join(lisflood_dischargedir,'RectTest_9sd8.bci')
print('bcifile:',f_bci)

###############################################################################################
# Parameters
#

# Domain to use
xbound = [89,90]
ybound = [24.5,26]

startmon = 4 # april (1)
endmon = 10 # october (31)
ntimes = None

gcms = ['NorESM1-HAPPI'] #'ECHAM6-3-LR',

sublist = []

qsub_script = '/newhome/pu17449/src/setup_scripts/lisflood_discharge/call_pythonscript.sh'

###############################################################################################
# Main script: Get points for discharge in river network

# Initialise lists of points
points_ids = []
points_us1 = []
points_us2 = []
point_coords = {}
points_inside = {}
points_outside = {}
ds_segments = {} # Used to match tributaries flowing into the same downstream reach

# First load points shapefile of downstream end of each river segment. 
dataSource = driver.Open(f_all_downstream, 0)
points = dataSource.GetLayer()
print('Opened points',f_all_downstream)
for feature in points:
	link = feature.GetField('LINKNO')
	dslink = feature.GetField('DSLINKNO')
	xx,yy,zz = feature.geometry().GetPoint()
	# Check if point is inside our bounds
	if in_bounds(xx,yy,xbound,ybound):
		print('id',feature.GetFID(),link)
		print('coord',xx,yy)
		points_ids.append(link)
		point_coords[link] = (xx,yy)
		ds_segments[link] = dslink
		points_us1.append(feature.GetField('USLINKNO1'))
		points_us2.append(feature.GetField('USLINKNO2'))

# Now check if there are upstream points outside of the domain or not
# Separate points into 'inside' and 'outside' points depending on this. 
for i,point in enumerate(points_ids):
	if point_notinlist(points_us1[i],points_ids) or point_notinlist(points_us2[i],points_ids):
		points_outside[point] = point_coords[point]
	else:
		points_inside[point] = point_coords[point]
print('Outside points:',points_outside)
print('Inside points:',points_inside)

# Load Mizuroute river network (latitude and longitude of upstream points of each segment)
# Also load segId (which is not necessarily the same as the index of the segment)
with Dataset(f_network,'r') as f:
	segids_mizu = f.variables['segId'][:]
	lats   = f.variables['lat_up'][:]
	lons   = f.variables['lon_up'][:]

# Work out the mizuroute segment index corresponding to lisflood river network 'linkno'
# Match upstream coordinates for each river segment
#
seg_index_map = {} 
dataSource = driver.Open(f_all_upstream, 0)
points = dataSource.GetLayer()
print('Opened all points',f_all_upstream)
for feature in points:
	link = feature.GetField('LINKNO')
	if link in points_ids:
		xx,yy,zz = feature.geometry().GetPoint()
		seg_index_map[link] = find_closest_list(yy,xx,lats,lons)

###############################################################################################
# Main script: Loop over discharge files and write out discharge values
#
for model in gcms:
	fpattern = os.path.join(mizuroute_outdir,'GBM-tiled2-2_904_calibrateRand0001_'+model+'_*_EWEMBI/q_*.nc')
	for f_discharge in glob.glob(fpattern):
		#f_discharge = '/home/pu17449/data2/mizuRoute/merithydro/q_GBM_MERIT-Hydro_1988-1-1.nc'
		fname = os.path.basename(f_discharge)
		print(fname)
		runname = fname[2:-7]
		year = int(runname[-4:])
		print(runname,year)
		f_csv = os.path.join(lisflood_dischargedir,runname+'.csv')
		f_bdy = os.path.join(lisflood_dischargedir,runname+'.bdy')
		f_par = os.path.join(lisflood_pardir,runname+'.par')
		if not os.path.exists(f_bdy):

			discharge_dict = {}
			# Read mizuroute output file for discharge values
			with Dataset(f_discharge,'r') as f_in:
				linkids = f_in.variables['reachID'][:]
				runoff_vals = f_in.variables['dlayRunoff']
				discharge_vals = f_in.variables['KWTroutedRunoff']
				times = f_in.variables['time']
				dates = num2date(times[:],times.units)

				# Subset data to be within startdate-endate
				startdate = datetime.datetime(year,startmon,1)
				enddate   = datetime.datetime(year,endmon+1,1)
				startindex = np.where(dates==startdate)[0][0]
				endindex = np.where(dates==enddate)[0][0]
				discharge_vals = discharge_vals[startindex:endindex,:]
				runoff_vals = runoff_vals[startindex:endindex,:]
				dates = dates[startindex:endindex]
				datestrings = map(format_date,dates)
				ntimes = len(dates)

				print('shapes',dates.shape,discharge_vals.shape,runoff_vals.shape)

				print('points outside:',points_outside.keys())
				print('writing outside points')
				for link,pt in points_outside.items():
					dslink = ds_segments[link]
					seg_index = seg_index_map[link]
					#print('link,ds',link,dslink)
					try:
						if dslink not in discharge_dict:
							discharge_dict[dslink] = [segids_mizu[seg_index],pt[0],pt[1],link]+list(discharge_vals[:,seg_index])
						else: # Add together discharge for two tributaries converging at this point
							row = discharge_dict[dslink]
							discharge_dict[dslink] = [str(row[0])+'/'+str(segids_mizu[seg_index]),pt[0],pt[1],str(row[0])+'/'+str(link)]+list(np.array(row[4:])+discharge_vals[:,seg_index])
					except:
						raise Exception('Error writing discharge for outside link',link)
				print('writing inside points')
				print('points inside:',points_inside.keys())
				for link,pt in points_inside.items():
					try:
						dslink = ds_segments[link]
						seg_index = seg_index_map[link]
						if dslink not in discharge_dict:
							discharge_dict[dslink] = [segids_mizu[seg_index],pt[0],pt[1],link]+list(runoff_vals[:,seg_index])
						else: # Add together discharge for two tributaries converging at this point
							row = discharge_dict[dslink]
							discharge_dict[dslink] = [str(row[0])+'/'+str(segids_mizu[seg_index]),pt[0],pt[1],str(row[0])+'/'+str(link)]+list(np.array(row[4:])+runoff_vals[:,seg_index]) 
					except:
						print('Error writing discharge for inside link',link,pt[0],pt[1])
						raise


			print('writing to csv file')
			with open(f_csv,'w') as f:
				fwriter = csv.writer(f)
				fwriter.writerow(['linkno(d8)','x','y','linkno (d4)']+list(datestrings))
				for row in discharge_dict.values():
					fwriter.writerow(row)

			print('writing to bdy file')
			write_bdy(f_bdy,f_csv,ntimes)
		else:
			print('file exists, skipping:',f_bdy)

		# Write bci file (just needs the list of points, so can use any csv file, only create once)
		if not os.path.exists(f_bci):
			print('writing to bci file')
			write_bci(f_bci,f_csv)

		bci_relative = f_bci[len(lisflood_basedir)+1:]
		bdy_relative = f_bdy[len(lisflood_basedir)+1:]

		if ntimes is None:
			tmp = open(f_csv,'r').readline()
			ntimes = len(tmp.split(','))-4
		sim_time = str(ntimes*86400)
		

		if not os.path.exists(f_par):
			# copy template and modify
			shutil.copy(f_par_template,f_par)
			sed_expr = 's#<RUNNAME>#'+runname+'#g; '
			sed_expr += 's#<SIMTIME>#'+sim_time+'#g; '
			sed_expr += 's#<BCI>#'+bci_relative+'#g; '
			sed_expr += 's#<BDY>#'+bdy_relative+'#g'
			print(sed_expr)
			cmd = ['sed','-i','-e',sed_expr ,f_par]
			subprocess.call(cmd)
	

		# add par to sublist
		sublist.append(f_par)

# submit any that are left
if len(sublist)>0:
	print('Submitting jobs',len(sublist))
	os.environ['CONTROL_FLIST']=':'.join(sublist)
	print(os.environ['CONTROL_FLIST'])
	subprocess.call(['qsub','-v','CONTROL_FLIST',qsub_script])
	#subprocess.call([qsub_script])
else:
	print('No more simulations to submit!')



