#! 
import sys,os
import subprocess
import time
import glob
import signal

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.pyplot import *
import matplotlib.pyplot as plt


import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtWidgets import *


# Include some functions to make the data quality monitoring plots
import joblib
import numpy as np
from processing import script_data_quality as dqm


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=8, height=4, dpi=100):
        self.fig, self.axes = plt.subplots(2, 3, figsize=(width, height), dpi=dpi, tight_layout=True)
        super(MplCanvas, self).__init__(self.fig)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('TOFPET2 data recorder')

        # Global variables
        self.config_dir="~"
        self.data_dir="~"
        self.__daqd_is_running=False
        self.__directory_set=False      
        self.__terminal_CR = False  
        self.__CURRENT_RUN = -1
        self.__RUN_FINISHED_LABLE = "=================Run finished================"
        self.__RUN_FINISHED_COUNTER = -1
        self.__ACQUISITION_FINISHED_LABLE = "=================Acquisition finished================"
        self.__ACQUISITION_ONGOING = False
        self.__PROCESSING_FINISHED_LABLE = "===============Processing finished=================="
        self.__PROCESSING_FINISHED = True
        self.__PROCESSING_FINISHED_COUNTER =-1
        self.__PROCESSING_ENABLED=False
        self.__DQM_INIT=False
        self.__DQM_INFO = {"runs_total":0,
                           "duration":0,
                           "events_total":0,
                           "event_rate":0,
                           "channels":[],
                           "coinc_pairs":[],
                           "data_filename_list":[]}
        self.__DQM_SETTING = {"run_selected":0,
                              "single_channels_all":[], # Each cell is the absolute ID
                              "single_channels_selected":[], # Each cell is the absolute ID
                              "coinc_channels_all":[], # Each cell is a pairl of absolute ID, starting with the larger one 
                              "coinc_channels_selected":[], # Each cell is a pairl of absolute ID, starting with the larger one 
                              }


        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        #---------------------------------------------------------------------------------
        # Top layout for buttons and plot
        top_layout = QHBoxLayout()
        #-------------------------------------------
        # Left side for buttons
        left_layout = QVBoxLayout()

        # Widget: Working directory select
        left_group1 = QGroupBox("Working directory")
        left_group1_vbox = QVBoxLayout()
        # Configuration
        self.btn_config_dir = QPushButton("Config dir")
        self.btn_config_dir.clicked.connect(self.set_config_dir)
        self.label_config_dir = QTextEdit("") 
        self.label_config_dir.setMaximumHeight(40)  
        self.label_config_dir.font().setPointSize(9)                
        self.btn_data_dir = QPushButton("Data dir")
        self.btn_data_dir.clicked.connect(self.set_data_dir)
        self.label_data_dir = QTextEdit("") 
        self.label_data_dir.setMaximumHeight(40)  
        self.label_data_dir.font().setPointSize(9)                
        self.btn_daqd_connect = QPushButton("Start DAQ driver")
        self.btn_daqd_connect.clicked.connect(self.start_daqd)
        left_group1_vbox.addWidget(self.btn_config_dir)
        left_group1_vbox.addWidget(self.label_config_dir) 
        left_group1_vbox.addWidget(self.btn_data_dir)
        left_group1_vbox.addWidget(self.label_data_dir)  
        left_group1_vbox.addWidget(self.btn_daqd_connect)  
        left_group1_vbox.setContentsMargins(0,0,0,0) 
        left_group1.setLayout(left_group1_vbox)  
        # left_group1.setMaximumWidth(200) # Use this to limit the max width of the left_layout

        # Widget: Taking data
        left_group2 = QGroupBox("Data acquisation")
        left_group2_vbox = QVBoxLayout()
        self.daq_setting={"mode":"TOT", "time":120, "HW trigger":True, "runs":1, "finished": False, "Series number auto": True, "Series number":"1"}
        # MODE
        hbox1 = QHBoxLayout()
        self.label_daq_mode = QLabel("Mode")
        self.cb_daq_mode = QComboBox()
        self.cb_daq_mode.addItems(["TOT", "QDC"])
        self.cb_daq_mode.currentTextChanged.connect(self.update_daq_settings)
        hbox1.addWidget(self.label_daq_mode)
        hbox1.addWidget(self.cb_daq_mode)
        # Time
        hbox2 = QHBoxLayout()
        self.label_daq_time = QLabel("Time [s]")
        self.cb_daq_time = QLineEdit("120")
        self.cb_daq_time.setMaximumHeight(25)                
        self.cb_daq_time.editingFinished.connect(self.update_daq_settings)
        hbox2.addWidget(self.label_daq_time,stretch=4)
        hbox2.addWidget(self.cb_daq_time, stretch=5) 
        # Trigger
        hbox3 = QHBoxLayout()
        self.label_daq_trigger = QLabel("HW Coinc. Trig.")
        self.cb_daq_trigger = QComboBox()
        self.cb_daq_trigger.addItems(["Yes", "No"])
        self.cb_daq_trigger.currentTextChanged.connect(self.update_daq_settings)
        hbox3.addWidget(self.label_daq_trigger,stretch=4)
        hbox3.addWidget(self.cb_daq_trigger, stretch=5) 
        # Number of runs
        hbox4 = QHBoxLayout()
        self.label_daq_runs = QLabel("Runs")
        self.cb_daq_runs = QLineEdit("1")
        self.cb_daq_runs.setMaximumHeight(50)                
        self.cb_daq_runs.editingFinished.connect(self.update_daq_settings)
        hbox4.addWidget(self.label_daq_runs,stretch=4)
        hbox4.addWidget(self.cb_daq_runs, stretch=5)  
        # Run series number
        hbox5 = QHBoxLayout()
        self.label_daq_series_number = QLabel("Series")
        self.checkbox_series_number_auto = QCheckBox()
        self.checkbox_series_number_auto.setText("Auto")
        self.checkbox_series_number_auto.setChecked(True)
        self.checkbox_series_number_auto.toggled.connect(self.update_daq_settings)
        self.cb_daq_series_number = QLineEdit("YYYYMMDD_HHMMSS")
        self.cb_daq_series_number.setReadOnly(True)                
        self.cb_daq_series_number.setMaximumHeight(25)                
        font = self.cb_daq_series_number.font()
        font.setPointSize(8)
        self.cb_daq_series_number.setFont(font)
        self.cb_daq_series_number.editingFinished.connect(self.update_daq_settings)
        # self.cb_daq_series_number.setDisabled(True)
        hbox5.addWidget(self.label_daq_series_number,stretch=3)
        hbox5.addWidget(self.checkbox_series_number_auto, stretch=3)          
        hbox5.addWidget(self.cb_daq_series_number, stretch=7)          
        # Run button
        self.btn_acquire = QPushButton("Acquire")
        self.btn_acquire.clicked.connect(self.acquire_start) 
        self.btn_process = QPushButton("Process")
        self.btn_process.clicked.connect(self.processing_start) 
        hbox6 = QHBoxLayout()        
        hbox6.addWidget(self.btn_acquire)
        hbox6.addWidget(self.btn_process)
        self.btn_acquire_process = QPushButton(r"Acquire and process")
        self.btn_acquire_process.setMinimumHeight(44)
        self.btn_acquire_process.clicked.connect(self.acquire_and_process)
        self.btn_acquire_stop = QPushButton("Stop")
        self.btn_acquire_stop.clicked.connect(self.acquire_stop)                

        left_group2_vbox.addLayout(hbox1)
        left_group2_vbox.addLayout(hbox2)
        left_group2_vbox.addLayout(hbox3)
        left_group2_vbox.addLayout(hbox4)
        left_group2_vbox.addLayout(hbox5)
        left_group2_vbox.addLayout(hbox6)
        left_group2_vbox.addWidget(self.btn_acquire_process)
        left_group2_vbox.addWidget(self.btn_acquire_stop)
        left_group2.setLayout(left_group2_vbox)  

        left_layout.addWidget(left_group1) 
        left_layout.addWidget(left_group2) 
        left_layout.addStretch() 

        #---------------------------------------------------
        # Middle  for plot canvas
        mid_layout = QVBoxLayout()
        # self.plot_canvas = PlotCanvas()
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        # self.sc.axes.plo([0,1,2,3,4], [10,1,20,3,40])
        # Widget: Plot toolbar
        toolbar = NavigationToolbar(self.sc, self) # toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        mid_layout.addWidget(toolbar)
        mid_layout.addWidget(self.sc)

        #---------------------------------------------------
        # Right for plot control
        right_layout=QVBoxLayout()

        # Data overview box
        right_group1=QGroupBox("Series overview")
        right_group1_layout=QVBoxLayout()
        self.txt_dqm = QTextBrowser()
        self.txt_dqm.setMinimumHeight(48)
        self.txt_dqm.setMaximumHeight(120)
        self.txt_dqm.setText("Runs: \nDuration[s]: \nTotal events: \nEvent rate [Hz]: \nActive channels: \nActive coinc. pairs: ")
        right_group1_layout.addWidget(self.txt_dqm)
        right_group1.setLayout(right_group1_layout)
        right_group1.setMaximumHeight(180)
        # Plot configurations
        self.btn_dqm_update=QPushButton("Get DQM info of series")
        self.btn_dqm_update.clicked.connect(self.init_dqm_info) 
        right_group2=QHBoxLayout()
        self.label_dqm_run = QLabel("#Run to plot")
        self.cb_dqm_run = QComboBox()
        self.cb_dqm_run.currentIndexChanged.connect(self.redraw_different_run)
        right_group2.addWidget(self.label_dqm_run)
        right_group2.addWidget(self.cb_dqm_run)        
        # Selection box for single channels
        right_group3=QGroupBox("Single channel selection")
        right_group3_layout=QVBoxLayout()
        self.list_single_channel = QListWidget()     
        self.list_single_channel.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)        
        self.list_single_channel.itemSelectionChanged.connect(self.redraw_single_channel)
        self.btn_single_channel_select_all=QPushButton("(Un)Select all")
        right_group3_layout.addWidget(self.list_single_channel)
        right_group3_layout.addWidget(self.btn_single_channel_select_all)
        right_group3.setLayout(right_group3_layout)
        # Selection box for coinc channels
        right_group4=QGroupBox("Coinc. channel selection")
        right_group4_layout=QVBoxLayout()
        self.list_coinc_channel = QListWidget()     
        self.list_coinc_channel.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)       
        self.btn_coinc_channel_select_all=QPushButton("(Un)Select all")
        right_group4_layout.addWidget(self.list_coinc_channel)
        right_group4_layout.addWidget(self.btn_coinc_channel_select_all)
        right_group4.setLayout(right_group4_layout)
        # Add everything to right panel       
        right_layout.addWidget(self.btn_dqm_update)
        right_layout.addWidget(right_group1)
        right_layout.addLayout(right_group2)
        right_layout.addWidget(right_group3)
        right_layout.addWidget(right_group4)
        right_layout.addStretch() 



        # Add layouts to top layout
        top_layout.addLayout(left_layout, stretch=2)
        top_layout.addLayout(mid_layout, stretch=9)
        top_layout.addLayout(right_layout, stretch=2)
        #-----------------------------------------------------------------------------------------------




        #-----------------------------------------------------------------------------------------------
        # Bottom layout for terminal
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_input = QLineEdit()
        self.terminal_input.returnPressed.connect(self.execute_command)

        # Add terminal output and input to a vertical layout
        terminal_layout = QVBoxLayout()
        terminal_layout.addWidget(self.terminal_output)
        terminal_layout.addWidget(self.terminal_input)
        #-----------------------------------------------------------------------------------------------



        #-----------------------------------------------------------------------------------------------
        # Add layouts to main layout
        main_layout.addLayout(top_layout, stretch=8)
        main_layout.addLayout(terminal_layout, stretch=2)

        # Set the main layout as the central widget's layout
        central_widget.setLayout(main_layout)
        #-----------------------------------------------------------------------------------------------



        # Setup QProcess for terminal
        # Show the output of this shell in the GUI
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.start('bash')

        # Setup QProcess for processing
        # Show the output of this shell in the terminal
        self.process_processing = QProcess(self)
        self.process_processing.start('bash') 
        self.process_processing.readyReadStandardOutput.connect(self.read_output_processing)
        self.process_processing.readyReadStandardError.connect(self.read_error_processing)

      

    # -------------------------------------------------------------------
    # Helper functions for embeded terminal and the processing process
    # Terminal: run command
    def execute_command(self, command=None):
        if not command:
            command = self.terminal_input.text()
        self.process.write(command.encode() + b'\n')
        self.terminal_input.clear()

    # Terminal: display output to the GUI text box
    def read_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        # self.terminal_output.insertPlainText(output)
        self.handle_output(output)
        sb = self.terminal_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    # Terminal: display output to the GUI text box
    def read_error(self):
        error = self.process.readAllStandardError().data().decode()
        self.handle_output(error)
        sb = self.terminal_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    # Processing: run commands
    def execute_command_processing(self, command=None):
        if not command:
            command = self.terminal_input.text()
        self.process_processing.write(command.encode() + b'\n')     
    
    # Processing: display output to the current terminal
    def read_output_processing(self):
        output = self.process_processing.readAllStandardOutput().data().decode()
        # Check if the processing finished
        if self.__PROCESSING_FINISHED_LABLE in output:
            self.__PROCESSING_FINISHED_COUNTER +=1
            self.update_dqm_info()
            if self.__PROCESSING_FINISHED_COUNTER==self.daq_setting["runs"]:
                self.__PROCESSING_FINISHED = True
                self.execute_command("echo 'All processing finished.'")

        if len(output)>0:
            print(output, end=output[-1])

    # Processing: display output to the current terminal
    def read_error_processing(self):
        output = self.process_processing.readAllStandardError().data().decode()
        if len(output)>0:
            print(output, end=output[-1])        

    def handle_output(self, output):
        # Special treatment for lines end with \r
        if self.__terminal_CR:
            self.replace_last_line(output)
        else:
            self.append_to_terminal(output)
        if output[-1]=="\r":
            self.__terminal_CR=True  
        else:
            self.__terminal_CR=False  

        # Start processing if run finished
        if self.__RUN_FINISHED_LABLE in output:
            self.__RUN_FINISHED_COUNTER+=1
            if self.__PROCESSING_ENABLED:
                print("Running processing in background")
                time.sleep(0.2)
                self.processing_start()
        if self.__ACQUISITION_FINISHED_LABLE in output:
            self.__PROCESSING_ENABLED  = False
            self.__ACQUISITION_ONGOING = False
            self.execute_command("echo 'Running processing on the last file. Please check the main ternimal for progress.'")

    def append_to_terminal(self, text):
        self.terminal_output.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal_output.insertPlainText(text)
        self.terminal_output.moveCursor(QTextCursor.MoveOperation.End)

    def replace_last_line(self, text):
        cursor = self.terminal_output.textCursor()
        cursor.deletePreviousChar()
        cursor.movePosition(QTextCursor.MoveOperation.End);
        cursor.select(QTextCursor.SelectionType.LineUnderCursor);        
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.terminal_output.setTextCursor(cursor)

    # Send interrupt singal to a process
    def send_sigint(self, process):
        if process is not None:
            os.kill(process.processId(), signal.SIGINT)

    def send_sigkill(self, process):
        if process is not None:
            os.kill(process.processId(), signal.SIGTERM)                
    # -------------------------------------------------------------------



    def set_config_dir(self):
        self.config_dir = QFileDialog.getExistingDirectory(self, 'Select directory contains config.ini', 
            self.config_dir)
        if not os.path.exists(self.config_dir+"/config.ini"):
            print(self.config_dir+"/config.ini")
            self.btn_config_dir.setStyleSheet("background-color: red")
            return
        else:
            self.btn_config_dir.setStyleSheet("background-color: green")
        self.label_config_dir.setText(self.config_dir)
        self.__directory_set = (self.config_dir!="~") & (self.data_dir!="~" )

    def set_data_dir(self):
        self.data_dir = QFileDialog.getExistingDirectory(self, 'Select directory to save data. A raw/ and processed/ folder will be made.', 
            os.path.dirname(self.config_dir))
        self.btn_data_dir.setStyleSheet("background-color: green")
        self.label_data_dir.setText(self.data_dir)   
        self.__directory_set = (self.config_dir!="~") & (self.data_dir!="~" )
        # Make two sub directories for raw and processed file
        os.makedirs(self.data_dir+"/raw", exist_ok=True)    
        os.makedirs(self.data_dir+"/processed", exist_ok=True)   



    def update_daq_settings(self):
        self.daq_setting["mode"] = self.cb_daq_mode.currentText()
        self.daq_setting["time"] = float(self.cb_daq_time.text())
        self.daq_setting["HW trigger"] = True if self.cb_daq_trigger.currentText()=="Yes" else False
        self.daq_setting["runs"] = int(self.cb_daq_runs.text())

        if self.checkbox_series_number_auto.isChecked():
            self.daq_setting["Series number auto"]=True
            self.cb_daq_series_number.setReadOnly(True)
        else:
            self.daq_setting["Series number auto"]=False
            self.daq_setting["Series number"]=self.cb_daq_series_number.text()
            self.cb_daq_series_number.setReadOnly(False)

        print(self.daq_setting)

    def is_daqd_running(self):
        isDaqdPresent = subprocess.call(["pidof", "daqd"], stdout= subprocess.PIPE) == 0
        return isDaqdPresent        


    # Start the DAQ server
    def start_daqd(self):
        command = "pushd petsysbuild\n ./daqd --socket-name /tmp/d.sock --daq-type GBE"
        command2 = "xterm -hold -e \"%s\"" % command
        # Check if there are other instances of daqd
        if not self.is_daqd_running():
            #Check if socket and shm files exist
            if os.path.exists('/tmp/d.sock'):
                subprocess.call("rm /tmp/d.sock", shell=True) 

            if os.path.exists('/dev/shm/daqd_shm'):
                subprocess.call("rm /dev/shm/daqd_shm", shell=True) 

            #Open ./daqd
            daqdOpenPipe = subprocess.Popen(command2, shell=True)    
            time.sleep(1.5)   
        if self.is_daqd_running():     
            self.__daqd_is_running = True
            self.btn_daqd_connect.setStyleSheet("background-color: green")
            self.btn_daqd_connect.setText("DAQ driver running")            
        else:
            self.__daqd_is_running = False
            self.btn_daqd_connect.setStyleSheet("background-color: red")
            self.btn_daqd_connect.setText("Failed to start DAQ driver")           



    def acquire_start(self, processing=False):
        if not self.__directory_set:
            self.execute_command("echo Directory not set. Please set the config and data directory first")
        if not self.__daqd_is_running:
            self.execute_command("echo DAQ driver is not running. Please start the driver first.")

        if not self.__ACQUISITION_ONGOING:
            self.__ACQUISITION_ONGOING = True
            if self.daq_setting["Series number auto"]==True:
                self.daq_setting["Series number"] = time.strftime("%Y%m%d_%H%M%S", time.gmtime())


            # Get the filename prefix
            series_number=self.daq_setting["Series number"]
            self.cb_daq_series_number.setText(series_number)
            series_raw_dir = self.data_dir+'/raw/'+series_number
            series_raw_prefix = f"{series_raw_dir}/{series_number}"
            os.makedirs(series_raw_dir, exist_ok=True)

            for irun in range(self.daq_setting["runs"]):
                command = f"""pushd petsysbuild
./acquire_sipm_data --config {self.config_dir}/config.ini -o {series_raw_prefix}_{irun} --mode {self.daq_setting['mode'].lower()} --time {self.daq_setting['time']} {'--enable-hw-trigger' if self.daq_setting['HW trigger'] else ''}
popd
    """
                
                self.execute_command("echo =====================================================")
                self.execute_command(f"echo Series number {series_number}")
                self.execute_command(f"echo Run {irun}/{self.daq_setting['runs']}")
                self.execute_command("echo =====================================================")
                self.execute_command(command)
                self.execute_command(f"echo {self.__RUN_FINISHED_LABLE}")
                self.execute_command("echo")

            self.execute_command(f"echo {self.__ACQUISITION_FINISHED_LABLE}")

        else:
            return
    

    def processing_start(self):
        if not self.__directory_set:
            self.execute_command("echo Directory not set. Please set the config and data directory first")

        # Get the diretory ready
        series_raw_prefix = self.data_dir+'/raw/'+self.daq_setting["Series number"] + "/"+ self.daq_setting["Series number"]
        series_process_dir = self.data_dir+'/processed/' +self.daq_setting["Series number"] + "/"
        os.makedirs(series_process_dir, exist_ok=True)

        # Get a list of file to process
        raw_file_list = glob.glob(series_raw_prefix+"*.rawf")
        unprocessed_file_list = []
        output_single_list=[]
        output_coinc_list=[]
        for file in raw_file_list:
            processed_single_filename=(series_process_dir + os.path.basename(file)).replace(".rawf", "_single.root")
            if not os.path.exists(processed_single_filename):
                unprocessed_file_list.append(file)
                output_single_list.append(processed_single_filename)
                output_coinc_list.append(processed_single_filename.replace("_single.root", "_coinc.root"))

        # Run processing on all files
        for i in range(len(unprocessed_file_list)):

            fname_coinc = output_coinc_list[i]
            fname_singles = fname_coinc.replace("_coinc.root", "_single.root")
            fname_recon = fname_coinc.replace("_coinc.root", "_coinc_triggered.pkl")
            command=f"""
echo "Convert raw to singles and coincidence"
pushd petsysbuild
./convert_raw_to_singles --config {self.config_dir}/config.ini -i {unprocessed_file_list[i].replace('.rawf','')} -o {output_single_list[i]} --writeRoot
./convert_raw_to_coincidence --config {self.config_dir}/config.ini -i {unprocessed_file_list[i].replace('.rawf','')} -o {output_coinc_list[i]} --writeRoot
popd

echo "Convert coincidence to hits and events, and do reconstruction"
pushd processing
./run_processing.sh {fname_coinc}

echo "Generate data quality plots (trigger rate, energy histograms)"
python script_data_quality.py {fname_singles} {fname_coinc} {fname_recon}
popd

echo "{self.__PROCESSING_FINISHED_LABLE}"

""" 
            self.execute_command_processing(command)

    def acquire_and_process(self):
        self.__PROCESSING_ENABLED=True
        self.acquire_start(processing=True)

    def acquire_stop(self):
        # Terminate
        self.send_sigkill(self.process)
        self.send_sigkill(self.process_processing)
        time.sleep(0.3)

        # Restart the two child process
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.start('bash')
        self.process_processing = QProcess(self)
        self.process_processing.start('bash') 
        self.process_processing.readyReadStandardOutput.connect(self.read_output_processing)
        self.process_processing.readyReadStandardError.connect(self.read_error_processing)

    def reset_dqm_info(self):
        self.__DQM_INIT=False
        self.__DQM_INFO = {"runs_total":0,
                           "duration":0,
                           "events_total":0,
                           "event_rate":0,
                           "channels":[],
                           "coinc_pairs":[],
                           "data_filename_list":[]}
        self.__DQM_SETTING = {"run_selected":0,
                              "single_channels_all":[], # Each cell is the absolute ID
                              "single_channels_selected":[], # Each cell is the absolute ID
                              "coinc_channels_all":[], # Each cell is a pairl of absolute ID, starting with the larger one 
                              "coinc_channels_selected":[], # Each cell is a pairl of absolute ID, starting with the larger one 
                              }  
        self.processed_file_list=[]

