# Generating XYZ Tiles

## Converting NetCDF to TIF

## Merging Multiple TIF to One

The following command can be used to merge input_files... into one merged_file. Their format should be TIF. 
`python tif_merger.py <merged_file> <input_files...>`

## Generating XYZ Tiles with Dates

The following command generates tiles from input_file to output_directory with the provided zoom_levels. The input_file format should be TIF.
`python xyz_creator.py <input_file> <output_directory> <zoom_levels>`

Where zoom_levels should be in the format: <from>-<to>, where from and to are integers and from <= to. A typical value would be "0-18".