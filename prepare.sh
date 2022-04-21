#!/usr/bin/env bash
log_dir=$1
mkdir -p ${log_dir}
cp build/insitu-ensemble-simulator ${log_dir}
cp solver/generator.py ${log_dir}
cp solver/scheduler.py ${log_dir}
cp run.sh ${log_dir}