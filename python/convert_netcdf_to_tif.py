import shlex
import subprocess

import netCDF4
import numpy as np

# Path to your NetCDF file
netcdf_file = '../data/cubes_demo/anomalies_2018_47.468318939208984_8.746687889099121.nc'

# Data variable name
data_variable = 'anomaly'

# Open the NetCDF file
ds = netCDF4.Dataset(netcdf_file)

# Read the latitude and longitude variables
lat_var = ds.variables['lat']
lon_var = ds.variables['lon']

latitudes = lat_var[:]
longitudes = lon_var[:]

# Get min and max values
lat_min = np.min(latitudes)
lat_max = np.max(latitudes)
lon_min = np.min(longitudes)
lon_max = np.max(longitudes)

# Close the NetCDF file
ds.close()

# Handle latitude ordering
if latitudes[0] > latitudes[-1]:
    lat_min, lat_max = lat_max, lat_min

# Construct the gdal_translate command
gdal_command = (
    f'gdal_translate -of GTiff '
    f'-a_srs EPSG:4326 '
    f'-a_ullr {lon_min} {lat_max} {lon_max} {lat_min} '
    f'NETCDF:"{netcdf_file}":{data_variable} '
    f'../data/cubes_demo/anomalies_2018_47.468318939208984_8.746687889099121.tif'
)

# Execute the command
subprocess.run(shlex.split(gdal_command))
