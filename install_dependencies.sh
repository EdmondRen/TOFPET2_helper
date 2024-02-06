sudo apt-get install libxcb-cursor0 python-is-python3 virtualenv
virtualenv --system-site-packages ../venv
source ../venv/bin/activate
pip install pyqt6 opencv-python-headless uproot numpy scipy matplotlib ipython jupyter
