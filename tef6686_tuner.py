#%%%                                                                                                      ####
####                                    IMPORT PACKAGES                                                   ####
####                                                                                                      ####
#%%%

import sys
import time

from PyQt5.QtWidgets import QApplication,QWidget,QMainWindow,QSlider,QLabel,QAction,QMenuBar
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import PyQt5.uic as uic

from TEF6686 import TEF6686

#%%%                                                                                                      ####
####                                     DEFINE CLASSES                                                   ####
####                                                                                                      ####
#%%%

MainApp_UI, QtBaseClass = uic.loadUiType("mainwindow.ui")
#
class MainApp(QMainWindow,MainApp_UI):
    
    FREQ = pyqtSignal(int)
    SIGNAL_STRENGTH = pyqtSignal(float)
    SIGNAL_STATUS = pyqtSignal(list)
    RDS_DATA = pyqtSignal(object)
    
    
    def __init__(self):
        
        # Generate user interface
        QMainWindow.__init__(self)
        MainApp_UI.__init__(self)
        self.setupUi(self)
        
        # Variables
        self.TUNER_ACTIVE = False
        
        # Generate menu bar
        self.Menu = QMenuBar()
        self.setMenuBar(self.Menu)
        # Add and connect entries
        self.Menu_File = self.Menu.addMenu("File")
        self.Menu_InitTuner = QAction("Initialize tuner module", self)
        self.Menu_Quit = QAction("Quit", self)
#       # Allocate actions
        self.Menu_File.addAction(self.Menu_InitTuner)
        self.Menu_InitTuner.triggered.connect(self.initialize_tuner)
        self.Menu_File.addAction(self.Menu_Quit)
        self.Menu_Quit.triggered.connect(self.close_app)
        
        # Connect buttons
        self.SeekDown_Button.clicked.connect(self.seek_down)
        self.SeekUp_Button.clicked.connect(self.seek_up)
        self.TuneDown_Button.clicked.connect(self.tune_down)
        self.TuneUp_Button.clicked.connect(self.tune_up)
        
       
        # Start tuner thread
        self.tuner_thread = QThread()
        self.tuner_worker = TunerWorker()
        self.tuner_worker.moveToThread(self.tuner_thread)
        self.tuner_thread.start()
        self.tuner_worker.FREQ.connect(self.update_frequency)
        self.tuner_worker.SIGNAL_STRENGTH.connect(self.update_signal_strength)
        self.tuner_worker.SIGNAL_STATUS.connect(self.update_indicators)
        self.tuner_worker.RDS_DATA.connect(self.update_RDS)
        
        
    def close_app(self):
        
        self.tuner_thread.quit()
        sys.exit()
        
    
    def initialize_tuner(self):
        
        self.tuner_worker.initialize_tuner()
        
        if self.tuner_worker.TUNER_ACTIVE == True:
            self.Menu_InitTuner.setDisabled(True)
        
    
    def tune_up(self):
        
        self.tuner_worker.tune_up()
        self.RDS_PS_QLabel.setText('--------')
        self.RDS_PI_QLabel.setText('----')
        self.RDSRT_TextBrowser.clear()
    
    
    def tune_down(self):
        
        self.tuner_worker.tune_down()
        self.RDS_PS_QLabel.setText('--------')
        self.RDS_PI_QLabel.setText('----')
        self.RDSRT_TextBrowser.clear()
        
    def seek_up(self):
        
        self.tuner_worker.seek_up()
        self.RDS_PS_QLabel.setText('--------')
        self.RDS_PI_QLabel.setText('----')
        self.RDSRT_TextBrowser.clear()
    
    
    def seek_down(self):
        
        self.tuner_worker.seek_down()
        self.RDS_PS_QLabel.setText('--------')
        self.RDS_PI_QLabel.setText('----')
        self.RDSRT_TextBrowser.clear()
    
    
    def update_frequency(self, frequency):
        
       self.Frequency_LCD.display(frequency)
       
    
    def update_signal_strength(self, signal_strength):
        
        self.Signal_dBuV_LCD.display(signal_strength)

        
    def update_indicators(self, signal_status):
        
        FM_stereo = signal_status[0]
        RDS_available = signal_status[1]
        
        if FM_stereo == True:
            self.Stereo_Ind_Label.setStyleSheet('color: red')
        else:
            self.Stereo_Ind_Label.setStyleSheet('color: black')
            
        if RDS_available == True:
            self.RDS_Ind_Label.setStyleSheet('color: red')
        else:
            self.RDS_Ind_Label.setStyleSheet('color: black')
    
    
    def update_RDS(self, RDS_data):
        
        for elem in RDS_data:
            RDS_data_temp = elem
        try:                                                   # sometimes this results in "UnboundLocalError"
            self.RDS_PS_QLabel.setText(RDS_data_temp['PS'])
        except:
            pass
        try:
            self.RDS_PI_QLabel.setText(RDS_data_temp['PI'])
        except:
            pass
        try:
            self.RDSRT_TextBrowser.append(RDS_data_temp['RT'])
        except:
            pass
        #print(RDS_data_temp["RT"])
        #self.RDSRT_TextEdit.appendPlainText(RDS_data['RT'])
        #elif RDS_data[0] == 'PS':
        #    print("Received PS: ", RDS_data[1])
        
        #elif RDS_data[0] == 'RT':
        #    print("Received Radiotext: ", RDS_data[1])
            
            
    def dummy_action(self):
        
        print("This function will soon be implemented!")




