# TOFPET2 helper

This repository contains helper scripts for TOFPET2 asic

## Scripts
### 1. Gui to view ROOT data



## Command line memo

### 0. Calibration

The DAQ software provides three calibrations: baseline, TDC, QDC. The latter two only needs to be done once, but baseline may change if different calbe/detectors are connected.

**Baseline** 

Here's a version that allows you trun on external HV bias.

```bash
#!/usr/bin/sh
DATA_DIR=/mnt/sda2/tofpet_data/two_preamp/
CONFIG_FILE=${DATA_DIR}/config.ini

./acquire_threshold_calibration --config ${CONFIG_FILE} -o ${DATA_DIR}/disc_calibration --ext-bias
./process_threshold_calibration --config ${CONFIG_FILE} -i  ${DATA_DIR}/disc_calibration -o ${DATA_DIR}/disc_calibration.tsv --root-file ${DATA_DIR}/disc_calibration.root

```


### 1. Acquire data

See the following example. 
* Define the working folder, output filename
* **Remember to check the mode (qdc or tot) and time**

```bash
data_folder=/mnt/sda2/tofpet_data/function_gen
data_prefix=data_test
./acquire_sipm_data --config ${data_folder}/config.ini --mode tot --time 2 -o ${data_folder}/${data_prefix} 
```

### 2. Parameter scan

See the following example. 
* Define the working folder, output filename, and scan parameter table. 
    * The parameter table is a text file with multiple columns.
* **Remember to check the mode (qdc or tot) and time** of each step (in seconds)

```bash
data_folder=/mnt/sda2/tofpet_data/two_preamp/
data_scan_prefix=data/data_scan_threshold_t1
par_table=scan_parameter_table_threshold_t1.txt

./acquire_sipm_data --config ${data_folder}/config.ini --mode tot --time 2 -o ${data_folder}/${data_scan_prefix} --param-table ${data_folder}/${par_table}
./convert_raw_to_singles --config ${data_folder}/config.ini -i ${data_folder}/${data_scan_prefix} -o ${data_folder}/${data_scan_prefix}_single.root --writeRoot
```


### 3. Trigger modes

Trigger mode is controlled by channel registers. Save the register value in config.ini and they will be updated to ASIC when taking data using the acquire_data scripts or GUI.

#### 3.1 Single threshold trigger T1
```
global.disc_lsb_t1 = [62...55]
channel.fe_delay = 16
channel.trigger_mode_2_t = 0
channel.trigger_mode_2_q = 0
channel.trigger_mode_2_e = 0
channel.trigger_mode_2_b = 0
```


#### 3.2 Dual threshold trigger T1,T2
```
global.disc_lsb_t1 = [62...55]
global.disc_lsb_t2 = 55
channel.fe_delay = 16
channel.trigger_mode_2_t = 0
channel.trigger_mode_2_q = 0
channel.trigger_mode_2_e = 1
channel.trigger_mode_2_b = 3
```

#### 3.3 Dual threshold trigger T1,E
```
global.disc_lsb_t1 = [62...55]
global.disc_lsb_e = 50
channel.fe_delay = 16
channel.trigger_mode_2_t = 0
channel.trigger_mode_2_q = 0
channel.trigger_mode_2_e = 2
channel.trigger_mode_2_b = 4
```

#### 3.4 Dual threshold trigger T1, T2 with FAST dark count rejection
```
global.disc_lsb_t1 = [62...55]
global.disc_lsb_t2 = 55
channel.fe_delay = [12...15]
channel.trigger_mode_2_t = 1
channel.trigger_mode_2_q = 1
channel.trigger_mode_2_e = 1
channel.trigger_mode_2_b = 3
```


#### 3.5 Tripple threshold trigger T1, T2, E with FAST dark count rejection
```
global.disc_lsb_t1 = [62...55]
global.disc_lsb_t2 = 55
global.disc_lsb_e = 50
channel.fe_delay = [12...15]
channel.trigger_mode_2_t = 1
channel.trigger_mode_2_q = 1
channel.trigger_mode_2_e = 2
channel.trigger_mode_2_b = 5
```



mathusla@mathusla-OptiPlex-7000:~/tofpet/sw_daq_tofpet2-2023.12.06/build$ ./acquire_sipm_data_with_monitoring --config ${data_folder}/config.ini --mode tot --time 2 -o ${data_folder}/${data_prefix} --monitor-toc=ste
INFO: active units on ports:  0
INFO: Evaluation kit: FEB/D with GBE connection @ ( 0,  0)
INFO: Setting FEM  power  ON @ (portID, slaveID) = (0,0)
INFO: FEB/D ( 0,  0) has  2 active ASICs: 4, 5
INFO: Setting BIAS power  ON @ (portID, slaveID) = (0,0)
/usr/lib/python3.10/subprocess.py:955: RuntimeWarning: line buffering (buffering=1) isn't supported in binary mode, the default buffer size will be used
  self.stdin = io.open(p2cwrite, 'wb', bufsize)
/usr/lib/python3.10/subprocess.py:961: RuntimeWarning: line buffering (buffering=1) isn't supported in binary mode, the default buffer size will be used
  self.stdout = io.open(c2pread, 'rb', bufsize)
INFO: Writing data to '/mnt/sda2/tofpet_data/function_gen/data_test.rawf' and index to '/mnt/sda2/tofpet_data/function_gen/data_test.idxf'
WARNING: time_offset_calibration_table not specified in section 'main' of '/mnt/sda2/tofpet_data/function_gen/config.ini': timestamps of different channels may present offsets
Opening '/ps_monitor' returned -1 (errno = 2)
Traceback (most recent call last):
  File "/home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build/./acquire_sipm_data_with_monitoring", line 27, in <module>
    daqd.acquire(args.time, 0, 0);
  File "/home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build/petsys/daqd.py", line 1216, in acquire
    pin.write(data); pin.flush()
BrokenPipeError: [Errno 32] Broken pipe


data_folder=/mnt/sda2/tofpet_data/function_gen
data_scan_prefix=data_scan_threshold
par_table=scan_parameter_table_threshold.txt

./acquire_sipm_data --config ${data_folder}/config.ini --mode tot --time 20 -o ${data_folder}/${data_scan_prefix} --param-table ${data_folder}/${par_table}
./convert_raw_to_singles --config ${data_folder}/config.ini -i ${data_folder}/${data_scan_prefix} -o ${data_folder}/${data_scan_prefix}_single.root --writeRoot
