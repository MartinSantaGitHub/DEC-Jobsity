# DEC-Jobsity
Data Engineering Challenge for _Jobsity_

## Requirements
  -  [Docker](https://www.docker.com/products/docker-desktop)

## Run the project

1. Open a terminal, go to the root source of the project and run `bash start.sh`

  This will create the docker containers with its images and the database with its tables and last, 
  it will run a server to host Fast Api, so we can test the solution

2. Once it finished, open the browser and navigate to [http://localhost:8000/docs](http://localhost:8000/docs)

There will be an endpoint (GET) called '**weekly_average_trips**' to get the average number of trips by region

3. When you're done, you can open another terminal and run `bash stop.sh` to stop the server and the database services

## ER Diagram

This is the ER model of the schema **trips**

![ER DEC-Jobsity Trips](https://user-images.githubusercontent.com/29830077/154868188-5fd6cca0-4520-4aa2-a723-26380a90900f.png)


## Notes

* There is a command `sleep 20` in the command section of the docker-compose yaml (under the _dec_ service) that is used to wait for the database
service to be initiated.
* The implementation that I did, is only to satisfy this challenge. I had to do it in a hurry in almost three days because
I didn't have much time. Every time you run the app, a new file is going to be processed and that means that new
rows are going to be added to the model. If you run the app twice, you will have the data duplicated and that is going to
affect the result of the average number of trips when you call the endpoint. To solve this, we can append to the 
.csv filename a timestamp and then keep track of the last processed file in a '_process_' table that
store this information based on the timestamp part of the file. With this approach, we can avoid processing the same file twice.  
* It is not recommended to store the environment file (**_.env_**) in the repository. But for simplicity and to 
fast test the application, I decided to upload this file.
* This solution could scale horizontally adding more machines to process more files since the files are processed 
in chunks to save the machine resources (CPU and RAM)
* The solution could be pushed to a _cloud run_ in GCP using the docker implementation. You can push a docker image to be
run on a GCP cloud run.
