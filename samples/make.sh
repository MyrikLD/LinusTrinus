#!/bin/bash

STEAM_PATH=~/.steam/steam
STEAMVR_PATH=$STEAM_PATH/steamapps/common/SteamVR

if ((1<<32)); then
  ARCH_TARGET=linux64
else
  ARCH_TARGET=linux32
fi

# Compile
cmake . -DCMAKE_PREFIX_PATH=/opt/Qt/5.6/gcc_64/lib/cmake -DCMAKE_BUILD_TYPE=Release
make -j4

# Install
rm -rf ~/.steam/steam/steamapps/common/SteamVR/drivers/sample
cp -r ./bin/drivers/sample $STEAMVR_PATH/drivers/sample
mkdir $STEAMVR_PATH/drivers/sample/bin/${ARCH_TARGET}
cp -r ./bin/${ARCH_TARGET} $STEAMVR_PATH/drivers/sample/bin/${ARCH_TARGET}

# Cleanup
rm CMakeCache.txt cmake_install.cmake Makefile
rm driver_sample/cmake_install.cmake driver_sample/Makefile 
rm -rf CMakeFiles
rm -rf driver_sample/CMakeFiles driver_sample/driver_sample_autogen
rm -rf ./bin/${ARCH_TARGET}

# Cleanup steam logs
rm $STEAM_PATH/logs/*
