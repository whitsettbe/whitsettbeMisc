import os
import numpy as np

#give the mean and std of a list
def summary(l):
    mean = sum(l) / len(l)
    stdev = (sum([(ll - mean) ** 2 for ll in l]) / (len(l) - 1)) ** .5
    return [mean, stdev]

files = os.listdir('.\\reduced')
out = ''

for file in files:
    #read data from the file
    with open('.\\reduced\\'+file) as fin:
        data = list(map(lambda x: list(map(lambda y: tuple(map(float, y.split())), x.strip().split('\t'))), fin.readlines()))
    gene, pref, corr = np.transpose(data, (2,1,0))
    
    #compute summary statistics for each generation
    # (we confirmed that no correlations were set to undefined-ness flags (2,3,4))
    geneSummary = []
    prefSummary = []
    corrSummary = []
    for i in range(len(gene)):
        geneSummary.append(summary(gene[i]))
        prefSummary.append(summary(pref[i]))
        corrSummary.append(summary(corr[i]))
        
    jointSummary = [geneSummary[i] + prefSummary[i] + corrSummary[i] for i in range(len(geneSummary))]
    formatted = [' '.join(map(lambda x: str(round(x, 5)), js)) for js in jointSummary]
    
    #add formatted data to the output batch
    # (NOTE: we no longer worry about generation counts in identifiers)
    out += ' '.join(file.split('.')[0].split('_')[1:]) + '\t' + '\t'.join(formatted) + '\n'
    
#print output
with open('summarized.txt', 'w') as fout:
    fout.write(out)
