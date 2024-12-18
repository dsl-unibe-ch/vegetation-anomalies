import os
import subprocess
import sys
import warnings
import zarr
import rasterio
from rasterio.transform import from_origin
from datetime import datetime, timedelta
from dateutil import parser

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

def convert_zarr_to_geotiff(zarr_file, output_file):
    # Open the Zarr dataset
    try:
        data = zarr.open_group(zarr_file, mode='r')
        # Assuming data is a 3D array with dimensions (bands, height, width) or (height, width)
        if len(data.shape) == 3:
            array = data[0, :, :]  # Taking the first band if multiple bands are present
        elif len(data.shape) == 2:
            array = data[:, :]
        else:
            raise ValueError("Unsupported Zarr data shape. Expected 2D or 3D array.")

        # Create a GeoTIFF using rasterio
        height, width = array.shape
        transform = from_origin(0, 0, 1, 1)  # Modify based on actual georeferencing needed

        with rasterio.open(
                output_file,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=array.dtype,
                crs='+proj=latlong',
                transform=transform,
        ) as dst:
            dst.write(array, 1)

        print(f"Successfully converted {zarr_file} to GeoTIFF {output_file}")
    except Exception as e:
        print(f"Error while converting Zarr to GeoTIFF: {e}")
        raise

def merge_input_files(input_files, output_file):
    if not input_files:
        raise RuntimeError("No valid input files to merge.")
    # Using gdalwarp to handle overlaps effectively
    command = ["gdalwarp", "-overwrite", "-r", "average", "-of", "GTiff"] + input_files + [output_file]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"GDAL command failed with output: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error during merging input files: {e}. Output: {e.stderr}")
        raise

def convert_band_to_8bit(input_file, output_file):
    # Map specific input values to colors: 0 -> transparent, -1 -> dark red, -2 -> light red
    ds = gdal.Open(input_file)
    if ds is None:
        raise RuntimeError(f"Failed to open {input_file} for band conversion.")
    band = ds.GetRasterBand(1)
    band_data = band.ReadAsArray()

    # Create a new 8-bit array with the same shape
    output_data = np.zeros_like(band_data, dtype=np.uint8)

    # Map -2 to light red, -1 to dark red, and keep 0 as 0 (transparent)
    output_data[band_data == -2] = 255  # Light red
    output_data[band_data == -1] = 127  # Dark red

    # Create the output file
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_file, ds.RasterXSize, ds.RasterYSize, 4, gdalconst.GDT_Byte)
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())

    # Write the red band
    out_ds.GetRasterBand(1).WriteArray(output_data)
    out_ds.GetRasterBand(1).SetColorInterpretation(gdal.GCI_RedBand)

    # Set the alpha channel to make 0 values transparent
    alpha_band = np.where(output_data == 0, np.uint8(0), np.uint8(255)).astype(np.uint8)
    out_ds.GetRasterBand(4).WriteArray(alpha_band)
    out_ds.GetRasterBand(4).SetColorInterpretation(gdal.GCI_AlphaBand)

def generate_png_tiles(input_file, output_directory, zoom_levels):
    command = [
        'gdal2tiles.py', '-z', zoom_levels, '-r', 'bilinear', '--xyz', '--s_srs', 'EPSG:4326', '-w', 'none',
        '--tile-format', 'png', input_file, output_directory
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during generating PNG tiles: {e}")
        raise

def remove_aux_files(output_directory):
    for root, _, files in os.walk(output_directory):
        for file in files:
            if file.endswith(".aux.xml"):
                os.remove(os.path.join(root, file))

def create_dates_from_initial(initial_date, step_in_days, number_of_days):
    dates = []
    for index in range(number_of_days):
        date = initial_date + timedelta(days=index * step_in_days)
        dates.append(date.strftime('%Y%m%d'))
    return dates

def main():
    if len(sys.argv) < 6:
        print("Usage: python zarr_to_png_tiles.py <input_directory> <output_directory> <zoom_levels> <base_date> <step_in_days>")
        print("zoom_levels example: 0-18")
        print("base_date example: 2018-01-15")
        print("step_in_days example: 5")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    zoom_levels = sys.argv[3]
    base_date = parser.parse(sys.argv[4])
    step_in_days = int(sys.argv[5])

    # Step 1: Get the dates from the parameters
    files = os.listdir(input_directory)
    time_steps = sorted(set(f.split('.')[-1] for f in files))
    dates = create_dates_from_initial(base_date, step_in_days, len(time_steps))

    # Step 2: For each time step, convert Zarr to GeoTIFF, merge the corresponding files, and generate PNG tiles
    for time_step, date in zip(time_steps, dates):
        print(f"Processing time step {time_step} for date {date}")
        matching_files = [os.path.join(input_directory, f) for f in files if f.endswith(f'.{time_step}')]

        # Convert Zarr files to GeoTIFF
        geotiff_files = []
        for zarr_file in matching_files:
            geotiff_file = os.path.join(output_directory, f'{os.path.basename(zarr_file)}.tif')
            convert_zarr_to_geotiff(zarr_file, geotiff_file)
            geotiff_files.append(geotiff_file)

        valid_files = validate_input_files(geotiff_files)

        if valid_files:
            merged_file = os.path.join(output_directory, f'merged_{date}.tif')
            merge_input_files(valid_files, merged_file)

            # Convert merged file to 8-bit
            merged_8bit_file = os.path.join(output_directory, f'merged_{date}_8bit.tif')
            convert_band_to_8bit(merged_file, merged_8bit_file)

            # Generate PNG tiles
            date_output_directory = os.path.join(output_directory, date)
            generate_png_tiles(merged_8bit_file, date_output_directory, zoom_levels)

            # Cleanup intermediate files
            os.remove(merged_file)
            os.remove(merged_8bit_file)
            for geotiff_file in geotiff_files:
                os.remove(geotiff_file)
        else:
            print(f"No valid files found for time step {time_step}. Skipping.")

    # Remove auxiliary files
    remove_aux_files(output_directory)

if __name__ == "__main__":
    main()
