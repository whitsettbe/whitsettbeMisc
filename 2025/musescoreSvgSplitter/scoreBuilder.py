"""
Assuming 5-line musical staves, use heuristic decisions to allocate objects
into separate lines of the sheet music. These rules may need to be expanded
if new musescore path classes are encountered. The divided score can be
exported as PartManagers.

Benjamin Whitsett
Jan. 30, 2025
"""

from prelimHierarchy import PathObj, PathSeg
from partManager import PartManager

STAFF = 'StaffLines'
DUMMY = 'dummy'
LINES_PER_STAFF = 5
LEAVE_ALONE = ['Text', 'Page'] # don't modify these
SKIP = [] # don't include these in the result
ASSOC_RULE = {
    'MeasureNumber': 'all',
    'InstrumentName': 'near',
    'TieSegment': 'near Note',
    'BarLine': 'all_',
    'Accidental': 'near Note',
    'LedgerLine': 'near Stem',
    'Stem': 'near',
    'Note': 'near Stem',
    'Clef': 'near',
    'KeySig': 'near',
    'TimeSig': 'near',
    'Rest': 'near',
    'Articulation': 'near Note',
    'Dynamic': 'up',
    'Beam': 'near Stem',
    'Tempo': 'all',
    'StaffText': 'down',
    'NoteDot': 'near Note',
    'SlurSegment': 'near Note',
    'Tuplet': 'near Stem',
    'HairpinSegment': 'up',
    'Bracket': 'all_',
    'Hook': 'near Note',
    'TrillSegment': 'near Note',
    'Tremolo': 'near Stem',
    'StemSlash': 'near Stem',
    'Fermata': 'down',
    'SystemText': 'all',
    'GlissandoSegment': 'near Note',
    'Marker': 'down',
    'Jump': 'down',
    'GradualTempoChangeSegment': 'all',
    'OttavaSegment': 'down',
    'RehearsalMark': 'all',
    'Breath': 'down',
    'VoltaSegment': 'all',
    DUMMY: 'near',        # if "down" or "up" fails, replaced with this temporarily
}
# all - assoc with every part in the nearest block
# all_ - assoc with every part in the nearest block AND restrict the copies to staff-height
# near - the one with min bounding octagon separation from [insert type]
# up - first one not entirely below it (from the bottom)
# down - first one not entirely above it (from the top)
for type in ASSOC_RULE:
    if ASSOC_RULE[type] == 'near':
        ASSOC_RULE[type] += ' ' + STAFF
        

# distance of object from vertical interval: find midpoint of top and bottom of object,
#  give dist to nearest boundary if outside the interval, 0 if inside
def objDistFromVertInterval(ob, low, high):
    y = (ob.getOctagon()[2][1] + ob.getOctagon()[6][1]) / 2
    return 0 if low <= y <= high else min(abs(y-low), abs(y-high))

