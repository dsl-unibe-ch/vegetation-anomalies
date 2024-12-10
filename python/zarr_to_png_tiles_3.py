from unittest import case

import zarr
import numpy as np
import os
import xarray as xr
from datetime import datetime, timedelta
from osgeo import gdal, osr
from tqdm import tqdm

# Function to map values to a color ramp
def map_value_to_color(value):
    match value:
        case 0:
            return (204, 0, 0, 255)     # Negative anomaly - dark red
        case 1:
            return (0, 0, 0, 0)         # Normal state - transparent
        case 2:
            return (204, 0, 0, 255)     # Positive anomaly - dark blue
        case 255:
            return (128, 128, 128, 128) # No data - translucent grey
        case _:
            raise ValueError(f"Unexpected value {value} in the data.")

# Constants for the conversion
START_DATE = datetime(2018, 1, 5)
TIME_STEP_DAYS = 5

# Path to the Zarr folder and output directory
zarr_folder = '../data/larger-anomalies.zarr'
output_folder = '../data/larger_cubes_demo_output_3'

# Create output folder if it doesn’t exist
os.makedirs(output_folder, exist_ok=True)

# Open the Zarr array
zarr_dataset = zarr.open(zarr_folder, mode='r')
# zarr_dataset = xr.open_zarr(zarr_folder)
zarr_crs = zarr_dataset.attrs['crs']

# # Verify the data shape matches expectations
# if z.shape != (11050, 17500, 73):
#     raise ValueError("Unexpected data shape in the Zarr array.")

# Generate tiles with GDAL
for t in tqdm(range(zarr_dataset.data.shape[0])):
    date = (START_DATE + timedelta(days=t * TIME_STEP_DAYS)).strftime("%Y%m%d")

    # Read the 2D array for the current timestep
    data = zarr_dataset.data[t, :, :]

    # Create an RGBA image array
    rgba_data = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
    for x in range(data.shape[0]):
        for y in range(data.shape[1]):
            rgba_data[x, y] = map_value_to_color(data[x, y])

    # Save the RGBA data to a temporary GeoTIFF
    temp_tiff_path = os.path.join(output_folder, f"temp_{date}.tif")
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(temp_tiff_path, data.shape[1], data.shape[0], 4, gdal.GDT_Byte)

    for band in range(4):
        dataset.GetRasterBand(band + 1).WriteArray(rgba_data[:, :, band])

    # Set a basic geotransform (you might need to adjust this for your use case)
    # dataset.SetGeoTransform([0, 1, 0, 0, 0, -1])
    srs = osr.SpatialReference(zarr_crs)
    # srs.ImportFromEPSG(4326)  # WGS84
    dataset.SetProjection(srs.ExportToWkt())
    dataset.FlushCache()

    # Use gdal2tiles to generate tiles
    tile_output_dir = os.path.join(output_folder, date)
    os.makedirs(tile_output_dir, exist_ok=True)
    os.system(f"gdal2tiles.py -z 0-5 -w none {temp_tiff_path} {tile_output_dir}")

    # Remove the temporary GeoTIFF
    os.remove(temp_tiff_path)

print("PNG image pyramids generated successfully.")
