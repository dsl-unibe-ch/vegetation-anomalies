import shlex
import subprocess
import sys

import netCDF4
import numpy as np

if len(sys.argv) != 3:
    print("2 arguments are expected.")
    exit(1)

# Path to your NetCDF file
netcdf_file = sys.argv[1]
output_file = sys.argv[2]

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
    f'"{output_file}"'
)

# Execute the command
subprocess.run(shlex.split(gdal_command))
