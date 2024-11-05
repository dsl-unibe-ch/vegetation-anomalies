import subprocess
import sys
import warnings

from osgeo import gdal

gdal.UseExceptions()

warnings.filterwarnings("ignore", category=UserWarning, append=True)

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

def main():
    if len(sys.argv) < 3:
        print("Usage: python tif_merger.py <merged_file> <input_files...>")
        sys.exit(1)

    merged_file = sys.argv[1]
    input_files = sys.argv[2:]

    if not input_files:
        raise RuntimeError("No input files to process.")

    merge_input_files(input_files, merged_file)


if __name__ == "__main__":
    main()
