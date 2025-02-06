"""
Mappings from svg path mode to number of arguments and mask for true coordinates

Benjamin Whitsett
Dec. 29, 2024
"""


MODE_TO_ARGNUM = {'M':2, 'm':2, 'L':2, 'l':2, 'H':2, 'h':2, 'V':2, 'v':2, 'C':6, 'c':6, 'S':4, 's':4, 'A':7, 'a':7}
MODE_OFFSET_MASK = {'a':(0,0,0,0,0,1,1), 'A':(0,0,0,0,0,1,1)}