# jupyter_micropython_developer_notebooks

This repo contains my work in progress micropython kernel notebooks 
for developing an asynchronous webserver and various sensor datalogging and analysis services 
primarily on an ESP32.

As code gets finished it is placed into .py files that can be deployed using the %sendtofile command

To install the Jupyter Micropython kernel into your copy of Jupyter, go here: https://github.com/goatchurchprime/jupyter_micropython_kernel 

## Useful notebooks

### In basicsockets/ 

* esptool.ipynb is good for flashing and reloading new micropython binaries onto your ESP32

* notebooks that begin with "pc_" run on your pc and open serial connections to your ESP32

* connecthotspot.py and connectwifi.pyare modules for doing what they say (the latter requires 
a wificodes.txt file for the passwords)

* syslog.py is a handy system logger module that tracks reboots

### In async_web_serve/

* commission_async.ipnb loads the uasyncio library, either by copying it up from a local copy or using
upip.  (This won't be necessary once it becomes part of the core library, as it is on the ESP8266)

* webserve_funcs.py and websocket_funcs.py are the necessary functions for operating the webserver and 
websockets capabilitie.  They contain functions like readhttpheaders(), and so on.  

* plain_main.py is a main.py file that turns your ESP32 into a static file webserver (although you can 
use uploadfiletest.html to upload and save text files for more rapid development of web front end).  
plain_server.ipynb deploys (and develops) this plain webserver.

### In essential_sensor_code/

* There are notebooks for the devices ms5611 (barometer), si7021 (humidity), VL53L0X (shortrange lidar to 1m), bme280 (baro,humid,temp).

* These are in various states of development, but in general are very trimmed down to the essentials and intended to be operated as python 
generators rather than as bloated class objects

* Finished code is in .py files.  





