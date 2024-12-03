# Preparing the Environment

## Virtual Environment

### Motivation

To be able to set up GDAL without relying on the libraries installed at the OS level a Conda environment has to me used.

### Miniconda

To install Miniconda - the more light-weight Conda environment - use the following commands. Change the path
`~/miniconda3` to a different one, if you prefer to have the installation in a different location.

`mkdir ~/miniconda3`
`wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh`
`bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3`
`rm ~/miniconda3/miniconda.sh`

To activate Miniconda in the current shell use the following command:

`source ~/miniconda3/bin/activate`

To deactivate it run the following command:

`conda deactivate`

## Installing Dependencies

### Install GDAL from conda-forge

Install gdal dependency separately.

`conda install -c conda-forge gdal`

Go to the `python` directory of the project and install the needed requirements using

`pip install -r requirements.txt`

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

# Running nginx Tiles Server

## Prerequisites

To install docker and a required plugin run

`sudo apt install docker.io docker-buildx`

## Preparatory steps

Look up is your container is running

`docker ps`

If it is the case stop the existing container with the command

`docker stop <conatiner name>`

## Building Image

If needed the image can be built from the Dockerfile recipe:

`docker build docker/tiles_server --tag tiles-server`

## Starting Container

To start the dockerized server use the following command (change the path of the local mounted directory if needed):

`docker run -p 8080:80 --mount type=bind,source=./data/cubes_demo_output,target=/usr/share/nginx/html,readonly --name tiles-server tiles-server &`

Press Enter at the end to exit to the shell. The server will be running in the background. If you want to keep the 
server process attached to see the output, remove the symbol '&' at the end. 

## Stopping Container

To stop a running container use the command:

`docker stop tiles-server`

## Removing Container

`docker rm tiles-server`

Note that the container does not have to be removed, unless the corresponding image has changed.

## Removing Image

If you want to remove the created image in the future, use the command:

`docker rmi tiles-server`

Note that the image does not have to be removed, if no changed have been made in Dockerfile.

# React App

## Installations on the OS level

Install the npm package manager. In Debian based Linux it is done with the following command:

`sudo apt install npm`

## Tiles Server Requirement

The application assumes, the tiles server is running on 'localhost:8080', so make sure to start the 
server before starting the web application.

## Installing Dependencies

When running the application for the first time and when adding/updating the dependencies run the following command:

`npm install`

## Running Locally for Debugging and Testing Purposes

From the 'python' directory run the following command.

`npm run start`

This command will open the web application in the browser.

## Building Production Version

Run the following command.

`npm run build`

It will deploy all necessary files in the build folder. This folder can be copied to the production server.


# TODO
+ Contact the customer to show the demo.
- We should go in direction of WMTS standard protocol for serving map tiles.
- One TIF per date.
- Add documentation what libraries are used for each tool - the tech stack.
+ Write requirements.txt - PIP format (pip freeze > requirements.txt - as the first step). pip install -r requirements.txt should work out of the box.

+ NGIX server with a configuration to fallback to an empty image can be used instead a custom server.
+ Consider GeoServer: https://geoserver.org/, or https://github.com/reyemtm/wmts-server.
    GeoServer request example:
    WMS: http://localhost:8080/geoserver/vegetaion-anomalies/wcs?service=WCS&version=2.0.1&request=GetCoverage&coverageId=vegetaion-anomalies:anomalies_2018&format=image/tiff
    WTMS: http://localhost:8080/geoserver/gwc/service/wmts?layer=vegetaion-anomalies:test-va2&tilematrixset=EPSG:4326&Service=WMTS&Request=GetTile&Version=1.1.1&Format=image/png&TileMatrix=EPSG:4326:1&TileCol=2&TileRow=0
 

- What will be the execution environment? Can we use Docker to run a containerized file processing tool?
- Discussion point: what to do if there are no data because of a cloud (for example), shall we take the data from one of the previous cubes?
- How to visualize the parameters?
- Any more specifics regarding the format for SwissTopo.
- 