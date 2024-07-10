#! 
import sys,os
import subprocess
import time
import glob
import signal

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtWidgets import *


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.plot()

    def plot(self):
        data = [1, 2, 3, 4, 5]
        self.axes.plot(data, 'r-')
        self.draw()

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.config_dir="~"
        self.data_dir="~"
        self.__daqd_is_running=False
        self.__directory_set=False      
        self.__terminal_CR = False  
        self.__CURRENT_RUN = 0
        self.__RUN_FINISHED = "=================Run finished================"
        self.__ACQUISITION_FINISHED = "=================Acquisition finished================"
        self.__PROCESSING_ENABLED=False

        self.setWindowTitle('TOFPET2 data recorder')

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Top layout for buttons and plot
        top_layout = QHBoxLayout()

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

        # Widget: Taking data
        left_group2 = QGroupBox("Data acquisation")
        left_group2_vbox = QVBoxLayout()
        self.daq_setting={"mode":"TOT", "time":120, "HW trigger":True, "runs":1, "Running": False, "Series number auto": True, "Series number":"1"}
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
        self.cb_daq_series_number.setMaximumHeight(25)                
        self.cb_daq_series_number.font().setPointSize(10)                
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

        # Right side for plot
        self.plot_canvas = PlotCanvas()

        # Add layouts to top layout
        top_layout.addLayout(left_layout, stretch=3)
        top_layout.addWidget(self.plot_canvas, stretch=7)

        # Bottom layout for terminal
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_input = QLineEdit()
        self.terminal_input.returnPressed.connect(self.execute_command)

        # Add terminal output and input to a vertical layout
        terminal_layout = QVBoxLayout()
        terminal_layout.addWidget(self.terminal_output)
        terminal_layout.addWidget(self.terminal_input)

        # Add layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addLayout(terminal_layout)

        # Set the main layout as the central widget's layout
        central_widget.setLayout(main_layout)

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
        if self.__RUN_FINISHED in output and self.__PROCESSING_ENABLED:
            print("Running processing in background")
            time.sleep(0.2)
            self.processing_start()
        if self.__ACQUISITION_FINISHED in output:
            self.__PROCESSING_ENABLED=False

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
        else:
            self.daq_setting["Series number auto"]=False
            self.daq_setting["Series number"]=self.cb_daq_series_number.text()

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

        if not self.daq_setting["Running"]:
            if self.daq_setting["Series number auto"]==True:
                self.daq_setting["Series number"] = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

            for irun in range(self.daq_setting["runs"]):
                series_number=self.daq_setting["Series number"]
                self.cb_daq_series_number.setText(series_number)
                command = f"""pushd petsysbuild
./acquire_sipm_data --config {self.config_dir}/config.ini -o {self.data_dir+'/raw/'+series_number+f'_{irun}'} --mode {self.daq_setting['mode'].lower()} --time {self.daq_setting['time']} {'--enable-hw-trigger' if self.daq_setting['HW trigger'] else ''}
popd
    """
                
                self.execute_command("echo =====================================================")
                self.execute_command(f"echo Series number {series_number}")
                self.execute_command(f"echo Run {irun}/{self.daq_setting['runs']}")
                self.execute_command("echo =====================================================")
                self.execute_command(command)
                self.execute_command(f"echo {self.__RUN_FINISHED}")
                self.execute_command("echo")

            self.execute_command(f"echo {self.__ACQUISITION_FINISHED}")

        else:
            return
    
    def processing_start(self):
        if not self.__directory_set:
            self.execute_command("echo Directory not set. Please set the config and data directory first")
        raw_file_list = glob.glob(self.data_dir+'/raw/'+self.daq_setting["Series number"]+"*.rawf")
        unprocessed_file_list = []
        output_single_list=[]
        output_coinc_list=[]
        for file in raw_file_list:
            processed_single_filename=(self.data_dir+'/processed/'+os.path.basename(file)).replace(".rawf", "_single.root")
            if not os.path.exists(processed_single_filename):
                unprocessed_file_list.append(file)
                output_single_list.append(processed_single_filename)
                output_coinc_list.append(processed_single_filename.replace("_single.root", "_coinc.root"))
        for i in range(len(unprocessed_file_list)):
            command=f"""pushd petsysbuild
./convert_raw_to_singles --config {self.config_dir}/config.ini -i {unprocessed_file_list[i].replace('.rawf','')} -o {output_single_list[i]} --writeRoot
./convert_raw_to_coincidence --config {self.config_dir}/config.ini -i {unprocessed_file_list[i].replace('.rawf','')} -o {output_coinc_list[i]} --writeRoot
popd
pushd processing
./run_processing.sh {output_coinc_list[i]}
popd
""" 
            self.execute_command_processing(command)

    def acquire_and_process(self):
        self.__PROCESSING_ENABLED=True
        self.acquire_start(processing=True)

    def acquire_stop(self):
        self.send_sigint(self.process)
        self.send_sigint(self.process_processing)
               

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())