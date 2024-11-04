import os
import subprocess
import sys
import warnings
from datetime import datetime, timedelta

import numpy as np
from osgeo import gdal, gdalconst

gdal.UseExceptions()

warnings.filterwarnings('ignore', category=UserWarning, append=True)

def validate_input_files(input_files):
    valid_files = []
    for file in input_files:
        ds = None
        try:
            ds = gdal.Open(file)
            if ds is None:
                print(f"Warning: Unable to open {file}. Skipping this file.")
            elif ds.RasterXSize > 0 and ds.RasterYSize > 0:
                valid_files.append(file)
            else:
                print(f"Warning: {file} has zero size. Skipping this file.")
        finally:
            if ds:
                ds = None
    return valid_files

def merge_input_files(input_files, output_file):
    if not input_files:
        raise RuntimeError("No valid input files to merge.")
    # Using gdalwarp to handle overlaps effectively
    command = ["gdalwarp", "-overwrite", "-r", "average", "-of", "GTiff"] + input_files + [output_file]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during merging input files: {e}")
        raise

def extract_band_nc(input_file, band_number, output_file):
    ds = None
    try:
        ds = gdal.Open(input_file)
        if ds is None:
            raise RuntimeError(f"Failed to open band {band_number} from {input_file}.")
        gdal.Translate(output_file, ds, bandList=[band_number], format='VRT', outputType=gdalconst.GDT_Byte, scaleParams=[[-2, 0, -2, 0]])
    finally:
        if ds:
            ds = None

def convert_band_to_8bit(input_file, band_number, output_file):
    # Adjust the scale parameters to map data range (-2, 0) to appropriate values:
    # 0 should remain 0 and be transparent, -1 and -2 should be different intensities of red
    ds = gdal.Open(input_file)
    if ds is None:
        raise RuntimeError(f"Failed to open {input_file} for band conversion.")
    vrt_options = gdal.TranslateOptions(
        bandList=[band_number],
        format='GTiff',
        outputType=gdalconst.GDT_Byte,
        scaleParams=[[0, -2, 0, 255]],
        noData=0,
        # creationOptions=['ALPHA=YES']
    )
    gdal.Translate(output_file, ds, options=vrt_options)
    ds = None

def generate_xyz_tiles(input_file, output_directory, zoom_levels):
    command = [
        'gdal2tiles.py', '-z', zoom_levels, '-r', 'bilinear', '--xyz', '--s_srs', 'EPSG:4326', '-w', 'none',
        input_file, output_directory
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during generating XYZ tiles: {e}")
        raise

def remove_aux_files(output_directory):
    for root, _, files in os.walk(output_directory):
        for file in files:
            if file.endswith(".aux.xml"):
                os.remove(os.path.join(root, file))

def get_base_date(time_variable):
    time_units = time_variable.units
    base_date_str = time_units.split('since ')[1]
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d %H:%M:%S")
    return base_date

def get_time_from_tif(input_file):
    ds = gdal.Open(input_file)
    if ds is None:
        raise RuntimeError(f"Failed to open {input_file}.")
    metadata = ds.GetMetadata()
    time_values = metadata.get('NETCDF_DIM_time_VALUES', None)
    if time_values is None:
        raise RuntimeError("NETCDF_DIM_time_VALUES metadata not found in the TIF file.")
    base_date_str = metadata.get('time#units', 'days since 1970-01-01 00:00:00')
    base_date = datetime.strptime(base_date_str, "days since %Y-%m-%d %H:%M:%S")
    time_values = [int(t) for t in time_values[1:-1].split(',')]
    dates = [(base_date + timedelta(days=t)).strftime("%Y%m%d") for t in time_values]
    return dates

def main():
    if len(sys.argv) < 4:
        print("Usage: python xyz_creator.py <input_file> <output_directory> <zoom_levels>")
        print("zoom_levels example: 0-18")
        sys.exit(1)

    input_file = sys.argv[1]
    output_directory = sys.argv[2]
    zoom_levels = sys.argv[3]

    # Step 1: Get the time variable from the merged TIF file
    dates = get_time_from_tif(input_file)
    actual_num_bands = len(dates)

    # Step 2: Extract each band, convert to 8-bit, and generate XYZ tiles
    for band_number, date in enumerate(dates, start=1):
        print(f"Processing band {band_number}/{actual_num_bands}")
        band_file = f'{input_file}_band_{band_number}_8bit.tif'
        band_output_directory = os.path.join(output_directory, date)

        # Convert the band to an 8-bit single-band file
        convert_band_to_8bit(input_file, band_number, band_file)

        # Access the band file and generate XYZ tiles if it contains valid data
        ds = gdal.Open(band_file)
        if ds is not None:
            band = ds.GetRasterBand(1)
            band_data = band.ReadAsArray()
            if band_data is not None and np.any(band_data != 0):
                generate_xyz_tiles(band_file, band_output_directory, zoom_levels)
            else:
                print(f"Skipping band {band_number} as it contains no valid data (all values are zero).")
        else:
            print(f"Skipping band {band_number} due to invalid dataset.")

        # Cleanup
        os.remove(band_file)

    # Remove auxiliary files and band directories
    remove_aux_files(output_directory)


if __name__ == "__main__":
    main()
