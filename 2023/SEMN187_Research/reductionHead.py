import os
import re

NUMRUN = 100
NUMCONF = 81

files = os.listdir('.\\data')
files.sort()
splitFiles = ['_'.join(files[i].split('_')[:-1]) for i in range(0, NUMCONF*NUMRUN, NUMRUN)]

for file in splitFiles:
    os.system("start .\dataReduce.exe " + file)
os.system('taskmgr')
