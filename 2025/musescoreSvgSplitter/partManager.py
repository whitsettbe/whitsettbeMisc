"""
Represent a page of a part of music, moving the lines around and taking lines from
subsequent pages until full.

Benjamin Whitsett
Jan. 30, 2025
"""

from prelimHierarchy import PathObj
import warnings

# Gap sizes, in units of [vertical space between lines on a staff]
SMALL_GAP_FACTOR = 0.5 # space between line and associated external objects
MED_GAP_FACTOR = 2 # space between music lines
BIG_GAP_FACTOR = 3 # space at the bottom and top

# Which types to transpose when doing a transposition,
# and which types to skip
TO_TRANSP = ['StaffLines', 'LedgerLine', 'BarLine', 'TimeSig', 'Rest', 'Bracket']
SKIP_IN_TRANSP = ['Fingering']

class PartManager:
    
    # internalObjs: list of pathobjs in the bounds of each line
    # externalObjs: list of pathobjs associated to each line
    # ymins: bounding ymin for each line
    # ymaxes: bounding ymax for each line
    # pageInfo: pathobjs associated to the page
    # staffLineGap: distance between lines on a single staff, used to calibrate spacing
    # (assumes lines given sequentially)
    def __init__(self, internalObjs : list[list[PathObj]], externalObjs : list[list[PathObj]],
                 ymins : list[float], ymaxes: list[float], pageInfo: list[PathObj],
                 staffLineGap : float, pageHeight : float, pageWidth : float, doCleanup = True):
        self.internalObjs = internalObjs
        self.externalObjs = externalObjs
        self.ymins = ymins
        self.ymaxes = ymaxes
        self.pageInfo = pageInfo
        self.staffLineGap = staffLineGap
        self.occupiedTop = None
        self.pageHeight = pageHeight
        self.pageWidth = pageWidth
        if doCleanup:
            self.cleanup()
        
    def numLines(self):
        return len(self.internalObjs)
        
    # Collect objects affiliated with each line, and move lines to the top of the page
    def cleanup(self):
        for idx in range(len(self.internalObjs)):
            
            # include overlapping externals
            anyOverlap = True
            while anyOverlap:
                anyOverlap = False
                shouldDelete = []
                for ext in self.externalObjs[idx]:
                    octagon = ext.getOctagon()
                    if any([self.ymins[idx] <= y <= self.ymaxes[idx] for x,y in octagon]):
                        self.internalObjs[idx].append(ext)
                        self.ymins[idx] = min(self.ymins[idx], min([y for x,y in octagon]))
                        self.ymaxes[idx] = max(self.ymaxes[idx], max([y for x,y in octagon]))
                        anyOverlap = True
                        shouldDelete.append(True)
                    else:
                        shouldDelete.append(False)
                self.externalObjs[idx] = [ext for ext,d in zip(self.externalObjs[idx], shouldDelete) if not d]
                        
            # move inward the externals of small y
            maxSmallY = None
            for ext in self.externalObjs[idx]:
                maxY = ext.getOctagon()[6][1]
                if maxY < self.ymins[idx] and (maxSmallY is None or maxY > maxSmallY):
                    maxSmallY = maxY
            if maxSmallY is not None:
                shouldDelete = []
                for ext in self.externalObjs[idx]:
                    if ext.getOctagon()[6][1] < self.ymins[idx]:
                        ext.offset(0, self.ymins[idx] - maxSmallY - self.staffLineGap * SMALL_GAP_FACTOR)
                        self.internalObjs[idx].append(ext)
                        shouldDelete.append(True)
                    else:
                        shouldDelete.append(False)
                    self.externalObjs[idx] = [ext for ext,d in zip(self.externalObjs[idx], shouldDelete) if not d]
                        
            # move inward the externals of large y
            minBigY = None
            for ext in self.externalObjs[idx]:
                minY = ext.getOctagon()[2][1]
                if minY > self.ymaxes[idx] and (minBigY is None or minY < minBigY):
                    minBigY = minY
            if minBigY is not None:
                shouldDelete = []
                for ext in self.externalObjs[idx]:
                    if ext.getOctagon()[2][1] > self.ymaxes[idx]:
                        ext.offset(0, self.ymaxes[idx] - minBigY + self.staffLineGap * SMALL_GAP_FACTOR)
                        self.internalObjs[idx].append(ext)
                        shouldDelete.append(True)
                    else:
                        shouldDelete.append(False)
                    self.externalObjs[idx] = [ext for ext,d in zip(self.externalObjs[idx], shouldDelete) if not d]
                    
            # update the bounds
            self.ymins[idx] = min([ob.getOctagon()[2][1] for ob in self.internalObjs[idx]])
            self.ymaxes[idx] = max([ob.getOctagon()[6][1] for ob in self.internalObjs[idx]])
            
        # measure space occupied above the top line of music
        occupiedTop = self.staffLineGap * BIG_GAP_FACTOR # margin padding
        for ob in self.pageInfo:
            if ob.getOctagon()[6][1] < self.ymins[0]:
                occupiedTop = max(occupiedTop, ob.getOctagon()[6][1])
        
        # move up the music lines
        for idx in range(len(self.internalObjs)):
            for ob in self.internalObjs[idx]:
                ob.offset(0, occupiedTop - self.ymins[idx] + self.staffLineGap * MED_GAP_FACTOR)
            self.ymaxes[idx] += occupiedTop - self.ymins[idx] + self.staffLineGap * MED_GAP_FACTOR
            self.ymins[idx] = occupiedTop + self.staffLineGap * MED_GAP_FACTOR
            occupiedTop = self.ymaxes[idx]
            
        self.occupiedTop = occupiedTop
        
    # take the first line from another PartManager (page) if there is space for it
    def takeFrom(self, other):
        # check if this will fit
        if other.numLines() == 0 or self.staffLineGap * MED_GAP_FACTOR + other.ymaxes[0] - other.ymins[0] \
                > self.pageHeight - self.occupiedTop - self.staffLineGap * BIG_GAP_FACTOR:
            return False
        
        # move up secondary lines in the other
        vertShift = other.ymins[0] - other.ymaxes[0] - other.staffLineGap * MED_GAP_FACTOR
        for idx in range(1, other.numLines()):
            for ob in other.internalObjs[idx]:
                ob.offset(0, vertShift)
            other.ymaxes[idx] += vertShift
            other.ymins[idx] += vertShift
        other.occupiedTop += vertShift
        
        # take the line
        self.internalObjs.append(other.internalObjs.pop(0))
        self.externalObjs.append(other.externalObjs.pop(0))
        self.ymins.append(other.ymins.pop(0))
        self.ymaxes.append(other.ymaxes.pop(0))
        
        # put the new line in place
        for ob in self.internalObjs[-1]:
            ob.offset(0, self.occupiedTop - self.ymins[-1] + self.staffLineGap * MED_GAP_FACTOR)
        self.ymaxes[-1] += self.occupiedTop - self.ymins[-1] + self.staffLineGap * MED_GAP_FACTOR
        self.ymins[-1] = self.occupiedTop + self.staffLineGap * MED_GAP_FACTOR
        self.occupiedTop = self.ymaxes[-1]
        return True
    
    # right-align all lines on this page (internal objects only - assumes external objs have already been absorbed)
    # and make sure the margins are of similar size
    def justify(self):
        if self.numLines() == 0:
            return
        
        # find the rightmost point in any line
        rightmost = max([max([ob.getOctagon()[4][0] for ob in lineObs]) for lineObs in self.internalObjs])
        
        # shift all lines to agree on their rightmost point
        for lineObs in self.internalObjs:
            horShift = rightmost - max([ob.getOctagon()[4][0] for ob in lineObs])
            for ob in lineObs:
                ob.offset(horShift, 0)
                
        # find the leftmost point in any line
        leftmost = min([min([ob.getOctagon()[0][0] for ob in lineObs]) for lineObs in self.internalObjs])
        
        # shift all lines so the margins are the same size
        horShift = ((self.pageWidth - rightmost) - leftmost) / 2
        for lineObs in self.internalObjs:
            for ob in lineObs:
                ob.offset(horShift, 0)
        
    # create line number svgs corresponding to the current lines
    def makeLineNums(self, offset):
        if self.numLines() == 0:
            return ''
        
        # find the x-coord defining the right margin
        margin = max([max([ob.getOctagon()[4][0] for ob in lineObs]) for lineObs in self.internalObjs])
        
        # build the text labels
        out = []
        for idx in range(self.numLines()):
            x = margin + (self.pageWidth - margin) / 4
            y = (self.ymaxes[idx] + self.ymins[idx]) / 2
            fontsize = (self.pageWidth - margin) / 3
            textlen = (self.pageWidth - margin) / 2 * len(str(idx+offset)) / 3
            out.append(f'<text x="{x}" y="{y}" alignment-baseline="middle" font-family="monospace"' \
                + f' font-size="{fontsize}px" textLength="{textlen}px" lengthAdjust="spacingAndGlyphs">' \
                + f'{idx + offset}</text>')
        return '\n'.join(out)
            
    # get the string of the page, merging segments from objects with the same padding (helps with fill rules)
    def toString(self):
        # collect all objects
        allObjs = []
        allObjs.extend(self.pageInfo)
        for idx in range(len(self.internalObjs)):
            allObjs.extend(self.internalObjs[idx])
            allObjs.extend(self.externalObjs[idx])
            if self.externalObjs[idx]:
                warnings.warn(f'Compiling line {idx}, which is not fully aligned.')
        
        # merge segments as appropriate
        out = ''
        currentSegs = []
        currentPadding = (None, None)
        for ob in allObjs:
            if currentPadding != (ob.startPad, ob.endPad):
                if currentPadding != (None, None):
                    out += currentPadding[0] + ' ' + ' '.join([seg.toString() for seg in currentSegs]) + ' ' + currentPadding[1] + '\n'
                currentPadding = (ob.startPad, ob.endPad)
                currentSegs = []
            currentSegs += ob.data
        out += currentPadding[0] + ' ' + ' '.join([seg.toString() for seg in currentSegs]) + ' ' + currentPadding[1] + '\n'
        return out
    
    # create a transposed copy of this part manager (move lines up by offset/2 line-gaps)
    def copyTransp(self, offset):
        # perform deep copy of this PM's data
        newPM = PartManager([[ob.copy() for ob in row if ob.type not in SKIP_IN_TRANSP] for row in self.internalObjs],
                [[ob.copy() for ob in row if ob.type not in SKIP_IN_TRANSP] for row in self.externalObjs],
                self.ymins.copy(), self.ymaxes.copy(), [ob.copy() for ob in self.pageInfo],
                self.staffLineGap, self.pageHeight, self.pageWidth, doCleanup = False)
        newPM.occupiedTop = self.occupiedTop
        
        # transpose relevant internal objects
        for row in newPM.internalObjs:
            for ob in row:
                if ob.type in TO_TRANSP:
                    ob.offset(0, -newPM.staffLineGap/2 * offset)
        return newPM