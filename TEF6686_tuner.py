####################################################################################################
####                                                                                            ####
####                                    IMPORT PACKAGES                                         ####
####                                                                                            ####
####################################################################################################

import sys
import time
from datetime import date, datetime
import os

import numpy as np

from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow,QSlider,QLabel,QAction,QMenuBar,QDialog,QTableWidget,QTableWidgetItem,QFileDialog
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import PyQt5.uic as uic

from TEF6686_driver import TEF6686

####################################################################################################
####                                                                                            ####
####                                     USER INTERFACE                                         ####
####                                                                                            ####
####################################################################################################

MainApp_UI, QtBaseClass = uic.loadUiType("mainwindow.ui")
StationList_UI, QtBaseClass = uic.loadUiType("station_list.ui")
DXMonitor_UI, QtBaseClass = uic.loadUiType("DX_monitor.ui")

###################################### DX MONITOR WINDOW ###########################################

class DXMonitor_Window(QDialog, DXMonitor_UI):

    def __init__(self,parent):
        
        QDialog.__init__(self,parent)
        #QDialog.setWindowFlags(Qt.Tool)
        DXMonitor_UI.__init__(self)
        self.setupUi(self)
            
        # fill in default entries
        self.WAIT_TIME = 3                                        # default wait time at empty frequency: 10s
        self.RDS_TIMEOUT = 20                                     # default timeout for RDS if signal is available
        self.WaitTime_Edit.setText(str(self.WAIT_TIME))
        self.RDSTimeout_Edit.setText(str(self.RDS_TIMEOUT))
        self.LOCAL_STATION_LIST = []
        self.UpperFreqLimit_Edit.setText(str(10800))               # default upper frequency limit for DX monitor
        
        # connect buttons
        self.CloseWindow_Button.clicked.connect(self.close_window)
        self.ScanLocalStations_Button.clicked.connect(self.scan_local_stations)
        self.ExportCSV_Button.setDisabled(True)
        self.ExportCSV_Button.clicked.connect(self.export_table)
        self.FreqMonitor_Button.setDisabled(True)
        self.FreqMonitor_Button.clicked.connect(self.start_frequency_monitor)
        self.ImportLocalStations_Button.clicked.connect(self.import_local_stations)
        
        self.clear_list()
        
    
    def clear_list(self):
        
        self.StationList_Table.setRowCount(1)
        self.StationList_Table.setColumnCount(4)
        self.StationList_Table.setItem(0,0, QTableWidgetItem("Frequency"))
        self.StationList_Table.setItem(0,1, QTableWidgetItem("Signal strength"))
        self.StationList_Table.setItem(0,2, QTableWidgetItem("PI Code"))
        self.StationList_Table.setItem(0,3, QTableWidgetItem("PS Code"))
        

    def add_to_list(self):
        
        if not self.parent().RDS_PI == '----':
            current_rows = self.StationList_Table.rowCount()
            self.StationList_Table.insertRow(current_rows)
            self.StationList_Table.setItem(current_rows, 0, QTableWidgetItem(str(self.parent().frequency)))
            self.StationList_Table.setItem(current_rows, 1, QTableWidgetItem('%.1f' %  self.parent().signal_strength))
            self.StationList_Table.setItem(current_rows, 2, QTableWidgetItem(self.parent().RDS_PI))
            self.StationList_Table.setItem(current_rows, 3, QTableWidgetItem(self.parent().RDS_PS))
            
    
    def log_station(self):
        
        current_date = date.today().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if not self.parent().RDS_PI == '----':
            print("Logging station...")
            try:
                os.chdir('/home/pi/logs/' + current_date)
            except:
                os.mkdir('/home/pi/logs/' + current_date)
            
            file_path = './' + current_date + '_' + str(self.parent().frequency) + '_' + str(self.parent().RDS_PI) + '.txt'
            
            with open(file_path, 'a') as file_handler:
                file_handler.write( current_time + ',' + str(self.parent().RDS_PI)+ ',' + self.parent().RDS_PS +',' + str(self.parent().signal_strength) +'\n')

    
    def export_table(self):
        
        file_path,_ = QFileDialog.getSaveFileName(self, 'Save File')
        print("Will save to ", file_path)
        
        no_of_columns = self.StationList_Table.columnCount()
        no_of_stations = self.StationList_Table.rowCount()
        
        export_array = np.zeros( (no_of_stations, no_of_columns), dtype = object)
        
        data_list = []
        data_row = []
        
        with open(file_path, 'w') as file_handler:
            
            for station in range(no_of_stations):
                
                data_row = ''
                
                for column in range(no_of_columns):
                    
                    data = self.StationList_Table.item(station,column).text()
                    data_row = data_row + ',' + data
                    print(data_row)
                
                data_row += '\n'
                data_list.append(data_row)
    
            file_handler.writelines(data_list)
        file_handler.close()
    

    def import_local_stations(self):
        
        file_path,_ = QFileDialog.getOpenFileName(self, 'Open File')
        
        with open(file_path, 'r') as file_handler:
            
            self.LOCAL_STATION_LIST = []
            
            for line in file_handler:
                try:
                    self.LOCAL_STATION_LIST.append(int(line.split(',')[1]))
                except:
                    pass
                
        print("Loaded list of local stations: ", self.LOCAL_STATION_LIST)
        file_handler.close()
        
        self.LocalStationNo_Label.setText(str(len(self.LOCAL_STATION_LIST)))  
        self.FreqMonitor_Button.setDisabled(False)
        
        
    def scan_local_stations(self):

        # user interface
        self.update_parent_tuning_buttons()
        self.ScanLocalStations_Button.setText("Stop")
        self.ScanLocalStations_Button.clicked.connect(self.stop_scan_local_stations)
        
        self.LOCAL_STATION_LIST = []
        self.parent().SCAN_LOCAL_ACTIVE = True                                           # variable to determine whether loca sc
        self.parent().tuner_worker.tune_to_freq(8750)
        self.STEPS_SKIPPED = 0
        self.TUNING_TYPE = 'find_locals'
        
        self.tuner_timer = QTimer()
        self.tuner_timer.timeout.connect(self.tune_and_wait)
        self.tuner_timer.start(self.WAIT_TIME*1000)
       
       
    def stop_scan_local_stations(self):
        
        self.tuner_timer.stop()
        self.parent().SCAN_LOCAL_ACTIVE = False
        
        #user interface
        self.ScanLocalStations_Button.setText("Scan")
        self.ScanLocalStations_Button.clicked.connect(self.scan_local_stations)
        self.update_parent_tuning_buttons()
        
        
    def tune_and_wait(self):
        
        self.SKIP_STEPS_IF_RDS = int(self.RDS_TIMEOUT/self.WAIT_TIME)                     # steps to wait for more RDS information after one block was detected
        self.RDS_timer = QTimer()
        self.RDS_timer.singleShot(self.WAIT_TIME*1000-100, self.check_RDS_and_tune_next)
            
    
    def check_RDS_and_tune_next(self):
        
        if self.parent().RDS_BLOCK_DETECTED == False:
            print("No RDS block detected...")
            
            if self.TUNING_TYPE == 'find_locals':
                self.parent().tuner_worker.tune_up_auto()
                
            elif self.TUNING_TYPE == 'monitor_list':
                if self.CURRENT_FREQ_IND == len(self.MONITOR_LIST):
                    self.CURRENT_FREQ_IND = 0
                else:
                    self.parent().tuner_worker.tune_to_freq(self.MONITOR_LIST[self.CURRENT_FREQ_IND])
                    self.CURRENT_FREQ_IND += 1
                
            self.STEPS_SKIPPED = 0
            
        else:
            print("RDS block detected!")
            self.STEPS_SKIPPED += 1
            if self.STEPS_SKIPPED == self.SKIP_STEPS_IF_RDS:
                
                self.LOCAL_STATION_LIST.append(self.parent().frequency)
                self.add_to_list()
                
                if self.TUNING_TYPE == 'find_locals':
                    self.parent().tuner_worker.tune_up_auto()
                    
                elif self.TUNING_TYPE == 'monitor_list':
                    self.log_station()
                    
                    if self.CURRENT_FREQ_IND == len(self.MONITOR_LIST):
                        self.CURRENT_FREQ_IND = 0
                    else:
                        self.parent().tuner_worker.tune_to_freq(self.MONITOR_LIST[self.CURRENT_FREQ_IND])
                        self.CURRENT_FREQ_IND += 1
                    
                self.STEPS_SKIPPED = 0
                
        if self.TUNING_TYPE == 'find_locals':
            
            if self.parent().frequency == 10800:
            
                self.tuner_timer.stop()
                self.parent().SCAN_LOCAL_ACTIVE = False
            
                print("Scan of local stations finished!")
                print("List of local frequencies: ", self.LOCAL_STATION_LIST)
            
                self.ExportCSV_Button.setDisabled(False)
                self.FreqMonitor_Button.setDisabled(False)
                self.LocalStationNo_Label.setText(str(len(self.LOCAL_STATION_LIST)))       


    def update_parent_tuning_buttons(self):
        
        print("Tuning buttons currently enabeld: ", self.parent().TuneDown_Button.isEnabled() )
        if self.parent().TuneDown_Button.isEnabled() == True:
            self.parent().TuneDown_Button.setDisabled(True)
            self.parent().TuneUp_Button.setDisabled(True)
            self.parent().SeekDown_Button.setDisabled(True)
            self.parent().SeekUp_Button.setDisabled(True)
        
        elif self.parent().TuneDown_Button.isEnabled() == False:
            self.parent().TuneDown_Button.setDisabled(False)
            self.parent().TuneUp_Button.setDisabled(False)
            self.parent().SeekDown_Button.setDisabled(False)
            self.parent().SeekUp_Button.setDisabled(False)


    def start_frequency_monitor(self):
        
        print("Starting frequency monitor...")
        self.make_monitor_freq_list()
        
        # user interface
        self.update_parent_tuning_buttons()
        self.FreqMonitor_Button.setText("Stop")
        self.FreqMonitor_Button.clicked.disconnect()
        self.FreqMonitor_Button.clicked.connect(self.stop_frequency_monitor)
        self.ScanLocalStations_Button.setDisabled(True)
        
        self.MONITOR_ACTIVE = True
        self.clear_list()
        self.STEPS_SKIPPED = 0
        self.CURRENT_FREQ_IND = 0
        self.TUNING_TYPE = 'monitor_list'
        
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.tune_and_wait)
        self.monitor_timer.start(self.WAIT_TIME*1000)
    
    
    def stop_frequency_monitor(self):
        
        print("Stop frequency monitor...")
        self.monitor_timer.stop()
        self.MONITOR_ACTIVE = False
        #self.MONITOR_LIST = []
        
        # user interface
        self.ScanLocalStations_Button.setDisabled(False)
        self.FreqMonitor_Button.setText("Start")
        self.FreqMonitor_Button.clicked.disconnect()
        self.FreqMonitor_Button.clicked.connect(self.start_frequency_monitor)
        self.update_parent_tuning_buttons()


    def make_monitor_freq_list(self):                                                                # generate list of frequencies to be monitored (excluding local stations)
        
        print("Generating list of frequencies to be monitored...")
        self.MONITOR_LIST = []
        self.UPPER_FREQ_LIMIT_IND = int((int(self.UpperFreqLimit_Edit.text())-8750)/10)
        
        for i in range(0,self.UPPER_FREQ_LIMIT_IND + 1):                                             # produces 206 frequencies to check if upper limit is 108.0 MHz
            freq = 8750 + i*10
            if freq not in self.LOCAL_STATION_LIST:
                self.MONITOR_LIST.append(freq)
        
        print("Frequency list: ", self.MONITOR_LIST)
        
    
    def close_window(self):
        
        self.hide()
        
        

