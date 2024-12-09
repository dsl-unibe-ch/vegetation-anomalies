import dask.array as da
import zarr
import rasterio
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from dask.diagnostics import ProgressBar

# Open Zarr dataset
zarr_dataset = zarr.open('../data/dimpeo_output/anomalies.zarr', mode='r')
zarr_array = da.from_zarr(zarr_dataset)

# Read metadata (update keys based on your dataset structure)
# Assuming the dataset includes georeferencing information in its attributes
try:
    metadata = zarr_dataset.attrs
    crs = metadata.get('crs', 'EPSG:4326')  # Replace or default to EPSG:4326
    transform = rasterio.Affine(*metadata["transform"])
except KeyError as e:
    raise ValueError(f"Missing metadata key: {e}")

for slice_index in range(zarr_array.shape[2]):
    # Select the slice along the third dimension
    # slice_index = 1  # Replace with your desired index
    data_slice = zarr_array[:, :, slice_index]

    # Optionally rechunk the data for better performance
    data_slice = data_slice.rechunk((512, 512))

    # Compute and write the data
    with ProgressBar():
        data_slice_computed = data_slice.compute()

    # Write the slice to GeoTIFF
    output_path = f'../data/dimpeo_output/anomalies{slice_index}.tif'
    with rasterio.Env():
        with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=data_slice_computed.shape[0],
                width=data_slice_computed.shape[1],
                count=1,
                dtype=data_slice_computed.dtype.name,
                crs=crs,
                transform=transform,
                compress='lzw',
                tiled=True,
                blockxsize=512,
                blockysize=512,
                num_threads='all_cpus'
        ) as dst:
            dst.write(data_slice_computed, 1)

    print(f"GeoTIFF saved to {output_path}")
