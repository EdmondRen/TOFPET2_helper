## teststand configuration

| Item | Comment |
| -------- | ------- |
| global:bars_pcb_time_offset | \[t0_1, t0_2, ..., t0_n\], time offset from the PCB trace length for each channel on the preamp.|
| assembly:reference_point | \[x0,y0,z0\], reference point of the assembly, defined as the coordinate of the SiPM on channel 1 of the assembly|
| assembly:direction | \[DIRECTION_OF_BAR, NORMAL_DIRECTION_OF_PLANE\], use +\- 1,2,3 for x,y,z|
| assembly:cable_time_offset | float, time offset of the entire assembly caused by the readout cable. Calculated from the cable length. Coax TCF-3850 has propagation delay of 1.46 ns/ft, --> 4.8 ns/m|
