import os

import mercantile
import pandas as pd
import xarray as xr
from PIL import Image
from matplotlib import pyplot as plt
from tqdm import tqdm

Image.MAX_IMAGE_PIXELS = None

cubes_dir = "../data/cubes_demo"
cubes_output_dir = "../data/cubes_demo_output"
cube_files = [f for f in os.listdir(cubes_dir) if f.startswith("anomalies") and f.endswith(".nc")]

for file in cube_files:
    bare_file_name = os.path.splitext(os.path.basename(file))[0]
    dataset = xr.open_dataset(os.path.join(cubes_dir, file))

    output_directory_path = cubes_output_dir
    os.makedirs(output_directory_path, exist_ok=True)

    # Extract latitude, longitude, anomaly, and time values
    lat = dataset["lat"].values
    lon = dataset["lon"].values
    time = dataset["time"].values.astype(str).tolist()
    anomaly_data = dataset["anomaly"]

    # Bounding box of the dataset
    lat_min, lat_max = lat.min(), lat.max()
    lon_min, lon_max = lon.min(), lon.max()

    # Iterate over the time dimension to extract anomaly images at each time step
    for i, time_step in enumerate(tqdm(time, desc=f"Processing {file}", unit="time_step")):
        date = pd.Timestamp(time_step).strftime('%Y-%m-%d')

        data_values = anomaly_data.isel(time=i).values
        plt.imshow(data_values, cmap="viridis", extent=[lon_min, lon_max, lat_min, lat_max])
        plt.axis("off")

        # Save the full-resolution image as a temporary file
        full_image_path = os.path.join(output_directory_path, f"{bare_file_name}_{date}_full.png")
        plt.savefig(full_image_path, format="png", bbox_inches="tight", pad_inches=0)
        plt.close()

        # Open the saved image with PIL for tiling
        full_image = Image.open(full_image_path)

        # Generate tiles for each zoom level
        for z in range(0, 10):  # Define the zoom levels you want, here 0 to 5
            tile_size = 256
            mercator_tiles = list(mercantile.tiles(lon_min, lat_min, lon_max, lat_max, zooms=[z]))

            for tile in mercator_tiles:
                x, y, z = tile.x, tile.y, tile.z

                # Calculate the pixel bounds for this tile
                bounds = mercantile.bounds(tile)
                left = int((bounds.west - lon_min) / (lon_max - lon_min) * full_image.width)
                right = int((bounds.east - lon_min) / (lon_max - lon_min) * full_image.width)
                upper = int((lat_max - bounds.north) / (lat_max - lat_min) * full_image.height)
                lower = int((lat_max - bounds.south) / (lat_max - lat_min) * full_image.height)

                # Ensure the bounds are within the image dimensions
                left = max(0, min(full_image.width, left))
                right = max(0, min(full_image.width, right))
                upper = max(0, min(full_image.height, upper))
                lower = max(0, min(full_image.height, lower))

                if left >= right or upper >= lower:
                    continue  # Skip invalid crop regions

                # Crop the tile image
                tile_image = full_image.crop((left, upper, right, lower))
                tile_image = tile_image.resize((tile_size, tile_size), Image.LANCZOS)

                # Save the tile
                tile_output_path = os.path.join(output_directory_path, f"{z}/{x}/{y}")
                os.makedirs(tile_output_path, exist_ok=True)
                tile_image.save(os.path.join(tile_output_path, f"{date}.png"))

        # Remove the full-resolution temporary image to save space
        os.remove(full_image_path)