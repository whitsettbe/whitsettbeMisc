from matplotlib import pyplot as plt
import math

#compute mean and standard deviation from many means and standard deviations
def meanAndStdComb(means, stdevs):
    mean = sum(means) / len(means)
    stdev = (sum([x**2 for x in stdevs])**.5) / len(stdevs)
    return (mean, stdev)

with open('summarized.txt', 'r') as fin:
    lines = list(map(lambda x: x.strip().split('\t'), fin.readlines()))
    labels = [line[0] for line in lines]
    lines = [list(map(lambda x: list(map(float, x.split(' '))), line[1:])) for line in lines]

#configure plot defaults
plt.rcParams['lines.linewidth'] = 1

#construct plots and summary stats
outLines = []
for i in range(len(labels)):
    geneTop = []; gene = []; geneBot = []
    prefTop = []; pref = []; prefBot = []
    corrTop = []; corr = []; corrBot = []
    for datum in lines[i]:
        gene.append(datum[0])
        geneTop.append(datum[0] + datum[1])
        geneBot.append(datum[0] - datum[1])
        pref.append(datum[2])
        prefTop.append(datum[2] + datum[3])
        prefBot.append(datum[2] - datum[3])
        corr.append(datum[4])
        corrTop.append(datum[4] + datum[5])
        corrBot.append(datum[4] - datum[5])
    
    xCoords = [math.log2(i+1) for i in range(len(geneTop))]
    
    #set up axes
    fig, axes = plt.subplots(ncols=2)
    plt.subplots_adjust(right=.85, wspace=.1)
    ax1, ax2 = axes
    ax1.set_xlabel('t (log2 generations)')
    ax1.set_ylabel('Homozygosity')
    ax2.set_xlabel('t (log2 generations)')
    ax2.set_ylabel('Homozygosity correlation (r)')
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position('right')
    
    #add data to axes
    ax1.plot(xCoords, geneTop, 'lightblue')
    ax1.plot(xCoords, geneBot, 'lightblue')
    ax1.plot(xCoords, gene, 'blue')
    ax1.plot(xCoords, prefTop, 'lightgreen')
    ax1.plot(xCoords, prefBot, 'lightgreen')
    ax1.plot(xCoords, pref, 'green')
    ax2.plot(xCoords, corrTop, 'pink')
    ax2.plot(xCoords, corrBot, 'pink')
    ax2.plot(xCoords, corr, 'red')
    
    #show the plot
    fig.set_figheight(4)
    fig.set_figwidth(5)
    ax1.set_ybound(.4, 1)
    ax2.set_ybound(-.2, .6)
    ax1.set_xbound(0,10)
    ax2.set_xbound(0,10)
    ax1.set_xticks([0,5,10])
    ax2.set_xticks([0,5,10])
    fig.suptitle(', '.join(labels[i].split()))
    ax1.grid()
    ax2.grid()
    plt.savefig('.\\plots\\'+labels[i]+'.png')
    plt.close()

    #also compute the means and standard deviations over the last 2^9 generations
    geneMean, geneStdev = meanAndStdComb(gene[len(gene)//2:], [geneTop[i]-gene[i] for i in range(len(gene)//2,len(gene))])
    prefMean, prefStdev = meanAndStdComb(pref[len(pref)//2:], [prefTop[i]-pref[i] for i in range(len(pref)//2,len(pref))])
    corrMean, corrStdev = meanAndStdComb(corr[len(corr)//2:], [corrTop[i]-corr[i] for i in range(len(corr)//2,len(corr))])
    outLines.append((tuple(map(int, labels[i].split())),
            str(round(geneMean, 3)) + ', ' + str(round(geneStdev, 3)) + '; ' +
            str(round(prefMean, 3)) + ', ' + str(round(prefStdev, 3)) + '; ' +
            str(round(corrMean, 3)) + ', ' + str(round(corrStdev, 3))))

outLines.sort()
outStrs = [', '.join(map(str, ol[0])) + ' -- ' + ol[1] for ol in outLines]
with open('briefStats.txt', 'w') as fout:
    fout.write('\n'.join(outStrs))