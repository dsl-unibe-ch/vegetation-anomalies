import os
import subprocess
import warnings

from osgeo import gdal

gdal.UseExceptions()

warnings.filterwarnings("ignore", category=UserWarning, append=True)

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
        gdal.Translate(output_file, ds, bandList=[band_number])
    finally:
        if ds:
            ds = None

def convert_to_8bit(input_file, output_file):
    command = ["gdal_translate", "-of", "GTiff", "-ot", "Byte", "-scale", input_file, output_file]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during converting to 8-bit: {e}")
        raise

def rename_and_move_tiles(output_directory, date):
    for root, _, files in os.walk(output_directory):
        for file in files:
            if file.endswith(".png"):
                old_path = os.path.join(root, file)
                # Create new directory structure {z}/{x}/{y}/{date}.png
                relative_path = os.path.relpath(root, output_directory)
                parts = relative_path.split(os.sep)
                if len(parts) >= 3:  # Ensure it has {date}/{z}/{x}
                    date_str, z, x = parts[-3], parts[-2], parts[-1]
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
    input_files = ['../data/cubes_demo/anomalies_2018_47.468318939208984_8.746687889099121.tif',
                   '../data/cubes_demo/anomalies_2018_47.468326568603516_8.7136812210083.tif',
                   '../data/cubes_demo/anomalies_2018_47.491363525390625_8.71367359161377.tif',
                   '../data/cubes_demo/anomalies_2018_47.491371154785156_8.680665969848633.tif']
    merged_file = '../data/cubes_demo/anomalies_2018_2.tif'

    # Validate input files
    valid_input_files = validate_input_files(input_files)

    if not valid_input_files:
        raise RuntimeError("No valid input files to process.")

    merge_input_files(valid_input_files, merged_file)


if __name__ == "__main__":
    main()
