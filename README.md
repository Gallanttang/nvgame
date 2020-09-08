# nvgame by Gallant Tang for the University of British Columbia, Sauder School of Business
A Newsvendor Simulator for Research
nvgame is a python flask web app custom designed for researcher use to collect experimental data. This application is meant to simulate the newvendors problem for its users.

## The App
This application is hosted on [pythonanywhere](http://harishk.pythonanywhere.com/). 
The application has a number of dependencies find details in [requirements.txt](https://github.com/Gallanttang/nvgame/blob/master/requirements.txt)
This is a python flask application, meaning that the core functions come from flask. Additionally, all database related functions are conducted through SQLAlchemy.

## Structure of the application
main.py hosts the code to start the application. The package containing all of the relevant code is app.

App contains template, distributions, data, and csv.

