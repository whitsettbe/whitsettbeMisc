"""
Given a path to an SVG file, convert all path coordinates to absolute, and split objects at a pen-up motion.
Keep track of the path types from which the child objects came, for later merging.

Benjamin Whitsett
Dec. 29, 2024
"""

import re
import random
from formatConsts import MODE_OFFSET_MASK, MODE_TO_ARGNUM
from prelimHierarchy import PathObj

class Path:
    
    # build list of data coordinates
    def __init__(self, svgPath):
        dataStart = re.search(r' d="', svgPath).end()
        dataEnd = re.search(r'"/>', svgPath).start()
        self._start = svgPath[:dataStart]
        data = svgPath[dataStart:dataEnd]
        self._end = svgPath[dataEnd:]
        self.type = re.search(r'class="([a-zA-Z]+?)"', self._start).group(1)
        
        self.data = []
        for c in data:
            if re.fullmatch(r'[^0-9.]', c):
                if len(self.data) == 0 or len(self.data[-1]) > 0:
                    self.data.append('')
                if c not in '- ':
                    self.data[-1] = c
                    self.data.append('')
                elif c == '-':
                    self.data[-1] += c
            else:
                self.data[-1] += c
        
        i = 0
        while i < len(self.data):
            if self.data[i].isalpha():
                i += 1
                continue
            
            while self.data[i].count('.') > 1: # split run-on numbers
                breakPt = self.data[i].rfind('.')
                self.data.insert(i+1,self.data[i][breakPt:])
                self.data[i] = self.data[i][:breakPt]
                
            while len(self.data[i]) > 1 and self.data[i][0] == '0': # separate 0-flags
                self.data[i] = self.data[i][1:]
                self.data.insert(i, 0)
                i += 1
            self.data[i] = float(self.data[i]) if '.' in self.data[i] else int(self.data[i])
            i += 1
            
        self.toAbsolute()
            
    def toAbsolute(self):
        idx = 0
        mode = None
        x = 0
        y = 0
        while idx < len(self.data):
            # guarantee we are at the index after a mode label
            if type(self.data[idx]) == str:
                mode = self.data[idx]
                modeLoc = idx
                
                # re-mark horizontal/vertical as lineto,
                #  and lowercase as uppercase
                if mode in 'hvHV':
                    self.data[idx] = 'L'
                elif mode.islower():
                    self.data[idx] = mode.upper()
            else:
                self.data.insert(idx, self.data[modeLoc])# copy the previous mode label
            idx += 1
                
            
            # expand h,v,H,V into l,L
            if mode == 'h':
                self.data.insert(idx+1,0)
            elif mode == 'v':
                self.data.insert(idx,0)
            elif mode == 'H':
                self.data.insert(idx+1,y)
            elif mode == 'V':
                self.data.insert(idx,x)
                
            # extract any 1-flags from a,A
            #  proper format: rx ry xrot largeFlag sweepFlag x y
            if mode in 'aA':
                if self.data[idx+3] != 0:
                    mixedValue = str(self.data[idx+3])
                    if len(mixedValue) > 1: #1 AND something else
                        self.data[idx+3] = float(mixedValue[1:]) if '.' in mixedValue else int(mixedValue[1:]) # remove the leading 1
                        self.data.insert(idx+3, 1)
                if self.data[idx+4] != 0:
                    mixedValue = str(self.data[idx+4])
                    if len(mixedValue) > 1: #1 AND something else
                        self.data[idx+4] = float(mixedValue[1:]) if '.' in mixedValue else int(mixedValue[1:]) # remove the leading 1
                        self.data.insert(idx+4, 1)
                
            #  convert relative coords to absolute coords
            if mode not in MODE_TO_ARGNUM:
                raise KeyError(f'{mode} is not yet supported in MODE_TO_ARGNUM')
            if mode.islower():
                if mode not in MODE_OFFSET_MASK:
                    #printMODE_TO_ARGNUM[mode])
                    for i in range(0, MODE_TO_ARGNUM[mode],2):
                        self.data[idx+i] += x
                        self.data[idx+i+1] += y
                else:
                    locs = [i for i in range(MODE_TO_ARGNUM[mode]) if MODE_OFFSET_MASK[mode][i]]
                    for ii,l in enumerate(locs): # assume offsettable coords are still x-y alternating
                        #print(l, self.data[idx+l], ii)
                        self.data[idx+l] += (x if ii % 2 == 0 else y)
            
            # get ready for next coordinates (update base x and y)
            idx += MODE_TO_ARGNUM[mode]
            x = self.data[idx-2]
            y = self.data[idx-1]
            
    def toString(self):
        return self._start + ' '.join(map(str, self.data)) + self._end
    
    def getObjs(self):
        objectDatasets = [[]]
        pastPts = []
        for i in range(len(self.data)):
            if type(self.data[i]) == str and i >= 2:
                pastPts.append(self.data[i-2:i])
                
            # move (aka pen-up motion)
            if self.data[i] == 'M' and len(pastPts) != 0: # and not pointInside(self.data[i+1:i+3], pastPts):
                objectDatasets.append([])
                pastPts = []
            objectDatasets[-1].append(self.data[i])
            
        return [PathObj(self.type, obDat, self._start, self._end) for obDat in objectDatasets]