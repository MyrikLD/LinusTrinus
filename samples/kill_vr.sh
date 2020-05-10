#!/bin/bash

STEAM_PATH=~/.steam/steam

killall -9 vrcompositor vrdashboard vrmonitor "Web Thread"
rm -f $STEAM_PATH/logs/*
