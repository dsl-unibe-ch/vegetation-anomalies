import json
import os
import shutil
import sys
from datetime import datetime, timedelta

import numpy as np
import zarr
from osgeo import gdal, osr
from tqdm import tqdm

CONFIG_FILE_NAME = 'metadata.json'
EMPTY_TILE_FILE_NAME = 'empty.png'
NEGATIVE_ANOMALY_COLOR = [204, 0, 0, 255]
NO_ANOMALY_COLOR = [128, 128, 128, 255]
POSITIVE_ANOMALY_COLOR = [0, 0, 204, 255]
NO_DATA_COLOR = [0, 0, 0, 0]

WEB_MERCATOR_CRS = 'EPSG:3857'

def map_value_to_color_cpu(value, colors_lookup_table, no_data_color):
    """
    Function to map values to a list of colors.

    :param value: 2D array of initial numerical values to map from.
    :param colors_lookup_table: Lookup list to do the following mapping: index -> colors_lookup_table[index].
    :param no_data_color: Color to use when there are no data.
    :return: 2D array of mapped colors.
    """
    colors = np.array(colors_lookup_table, dtype=np.uint8)
    default_color = np.array(no_data_color, dtype=np.uint8)  # No data (value = 255) - transparent

    # Create a result array filled with the default color
    result = np.full((value.shape[0], value.shape[1], 4), default_color, dtype=np.uint8)

    # Mask valid indices and map them to the appropriate colors
    mask = (value >= 0) & (value < 3) # Boolean mask, with True values everywhere, where the condition holds
    # Assign to those values of result 3D array, where mask=True, and those should be the colors of the initial values,
    # where mask=True. This means that we are assigning the colors, corresponding to the non-empty values.
    result[mask] = colors[value[mask]]

    return result


def get_colors_lookup_table(missing_id, negative_anomaly_id, normal_id, positive_anomaly_id):
    """
    Creates a lookup table to do the mapping index -> colors_lookup_table[index]. The IDs in the parameters correspond
    to indices in the result.

    :param missing_id: Value that indicates no data at the location.
    :param negative_anomaly_id: Value that indicates negative anomaly the location.
    :param normal_id: Value that indicates no anomaly the location.
    :param positive_anomaly_id: Value that indicates positive anomaly the location.
    :return: Mapped result index -> colors_lookup_table[index].
    """
    colors_lookup_table = [NO_DATA_COLOR] * 256
    colors_lookup_table[missing_id] = NO_DATA_COLOR
    colors_lookup_table[negative_anomaly_id] = NEGATIVE_ANOMALY_COLOR
    colors_lookup_table[normal_id] = NO_ANOMALY_COLOR
    colors_lookup_table[positive_anomaly_id] = POSITIVE_ANOMALY_COLOR
    return colors_lookup_table


def create_tiff(data, tiff_path, colors_lookup_table, transform, source_crs):
    """
    Creates GeoTIFF for data by mapping them to colors and saving into a file.

    :param data: Data to be saved.
    :param tiff_path: Path to the file save the data at.
    :param colors_lookup_table Lookup table in format index -> colors_lookup_table[index].
    :param transform: Geotransform computed from all initial values.
    :param source_crs: Coordinate reference system to be assigned to the resulting dataset.
    :return: Dataset with the GeoTIFF data.
    """
    # Save the RGBA data to a temporary GeoTIFF
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(tiff_path, data.shape[1], data.shape[0], 4, gdal.GDT_Byte)

    rgba_data = map_value_to_color_cpu(data, colors_lookup_table, NO_DATA_COLOR)

    for band in range(4):
        dataset.GetRasterBand(band + 1).WriteArray(rgba_data[:, :, band])

    dataset.SetGeoTransform(transform)

    # Set spatial reference
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(source_crs.split(':')[1]))
    dataset.SetProjection(srs.ExportToWkt())
    dataset.FlushCache()

    return dataset


def reproject_riff(dataset, target_tiff_path, target_crs):
    """
    Reprojects GeoTIFF to a new target CRS using gdal.Warp(). Used the nearest neighbour algorithm to avoid
    antialiasing.

    :param dataset: GeoTIFF dataset to reproject from.
    :param target_tiff_path: Path to the target file.
    :param target_crs: Coordinate reference system to be assigned to the resulting dataset.
    """

    gdal.Warp(
        target_tiff_path,
        dataset,
        dstSRS=target_crs,
        resampleAlg=gdal.GRA_NearestNeighbour
    )