##################################### STATION LIST WINDOW ##########################################

class StationList_Window(QDialog, StationList_UI):
    
    def __init__(self, parent):
        
        QDialog.__init__(self,parent)
        StationList_UI.__init__(self)
        self.setupUi(self)
        
        # connect buttons
        self.CloseWindow_Button.clicked.connect(self.close_window)
        self.AddToList_Button.clicked.connect(self.add_to_list)
        self.ClearList_Button.clicked.connect(self.clear_list)
        self.ExportCSV_Button.clicked.connect(self.export_table)
        
        self.prepare_list()
        
        
    def add_to_list(self):
        
        current_rows = self.StationList_Table.rowCount()
        self.StationList_Table.insertRow(current_rows)
        self.StationList_Table.setItem(current_rows, 0, QTableWidgetItem(str(self.parent().frequency)))
        self.StationList_Table.setItem(current_rows, 1, QTableWidgetItem('%.1f' %  self.parent().signal_strength))
        self.StationList_Table.setItem(current_rows, 2, QTableWidgetItem(self.parent().RDS_PI))
        self.StationList_Table.setItem(current_rows, 3, QTableWidgetItem(self.parent().RDS_PS))
        
        
    def prepare_list(self):
        
        self.StationList_Table.setRowCount(1)
        self.StationList_Table.setColumnCount(4)
        self.StationList_Table.setItem(0,0, QTableWidgetItem("Frequency"))
        self.StationList_Table.setItem(0,1, QTableWidgetItem("Signal strength"))
        self.StationList_Table.setItem(0,2, QTableWidgetItem("PI Code"))
        self.StationList_Table.setItem(0,3, QTableWidgetItem("PS Code"))
        
        
    def clear_list(self):
        
        self.StationList_Table.clear()
        self.prepare_list()
        
    
    def export_table(self):
        
        file_path,_ = QFileDialog.getSaveFileName(self, 'Save File')
        #print("Will save to ", file_path)
        
        no_of_columns = self.StationList_Table.columnCount()
        no_of_stations = self.StationList_Table.rowCount()
        
        export_array = np.zeros( (no_of_stations, no_of_columns), dtype = object)
        
        data_list = []
        data_row = []
        
        with open(file_path, 'w') as file_handler:
            
            for station in range(no_of_stations):
                
                data_row = ''
                
                for column in range(no_of_columns):
                    
                    data = self.StationList_Table.item(station,column).text()
                    data_row = data_row + ',' + data
                    #print(data_row)
                
                data_row += '\n'
                data_list.append(data_row)
    
            file_handler.writelines(data_list)
        file_handler.close()
        
        
    def close_window(self):
        
        self.hide()

