#!/usr/bin/env bash
python3 solver/generator.py config.yml platform.xml
python3 solver/scheduler.py config.yml