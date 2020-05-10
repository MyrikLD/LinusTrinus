#!/bin/bash

if ((1 << 32)); then
  ARCH_TARGET=linux64
else
  ARCH_TARGET=linux32
fi

# Compile
cmake . -DCMAKE_PREFIX_PATH=/opt/Qt/5.6/gcc_64/lib/cmake -DCMAKE_BUILD_TYPE=Release
make -j4

STEAM_PATH=~/.steam/steam
STEAMVR_PATH=$STEAM_PATH/steamapps/common/SteamVR
DRIVER_NAME=linus_trinus

# Install
rm -rf $STEAMVR_PATH/drivers/$DRIVER_NAME
cp -r ./bin/drivers/$DRIVER_NAME $STEAMVR_PATH/drivers/
mkdir $STEAMVR_PATH/drivers/$DRIVER_NAME/bin/
cp -r ./bin/${ARCH_TARGET} $STEAMVR_PATH/drivers/$DRIVER_NAME/bin/

# Cleanup
rm CMakeCache.txt cmake_install.cmake Makefile
rm driver_$DRIVER_NAME/cmake_install.cmake driver_$DRIVER_NAME/Makefile
rm -rf CMakeFiles
rm -rf driver_$DRIVER_NAME/CMakeFiles driver_$DRIVER_NAME/*_autogen
rm -rf ./bin/${ARCH_TARGET}