########################################### MAIN WINDOW ############################################


class MainApp(QMainWindow,MainApp_UI):
    
    FREQ = pyqtSignal(int)
    SIGNAL_INFO = pyqtSignal(list)
    RDS_DATA = pyqtSignal(object)
    
    
    def __init__(self):
        
        # Generate user interface
        QMainWindow.__init__(self)
        MainApp_UI.__init__(self)
        self.setupUi(self)
        app.aboutToQuit.connect(self.closeEvent)
        
        # Initialize variables
        self.frequency = None
        self.signal_strength = None
        self.SCAN_LOCAL_ACTIVE = False
        self.MONITOR_ACTIVE = False
        self.RDS_BLOCK_DETECTED = False                               # check if at least one RDS block was detected in a specific time interval
        self.IF_BANDWIDTH_DICT = {'0': 560, '1': 640, '2': 720, '3': 840, '4': 970, '5': 1140, '6': 1330, '7': 1510, '8': 1680, '9': 1840, '10': 2000, '11': 2170, '12': 2360, '13': 2540, '14': 2870, '15': 3110}

        # Generate menu bar
        self.Menu = QMenuBar()
        self.setMenuBar(self.Menu)
        # Add and connect entries
        self.Menu_File = self.Menu.addMenu("File")
        self.Menu_InitTuner = QAction("Initialize tuner module", self)
        self.Menu_Quit = QAction("Quit", self)
        self.Menu_Window = self.Menu.addMenu("Tools")
        self.Menu_StationList = QAction("Manual logging", self)
        self.Menu_DXMonitor = QAction("Automatic logging", self)
        
        self.Frequency_LCD.setStyleSheet('QLCDNumber {color: red; background-color: white;}')
        self.Frequency_LCD.display('---.--')
        self.Signal_dBuV_LCD.setStyleSheet('QLCDNumber {color: red; background-color: white;}')
        self.Signal_dBuV_LCD.display('--.-')
        
        # Allocate actions
        self.Menu_File.addAction(self.Menu_InitTuner)
        self.Menu_InitTuner.triggered.connect(self.initialize_tuner)
        
        self.Menu_File.addAction(self.Menu_Quit)
        self.Menu_Quit.triggered.connect(self.close_app)
        
        self.Menu_Window.addAction(self.Menu_StationList)
        self.Menu_StationList.triggered.connect(self.show_manual_log)
        
        self.Menu_Window.addAction(self.Menu_DXMonitor)
        self.Menu_DXMonitor.triggered.connect(self.show_auto_log)
        
        # Connect input objects to functions
        self.SeekDown_Button.clicked.connect(self.seek_down)
        self.SeekUp_Button.clicked.connect(self.seek_up)
        self.TuneDown_Button.clicked.connect(self.tune_down)
        self.TuneUp_Button.clicked.connect(self.tune_up)
        self.Volume_Dial.setMinimum(-59.9)
        self.Volume_Dial.setMaximum(24.0)
        self.Volume_Dial.setValue(0)                                 # default value: 0dB volume gain
        self.Volume_Dial.valueChanged.connect(self.set_volume)
        self.Volume_Ind.setText( str(self.Volume_Dial.value() ) + 'dB')
        
        # Create entries in "Seek sensitivity" combo
        self.SeekSensitivity_Combo.addItem('local')
        self.SeekSensitivity_Combo.addItem('DX')
        
        # Create entries in "Tune Steps" combo
        self.TUNESTEPS_LIST = [1,5,10,20,50,100]
        self.TuneSteps_Combo.addItem('10 kHz')
        self.TuneSteps_Combo.addItem('50 kHz')
        self.TuneSteps_Combo.addItem('100 kHz')
        self.TuneSteps_Combo.addItem('200 kHz')
        self.TuneSteps_Combo.addItem('500 kHz')
        self.TuneSteps_Combo.addItem('1 MHz')
        self.TuneSteps_Combo.setCurrentIndex(2)
        
        # Create entries in "IF filter bandwidth" combo
        self.IF_Bandwidth_Combo.addItem('auto')
        for key in self.IF_BANDWIDTH_DICT.keys():
            self.IF_Bandwidth_Combo.addItem(str(int(self.IF_BANDWIDTH_DICT[key]/10)) + ' kHz')

        # Start tuner thread
        self.tuner_thread = QThread()
        self.tuner_worker = TunerWorker()
        self.tuner_worker.moveToThread(self.tuner_thread)
        self.tuner_thread.start()
        
        # connect pyqtSignals
        self.IF_Bandwidth_Combo.currentIndexChanged.connect( self.set_IF_bandwidth )
        self.tuner_worker.FREQ.connect(self.update_frequency)
        self.tuner_worker.RDS_DATA.connect(self.update_RDS)
        self.tuner_worker.SIGNAL_INFO.connect(self.update_signal_info)
        
        self.statusBar.showMessage('Tuner: DISCONNECTED')
        
    
    def set_volume(self):
        
        self.Volume_Ind.setText( str(self.Volume_Dial.value() ) + ' dB' )
        self.tuner_worker.tuner.set_volume_gain( self.Volume_Dial.value()*10 )
        
    
    def set_IF_bandwidth(self):
        
        if self.IF_Bandwidth_Combo.currentIndex() == 0:
            self.tuner_worker.tuner.set_IF_bandwidth('FM', 'auto', dbg = True)
        elif self.IF_Bandwidth_Combo.currentIndex() > 0:
            self.tuner_worker.tuner.set_IF_bandwidth('FM', self.IF_Bandwidth_Combo.currentIndex()-1, dbg = True )
        else:
            raise ValueError('Unsupported IF filter bandwidth chosen!')
        
        
    def show_manual_log(self):

        try:
            self.manual_log_window.show()                                           # try to open existing station list
        except:
            self.manual_log_window = StationList_Window(self)
            self.manual_log_window.setWindowTitle('Manual logging')
            self.manual_log_window.show()
            
    
    def show_auto_log(self):

        try:
            self.auto_log_window.show()                                           # try to open existing DX monitor
        except:
            self.auto_log_window = DXMonitor_Window(self)
            self.auto_log_window.setWindowTitle('Automatic logging')
            self.auto_log_window.show()
    
    
    def closeEvent(self,event):
        try:
            self.tuner_thread.quit()
        except:
            pass
        sys.exit(0)
        
    def close_app(self):
        
        try:
            self.tuner_thread.quit()
        except:
            pass
        sys.exit(0)
        
    
    def initialize_tuner(self):
        
        self.tuner_worker.initialize_tuner()
        print("Tuner active: ", self.tuner_worker.TUNER_ACTIVE)
        
        if self.tuner_worker.TUNER_ACTIVE == True:
            self.Menu_InitTuner.setDisabled(True)
        
    
    def tune_up(self):
        
        self.tuner_worker.tune_up(self.TUNESTEPS_LIST[self.TuneSteps_Combo.currentIndex()] )
    
    
    def tune_down(self):
        
        self.tuner_worker.tune_down(self.TUNESTEPS_LIST[self.TuneSteps_Combo.currentIndex()] )
        
        
    def seek_up(self):
        
        seek_sensitivity = self.SeekSensitivity_Combo.currentText()
        self.tuner_worker.seek_up(seek_sensitivity)
    
    
    def seek_down(self):
        
        seek_sensitivity = self.SeekSensitivity_Combo.currentText()
        self.tuner_worker.seek_down(seek_sensitivity)
    
    
    def update_frequency(self, frequency):
        
        self.RDS_PS_QLabel.setText('--------')
        self.RDS_PI_QLabel.setText('----')
        self.RDSRT_TextBrowser.clear()
        self.RDS_BLOCK_DETECTED = False
        self.TP_Ind_Label.setStyleSheet('color: black')
        self.Frequency_LCD.display('%.2f' % (frequency/100) )
        self.frequency = frequency
        
        
    def update_signal_info(self, signal_info):                                # signal info: [signal_strength, IF_bandwidth, FM_stereo, RDS_available]
        
        # store signal info variables
        self.signal_strength = signal_info[0]
        self.IF_bandwidth = signal_info[1]
        self.FM_stereo = signal_info[2]
        self.RDS_available = signal_info[3]
        
        # refresh GUI elements
        self.Signal_dBuV_LCD.display('%.1f' % self.signal_strength)
        
        if self.FM_stereo == True:
            self.Stereo_Ind_Label.setStyleSheet('color: red')
        else:
            self.Stereo_Ind_Label.setStyleSheet('color: black')
            
        if self.RDS_available == True:
            self.RDS_Ind_Label.setStyleSheet('color: red')
            self.RDS_BLOCK_DETECTED = True
            
        else:
            self.RDS_Ind_Label.setStyleSheet('color: black')
        
        STATUSBAR_MESSAGE = 'Tuner: ON   |   ' + 'IF Filter: ' + str(int(self.IF_bandwidth)) + ' kHz'
        self.statusBar.showMessage(STATUSBAR_MESSAGE)
        
        
    def update_RDS(self, RDS_data):
        
        for elem in RDS_data:
            RDS_data_temp = elem
        try:                                                   # sometimes this results in "UnboundLocalError"
            self.RDS_PS = RDS_data_temp['PS']
            self.RDS_PS_QLabel.setText(RDS_data_temp['PS'])
        except:
            pass
        try:
            self.RDS_PI = RDS_data_temp['PI']
            self.RDS_PI_QLabel.setText(RDS_data_temp['PI'])
        except:
            pass
        try:
            self.RDSRT_TextBrowser.append(RDS_data_temp['RT'])
        except:
            pass
        try:
            if RDS_data_temp['TP'] == '1':
                self.TP_Ind_Label.setStyleSheet('color: red')
            else:
                self.TP_Ind_Label.setStyleSheet('color: black')
        except:
            pass
            
            
    def dummy_action(self):
        
        print("This function will soon be implemented!")
        

