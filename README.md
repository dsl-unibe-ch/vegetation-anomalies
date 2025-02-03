# Deployment

## Generating XYZ Tiles

### Conversion from zarr to XYZ Tiles Locally

This is the command ro run the generation process.

`python zar_to_png_tiles.py <zarr_folder> <output_folder> <zoom_levels> <processes>`

Where zoom_levels should be in the format: `<from>-<to>`, where from and to are integers and from <= to.
A typical value would be "0-13".

processes indicates the number of parallel processes to use for tiling to speed up the computation.

### Conversion from zarr to XYZ Tiles Using UBELIX

After SSH login at submit.unibe.ch this is the command that can be used to schedule a job for execution.

`sbatch zarr_to_png_tiles.sh`

Once the computational resource is allocated successfully, the console output of the job can be found at slurm-<job_id>.out, where job_id 
is shown by the previous command.

At the link https://hpc-unibe-ch.github.io/, there is more information about how to use UBELIX.

## Hosting Application and Tiles with nginx

To host the files with nginx, use the vegetation-anomalies.conf config file from here and put it at 
/etc/nginx/conf.d. This file has some configurations missing, which should be set according to the place 
where the server will be used. In the file they are commented out.
Make sure that the main config file of nginx, nginx.conf (typically located at /etc/nginx), includes the configs from conf.d.

The web application files should be put at /var/www/<web_application_name>. They are produced by the following command:

`npm run build`

If npm is not installed, install it.

This will create the build folder in the root folder of the project. Before running the command, make sure that the 
.env.production file has the parameter REACT_APP_ANOMALIES_MAPS_API_URL, which points to the web URL with the tiles.

# Development

## Preparing the Environment

### Virtual Environment

To be able to set up GDAL without relying on the libraries installed at the OS level a Conda environment has to be used.

To install Miniconda - the more light-weight Conda environment - use the following commands. Change the path
`~/miniconda3` to a different one, if you prefer to have the installation in a different location.

`mkdir ~/miniconda3`

`wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh`

`bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3`

`rm ~/miniconda3/miniconda.sh`

To activate Miniconda in the current shell use the following command:

`source ~/miniconda3/bin/activate`

To deactivate it run

`conda deactivate`

### Installing Dependencies

Install gdal dependency separately.

`conda install -y -c conda-forge gdal zarr`

Go to the `python` directory of the project and install the needed requirements using

`pip install -r requirements.txt`

## Running nginx Tiles Server

### Prerequisites

To be able to develop with nginx locally a docker image can be used.

To install docker and the required plugin run

`sudo apt install docker.io docker-buildx`

### Preparatory steps

Look up if your container is running

`docker ps`

If it is the case, stop the existing container with the command

`docker stop <conatiner name>`

### Building Image

If needed, the image can be built from the Dockerfile recipe:

`docker build docker/tiles_server --tag tiles-server`

### Starting Container

To start the dockerized server use the following command (change the path of the local mounted directory if needed):

`docker run -p 8080:80 --mount type=bind,source=./data/cubes_demo_output,target=/usr/share/nginx/html,readonly --name tiles-server tiles-server &`

Press Enter at the end to exit to the shell. The server will be running in the background. If you want to keep the 
server process attached to see the output, remove the symbol '&' at the end. 

### Stopping Container

To stop a running container use the command:

`docker stop tiles-server`

### Removing Container

`docker rm tiles-server`

Note that the container does not have to be removed, unless the corresponding image has changed.

### Removing Image

If you want to remove the created image in the future, use the command:

`docker rmi tiles-server`

Note that the image does not have to be removed, if no changed have been made in Dockerfile.

## React App

### Installations on the OS level

Install the npm package manager. In Debian based Linux it is done with the following command:

`sudo apt install npm`

### Tiles Server Requirement

The application assumes, the tiles server is running on 'localhost:8080', so make sure to start the 
server before starting the web application.

### Installing Dependencies

When running the application for the first time and when adding/updating the dependencies run the following command:

`npm install`

### Running Locally for Debugging and Testing Purposes

From the 'python' directory run the following command.

`npm run start`

This command will open the web application in the browser.

### Building Production Version

Run the following command.

`npm run build`

It will deploy all necessary files in the build folder. This folder can be copied to the production server.
