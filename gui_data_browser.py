import sys,os
import matplotlib
matplotlib.use('QtAgg')

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.pyplot import *

# ROOT file related
import ROOT, uproot
import numpy as np 


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class RootFile():
    def __init__(self, filename):

        self.file = ROOT.TFile(filename)
        try:
            # self.tree = self.file.Get("data")
            # self.barnches = self.tree.GetListOfBranches(); self.barnches = [self.barnches[i].GetName() for i in range(len(self.barnches))]
            # self.nevents = int(self.tree.GetEntries())
            # self.channelIDs = np.sort(np.unique(self.read_branch(self.tree,"channelID")))
            # print(self.nevents,self.channelIDs)
            # self.channelIDs_decomp = [self.decomp_channelID(i) for i in self.channelIDs] # decompose Abs ChannelID into portID, slaveID, chipID, channelID
            # self.isTOFPETdata=True

            self.file = uproot.open(filename) # or root:// or http://
            self.tree = self.file["data"]
            self.data = self.tree.arrays(self.tree.keys())

            self.barnches = self.tree.keys()
            self.nevents = len(self.data["channelID"])
            self.channelIDs = np.sort(np.unique(self.data["channelID"]))
            self.channelIDs_decomp = [self.decomp_channelID(i) for i in self.channelIDs]
            self.isTOFPETdata=True

        except:
            self.isTOFPETdata=False

        print("Is TOFPET data",self.isTOFPETdata)
            

    # @staticmethod
    # def read_branch(tree, branch, mask_str=None, mask_branch=None):
    #     content=[]
    #     for iev in range(tree.GetEntries()):
    #         tree.GetEntry(iev)
    #         if mask_str is None:
    #             content.append(getattr(tree, branch))
    #         else:
    #             mask = eval(f"{getattr(tree, mask_branch)}" + mask_str, locals())
    #             if mask is True:
    #                 content.append(getattr(tree, branch))
    #     return content
    
    @staticmethod
    def decomp_channelID(channelIDabs):
        portID, slaveID, chipID, channelID = channelIDabs>>17, channelIDabs>>12 & 0b11111, channelIDabs>>6 & 0b111111, channelIDabs & 0b111111
        return portID, slaveID, chipID, channelID        
        


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.ROOTFILE=None
        self.XRANGE=None
        self.YRANGE=None

        # Widget: Input file select
        self.current_directory="~"
        self.btn_file = QPushButton("Open file")
        self.btn_file.clicked.connect(self.getfile)
        self.label_file = QTextEdit("File path") 
        self.label_file.setMaximumHeight(25)        #self.btn_file.size().height()
        layout_file = QtWidgets.QHBoxLayout()
        layout_file.addWidget(self.btn_file,1)
        layout_file.addWidget(self.label_file,20)        

        # Widget: Plot option
        # 1. Histogram or 2D
        self.PLOT_MODE = "Hist"
        self.b1 = QRadioButton("Hist")
        self.b1.setChecked(True)
        self.b1.toggled.connect(lambda:self.btnstate_hist_2d(self.b1))
        self.b2 = QRadioButton("2D")
        self.b2.toggled.connect(lambda:self.btnstate_hist_2d(self.b2))        
        # 2. Variables
        self.PLOT_VAR = ""
        self.cb1_variables = QComboBox()
        self.cb1_variables.currentIndexChanged.connect(self.updateSettings)
        self.cb1_variables.setMinimumWidth(200)
        if self.PLOT_MODE=="Hist":
            self.cb1_variables.addItems(["tqT"])
        else:
            self.cb1_variables.addItems(["tqT  time"])

        # 3. Channel selection and Plot options
        self.list_channels = QListWidget()
        self.list_channels.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.list_channels.itemSelectionChanged.connect(self.updateSettings)
        self.text_fileinfo = QTextBrowser()
        self.text_fileinfo.setText("File info:")
        layout_channels = QtWidgets.QVBoxLayout()
        layout_channels.addWidget(self.text_fileinfo, 2)
        layout_channels.addWidget(QLabel("Availabel Channels:\nAbsID (port, slave, chip, channel)"))
        layout_channels.addWidget(self.list_channels,10)

        self.plot_settings = QGroupBox()
        self.plot_settings.setTitle("Plotting Range")
        self.button_autox = QCheckBox("Auto X")
        self.button_autox.setChecked(True)
        self.button_autox.stateChanged.connect(self.set_xrange)
        self.button_autoy = QCheckBox("Auto Y")
        self.button_autoy.setChecked(True)
        # self.button_autox.stateChanged.connect(self.set_yrange)
        self.xrange = QLineEdit()
        self.xrange.setMaximumHeight(25)
        self.xrange.setDisabled(True)
        self.xrange.editingFinished.connect(self.set_xrange)



        layout_xrange = QHBoxLayout()
        layout_yrange = QHBoxLayout()
        layout_range = QVBoxLayout(self.plot_settings)
        layout_xrange.addWidget(self.button_autox),1
        layout_xrange.addWidget(QLabel("min,max:"),1)
        layout_xrange.addWidget(self.xrange,3)
        # layout_yrange.addWidget(self.button_autoy)
        # layout_yrange.addWidget(QLabel("min,max:"))
        # layout_yrange.addWidget(self.yrange)        
        layout_range.addLayout(layout_xrange)
        # layout_range.addLayout(layout_yrange)

        layout_channels.addWidget(self.plot_settings,)



        # Widget: Plot canvas
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        # self.sc.axes.plot([0,1,2,3,4], [10,1,20,3,40])
        # Widget: Plot toolbar
        toolbar = NavigationToolbar(self.sc, self) # toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        
        # Layout
        layout_plotbar = QtWidgets.QHBoxLayout()
        layout_plotbar.addWidget(QLabel("Plot type:"))
        layout_plotbar.addWidget(self.b1)
        layout_plotbar.addWidget(self.b2)
        layout_plotbar.addSpacing(30)
        layout_plotbar.addWidget(QLabel("Variable to plot:"))
        layout_plotbar.addWidget(self.cb1_variables)
        layout_plotbar.addStretch()
        layout_plotbar.addWidget(toolbar)
        layout_plotarea = QtWidgets.QHBoxLayout()
        layout_plotarea.addLayout(layout_channels,3)
        layout_plotarea.addWidget(self.sc,9)
        layout_plot = QtWidgets.QVBoxLayout()
        layout_plot.addLayout(layout_plotbar)
        layout_plot.addLayout(layout_plotarea)


        # Main Layout
        self.layout_main = QtWidgets.QVBoxLayout()
        self.layout_main.addLayout(layout_file,1)
        self.layout_main.addLayout(layout_plot,20)         


        # Create a placeholder widget to hold our toolbar and canvas.
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(self.layout_main)
        self.setCentralWidget(self.widget)

    def getfile(self):
        self.FILENAME,*_ = QFileDialog.getOpenFileName(self, 'Open file', 
            self.current_directory,"ROOT files (*.root)")
        if len(self.FILENAME)==0:
            self.btn_file.setStyleSheet("background-color: red")
            return
        print(self.FILENAME)
        self.label_file.setText(self.FILENAME )
        # Update the current working directory
        self.current_directory = os.path.dirname(self.FILENAME)

        # Open ROOT file
        self.ROOTFILE = RootFile(self.FILENAME)
        self.btn_file.setStyleSheet("border:  none")
        if self.ROOTFILE.isTOFPETdata:
            self.btn_file.setStyleSheet("background-color: green")
        else:
            self.btn_file.setStyleSheet("background-color: red")   
        # Update Information
        if self.ROOTFILE.isTOFPETdata:
            self.initiSettings() 

    def initiSettings(self):
        if self.ROOTFILE.isTOFPETdata:
            self.list_channels.clear()
            for i, ch in enumerate(self.ROOTFILE.channelIDs):
                ch_decomp = self.ROOTFILE.channelIDs_decomp[i]
                item = QListWidgetItem(f"{ch:<6} {ch_decomp}")
                # item = QListWidgetItem(f"{ch}")
                # item.setFlags(item.flags() | Qt.ItemIsUserCheckable )
                # item.setCheckState(QtCore.Qt.Unchecked)
                self.list_channels.addItem(item)

            self.cb1_variables.clear()
            if self.PLOT_MODE=="Hist":
                for key in self.ROOTFILE.barnches:
                    self.cb1_variables.addItem(key)
            elif self.PLOT_MODE=="2D":
                for i in range(len(self.ROOTFILE.barnches)):
                    for j in range(i,len(self.ROOTFILE.barnches)):
                        self.cb1_variables.addItem(self.ROOTFILE.barnches[i]+"--"+self.ROOTFILE.barnches[j]) 

            # timestamps = RootFile.read_branch(self.ROOTFILE.tree, "time")
            timestamps = self.ROOTFILE.data["time"]
            self.DURATION =  (np.max(timestamps) - np.min(timestamps))*1e-12
            self.TRIGGER_RATE = self.ROOTFILE.nevents/self.DURATION
            self.text_fileinfo.setText(f"File info:\n * Events:\t{self.ROOTFILE.nevents} \n * Duration:\t{self.DURATION:.1f} [s] \n * Trigger rate: {self.TRIGGER_RATE:.1f} [Hz]")

    def updateSettings(self):   
        # Update Information
        # try:
        if(1):
            if self.ROOTFILE is not None and self.ROOTFILE.isTOFPETdata:
                self.channels_selected = [item.text().split(" ")[0] for item in self.list_channels.selectedItems()] 
                self.variable_selected = str(self.cb1_variables.currentText())
                if len(self.variable_selected)>0 and len(self.channels_selected)>0 :
                    self.make_plots()
        # except Exception as e:
        #     print("Exception:", e)
        #     pass
            
    def set_xrange(self):
        if self.button_autox.isChecked():
            self.xrange.setReadOnly(True)
            self.xrange.setDisabled(True)
            self.XRANGE=None
            if self.ROOTFILE.isTOFPETdata:
                self.updateSettings()              
        else:            
            self.xrange.setEnabled(True)
            self.xrange.setReadOnly(False)
            xrange_content = self.xrange.text().split(",")
            if len(xrange_content)==2:
                try:
                    self.XRANGE = [float(xrange_content[0]), float(xrange_content[1])]
                    if self.ROOTFILE.isTOFPETdata:
                        self.updateSettings()                    
                except Exception as e:
                    print("Range setting error", e)





    def make_plots(self):
        # self.sc.axes.plot([0,1,2,3,4], [10,1,20,3,40])
        # print("Plot key",str(self.cb1_variables.currentText()))
        # print("Plot channels",self.channels_selected)

        if self.PLOT_MODE=="Hist":
            if self.variable_selected !="channelID":
                self.plot_hists(self.ROOTFILE.data, self.variable_selected, channels=self.channels_selected, range=self.XRANGE)
            else:
                h = MainWindow.plot_hist(self.ROOTFILE.data, self.variable_selected, bins=np.linspace(0,384, 385))    
                # current_yscale = self.sc.axes.get_yscale()
                self.sc.axes.clear()
                self.sc.axes.step(np.array(h[1][:-1]), np.array(h[0]), label=f"All channels")              
                self.sc.axes.set_xlabel("Channel ID")
                self.sc.axes.set_ylabel("Counts per channel")
                self.sc.axes.legend()
                # self.sc.axes.set_yscale(current_yscale)
                self.sc.axes.set_yscale("log")
                self.sc.axes.grid(visible=True, which="both")
                self.sc.axes.autoscale() 
                self.sc.axes.format_coord = lambda x, y: ""
                self.sc.draw()                
        elif self.PLOT_MODE=="2D": 
            pass
        return
    
    @staticmethod
    def plot_hist(data, key, channel=None, range=None, bins=100):
      
        if channel is not None:
            h = np.histogram(data[key][data["channelID"]==int(channel)], range = range, bins=bins)
        else:
            h = np.histogram(data[key],range = range, bins=bins)
        return h

    def plot_hists(self, data, key, channels=[0], range=None, bins=100):
        # Calculate histograms
        all_hists=[]
        all_x = []
        for channel in channels:
            h = MainWindow.plot_hist(data, key, channel=channel, range=range, bins=100)        
            all_hists.append(h)
            all_x.append(h[1])
        

        # Remake hist with common range    
        if range is None:
            range_common = [np.min(all_x),np.max(all_x)]
            all_hists=[]
            for channel in channels:
                h = MainWindow.plot_hist(data, key, channel=channel, range=range_common, bins=100)  
                all_hists.append(h)             

        # Make plots
        current_yscale = self.sc.axes.get_yscale()
        self.sc.axes.clear()
        for i,h in enumerate(all_hists):
            self.sc.axes.step(np.array(h[1][:-1]), np.array(h[0]), label=f"{channels[i]}")              
        self.sc.axes.set_xlabel(key)
        self.sc.axes.set_ylabel("counts")
        self.sc.axes.legend()
        self.sc.axes.grid(which="both")
        self.sc.axes.set_yscale(current_yscale)
        self.sc.axes.autoscale() 
        self.sc.axes.format_coord = lambda x, y: ""
        self.sc.draw()

    def btnstate_hist_2d(self,b):
        self.PLOT_MODE = b.text()

        try:
            self.cb1_variables.clear()
            if self.PLOT_MODE=="Hist":
                for key in self.ROOTFILE.barnches:
                    self.cb1_variables.addItem(key)
            elif self.PLOT_MODE=="2D":
                for i in range(len(self.ROOTFILE.barnches)):
                    for j in range(i,len(self.ROOTFILE.barnches)):
                        self.cb1_variables.addItem(self.ROOTFILE.barnches[i]+"--"+self.ROOTFILE.barnches[j]) 
        except:
            pass

        self.updateSettings()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('TOFPET ROOT viewer')

    main = MainWindow()
    main.resize(950, 500)
    # main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec())