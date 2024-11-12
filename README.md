# Preparing the Environment

To be able to build and run the project python 3 and npm a required. Create a virtual environment using the command

`python -m venv <path to new virtual environment>`

To activate the environment use the following command.

`source <path to new virtual environment/bin/activate`

To deactivate the environment type `deactivate` in your shell.

# Generating XYZ Tiles

## Converting NetCDF to TIF

To convert NetCDF files to TIF use the following command. The output files have the same name but the extension is ".tif".

`python netcdf_to_tif_converter.py <input_files...>`

## Merging Multiple TIF to One

The following command can be used to merge input_files... into one merged_file. Their format should be TIF. 

`python tif_merger.py <merged_file> <input_files...>`

## Generating XYZ Tiles with Dates

The following command generates tiles from input_file to output_directory with the provided zoom_levels. The input_file format should be TIF.

`python xyz_creator.py <input_file> <output_directory> <zoom_levels>`

Where zoom_levels should be in the format: <from>-<to>, where from and to are integers and from <= to. A typical value would be "0-18".

# React App

The application assumes, the tiles server is running on `localhost:8080`, so make sure to start the server before starting the web application. 

## Running Locally for Debugging and Testing Purposes

Run the following command.

`npm run start`

This command will open the web application in the browser.

## Building Production Version

Run the following command.

`npm run build`

It will deploy all necessary files in the build folder. This folder can be copied to the production server.