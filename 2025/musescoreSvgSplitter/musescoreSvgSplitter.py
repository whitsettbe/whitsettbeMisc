"""
Get a directory from the user.
Get the svg files in said directory, convert their path data to absolute coordinates,
expand paths into discrete objects, hierarchically categorize objects into lines
of music, separate lines into part managers that rearrange and exchange lines,
and label parts with extra line numbers just in case.
Save the individual svg files and merge them into a single pdf, with blank pages
after odd-length sections to enable double-sided printing.

Benjamin Whitsett
Jan. 21, 2025
"""

import re
import os
from basicPathHandling import Path
from formatConsts import MODE_OFFSET_MASK, MODE_TO_ARGNUM
import random
from scoreBuilder import Score
from partManager import PartManager
import traceback
from tqdm import tqdm

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from pypdf import PdfWriter


TMP_SVG = os.path.join(os.path.split(__file__)[0], 'tmp.svg')
TMP_PDF = os.path.join(os.path.split(__file__)[0], 'tmp.pdf')
OUT_NAME = 'mergedParts.pdf'


# function to get part count from user if needed
knownPartNum = None
def uiPartNumGetter():
    global knownPartNum
    if knownPartNum is None:
        knownPartNum = int(input('How many parts? '))
    return knownPartNum

# get the padding rule and part managers for a specific page
def readPage(pagePath):

    with open(pagePath, 'r') as fin:
        inDat = ''.join(fin.readlines())

    # get existing paths from the file
    paths = re.findall(r'<path class.*?/>', inDat)
    startStuff = inDat[:inDat.index(paths[0])]
    endStuff = inDat[inDat.rindex(paths[-1])+len(paths[-1]):]
    padder = lambda s: '\n'.join([startStuff, s, endStuff])
    pageHeight = float(re.search(r'(?<=height=")[^"]+', startStuff).group())
    pageWidth = float(re.search(r'(?<=width=")[^"]+', startStuff).group())
    
    # split paths into distinct objects
    paths = [Path(path) for path in paths]
    objects = []
    for path in paths:
        objects += path.getObjs()

    # assemble objects into scores, then separate into parts
    score = Score(objects, uiPartNumGetter)
    managers = score.getPartManagers(pageHeight, pageWidth)
    #for m in managers:
    #    print(1 - m.occupiedTop/m.pageHeight)
    return padder, managers

# build svg parts from a nonempty ordered list of pages
#  (all pages should have the same parts)
#  (also accepts list of transpositions to include)
#  returns: for each part, a list of completed pages
def buildSvgParts(pagePaths, extras):
    
    # initialize the part managers
    print('Reading svg...')
    padders = []
    managers = []
    for path in tqdm(pagePaths):
        p,m = readPage(path)
        padders.append(p)
        managers.append(m)
        
    # add transpositions
    for src, amt in extras:
        for page in managers:
            page.append(page[src].copyTransp(amt))
        
    # allow lines to flow to earlier pages within each part
    print('Rearranging lines...')
    for partNum in range(len(managers[0])):
        for i in range(len(managers)): # page pulling lines
            j = i + 1 # page giving lines
            while j < len(managers):
                while managers[i][partNum].takeFrom(managers[j][partNum]):
                    pass
                if managers[j][partNum].numLines() > 0: # something didn't fit
                    break
                j += 1 # we exhausted the page
            managers[i][partNum].justify()
                
    # create line numbers for each page/part
    print('Creating line numbers...')
    lineNums = [] # for each part, a list of number strings for each page
    for partNum in range(len(managers[0])):
        lineNums.append([])
        startingLine = 1
        for pageNum in range(len(managers)):
            lineNums[-1].append(managers[pageNum][partNum].makeLineNums(startingLine))
            startingLine += managers[pageNum][partNum].numLines()
                
    # build part svg strings
    print('Recompiling svg...')
    out = [] # for each part, a list of completed page strings
    for partNum in range(len(managers[0])):
        out.append([])
        for pageNum in range(len(managers)):
            if managers[pageNum][partNum].numLines() > 0:
                out[-1].append(padders[pageNum](managers[pageNum][partNum].toString() \
                        + '\n' + lineNums[partNum][pageNum]))
    return out

# get music svgs from the given folder, rearrange into parts
# (sorts on only the numerical digits in the file name)
# (also accepts list of transpositions to include)
def toPartPdf(dir, extras):
    assert os.path.exists(dir)
    
    files = os.listdir(dir)
    files = [f for f in files if os.path.splitext(f)[1] == '.svg']
    files.sort(key = lambda f: int(''.join([c for c in f if c in '0123456789'])))
    files = [os.path.join(dir, f) for f in files]
    svgPartPages = buildSvgParts(files, extras)
    
    print('Writing parts to pdf...')
    merger = PdfWriter()
    for pages in tqdm(svgPartPages):
        for svg in pages:
            with open(TMP_SVG, 'w') as fout:
                fout.write(svg)
            drawing = svg2rlg(TMP_SVG)
            renderPDF.drawToFile(drawing, TMP_PDF)
            merger.append(TMP_PDF)
        if len(pages) % 2 == 1:
            merger.add_blank_page()
        
    merger.write(os.path.join(dir, OUT_NAME))
    merger.close()

if __name__ == '__main__':
    
    try:
        dirPath = input('Path to directory with svgs: ')
        doExtra = input('Include transpositions? [y/N]: ')
        extras = []
        if doExtra.lower().startswith('y'):
            extras = input('Transposition requests as (part #, how far to move notes down, repeat) [default: 1 1 1 2]: ')
            if extras == '':
                extras = '1 1 1 2'
            extras = list(map(int, extras.split()))
            extras = [(extras[i]-1, extras[i+1]) for i in range(0,len(extras),2)]
        print()
        if dirPath[0] in '"\'':
            dirPath = dirPath[1:-1]
        toPartPdf(dirPath, extras)
        input('\nConversion complete! (Note that poorly-placed ornaments can be misattributed).\nPress Enter to exit.')
    except:
        traceback.print_exc()
        input('\nThe above error occurred.\nPress Enter to exit.')
    