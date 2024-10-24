import os
import subprocess
import warnings
from datetime import datetime, timedelta

import netCDF4 as nc
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
    # # Using gdalwarp to handle overlaps effectively
    # command = ['gdalwarp', '-overwrite', '-r', 'average', '-of', 'GTiff'] + input_files + [output_file]
    # try:
    #     subprocess.run(command, check=True)
    # except subprocess.CalledProcessError as e:
    #     print(f"Error during merging input files: {e}")
    #     raise

    # Using gdal.Warp to handle overlaps effectively, bypassing geotransform issues
    warp_options = gdal.WarpOptions(format='GTiff', srcNodata=None, dstNodata=None, resampleAlg='average', options=['-overwrite'], srcSRS='EPSG:4326',
                                    dstSRS='EPSG:4326')
    try:
        gdal.Warp(destNameOrDestDS=output_file, srcDSOrSrcDSTab=input_files, options=warp_options)
    except RuntimeError as e:
        print(f"Error during merging input files: {e}")
        raise

# def merge_input_files(input_files, output_file):
#     if not input_files:
#         raise RuntimeError("No valid input files to merge.")
#     # Using gdal.Warp to handle overlaps effectively and manually setting the geotransform
#     try:
#         # Open the first dataset to determine dimensions
#         ds = gdal.Open(input_files[0])
#         if ds is None:
#             raise RuntimeError(f"Failed to open {input_files[0]} for geotransform setup.")
#
#         # Manually set a default geotransform to avoid issues
#         geotransform = (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
#         projection = ds.GetProjection()
#         x_size = ds.RasterXSize
#         y_size = ds.RasterYSize
#         ds = None
#
#         # Create an in-memory raster with the specified geotransform
#         driver = gdal.GetDriverByName("GTiff")
#         out_ds = driver.Create(output_file, x_size, y_size, len(input_files), gdal.GDT_Float32)
#         out_ds.SetGeoTransform(geotransform)
#         out_ds.SetProjection(projection)
#
#         # Merge all the input files into the output dataset
#         for idx, input_file in enumerate(input_files):
#             src_ds = gdal.Open(input_file)
#             if src_ds is None:
#                 print(f"Warning: Unable to open {input_file} during merging. Skipping.")
#                 continue
#             gdal.ReprojectImage(src_ds, out_ds, None, None, gdal.GRA_Average)
#             src_ds = None
#
#         out_ds = None
#     except RuntimeError as e:
#         print(f"Error during merging input files: {e}")
#         raise

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

def rename_and_move_tiles(output_directory, date):
    for root, _, files in os.walk(output_directory):
        for file in files:
            if file.endswith('.png'):
                old_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, output_directory)
                parts = relative_path.split(os.sep)
                if len(parts) >= 3:  # Ensure it has {date}/{z}/{x}
                    date_str, z, x = parts[-3], parts[-2], parts[-1]
                    y = os.path.splitext(file)[0]
                    new_dir = os.path.join(output_directory, z, x, y)
                    os.makedirs(new_dir, exist_ok=True)
                    new_path = os.path.join(new_dir, f'{date}.png')
                    os.rename(old_path, new_path)
                else:
                    print(f"Warning: Unexpected directory structure for {old_path}. Skipping.")

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


def main():
    input_files = ['../data/cubes_demo/anomalies_2018_47.468318939208984_8.746687889099121.nc',
                   '../data/cubes_demo/anomalies_2018_47.468326568603516_8.7136812210083.nc',
                   '../data/cubes_demo/anomalies_2018_47.491363525390625_8.71367359161377.nc',
                   '../data/cubes_demo/anomalies_2018_47.491371154785156_8.680665969848633.nc']
    merged_file = '../data/cubes_demo/anomalies_2018_1.tif'
    zoom_levels = '0-18'
    output_directory = '../data/cubes_demo_output'

    # Validate input files
    valid_input_files = validate_input_files(input_files)

    merge_input_files(valid_input_files, merged_file)

    if not valid_input_files:
        raise RuntimeError("No valid input files to process.")

    # Step 1: Get the time variable from the NetCDF file
    dataset = nc.Dataset(valid_input_files[0], mode='r')
    time_variable = dataset.variables['time']
    base_date = get_base_date(time_variable)
    time_values = time_variable[:]
    dates = [(base_date + timedelta(days=int(t))).strftime("%Y%m%d") for t in time_values]
    dataset.close()

    actual_num_bands = len(dates)

    # Step 2: Extract each band, convert to 8-bit, and generate XYZ tiles
    # for band_number, date in tqdm(enumerate(dates, start=1), total=actual_num_bands, desc="Processing bands"):
    for band_number, date in enumerate(dates, start=1):
        print(f"Processing band {band_number}/{actual_num_bands}")
        band_file = f'band_{band_number}.tif'
        band_output_directory = os.path.join(output_directory, date)

        # Extract the band from the merged file
        extract_band_nc(merged_file, band_number, band_file)

        # Generate XYZ tiles, only if the band contains actual data
        ds = gdal.Open(band_file)
        if ds is not None:
            band = ds.GetRasterBand(1)
            if np.any(band.ReadAsArray() != 0):
                generate_xyz_tiles(band_file, band_output_directory, zoom_levels)
            else:
                print(f"Skipping band {band_number} due to lack of valid data.")
        else:
            print(f"Skipping band {band_number} due to invalid dataset.")

        # Rename and move tiles to follow {z}/{x}/{y}/{date}.png format
        rename_and_move_tiles(band_output_directory, date)

        # Cleanup
        os.remove(band_file)

    # Remove auxiliary files and band directories
    remove_aux_files(output_directory)


if __name__ == "__main__":
    main()