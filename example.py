import TEF6686

#-------------- NEW TUNER INSTANCE ----------------

tuner = TEF6686('RPi')

#------- INIT TUNER MODULE AND SETTINGS -----------

tuner.init_tuner()

tuner.init_oscillator()

tuner.init_settings()

tuner.check_module_status() 				# should now return "Radio standby mode"

#----------------   USE TUNER ---------------------

tuner.set_volume(32)					# volume control not yet properly implemented

tuner.tune_to('FM',8760)

tuner.get_signal_info()					# returns info about tuned signal: strength in dBµV, stereo (true/false), RDS available (true/false)

tuner.get_RDS_data()					# rudimentary implementation to read RDS PS, PTY, TP