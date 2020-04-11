# pyTEF6686
(Micro-) Python library for controlling TEF6686 FM/MW/LW/SW tuner module

## 1. Currently implemented host devices:
* ESP32 microcontroller running Micropython
* Raspberry Pi (tested with model 2B), using SMBus library (make sure I2C is activated, e.g. using "raspi-config")

**IMPORTANT:** TTL logic level of Raspberry Pi is 3.3V, for the TEF6686 it is 5V! IT IS CRITICAL TO USE A LEVEL SHIFTER !*

## 2. Implemented functions:
* Tuner initialization & status check
* Tuning (at the moment only FM is implemented)
* RDS decoding (PI, PS)
* Volume gain control

## 3. Ongoing work
* Implement radio text & AF decoding
* Implement bands other than FM
* FM filter bandwidth control

## 4. Usage of the library
* See example.py
