"""
PathObj stores a discrete svg object, breaking up its internal data
into individual segments of path (PathSeg).
Utilities for finding a "bounding octagon" and using this for heuristic
alignment decisions are provided. The bounding octagon is the points
in the object which have:
        min x, min x+y, min y, min y-x, max x, max x+y, max y, max y-x
(the diagonal points should be unneeded in most cases)

Benjamin Whitsett
Dec. 29, 2024
"""


from formatConsts import MODE_OFFSET_MASK, MODE_TO_ARGNUM

class PathSeg:
    def __init__(self, mode, args):
        self.mode = mode
        self.args = args
        
    def copy(self):
        return PathSeg(self.mode, [pt for pt in self.args])
    
    def vertRestrict(self, minBound, maxBound):
        toEdit = list(range(len(self.args)))
        if self.mode in MODE_OFFSET_MASK:
            toEdit = [i for i in range(len(self.args)) if MODE_OFFSET_MASK[self.mode][i]]
        for k, idx in enumerate(toEdit):
            if k%2 == 1:
                self.args[idx] = max(minBound, min(maxBound, self.args[idx]))
        
        
    def toString(self):
        return self.mode + ' ' + ' '.join(map(str, self.args))
    
    def points(self):
        pts = self.args
        if self.mode in MODE_OFFSET_MASK:
            pts = [pts[i] for i in range(len(pts)) if MODE_OFFSET_MASK[self.mode][i]]
        out = list(zip(pts[0::2], pts[1::2]))
        return out
    
    # offset this segment
    def offset(self, dx, dy):
        toEdit = list(range(len(self.args)))
        if self.mode in MODE_OFFSET_MASK:
            toEdit = [i for i in range(len(self.args)) if MODE_OFFSET_MASK[self.mode][i]]
        for k, idx in enumerate(toEdit):
            self.args[idx] += [dx,dy][k%2]

# path object from pre-sanitized svg data
class PathObj:
    def __init__(self, type, data, startPad, endPad):
        self.type = type
        self.startPad = startPad
        self.endPad = endPad
        self.octagon = None
        
        self.data = []
        i = 0
        while i < len(data):
            self.data.append(PathSeg(data[i], data[i+1:i+MODE_TO_ARGNUM[data[i]]+1]))
            i += MODE_TO_ARGNUM[data[i]] + 1
            
    def copy(self):
        newPathObj = PathObj(self.type, [], self.startPad, self.endPad)
        for pathSeg in self.data:
            newPathObj.data.append(pathSeg.copy())
        return newPathObj
    
    def vertRestrict(self, minBound, maxBound):
        for pathSeg in self.data:
            pathSeg.vertRestrict(minBound, maxBound)
    
    def toString(self):
        return self.startPad + ' ' + ' '.join([seg.toString() for seg in self.data]) + ' ' + self.endPad
    
    # construct/retreive the "bounding octagon" of this object
    def getOctagon(self):
        if self.octagon is None:
            points = []
            for pathSeg in self.data:
                points += pathSeg.points()
            
            # remove 0,0 from consideration
            
            verts = []
            for axisWeights in [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]:
                axisFn = lambda x: axisWeights[0]*x[0]+axisWeights[1]*x[1]
                m = min([axisFn(p) for p in points])
                verts.append(next(p for p in points if axisFn(p) == m))
                
            self.octagon = verts
        
        return self.octagon
    
    # is this object not-entirely-below (below = big y) another object?
    def notEntirelyBelow(self, other):
        thisOct = self.getOctagon()
        otherOct = other.getOctagon()
        thisMinY = min([pt[1] for pt in thisOct])
        otherMaxY = max([pt[1] for pt in otherOct])
        return thisMinY < otherMaxY
    
    # is this object not-entirely-above (above = small y) another object?
    def notEntirelyAbove(self, other):
        thisOct = self.getOctagon()
        otherOct = other.getOctagon()
        thisMaxY = max([pt[1] for pt in thisOct])
        otherMinY = min([pt[1] for pt in otherOct])
        return thisMaxY > otherMinY
    
    # distance defined as min euclidean between verts of bounding octagon
    def octagonDist(self, other):
        best = None
        for a in self.getOctagon():
            for b in other.getOctagon():
                d = ((a[0]-b[0])**2 + (a[1]-b[1])**2)**.5
                if best is None or d < best:
                    best = d
        return best
    
    # offset this object
    def offset(self, dx, dy):
        for seg in self.data:
            seg.offset(dx, dy)
        if self.octagon is not None:
            self.octagon = [(x+dx, y+dy) for x,y in self.octagon]