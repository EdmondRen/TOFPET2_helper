# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.22

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Disable VCS-based implicit rules.
% : %,v

# Disable VCS-based implicit rules.
% : RCS/%

# Disable VCS-based implicit rules.
% : RCS/%,v

# Disable VCS-based implicit rules.
% : SCCS/s.%

# Disable VCS-based implicit rules.
% : s.%

.SUFFIXES: .hpux_make_needs_suffix_list

# Command-line flag to silence nested $(MAKE).
$(VERBOSE)MAKESILENT = -s

#Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E rm -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build

# Include any dependencies generated for this target.
include CMakeFiles/convert_raw_to_raw.dir/depend.make
# Include any dependencies generated by the compiler for this target.
include CMakeFiles/convert_raw_to_raw.dir/compiler_depend.make

# Include the progress variables for this target.
include CMakeFiles/convert_raw_to_raw.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/convert_raw_to_raw.dir/flags.make

CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o: CMakeFiles/convert_raw_to_raw.dir/flags.make
CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o: ../src/petsys_util/convert_raw_to_raw.cpp
CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o: CMakeFiles/convert_raw_to_raw.dir/compiler_depend.ts
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -MD -MT CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o -MF CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o.d -o CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o -c /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/src/petsys_util/convert_raw_to_raw.cpp

CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.i"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/src/petsys_util/convert_raw_to_raw.cpp > CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.i

CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.s"
	/usr/bin/c++ $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/src/petsys_util/convert_raw_to_raw.cpp -o CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.s

# Object files for target convert_raw_to_raw
convert_raw_to_raw_OBJECTS = \
"CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o"

# External object files for target convert_raw_to_raw
convert_raw_to_raw_EXTERNAL_OBJECTS =

convert_raw_to_raw: CMakeFiles/convert_raw_to_raw.dir/src/petsys_util/convert_raw_to_raw.cpp.o
convert_raw_to_raw: CMakeFiles/convert_raw_to_raw.dir/build.make
convert_raw_to_raw: /usr/lib/x86_64-linux-gnu/libpython3.10.so
convert_raw_to_raw: /usr/lib/x86_64-linux-gnu/libpython3.10.so
convert_raw_to_raw: libcommon.a
convert_raw_to_raw: /usr/lib/x86_64-linux-gnu/libboost_python310.so.1.74.0
convert_raw_to_raw: /usr/lib/x86_64-linux-gnu/libboost_regex.so.1.74.0
convert_raw_to_raw: /usr/lib/x86_64-linux-gnu/libpython3.10.so
convert_raw_to_raw: /usr/lib/x86_64-linux-gnu/libpython3.10.so
convert_raw_to_raw: CMakeFiles/convert_raw_to_raw.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable convert_raw_to_raw"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/convert_raw_to_raw.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/convert_raw_to_raw.dir/build: convert_raw_to_raw
.PHONY : CMakeFiles/convert_raw_to_raw.dir/build

CMakeFiles/convert_raw_to_raw.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/convert_raw_to_raw.dir/cmake_clean.cmake
.PHONY : CMakeFiles/convert_raw_to_raw.dir/clean

CMakeFiles/convert_raw_to_raw.dir/depend:
	cd /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06 /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06 /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build /home/mathusla/tofpet/sw_daq_tofpet2-2023.12.06/build/CMakeFiles/convert_raw_to_raw.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/convert_raw_to_raw.dir/depend
