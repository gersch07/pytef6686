# Description and features of pyTEF6686
* tef6686_driver.py: (Micro-) Python library for controlling TEF6686 FM/MW/LW/SW tuner module
* tef6686_tuner.py (Raspberry Pi only): application with graphical user interface based on pyqt, including manual, automatic logging and bandscan modes 

## 1. Currently implemented host devices:
* ESP32 microcontroller running Micropython
* Raspberry Pi (tested with model 2B), using SMBus library (make sure I2C is activated, e.g. using "raspi-config")

**IMPORTANT:** TTL logic level of Raspberry Pi is 3.3V, for the TEF6686 it is 5V! IT IS CRITICAL TO USE A LEVEL SHIFTER !*

## 2. Implemented functions:
* Tuner initialization & status check
* Tuning (FM, MW, SW, LW; FM-OIRT is not yet implemented)
* RDS decoding (PI, PS, AF, radio text)
* Volume gain control
* FM filter bandwidth control
* GUI application: currently only FM-CCIR available

## 3. Ongoing work
* Make bands other than FM accessible from GUI application

## 4. Usage of the library
* See example.py
* Graphical user interface: TEF6686_tuner.py