####################################################################################################
####                                                                                            ####
####                                     TUNER INTERFACE                                        ####
####                                                                                            ####
####################################################################################################



class TunerWorker(QObject):
    
    RDS_DATA = pyqtSignal(object)
    FREQ = pyqtSignal(int)
    SIGNAL_STRENGTH = pyqtSignal(float)
    SIGNAL_STATUS = pyqtSignal(list)
    SIGNAL_INFO = pyqtSignal(list)
    
    
    def __init__(self):
        QObject.__init__(self)
        self.TUNER_ACTIVE = False
        self.__MONITOR_SIGNAL__ = False
        self.__REFRESH_SIGNAL_INTERVAL__ = 88.5                      # msec, produces 25 refreshes/sec
    
    
    def initialize_tuner(self):
        
        # 
        self.tuner = TEF6686('RPi')
        self.tuner.init()
        #
        self.TUNER_ACTIVE = True
        #
        self.tuner.set_volume_gain(10)
        self.tuner.tune_to('FM',8750)
        #
        self.FREQ.emit(self.tuner.FREQ)
        self.__MONITOR_SIGNAL__ = False
        #self.tuner.set_IF_bandwidth('FM', 'auto', dbg = True)
        time.sleep(2)
        print("Starting signal monitor...")
        self.toggle_signal_monitor()
    
    
    def toggle_signal_monitor(self):
        
        if self.__MONITOR_SIGNAL__ == False:
            self.signal_timer = QTimer()
            self.signal_timer.timeout.connect(self.signal_monitor)
            self.signal_timer.start(self.__REFRESH_SIGNAL_INTERVAL__)
            print("Signal monitor timer started...")
            self.__MONITOR_SIGNAL__ = True
        
        elif self.__MONITOR_SIGNAL__ == True:
            self.signal_timer.stop()
            print("Signal monitor timer stopped...")
            self.__MONITOR_SIGNAL__ = False
            
            
    @pyqtSlot()
    def signal_monitor(self):
        
        signal_strength, FM_stereo, RDS_available, IF_bandwidth = self.tuner.get_signal_info('full')
        self.SIGNAL_INFO.emit([signal_strength, IF_bandwidth, FM_stereo, RDS_available])
                
        if RDS_available == True:
            RDS_data_dict = self.tuner.get_RDS_data(pause_time = 0, repeat = False)
            self.RDS_DATA.emit(RDS_data_dict)
        else:
            pass
        