def compute_transform(x_values, y_values):
    """
    Computes the geo-transformation array from X and Y values that can be used in the gdal.Warp() method indirectly.

    :param x_values: Input X values.
    :param y_values: Input Y values.
    :return: Geo-transformation array of format [x_min, pixel_width, 0, y_max, 0, -pixel_height].
    """
    x_min = x_values.min()
    y_min = y_values.min()
    x_max = x_values.max()
    y_max = y_values.max()
    pixel_width = (x_max - x_min) / len(x_values)
    pixel_height = (y_max - y_min) / len(y_values)
    return [x_min, pixel_width, 0, y_max, 0, -pixel_height]


def create_json_file(output_folder, **kwargs):
    """
    Creates a JSON file in a folder with the specified map of values.

    :param output_folder: the folder to create the file at.
    :param kwargs: Keyword arguments to be dumped to the config JSON file.
    """
    with open(output_folder + '/' + CONFIG_FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(kwargs, f, default=str) # default=str is used to encode dates as simple strings


def copy_empty_png(output_folder):
    """
    Copies empty PNG file from the current directory

    :param output_folder: The folder to copy the empty PNG file to.
    """
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)
    shutil.copy(os.path.join(script_dir, EMPTY_TILE_FILE_NAME), output_folder)


def safe_get(lst, index):
    """
    Safely gets an element from a list.

    :param lst: List to probe for the element.
    :param index: Index of the element to probe.
    :return: lst[index] if the value is not outside the range, otherwise None.
    """
    return lst[index] if 0 <= index < len(lst) else None


def parse_zoom_levels(zoom_levels):
    """
    Gets the values from the zoom levels string

    :param zoom_levels: Input string of format <from>-<to>, where from <= to are integer values.
    :return: List with two parsed values from the string as integers.
    """
    zoom_levels_list = list(map(int, zoom_levels.split('-')))

    # Check for correctness
    if len(zoom_levels_list) != 2:
        raise RuntimeError("There should be exactly two zoom levels in the format <from>-<to>")
    if zoom_levels_list[0] > zoom_levels_list[1]:
        raise RuntimeError("Zoom level from should not be greater than to")
    return zoom_levels_list


def main():
    """
    Application entry point.
    """

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

    x_values = zarr_dataset['E'][:]
    y_values = zarr_dataset['N'][:]
    transform = compute_transform(x_values, y_values)
    time_values = zarr_dataset['time'][:]
    start_date = datetime.strptime(zarr_dataset['time'].attrs['units'], 'days since %Y-%m-%d')

    # Create config file for the UI to read from
    create_json_file(output_folder, start_date=start_date, time_values=time_values.tolist(),
                     zoom_levels=parse_zoom_levels(zoom_levels),
                     negative_anomaly_color=NEGATIVE_ANOMALY_COLOR, no_anomaly_color=NO_ANOMALY_COLOR,
                     positive_anomaly_color=POSITIVE_ANOMALY_COLOR, no_data_color=NO_DATA_COLOR)

    copy_empty_png(output_folder)

    # Reading parameters from attributes of the Zarr format.
    zarr_attrs = zarr_dataset.attrs
    zarr_crs = zarr_attrs['crs']
    missing_id = int(zarr_attrs['missing_id'])
    negative_anomaly_id = int(zarr_attrs['negative_anomaly_id'])
    normal_id = int(zarr_attrs['normal_id'])
    positive_anomaly_id = int(zarr_attrs['positive_anomaly_id'])

    colors_lookup_table = get_colors_lookup_table(missing_id, negative_anomaly_id, normal_id, positive_anomaly_id)

    # Generate tiles with GDAL
    for t in tqdm(range(start_date_index, zarr_dataset['data'].shape[0])):
        date = (start_date + timedelta(days=time_values[t].item())).strftime("%Y%m%d")

        # Read the 2D array for the current timestep
        data = zarr_dataset['data'][t, :, :]

        # Create temporary GeoTIFF as an intermediary step
        temp_tiff_path = os.path.join(output_folder, f"temp_{date}.tif")
        temp_tiff_path_reprojected = temp_tiff_path.replace(".tif", "_reprojected.tif")

        create_tiff(data, temp_tiff_path, colors_lookup_table, transform, zarr_crs)
        reproject_riff(temp_tiff_path, temp_tiff_path_reprojected, WEB_MERCATOR_CRS)

        # Use gdal2tiles to generate tiles from the temporary GeoTIFF
        tile_output_dir = os.path.join(output_folder, date)
        os.makedirs(tile_output_dir, exist_ok=True)
        os.system(f'gdal2tiles.py -s {WEB_MERCATOR_CRS} -z {zoom_levels} -w none --processes={processes} --xyz -x -r near {temp_tiff_path_reprojected} {tile_output_dir}')

        # Remove the temporary GeoTIFFs
        os.remove(temp_tiff_path)
        os.remove(temp_tiff_path_reprojected)

    print("PNG image pyramids generated successfully.")


if __name__ == "__main__":
    main()