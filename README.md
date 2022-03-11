# DEC-Jobsity
### Data Engineering Challenge for _Jobsity_

This is a coding challenge for a **Data Engineer** position, that the company **Jobsity** made me did 
without any support. So I did it taking into account my own interpretations of the requirements. The features 
are listed in the _data-engineering-challenge.pdf_ file in the **docs** folder. There are all the requirements and
tasks to do for this challenge. The .csv file needed for this challenge (_trips.csv_) is in the **files** folder.

## Requirements
  -  [Docker](https://www.docker.com/products/docker-desktop)

## Run the project

1. Open a terminal, go to the root source of the project and run `bash start.sh`

  This will create the docker containers with its images and the database with its tables and last, 
  it will run a server to host Fast Api, so we can test the solution

2. Once it finished, open the browser and navigate to [http://localhost:8000](http://localhost:8000)

From there, you can upload the '_trips.csv_' file pressing the '**Choose Files**' button and then pressing the '**Load Files**' button 
to start populating the tables or directly press the Load button without uploading any file. 
If you do the last, the current '_trips.csv_' file in the folder **files** is going to be used. 
You can upload more than one file (and of course, have more than one .csv file inside **files** folder). 
The only requirement for others .csv files is that must be valid _trip_ .csv files, with the same structure
that the _trips.csv_ file.

There's a button called **Get Weekly Average Trips By Bounding Box** and another called **Get Weekly Average Trips By Region**. 
The first one is used to get the average weekly number of trips in some sector defined by a bounding box and the second is used 
to get the average weekly number of trips by region. You may be wonder 'how do I define the bounding box and what is that bounding box'.
In the UI there are two sections, Point A and Point B. In the input boxes, you have to define two points 
(coordinates X and Y for each one, respectively) that represent the points of the hypotenuse of the bi-rectangled triangle that
defines the 'box' area from where you want to get the average weekly number of trips.

3. When you're done, you can open another terminal and run `bash stop.sh` to stop the server and the database services. 
You can also delete all the containers and images created with the command `bash delete.sh`

## ER Diagram

This is the ER model of the schema **trips**

![ER DEC-Jobsity Trips](https://user-images.githubusercontent.com/29830077/157293926-6eb0af1c-acab-4f79-8936-e03065d560b5.png)

## Version Changes

### 2.2
* Added support to the progress bar for multi connected users.

### 2.1.1
* The progress bar didn't work very well in most cases. It was fixed, and now it shows the final 
percentage when it finishes. The progress bar only works when processing big files.
* Fixed Average Weekly Trips By Bounding Box functionality.

### 2.1
* It was added the **Weekly Average Trips By Bounding Box** feature. In the _Run the project_ section is
explained how to use it.

### 2.0
* There is a UI loaded in the browser to upload the files, process them and get the weekly average trips. The processing
of the files includes a status bar that indicates the completed percentage. 
* When you choose and load a file, it starts to process in the backend populating the model's tables. The user can see the status of the process in the browser. 
I used a mechanism called SSE (Server Sent Event) to keep track of the status without using a polling solution. But this only works with bigger files. The '_trips.csv_' file
is too small (only a hundred of rows), and it finished just in a blink. 
* There is a new environment variable in the '**.env**' file called **PERCENT_UPDATE_RATE**. You can adjust the percent update rate from there, that means, when a file is
being processing, the user is going to see a change on the file processing status every time the file is processed a percent that is multiple of the PERCENT_UPDATE_RATE. 
To do this, I used the subscriber event approach. The 'ProcessManager' class exposes two events and then the 'services' module subscribes to them.

### 1.0
* There is a command `sleep 20` in the command section of the docker-compose yaml (under the _dec_ service) that is used to wait for the database
service to be initiated.
* Every time you upload a file, it's going to be processed and that means that new rows are going to be added to the model. 
If you run the app twice, you will have the data duplicated and that is going to affect the result of the average number of trips when you call 
the endpoints. To solve this, we can append to the .csv filename a timestamp and then keep track of the last processed file in a '_process_' 
table that store this information based on the timestamp part of the file. With this approach, we can avoid processing the same file twice.
This could be implemented in a future version.
* It is not recommended storing the environment file (**_.env_**) in the repository. But for simplicity and to 
fast test the application, I decided to upload this file.
* This solution could scale horizontally adding more machines to process more files since the files are processed 
in chunks to save the machine resources (CPU and RAM)
* The solution could be pushed to a _cloud run_ in GCP using the docker implementation. You can push a docker image to be
run on a GCP cloud run.