#              DEPRECATED, USE OF QTIMER SHOULD BE MORE EFFICIENT
#
#     @pyqtSlot()
#     def monitor_signal(self):
#         
#         loop_count = 0
#         
#         while self.__MONITOR_SIGNAL__ == True:
#             loop_count += 1
#             
#             if loop_count == 5:
#                 
#                 signal_strength, FM_stereo, RDS_available, IF_bandwidth = self.tuner.get_signal_info('full')
#                 self.SIGNAL_STRENGTH.emit(signal_strength)
#                 self.SIGNAL_STATUS.emit([FM_stereo, RDS_available])
#                 loop_count = 0
#                 
#                 if RDS_available == True:
#                     RDS_data_dict = self.tuner.get_RDS_data(pause_time = 0, repeat = False)
#                     self.RDS_DATA.emit(RDS_data_dict)
#                 else:
#                     pass
#                     
#             QApplication.processEvents()
#             time.sleep(0.012)
        
        
    def tune_up_auto(self):
        
        self.tuner.tune_step(mode = 'UP', step = 10)
        self.FREQ.emit(self.tuner.FREQ)
        
        
    def tune_down_auto(self):
        
        self.tuner.tune_step(mode = 'DOWN', step = 10)
        self.FREQ.emit(self.tuner.FREQ)
        
    
    def tune_up(self, step=10):
        
        self.tuner.tune_step(mode = 'UP', step = step)
        self.FREQ.emit(self.tuner.FREQ)
    
    
    def tune_down(self, step=10):
        
        self.tuner.tune_step(mode = 'DOWN', step = step)
        self.FREQ.emit(self.tuner.FREQ)
        
        
    def seek_up(self,seek_sensitivity):

        self.tuner.seek(mode = 'UP', sens = seek_sensitivity)
        self.FREQ.emit(self.tuner.FREQ)
    
    
    def seek_down(self,seek_sensitivity):

        self.tuner.seek(mode = 'DOWN', sens = seek_sensitivity)
        self.FREQ.emit(self.tuner.FREQ)


    def tune_to_freq(self,frequency):
        
        self.tuner.tune_to('FM',frequency)
        self.FREQ.emit(self.tuner.FREQ)
        

####################################################################################################
####                                                                                            ####
####                                               MAIN                                         ####           ####
####                                                                                            ####    
####################################################################################################

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    print('Application running...')
    MainWindow = QMainWindow()
    a = MainApp()
    a.setWindowTitle("TEF6686 Tuner")
    a.show()
    sys.exit(app.exec())