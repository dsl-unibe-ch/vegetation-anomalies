import os
import subprocess
from datetime import datetime, timedelta

from osgeo import gdal


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

def merge_tiffs(input_files, output_file):
    if not input_files:
        raise RuntimeError("No valid input files to merge.")
    # Using gdalwarp to handle overlaps effectively
    command = ["gdalwarp", "-overwrite", "-r", "average", "-of", "GTiff"] + input_files + [output_file]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during merging TIFF files: {e}")
        raise

# def reproject_to_wgs84(input_file, output_file):
#     command = ["gdalwarp", "-t_srs", "EPSG:4326", input_file, output_file]
#     subprocess.run(command, check=True)

def extract_band(input_file, band_number, output_file):
    ds = None
    try:
        ds = gdal.Open(input_file)
        gdal.Translate(output_file, ds, bandList=[band_number])
    finally:
        if ds:
            ds = None

def convert_to_8bit(input_file, output_file):
    command = ["gdal_translate", "-of", "VRT", "-ot", "Byte", "-scale", input_file, output_file]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during converting to 8-bit: {e}")
        raise

def generate_xyz_tiles(input_file, output_directory, zoom_levels):
    command = [
        "gdal2tiles.py", "-z", zoom_levels, "-r", "bilinear", "--xyz", "--s_srs", "EPSG:4326", "-w", "none",
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
            if file.endswith(".png"):
                old_path = os.path.join(root, file)
                # Create new directory structure {z}/{x}/{y}/{date}.png
                relative_path = os.path.relpath(root, output_directory)
                parts = relative_path.split(os.sep)
                if len(parts) >= 3:  # Ensure it has {band}/{z}/{x}
                    band, z, x = parts[-3], parts[-2], parts[-1]
                    y = os.path.splitext(file)[0]
                    new_dir = os.path.join(output_directory, z, x, y)
                    os.makedirs(new_dir, exist_ok=True)
                    new_path = os.path.join(new_dir, f"{date}.png")
                    os.rename(old_path, new_path)
                else:
                    print(f"Warning: Unexpected directory structure for {old_path}. Skipping.")

def remove_aux_files(output_directory):
    for root, _, files in os.walk(output_directory):
        for file in files:
            if file.endswith(".aux.xml"):
                os.remove(os.path.join(root, file))

def main():
    input_files = ["../data/cubes_demo/anomalies_2018_47.468318939208984_8.746687889099121.tif",
                   "../data/cubes_demo/anomalies_2018_47.468326568603516_8.7136812210083.tif",
                   "../data/cubes_demo/anomalies_2018_47.491363525390625_8.71367359161377.tif",
                   "../data/cubes_demo/anomalies_2018_47.491371154785156_8.680665969848633.tif"]
    merged_file = "../data/cubes_demo/anomalies_2018.tif"
    zoom_levels = "0-18"
    output_directory = "../data/cubes_demo_output"

    # Validate input files
    valid_input_files = validate_input_files(input_files)

    # Step 1: Merge TIFF files into a single raster
    merge_tiffs(valid_input_files, merged_file)

    # Verify the number of bands in the merged file
    ds = None
    try:
        ds = gdal.Open(merged_file)
        if ds is None:
            raise RuntimeError("Failed to open merged file.")
        actual_num_bands = ds.RasterCount
    finally:
        if ds:
            ds = None

    # Generate dates starting from 2018-01-05 with a step of 5 days
    start_date = datetime(2018, 1, 5)
    dates = [(start_date + timedelta(days=5 * i)).strftime("%Y%m%d") for i in range(actual_num_bands)]

    # Step 2: Extract each band, convert to 8-bit, and generate XYZ tiles
    for band_number, date in enumerate(dates, start=1):
        print(f"Processing band {band_number}/{actual_num_bands}.")

        band_file = f"band_{band_number}.tif"
        band_8bit_file = f"band_{band_number}_8bit.vrt"
        band_output_directory = os.path.join(output_directory, str(date))

        # Extract the band
        extract_band(merged_file, band_number, band_file)

        # Convert to 8-bit
        convert_to_8bit(band_file, band_8bit_file)

        # Generate XYZ tiles
        generate_xyz_tiles(band_8bit_file, band_output_directory, zoom_levels)

        # Rename and move tiles to follow {z}/{x}/{y}/{date}.png format
        rename_and_move_tiles(band_output_directory, date)

        # Cleanup
        os.remove(band_file)
        os.remove(band_8bit_file)

    # Remove auxiliary files and band directories
    remove_aux_files(output_directory)
    # for band_dir in os.listdir(output_directory):
    #     band_path = os.path.join(output_directory, band_dir)
    #     if os.path.isdir(band_path) and band_dir.startswith("band_"):
    #         shutil.rmtree(band_path)

if __name__ == "__main__":
    main()