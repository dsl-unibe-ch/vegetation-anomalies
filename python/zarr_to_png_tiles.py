import os
from datetime import datetime, timedelta

import numpy as np
import zarr
from osgeo import gdal, osr
from tqdm import tqdm

# import cupy as cp

# # Function to map values to a color ramp
# def map_value_to_color_gpu(value):
#     colors = cp.array([
#         [204, 0, 0, 255],  # Negative anomaly - dark red
#         [0, 0, 0, 0],      # Normal state - transparent
#         [204, 0, 0, 255],  # Positive anomaly - dark blue
#     ], dtype=cp.uint8)
#     default_color = cp.array([128, 128, 128, 128], dtype=cp.uint8) # No data - translucent grey
#
#     mask = (value >= 0) & (value <= 255)
#     result = cp.where(mask[:, :, None], colors[value], default_color)
#     return result

# Function to map values to a color ramp
def map_value_to_color_cpu(value):
    colors = np.array([
        [204, 0, 0, 255],    # Negative anomaly - dark red
        [128, 128, 128, 128],# Normal state - grey
        [204, 0, 0, 255],    # Positive anomaly - dark blue
    ], dtype=np.uint8)
    default_color = np.array([0, 0, 0, 0], dtype=np.uint8)  # No data (value = 255) - transparent

    # Create a result array filled with the default color
    result = np.full((value.shape[0], value.shape[1], 4), default_color, dtype=np.uint8)

    # Mask valid indices and map them to the appropriate colors
    mask = (value >= 0) & (value < 3)
    result[mask] = colors[value[mask]]

    return result

# Set PROJ_LIB dynamically based on Conda installation
conda_prefix = os.environ.get('CONDA_PREFIX')
if conda_prefix:
    os.environ['PROJ_LIB'] = os.path.join(conda_prefix, 'share', 'proj')

# Constants for the conversion
START_DATE = datetime(2018, 1, 5) #TODO: Read the values from the settings
TIME_STEP_DAYS = 5

# Path to the Zarr folder and output directory
zarr_folder = '../data/larger-anomalies.zarr'
output_folder = '../data/larger_cubes_demo_output_4'
zoom_levels = '0-18'

# Create output folder if it doesn’t exist
os.makedirs(output_folder, exist_ok=True)

# Open the Zarr array
zarr_dataset = zarr.open(zarr_folder, mode='r')

zattrs = zarr_dataset.attrs
x_values = zarr_dataset.E[:]
y_values = zarr_dataset.N[:]
time_values = zarr_dataset.time[:] #TODO: use these values.

print("Extracted .zattrs values:")
for key, value in zattrs.items():
    print(f"{key}: {value}")

zarr_crs = zattrs['crs']

# Generate tiles with GDAL
for t in tqdm(range(zarr_dataset.data.shape[0])):
    date = (START_DATE + timedelta(days=t * TIME_STEP_DAYS)).strftime("%Y%m%d")

    # Read the 2D array for the current timestep
    data = zarr_dataset.data[t, :, :]

    rgba_data = map_value_to_color_cpu(data)

    # # Transfer data to GPU
    # data_gpu = cp.array(data, dtype=cp.uint8)
    #
    # # Map values to RGBA colors on GPU
    # rgba_data_gpu = map_value_to_color_gpu(data_gpu)
    #
    # # Transfer RGBA data back to CPU
    # rgba_data = cp.asnumpy(rgba_data_gpu)

    # Save the RGBA data to a temporary GeoTIFF
    temp_tiff_path = os.path.join(output_folder, f"temp_{date}.tif")
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(temp_tiff_path, data.shape[1], data.shape[0], 4, gdal.GDT_Byte)

    for band in range(4):
        dataset.GetRasterBand(band + 1).WriteArray(rgba_data[:, :, band])

    x_min = x_values.min()
    y_min = y_values.min()
    x_max = x_values.max()
    y_max = y_values.max()

    pixel_width = (x_max - x_min) / len(x_values)
    pixel_height = (y_min - y_max) / len(y_values)  # Negative for top-to-bottom
    dataset.SetGeoTransform([x_min, pixel_width, 0, y_min, 0, -pixel_height])

    # Set spatial reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(zarr_crs.split(':')[1]))
    dataset.SetProjection(srs.ExportToWkt())

    dataset.FlushCache()
    dataset = None

    # Use gdal2tiles to generate tiles from the temporary GeoTIFF
    tile_output_dir = os.path.join(output_folder, date)
    os.makedirs(tile_output_dir, exist_ok=True)
    os.system(f"gdal2tiles.py -s {zarr_crs} -z {zoom_levels} -w none --processes=20 --xyz {temp_tiff_path} {tile_output_dir}")

    # Remove the temporary GeoTIFF
    os.remove(temp_tiff_path)

print("PNG image pyramids generated successfully.")
