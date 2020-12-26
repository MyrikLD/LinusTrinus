#!/bin/bash

STEAM_PATH=~/.steam/steam

killall -9 vrcompositor vrdashboard vrmonitor "Web Thread" vrstartup
rm -f $STEAM_PATH/logs/*
