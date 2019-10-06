# OpenVR driver

## Build for Linux

Download header file from openvr 1.5.17 and copy them to the driver_sample folder before compiling 

Generate the CMake cache using Makefile:
```
cmake . -G Makefile -DCMAKE_PREFIX_PATH=/opt/Qt/5.6/gcc_64/lib/cmake -DCMAKE_BUILD_TYPE=Release
```

To build type:
```
make -j4
```

Or simply run bash script from this directory:
```
bash make.sh
```
