#from petsys import daqd, config
from copy import deepcopy
import argparse
import math
import time
import os.path
import sys
import pandas as pd
import configparser

from PyQt6.QtGui import QPainter, QColor, QPen, QIcon

from PyQt6.QtCore import (Qt,QObject,QThread,pyqtSignal)

from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QToolBar,
    QComboBox,
    QTabWidget,
    QScrollArea,
    QScrollBar
)

from functools import partial

WINDOW_SIZE =  900
DISPLAY_HEIGHT = 200
BUTTON_SIZE = 40
ERROR_MSG = "ERROR!"

class TofpetConfigWindow(QMainWindow):


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modify DAQ Config")

        self.chanconfig_new = 0
        self.globconf_new = 0
        self.configstr = [QLineEdit("Config String (Replace)"),"",QPushButton("Set Config")]
        self.globdf = pd.read_csv('globalconfigurationmap.csv')
        self.chandf = pd.read_csv('channelconfigurationmap.csv')
        
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.globvalmap = {}
        self.chanvalmap = {}
        self.buttonslist = [QPushButton("Set Global Configuration"),QPushButton("Set Channel Configuration")]
        self.displaytext = [QLabel("Hi!"),""]

        for index, row in self.globdf.iterrows():
            self.globvalmap[row["Label"]] = [row["Default Value"],QLineEdit(row["Default Value"][2:])]
        for index, row in self.chandf.iterrows():
            self.chanvalmap[row["Label"]] = [row["Default Value"],QLineEdit(row["Default Value"][2:])]

        mainwidg = QWidget()
        layout = QVBoxLayout()
        mainwidg.setLayout(layout)
        self.setCentralWidget(mainwidg)
        
        tabs = QTabWidget()
        tabs.addTab(self.globalTabUI(), "Global Configuration")
        tabs.addTab(self.channelTabUI(), "Channel")
        layout.addWidget(self.configstr[0])
        layout.addWidget(self.configstr[2])
        layout.addWidget(tabs)
        self.connectButtons()

        scroll = QScrollArea()
        scroll.setWidget(tabs)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(550)
        layout.addWidget(scroll)
        self.displaytext[0].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.displaytext[0].setFixedHeight(DISPLAY_HEIGHT)
        layout.addWidget(self.displaytext[0])

    def globalTabUI(self):
        globalTab = QWidget()
        layout = QGridLayout()
        for index, row in self.globdf.iterrows():
            layout.addWidget(QLabel(row["Label"]),index,0)
            layout.addWidget(QLabel("Default value: " + row["Default Value"]),index,1)
            layout.addWidget(self.globvalmap[row["Label"]][1],index,2)
        layout.addWidget(self.buttonslist[0])
        self.buttonslist[0].clicked.connect(self.updateglobvar)
        globalTab.setLayout(layout)
        return globalTab
    
    def channelTabUI(self):
        channelTab = QWidget()
        layout = QGridLayout()
        for index, row, in self.chandf.iterrows():
            layout.addWidget(QLabel(row["Label"]),index,0)
            layout.addWidget(QLabel("Default value: " + row["Default Value"]),index,1)
            layout.addWidget(self.chanvalmap[row["Label"]][1],index,2)
        layout.addWidget(self.buttonslist[1])
        channelTab.setLayout(layout)
        return channelTab
    
    def updateglobvar(self):
        self.displaytext[1] = ""
        for value in self.globvalmap:
            if self.globvalmap[value][0] != ("0b" + self.globvalmap[value][1].text()):
                self.displaytext[1] = self.displaytext[1] + value + ": 0b" + self.globvalmap[value][1].text() + "\n"
                self.config["asic_parameters"]["global."+value] = str(int("0b"+self.globvalmap[value][1].text(),2))
        self.displaytext[0].setText(self.displaytext[1])

        with open(self.configstr[1], 'w') as configfile:    # save
            self.config.write(configfile)

    def updatechanvar(self):
        self.displaytext[1] = ""
        for value in self.chanvalmap:
            if self.chanvalmap[value][0] != ("0b" + self.chanvalmap[value][1].text()):
                self.displaytext[1] = self.displaytext[1] + value + ": 0b" + self.chanvalmap[value][1].text() + "\n"
                self.config["asic_parameters"]["channel."+value] = str(int("0b"+self.chanvalmap[value][1].text(),2))
        self.displaytext[0].setText(self.displaytext[1])
       
        with open(self.configstr[1], 'w') as configfile:    # save
            self.config.write(configfile)

    def setconfigfilename(self):
        self.configstr[1] = self.configstr[0].text() + ".ini"
        self.config = configparser.ConfigParser()
        self.config.read(self.configstr[1])
        self.displaytext[0].setText("Configuration File Name or Path: "+ self.configstr[1])

    def connectButtons(self):
        self.buttonslist[0].clicked.connect(self.updateglobvar)
        self.buttonslist[1].clicked.connect(self.updatechanvar)
        self.configstr[2].clicked.connect(self.setconfigfilename)


def main():
    tofpetconfigApp = QApplication([])
    tofpetconfigWindow = TofpetConfigWindow()
    tofpetconfigWindow.show()
    sys.exit(tofpetconfigApp.exec())

if __name__ == "__main__":
    main()


            

