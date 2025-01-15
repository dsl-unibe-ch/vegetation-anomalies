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

`conda install -y -c conda-forge gdal zarr`

Go to the `python` directory of the project and install the needed requirements using

`pip install -r requirements.txt`

# Generating XYZ Tiles

## Conversion from zarr to XYZ Tiles

`python zar_to_png_tiles.py <zarr_folder> <output_folder> <zoom_levels> <processes> [<start_date_index>]`

Where zoom_levels should be in the format: `<from>-<to>`, where from and to are integers and from <= to. 
A typical value would be "0-13".

processes indicates the number of parallel processes to use for tiling, 
to speed up the computation.

The optional start_date_index (0-based) parameter indicates from which date to start. 
By default, it is set to 0, which means to start from the beginning. This parameter is useful to continue interrupted 
tiles generation.

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
