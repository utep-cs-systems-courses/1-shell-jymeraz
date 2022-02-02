#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys

while (True):
    path = os.getcwd()
    val = input(f'{path} $ ').split()
    
    # exit [n] command
    if val == None or len(val) == 0:
        continue
    if val[0] == "exit":
        if len(val) > 1:
            print("Program terminated with exit code", val[1])
            sys.exit(int(val[1]))
        print("exit")
        sys.exit(0)
    
    # cs <dir> command
    if val[0] == "cd": 
        if len(val) > 1:
            try:
                os.chdir(val[1])
            except:
                print(f'{val[0]}: no such file or directory: {val[1]}')
        else:
            os.chdir(os.path.expanduser("~"))
    
        
        
        
        
        
        