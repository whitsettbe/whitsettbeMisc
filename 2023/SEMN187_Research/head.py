import os

argOptions = [
    [1023], #generations
    [4, 8, 16], #genome size
    [50, 100, 200], #population size
    [0, 1], #restricted editing
    [1, 2, 3, 4] #edit cap (in fourths of genome size) NOTE: we may use 0 & restricted once
]

def genStates(topState = []):
    if len(topState) == 0: #add number of generations
        return genStates([1023])
    elif len(topState) == 1: #add genome size
        out = []
        for x in [4,8,16]:
            out += genStates(topState+[x])
        return out
    elif len(topState) == 2: #add population size
        out = []
        for x in [50,100,200]:
            out += genStates(topState+[x])
        return out
    elif len(topState) == 3: #add restriction
        out = []
        for x in [0,1]:
            out += genStates(topState+[x])
        return out
    elif len(topState) == 4: #add edit cap (measured in fourths of genome)
        out = []
        for x in [0,1,2,3,4]:
            if topState[3] == 1 or x != 0:
                out += genStates(topState+[x*topState[1]//4])
        return out
    else:
        return [topState]

states = genStates()

files = os.listdir('.\data')
seedsDone = 1
while any([file.endswith(str(seedsDone) + '.txt') for file in files]):
    seedsDone += 1
print(f'Seeds before #{seedsDone} have been run.')
toRun = int(input(f'How many seeds should run, starting with #{seedsDone}?  '))
if toRun + seedsDone - 1 > 100:
    toRun = 0
for state in states:
    os.system("start .\simGroup.exe " + " ".join(map(str, state)) + f" {seedsDone} {seedsDone + toRun - 1}")
os.system('taskmgr')