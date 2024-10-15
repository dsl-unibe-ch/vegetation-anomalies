import json
import os

import pandas as pd
import xarray as xr
from matplotlib import pyplot as plt
from tqdm import tqdm

cubes_dir = "../data/cubes_demo"
cubes_output_dir = "../data/cubes_demo_output"
cube_files = [f for f in os.listdir(cubes_dir) if f.startswith("anomalies") and f.endswith(".nc")]

for file in cube_files:
    bare_file_name = os.path.splitext(os.path.basename(file))[0]
    dataset = xr.open_dataset(os.path.join(cubes_dir, file))

    output_directory_path = os.path.join(cubes_output_dir, bare_file_name)
    os.makedirs(output_directory_path, exist_ok=True)

    # Extract latitude, longitude, anomaly, and time values
    lat = dataset["lat"].values.tolist()
    lon = dataset["lon"].values.tolist()
    time = dataset["time"].values.astype(str).tolist()
    anomaly_data = dataset["anomaly"]

    # Create a dictionary to store lat, lon, and images
    cube_metadata = {
        "lat": lat,
        "lon": lon,
        "images": []
    }

    # Iterate over the time dimension to extract anomaly images at each time step
    for i, time_step in enumerate(tqdm(time, desc=f"Processing {file}", unit="time_step")):
        date = pd.Timestamp(time_step).strftime('%Y-%m-%d')

        data_values = anomaly_data.isel(time=i).values
        plt.imshow(data_values, cmap="viridis")
        plt.axis("off")

        fig_file_name = f"{bare_file_name}_{date}.png"
        plt.savefig(os.path.join(output_directory_path, fig_file_name), format="png", bbox_inches="tight", pad_inches=0)

        cube_metadata["images"].append({
            "time": date,
            "image": fig_file_name
        })


    # Save the extracted data to a JSON file
    with open(os.path.join(output_directory_path, f"{bare_file_name}.json"), "w") as f:
        json.dump(cube_metadata, f)