class TunerWorker(QObject):
    
    RDS_DATA = pyqtSignal(object)
    FREQ = pyqtSignal(int)
    SIGNAL_STRENGTH = pyqtSignal(float)
    SIGNAL_STATUS = pyqtSignal(list)
    
    
    def __init__(self):
        QObject.__init__(self)
        self.TUNER_ACTIVE = False
        self.__MONITOR_SIGNAL__ = False
    
    
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
        self.__MONITOR_SIGNAL__ = True
        time.sleep(2)
        print("Starting signal monitor...")
        self.monitor_signal()
    
    
    @pyqtSlot()
    def monitor_signal(self):
        
        loop_count = 0
        
        while self.__MONITOR_SIGNAL__ == True:
            loop_count += 1
            
            if loop_count == 5:
                
                signal_strength, FM_stereo, RDS_available = self.tuner.get_signal_info('full')
                self.SIGNAL_STRENGTH.emit(signal_strength)
                self.SIGNAL_STATUS.emit([FM_stereo, RDS_available])
                loop_count = 0
                
                if RDS_available == True:
                    RDS_data_dict = self.tuner.get_RDS_data(pause_time = 0, repeat = False)
                    self.RDS_DATA.emit(RDS_data_dict)
                else:
                    pass
                    
            QApplication.processEvents()
            time.sleep(0.012)
        
    
    def tune_up(self):
        
        self.tuner.tune_step(mode = 'UP', step = 5)
        self.FREQ.emit(self.tuner.FREQ)
    
    
    def tune_down(self):
        
        self.tuner.tune_step(mode = 'DOWN', step = 5)
        self.FREQ.emit(self.tuner.FREQ)
        
        
    def seek_up(self):
        
        self.tuner.seek(mode = 'UP', sens = 'local')
        self.FREQ.emit(self.tuner.FREQ)
    
    
    def seek_down(self):
        
        self.tuner.seek(mode = 'DOWN', sens = 'local')
        self.FREQ.emit(self.tuner.FREQ)
        
    
        

#%%%                                                                                                      ####
####                                               MAIN                                                   ####
####                                                                                                      ####
#%%%

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    print('Application running...')
    MainWindow = QMainWindow()
    a = MainApp()
    a.setWindowTitle("TEF6686 Tuner")
    a.show()
    sys.exit(app.exec())