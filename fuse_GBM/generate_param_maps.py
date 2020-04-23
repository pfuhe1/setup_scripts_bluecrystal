# Script to produce maps of FUSE parameter sets, based on parameter transfer / regionalisation
# Peter Uhe
# June 2019
#

import numpy as np
import pickle,glob,os,sys
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib.cm
import cartopy.crs as ccrs
import cartopy.feature as cfeature

#########################################################################################
# Input files

dec = 900

# List of donor catchments (dimensions: rank, lat, longitude)
# Has up to 10 donors per point, minimum of 3 for 'reducedset'. 
# Reducedset has some donors removed, given value -1
f_donors = '/newhome/pu17449/src/fuse_processing/GBM-5deg_distances_GBM-hisnowIQR_reducedset.pkl'
f_grid = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2/input/GBM-tiled2-2_elev_bands.nc'
f_out = '/newhome/pu17449/data/fuse/fuse_GBM_v2-2/output/GBM-tiled2-2_'+str(dec)+'_calibratedparams.nc'
basedir = '/newhome/pu17449/data/fuse/grdc_catchments/'
#fpattern_params = '/newhome/pu17449/data/fuse/grdc_catchments/fuse_grdc_*/output/grdc_*_900_para_sce.nc'

#########################################################################################

# Load grid 
with Dataset(f_grid,'r') as f:
	lons = f.variables['longitude'][:]
	lats = f.variables['latitude'][:]


# Load donor catchments
with open(f_donors,'rb') as f:
	donor_catchments = pickle.load(f)

# Get array shape 
nz,ny,nx = donor_catchments.shape

# Convert donor catchments to masked array
donor_catchments = np.ma.masked_where(donor_catchments==-1,donor_catchments)

# find best donor for each grid point (first in list after removing masked points)
donor_indices  = {}
best_donor = np.ones([ny,nx],dtype=int)*-1
for i in range(nx):
	for j in range(ny):
		# compress to remove masked values, then take first point
		catchs = donor_catchments[:,j,i].compressed()
		if len(catchs>0):
			catch = catchs[0]
			best_donor[j,i] = catch
			if catch in donor_indices:
				donor_indices[catch].append((j,i))
			else:
				donor_indices[catch] = [(j,i)]

##########################################################################


param_longname = {}
param_units = {}
# Get list of parameters from an example parameter file
#with Dataset('/newhome/pu17449/data/fuse/grdc_catchments/fuse_grdc_4203910/output/grdc_4203910_900_para_sce.nc','r') as f:
with Dataset('/newhome/pu17449/data/fuse/grdc_catchments/fuse_grdc_4120800/output/grdc_4120800_'+str(dec)+'_para_sce.nc','r') as f:
	param_list = list(f.variables.keys())
	for param in param_list:
		param_longname[param] = f.variables[param].long_name
		param_units[param] = f.variables[param].units


print('params',sorted(param_list))
param_maps = {}
# initialise parameter maps
for param in param_list:
	param_maps[param] = np.ones([ny,nx],dtype=np.float32)*-1
	param_longname

for catchment,indices in donor_indices.items():
	f_param = os.path.join(basedir,'fuse_grdc_'+str(catchment),'output','grdc_'+str(catchment)+'_'+str(dec)+'_para_sce.nc')
	print('catchment',catchment,f_param)
	with Dataset(f_param,'r') as f:
		# First get best trial from calibration (use raw_rmse)
		rmse = f.variables['raw_rmse'][:].compressed()
		if len(rmse)>0:
			besttry = rmse.argmin()
			numtrials = len(rmse)
			print('best parameter is from trial',besttry,'of',numtrials)
			for param in param_list:
				catch_param = f.variables[param][besttry]
				for point in indices:
					param_maps[param][point[0],point[1]] = catch_param
		else:
			print('Error, no valid data for catchment',catchment)

# Write grid to output
with Dataset(f_out,'w') as f_out:

	f_out.createDimension('latitude',len(lats))
	f_out.createVariable('latitude',np.float,('latitude'))
	f_out.variables['latitude'].standard_name = "latitude"
	f_out.variables['latitude'].long_name = "latitude"
	f_out.variables['latitude'].units = "degrees_north"
	f_out.variables['latitude'].axis = "Y"
	f_out.variables['latitude'][:] = lats

	f_out.createDimension('longitude',len(lons))
	f_out.createVariable('longitude',np.float,('longitude'))
	f_out.variables['longitude'].standard_name = "longitude"
	f_out.variables['longitude'].long_name = "longitude"
	f_out.variables['longitude'].units = "degrees_east"
	f_out.variables['longitude'].axis = "X"
	f_out.variables['longitude'][:] = lons

	for param,field in param_maps.items():
		# Simple selection of output paramsdd
		#if param[0].isupper()
		var = f_out.createVariable(param,np.float,('latitude','longitude'))
		var.long_name = param_longname[param]
		var.units = param_units[param]
		var[:] = np.ma.masked_where(field==-1,field)
	

############################################################################
# Plot stuff

fig=plt.figure()
ax = fig.add_subplot(1,1,1,projection=ccrs.PlateCarree())
ax.set_extent([73.25, 97.75, 22.25, 31.25], crs=ccrs.PlateCarree())
#ax.pcolormesh(lons,lats,distarray[0,::-1,:],vmin=0,vmax=1,cmap='jet')
marr = np.ma.masked_where(param_maps['raw_rmse']==-1,param_maps['raw_rmse'])
cm = ax.pcolormesh(lons,lats,marr,cmap='jet',vmin=0,vmax=5,transform=ccrs.PlateCarree())
ax.coastlines()
ax.add_feature(cfeature.BORDERS)
plt.colorbar(cm,ax=ax,shrink=0.3)
plt.title('RMSE of donor catchment from calibration')
#plt.show()
plt.savefig('figs/calib_RMSE_donor.png')
