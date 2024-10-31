import shlex
import subprocess
import sys

import netCDF4
import numpy as np


def main():
    if len(sys.argv) < 2:
        print("Usage: python netcdf_to_tif_converter.py <input_files...>")
        exit(1)

    # Data variable name
    data_variable = 'anomaly'

    # NetCDF file paths
    input_files = sys.argv[1:]

    for input_file in input_files:
        output_file = input_file[0:input_file.rfind('.')] + '.tif'

        # Open the NetCDF file
        ds = netCDF4.Dataset(input_file)

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
            f'NETCDF:"{input_file}":{data_variable} '
            f'"{output_file}"'
        )

        # Execute the command
        subprocess.run(shlex.split(gdal_command))

if __name__ == "__main__":
    main()