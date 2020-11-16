README

GROUP HDPP COMP9900

Our project (filmfinder) exceeds the size limit of 100MB, due to the large quantity of images and database. We have followed the instruction on assessment summary, to upload the 'HDppFinalSoftwareQuality.zip' onto Github Classroom via git lfs at 20:22:52 (GMT+11) 16/11/2020.
Here is the link to the .zip file:

https://github.com/unsw-cse-capstone-project/capstone-project-comp9900-h17b-hdpp/blob/master/HDppFinalSoftwareQuality.zip

This project can be run on web browser like Google Chrome, IE and
Firefox. We recommend using Google Chorme.
The setup steps are shown below:

First create the virtual environment:

	$ conda create -n hdpp python=3.7

and press y when asked to.

Then activate the virtual environment.

	$ conda activate hdpp
	
Or you can install packages outside the virtual environment.

Then you should download the ‘HDppFinalSoftwareQuality.zip’ from
Github and unzip it. The website is:
https://github.com/unsw-cse-capstone-project/capstone-project-comp9900-h17b-hdpp

Aftering downloading all the zip file, unzip by typing in terminal:

	$ unzip ‘HDppFinalSoftwareQuality.zip’

After unzipping the zip file, you can open the folder called ‘HDpp’. And
inside ‘HDpp’ folder you can find the requirements.txt where all required
packages are listed.

And then install the necessary packages. Requirements.txt can be found
at the root folder of the project.

	(hdpp)$ pip3 install -r requirements.txt

When all packages are correctly installed, the website should be able to
work:

	(hdpp)$ python3 run.py

Then you can type

	127.0.0.1:5000

in the web browser to access the web app.

HDpp 

16/11/2020