# 20240712_162718
    def init_dqm_info(self):
        self.reset_dqm_info()
        self.update_dqm_info()
        return

    def update_dqm_info(self):
         # Find all the processed file of this series
        series_process_prefix = self.data_dir+'/processed/' + self.daq_setting["Series number"] + "/" + self.daq_setting["Series number"]
        self.processed_file_list = sorted(glob.glob(series_process_prefix+f"_*_data_quality.joblib"), key=os.path.getmtime)
        if len(self.processed_file_list)==0:
            print(f"No file found starting with {series_process_prefix}. Does the series exist? Is it processed?")
            return        

        # Set the dqm information dict
        files_to_check  = self.processed_file_list[self.__DQM_INFO["runs_total"]:]
        print("Processed files found:", self.processed_file_list)
        for fname in files_to_check:
            data=joblib.load(fname)
            channel_list = list(data["hist1_single_rate"].keys())
            coinc_list = list(data["hist3_coinc_rate"].keys())
            events = np.sum([data["hist1_single_rate"][ch][0] for ch in channel_list])
            ch=channel_list[0]
            duration = data["hist1_single_rate"][ch][1][-1] - data["hist1_single_rate"][ch][1][0]
            self.__DQM_INFO['runs_total']+=1
            self.__DQM_INFO['event_rate'] = (self.__DQM_INFO["events_total"]+events)/(self.__DQM_INFO["duration"]+duration)
            self.__DQM_INFO['duration']+=duration
            self.__DQM_INFO['events_total']+=events
            self.__DQM_INFO['channels'] = list(np.unique(self.__DQM_INFO["channels"]+channel_list))
            self.__DQM_INFO['coinc_pairs'] = list(np.unique(self.__DQM_INFO["coinc_pairs"]+coinc_list, axis=0))
            self.__DQM_INFO['data_filename_list'] += fname

        # Update the information text box on top right
        self.txt_dqm.setText(f"""Runs: {self.__DQM_INFO['runs_total']}
Duration [s]: {self.__DQM_INFO['duration']:.1f}
Total events: {self.__DQM_INFO['events_total']:.0f}
Event rate [Hz]: {self.__DQM_INFO['event_rate']:.1f}
Active channels: {len(self.__DQM_INFO['channels'])}
Active coinc. pairs: {len(self.__DQM_INFO['coinc_pairs'])}""")

        # Update the drop down list of runs
        self.cb_dqm_run.clear()
        for i in range(self.__DQM_INFO['runs_total']):
            self.cb_dqm_run.addItem(str(i))
        self.cb_dqm_run.setCurrentIndex(self.__DQM_INFO['runs_total']-1)

        # Update the single/coinc channel selection list
        # Remove existing items first
        self.list_single_channel.clear()
        for i in range(len(channel_list)):
            c=QListWidgetItem(f"{channel_list[i]}")
            self.list_single_channel.addItem(c)
        self.list_single_channel.update()
        # 20240711_195553
        
        # for i in reversed(range(self.chekbox_single_channel_layout.count())): 
        #     self.chekbox_single_channel_layout.itemAt(i).widget().setParent(None)
        # self.checkbox_single_channels=[]
        # for i in range(len(channel_list)):
        #     print("add checkbox",i)
        #     c=QCheckBox(f"{channel_list[i]}")
        #     self.chekbox_single_channel_layout.addWidget(c)
        #     self.checkbox_single_channels.append(c)
        # self.chekbox_single_channel_layout.update()



        # Make the initial plot
        self.update_dqm_plot(run_to_plot=-1)
        



    def update_dqm_plot(self, run_to_plot=None):
        # series_process_prefix = self.data_dir+'/processed/' + self.daq_setting["Series number"] + "/" + self.daq_setting["Series number"] 
        # processed_list = series_process_prefix+f"_{self.__PROCESSING_FINISHED_COUNTER}_data_quality.joblib"
        # processed_list = sorted(glob.glob(series_process_prefix+f"_*_data_quality.joblib"), key=os.path.getmtime)
        if run_to_plot is None:
            self.update_dqm_info()
            run_to_plot = -1
        fname = self.processed_file_list[run_to_plot]


        plotdata = joblib.load(fname)

        # Clear the axis
        for ax in self.sc.fig.axes:
            ax.clear()
        # Make new plots
        fig = dqm.make_plots(plotdata, fig=self.sc.fig, plot_singles_list=None, plot_coinc_list=None)
        self.sc.draw() # Don't forget this line...

        return
    
    def redraw_single_channel(self):
        return
    
    def redraw_different_run(self):
        run = self.cb_dqm_run.currentIndex()
        self.update_dqm_plot(run_to_plot=run)
               

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    main_window.resize(1600, 900) # start up resolution

    sys.exit(app.exec())