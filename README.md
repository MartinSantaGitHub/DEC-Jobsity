# DEC-Jobsity
Data Engineering Challenge for _Jobsity_

## Requirements
  -  [Docker](https://www.docker.com/products/docker-desktop)

## Run the project

1. Open a terminal, go to the root source of the project and run `bash start.sh`

  This will create the docker containers with its images and the database with its tables and last, 
  it will run a server to host Fast Api, so we can test the solution

2. Once it finished, open the browser and navigate to [http://localhost:8000](http://localhost:8000)

From there, you have to upload the '_trips.csv_' file to start populating the tables. You can upload more than one file. 
Just press the '**Choose Files**' button to select the files and then press the '**Load Files**' button.

There's a button called '**Get Weekly Average Trips**' to get the average number of trips by region

3. When you're done, you can open another terminal and run `bash stop.sh` to stop the server and the database services. 
You can also delete all the containers and images created with the command `bash delete.sh`

## ER Diagram

This is the ER model of the schema **trips**

![ER DEC-Jobsity Trips](https://user-images.githubusercontent.com/29830077/154868188-5fd6cca0-4520-4aa2-a723-26380a90900f.png)


## Notes

* There is a command `sleep 20` in the command section of the docker-compose yaml (under the _dec_ service) that is used to wait for the database
service to be initiated.
* The implementation has changed. Every time you upload a file, it's going to be processed and that means that new
rows are going to be added to the model. If you run the app twice, you will have the data duplicated and that is going to
affect the result of the average number of trips when you call the endpoint. To solve this, we can append to the 
.csv filename a timestamp and then keep track of the last processed file in a '_process_' table that
store this information based on the timestamp part of the file. With this approach, we can avoid processing the same file twice.  
* It is not recommended storing the environment file (**_.env_**) in the repository. But for simplicity and to 
fast test the application, I decided to upload this file.
* This solution could scale horizontally adding more machines to process more files since the files are processed 
in chunks to save the machine resources (CPU and RAM)
* The solution could be pushed to a _cloud run_ in GCP using the docker implementation. You can push a docker image to be
run on a GCP cloud run.

## Changes from the last version

* There is a UI loaded in the browser to upload the files, process them and get the weekly average trips. The processing
of the files includes a status bar that indicates the completed percentage. 
* When you choose and load a file, it starts to process in the backend populating the model's tables. The user can see the status of the process in the browser. 
I used a mechanism called SSE (Server Sent Event) to keep track of the status without using polling solution. But this only works with bigger files. The '_trips.csv_' file
is too small (only a hundred of rows), and it finished just in a blink. 
* There is a new environment variable in the '**.env**' file called **PERCENT_UPDATE_RATE**. You can adjust the percent update rate from there, that means, when a file is
being processing, the user is going to see a change on the file processing status every time the file is processed a percent that is multiple of the PERCENT_UPDATE_RATE. 
To do this, I used the subscriber event approach. The 'ProcessManager' class exposes two events and then the 'services' module subscribes to them.