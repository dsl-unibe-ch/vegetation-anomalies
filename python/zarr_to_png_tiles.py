import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import zarr
from osgeo import gdal, osr
from tqdm import tqdm

CONFIG_FILE_NAME = 'metadata.json'
NEGATIVE_ANOMALY_COLOR = [204, 0, 0, 255]
NO_ANOMALY_COLOR = [128, 128, 128, 255]
POSITIVE_ANOMALY_COLOR = [0, 0, 204, 255]
NO_DATA_COLOR = [0, 0, 0, 0]

# Function to map values to a color ramp
def map_value_to_color_cpu(value, colors_lookup_table, no_data_color):
    colors = np.array(colors_lookup_table, dtype=np.uint8)
    default_color = np.array(no_data_color, dtype=np.uint8)  # No data (value = 255) - transparent

    # Create a result array filled with the default color
    result = np.full((value.shape[0], value.shape[1], 4), default_color, dtype=np.uint8)

    # Mask valid indices and map them to the appropriate colors
    mask = (value >= 0) & (value < 3) # Boolean mask, with True values everywhere, where the condition holds
    # Assign to those values of result 3d array, where mask=True, and those should be the colors of the initial values,
    # where mask=True. This means that we are assigning the colors, corresponding to the non-empty values.
    result[mask] = colors[value[mask]]

    return result


def get_colors_lookup_table(missing_id, negative_anomaly_id, normal_id, positive_anomaly_id):
    colors_lookup_table = [NO_DATA_COLOR] * 256
    colors_lookup_table[missing_id] = NO_DATA_COLOR
    colors_lookup_table[negative_anomaly_id] = NEGATIVE_ANOMALY_COLOR
    colors_lookup_table[normal_id] = NO_ANOMALY_COLOR
    colors_lookup_table[positive_anomaly_id] = POSITIVE_ANOMALY_COLOR
    return colors_lookup_table


def create_temporary_tiff(data, temp_tiff_path, rgba_data, x_values, y_values, zarr_crs):
    # Save the RGBA data to a temporary GeoTIFF
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(temp_tiff_path, data.shape[1], data.shape[0], 4, gdal.GDT_Byte)

    for band in range(4):
        dataset.GetRasterBand(band + 1).WriteArray(rgba_data[:, :, band])

    x_min = x_values.min()
    y_min = y_values.min()
    x_max = x_values.max()
    y_max = y_values.max()

    pixel_width = (x_max - x_min) / len(x_values)
    pixel_height = (y_max - y_min) / len(y_values)
    dataset.SetGeoTransform([x_min, pixel_width, 0, y_max, 0, -pixel_height])

    # Set spatial reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(zarr_crs.split(':')[1]))
    dataset.SetProjection(srs.ExportToWkt())
    dataset.FlushCache()


def create_config_file(output_folder, **kwargs):
    with open(output_folder + '/' + CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(kwargs, f, default=str) # default=str is used to encode dates as simple strings


def safe_get(lst, index):
    return lst[index] if 0 <= index < len(lst) else None


def parse_zoom_levels(zoom_levels):
    # Get the values from the zoom levels string
    zoom_levels_list = list(map(int, zoom_levels.split('-')))

    # Check for correctness
    if len(zoom_levels_list) != 2:
        raise RuntimeError("There should be exactly two zoom levels in the format <from>-<to>")
    if zoom_levels_list[0] > zoom_levels_list[1]:
        raise RuntimeError("Zoom level from should not be greater than to")
    return zoom_levels_list


def main():
    if len(sys.argv) < 5:
        print(f"Usage: python {sys.argv[0]} <zarr_folder> <output_folder> <zoom_levels> <processes> [<start_date_index>]")
        sys.exit(1)

    zarr_folder = sys.argv[1]
    output_folder = sys.argv[2]
    zoom_levels = sys.argv[3]
    processes = int(sys.argv[4])
    start_date_index = int(safe_get(sys.argv, 5) or 0)

    # Set PROJ_LIB dynamically based on Conda installation
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        os.environ['PROJ_LIB'] = os.path.join(conda_prefix, 'share', 'proj')

    # Create output folder if it doesn’t exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the Zarr array
    zarr_dataset = zarr.open(zarr_folder, mode='r')

    zattrs = zarr_dataset.attrs
    x_values = zarr_dataset.E[:]
    y_values = zarr_dataset.N[:]
    time_values = zarr_dataset.time[:]
    start_date = datetime.strptime(zarr_dataset.time.attrs['units'], 'days since %Y-%m-%d')

    # Create config file for the UI to read from
    create_config_file(output_folder, start_date=start_date, time_values=time_values.tolist(),
                       zoom_levels=parse_zoom_levels(zoom_levels),
                       negative_anomaly_color=NEGATIVE_ANOMALY_COLOR, no_anomaly_color=NO_ANOMALY_COLOR,
                       positive_anomaly_color=POSITIVE_ANOMALY_COLOR, no_data_color=NO_DATA_COLOR)

    # Reading parameters from attributes of the Zarr format.
    zarr_crs = zattrs['crs']
    missing_id = int(zattrs['missing_id'])
    negative_anomaly_id = int(zattrs['negative_anomaly_id'])
    normal_id = int(zattrs['normal_id'])
    positive_anomaly_id = int(zattrs['positive_anomaly_id'])

    colors_lookup_table = get_colors_lookup_table(missing_id, negative_anomaly_id, normal_id, positive_anomaly_id)

    # Generate tiles with GDAL
    for t in tqdm(range(start_date_index, zarr_dataset.data.shape[0])):
        date = (start_date + timedelta(days=time_values[t].item())).strftime("%Y%m%d")

        # Read the 2D array for the current timestep
        data = zarr_dataset.data[t, :, :]

        rgba_data = map_value_to_color_cpu(data, colors_lookup_table, NO_DATA_COLOR)

        temp_tiff_path = os.path.join(output_folder, f"temp_{date}.tif")
        create_temporary_tiff(data, temp_tiff_path, rgba_data, x_values, y_values, zarr_crs)

        # Use gdal2tiles to generate tiles from the temporary GeoTIFF
        tile_output_dir = os.path.join(output_folder, date)
        os.makedirs(tile_output_dir, exist_ok=True)
        os.system(f'gdal2tiles.py -s {zarr_crs} -z {zoom_levels} -w none --processes={processes} --xyz -x {temp_tiff_path} {tile_output_dir}')

        # Remove the temporary GeoTIFF
        os.remove(temp_tiff_path)

    print("PNG image pyramids generated successfully.")


if __name__ == "__main__":
    main()