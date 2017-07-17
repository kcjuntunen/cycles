#!/bin/env bash

cd /tmp
git clone https://github.com/kcjuntunen/cycles
cd cycles
python3 ./setup.py install
systemctl restart cycles

