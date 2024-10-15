import base64
import json
import os
from io import BytesIO

import xarray as xr
from matplotlib import pyplot as plt
from tqdm import tqdm

cubes_dir = "../data/cubes_demo"
cube_files = [f for f in os.listdir(cubes_dir) if f.startswith('anomalies') and f.endswith('.nc')]

cube_predictions = []

for file in cube_files:
    dataset = xr.open_dataset(os.path.join(cubes_dir, file))

    # Extract latitude, longitude, anomaly, and time values
    lat = dataset['lat'].values.tolist()
    lon = dataset['lon'].values.tolist()
    time = dataset['time'].values.astype(str).tolist()

    # print(f"{time}")

    anomaly_data = dataset['anomaly']

    # Iterate over the time dimension to extract anomaly images at each time step
    for i, time_step in enumerate(tqdm(time, desc=f"Processing {file}", unit="time_step")):
        data_values = anomaly_data.isel(time=i).values
        plt.imshow(data_values, cmap='viridis')
        plt.axis('off')

        # Save image to buffer and encode as base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
        buffer.seek(0)
        img_data = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()

        cube_predictions.append({
            "lat": lat[i],
            "lon": lon[i],
            "time": time_step,
            "image_data": img_data
        })

# Save the extracted data to a JSON file
with open("../data/cubes_anomalies.json", "w") as f:
    json.dump(cube_predictions, f)
