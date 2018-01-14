# OpenVR driver

## Build for Linux

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