# object to group staff lines and other objects
class Score:
    
    def __init__(self, objs : list[PathObj], uiPartGetter):
        # instantiates the following object properties
        # objsByType, width, lineGap, numParts, numGroups, groupings, uppers, lowers
        
        # error if unknown type
        # build objs by type
        self.objsByType = {t:[] for t in [STAFF, *LEAVE_ALONE, *ASSOC_RULE.keys()]}
        self.width = 0
        badTypes = set()
        for ob in objs:
            if ob.type not in [STAFF, *LEAVE_ALONE, *ASSOC_RULE.keys(), *SKIP]:
                badTypes.add(ob.type)
            elif ob.type in SKIP:
                continue
            else:
                self.objsByType[ob.type].append(ob)
                self.width = max(self.width, ob.getOctagon()[4][0]) # compute max x
        if badTypes:
            for t in badTypes:
                print(f'Type {t} not recognized.')
            raise Exception()
        
        # find staff lines (assumes there are at least two, none at top)
        # learn about y-gaps
        self.objsByType[STAFF].sort(key=lambda ob: ob.getOctagon()[0][1]) # increasing y
        assert len(self.objsByType[STAFF]) % LINES_PER_STAFF == 0
        self.lineGap = self.objsByType[STAFF][1].getOctagon()[0][1] - self.objsByType[STAFF][0].getOctagon()[0][1]
        
        # use measure numbers to find number of parts
        if self.objsByType['MeasureNumber']:
            self.objsByType['MeasureNumber'].sort(key=lambda ob: ob.getOctagon()[6][1])
            self.numParts = sum([1 for ob in self.objsByType[STAFF]
                                if ob.notEntirelyAbove(self.objsByType['MeasureNumber'][-1])]) // LINES_PER_STAFF
        else:
            self.numParts = uiPartGetter()
        assert len(self.objsByType[STAFF]) % self.numParts == 0
        self.numGroups = len(self.objsByType[STAFF]) // LINES_PER_STAFF // self.numParts
        
        # start grouping staff lines together
        # CONVENTION: "uppers" have greater y than "lowers", which actually makes them
        # appear lower on the page.
        self.groupings = [[self.objsByType[STAFF][LINES_PER_STAFF*(p+self.numParts*g) : LINES_PER_STAFF*(p+1+self.numParts*g)]
                                for p in range(self.numParts)] for g in range(self.numGroups)]
        self.uppers = [[self.groupings[g][p][-1].getOctagon()[0][1]
                                for p in range(self.numParts)] for g in range(self.numGroups)]
        self.lowers = [[self.groupings[g][p][0].getOctagon()[0][1]
                                for p in range(self.numParts)] for g in range(self.numGroups)]
        
        # handle "down" and "up" types (no relation to barriers)
        for type in ASSOC_RULE:
            rule = ASSOC_RULE[type]
            if rule == 'down': # assoc w/ first from top not entirely above
                for ob in self.objsByType[type][::-1]:
                    try:
                        matchIdx = next(i for i,s in enumerate(self.objsByType[STAFF])
                                        if s.notEntirelyAbove(ob))
                    except: # if can't go down, default to near
                        ob.type = DUMMY
                        self.objsByType[type].remove(ob)
                        self.objsByType[DUMMY].append(ob)
                        continue
                    self.groupings[matchIdx//LINES_PER_STAFF//self.numParts] \
                            [matchIdx//LINES_PER_STAFF%self.numParts].append(ob)
                            
            elif rule == 'up': # assoc w/ first from bottom not entirely below
                for ob in self.objsByType[type][::-1]:
                    try:
                        matchIdx = next(i for i,s in list(enumerate(self.objsByType[STAFF]))[::-1]
                                        if s.notEntirelyBelow(ob))
                    except: # if can't go up, default to near
                        ob.type = DUMMY
                        self.objsByType[type].remove(ob)
                        self.objsByType[DUMMY].append(ob)
                        continue
                    self.groupings[matchIdx//LINES_PER_STAFF//self.numParts] \
                            [matchIdx//LINES_PER_STAFF%self.numParts].append(ob)
        
        # handle "all_" types - like "all" but vertically restricted
        for type in ASSOC_RULE:
            rule = ASSOC_RULE[type]
            if rule == 'all_': # assoc w/ all parts in the nearest group, but restrict to staff height
                for ob in self.objsByType[type]:
                    # loop possible barriers
                    bestGroup = None
                    bestDist = None
                    for g in range(self.numGroups):
                        for p in range(self.numParts):
                            d = objDistFromVertInterval(ob, self.lowers[g][p], self.uppers[g][p])
                            if bestGroup is None or d < bestDist:
                                bestGroup = g
                                bestDist = d
                    
                    # identify copies with parts in the best group, and vertically restrict them
                    for p in range(self.numParts):
                        self.groupings[bestGroup][p].append(ob.copy())
                        self.groupings[bestGroup][p][-1].vertRestrict(self.lowers[bestGroup][p], self.uppers[bestGroup][p])
        
        # prep the order for "near" types
        followedBy = {key:[] for key in ASSOC_RULE}
        followedBy[STAFF] = []
        for type in ASSOC_RULE:
            rule = ASSOC_RULE[type]
            if rule.startswith('near'):
                followedBy[rule.split()[1]].append(type)
        nearOrder = [STAFF]
        i = 0
        while i < len(nearOrder):
            nearOrder += followedBy[nearOrder[i]]
            i += 1
        nearOrder = nearOrder[1:]
        
        # process the "near" types
        for type in nearOrder:
            for ob in self.objsByType[type]:
                
                # loop possible barriers
                bestGroup = None
                bestPart = None
                bestDist = None
                for g in range(self.numGroups):
                    for p in range(self.numParts):
                        d = objDistFromVertInterval(ob, self.lowers[g][p], self.uppers[g][p])
                        if bestGroup is None or d < bestDist:
                            bestGroup = g
                            bestPart = p
                            bestDist = d
                    
                # identify with the best part
                self.groupings[bestGroup][bestPart].append(ob)
                self.uppers[bestGroup][bestPart] = max(self.uppers[bestGroup][bestPart], ob.getOctagon()[6][1])
                self.lowers[bestGroup][bestPart] = min(self.lowers[bestGroup][bestPart], ob.getOctagon()[2][1])
        
        # handle "all" types
        for type in ASSOC_RULE:
            rule = ASSOC_RULE[type]
            if rule == 'all': # assoc w/ all parts in the nearest group
                for ob in self.objsByType[type]:
                    # loop possible barriers
                    bestGroup = None
                    bestDist = None
                    for g in range(self.numGroups):
                        for p in range(self.numParts):
                            d = objDistFromVertInterval(ob, self.lowers[g][p], self.uppers[g][p])
                            if bestGroup is None or d < bestDist:
                                bestGroup = g
                                bestDist = d
                    
                    # identify copies with parts in the best group
                    for p in range(self.numParts):
                        self.groupings[bestGroup][p].append(ob.copy())
    
    # get the string of all objects not belonging to a part
    def getSuppString(self):
        # collect segments from objects with the same padding (helps with fill rules)
        out = ''
        currentSegs = []
        currentPadding = (None, None)
        for type in LEAVE_ALONE:
            for ob in self.objsByType[type]:
                if currentPadding != (ob.startPad, ob.endPad):
                    if currentPadding != (None, None):
                        out += currentPadding[0] + ' ' + ' '.join([seg.toString() for seg in currentSegs]) + ' ' + currentPadding[1] + '\n'
                    currentPadding = (ob.startPad, ob.endPad)
                    currentSegs = []
                currentSegs += ob.data
        out += currentPadding[0] + ' ' + ' '.join([seg.toString() for seg in currentSegs]) + ' ' + currentPadding[1] + '\n'
        return out
    
    # get the string of all objects in specified part
    def getPartString(self, g, p):
        # collect segments from objects with the same padding (helps with fill rules)
        out = ''
        currentSegs = []
        currentPadding = (None, None)
        for ob in self.groupings[g][p]:
            if currentPadding != (ob.startPad, ob.endPad):
                if currentPadding != (None, None):
                    out += currentPadding[0] + ' ' + ' '.join([seg.toString() for seg in currentSegs]) + ' ' + currentPadding[1] + '\n'
                currentPadding = (ob.startPad, ob.endPad)
                currentSegs = []
            currentSegs += ob.data
        out += currentPadding[0] + ' ' + ' '.join([seg.toString() for seg in currentSegs]) + ' ' + currentPadding[1] + '\n'
        return out
    
    # get the PartManager objects for parts on this page
    # (needs to know pageheight to help managers calibrate)
    def getPartManagers(self, pageHeight, pageWidth):
        # find page info objects
        pageInfo = []
        for type in LEAVE_ALONE:
            pageInfo += self.objsByType[type]
        
        # build part managers
        out = []
        for p in range(self.numParts):
            internals = []
            externals = [] # stuff that might need to be realigned with the lines
            ymins = []
            ymaxes = []
            for g in range(self.numGroups):
                internals.append([])
                externals.append([])
                ymins.append(self.lowers[g][p])
                ymaxes.append(self.uppers[g][p])
                for ob in self.groupings[g][p]:
                    if ob.type in ASSOC_RULE and ASSOC_RULE[ob.type] == 'all': # these might need to be realigned
                        externals[-1].append(ob)
                    else:
                        internals[-1].append(ob)
                        ymins[-1] = min(ymins[-1], ob.getOctagon()[2][1])
                        ymaxes[-1] = max(ymaxes[-1], ob.getOctagon()[6][1])
            out.append(PartManager(internals, externals, ymins, ymaxes, pageInfo, self.lineGap, pageHeight, pageWidth))
        return out