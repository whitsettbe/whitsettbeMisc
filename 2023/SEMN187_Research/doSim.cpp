#include <iostream>
#include <fstream>
#include <cstdlib>
#include <tuple>
#include <vector>
#include <algorithm>
#include <deque>
#include <sstream>
using namespace std;

//so that we may pass genome length (<=32) as a parameter to the program,
// we use uints to store genome bits in a new class
class Bitset
{
	public:
		int size = 0;
		unsigned int bits = 0;

		Bitset(){}

		Bitset(int theSize)
		{
			size = theSize;
		}

		Bitset operator~()
		{
			Bitset out(size);
			out.bits = ~bits & ((1<<size)-1);
			return out;
		}

		Bitset operator&(Bitset const& x)
		{
			Bitset out(size);
			out.bits = bits & x.bits;
			return out;
		}

		Bitset operator^(Bitset const& x)
		{
			Bitset out(size);
			out.bits = (bits ^ x.bits) & ((1<<size)-1);
			return out;
		}

		Bitset operator|(Bitset const& x)
		{
			Bitset out(size);
			out.bits = (bits | x.bits) & ((1<<size) - 1);
			return out;
		}

		short operator[](int i)
		{
			return (bits>>i)&1;
		}

		void set(int i, int b)
		{
			bits &= ~(1<<i);
			bits |= (b<<i);
		}

		short count()
		{
			short out = 0;
			for(int i = 0; i < size; i++) out += ((1<<i)&bits) > 0;
			return out;
		}

		unsigned long to_ulong()
		{
			return bits;
		}
};

//give a random bitstring of the desired length
Bitset randbits(int depth)
{
    Bitset x(depth);
    for(int i = 0; i < depth; i++)
    {
        x.set(i, rand()%2);
    }
    return x;
}

//blend two bitstrings of the desired length
Bitset blend(Bitset a, Bitset b)
{
	Bitset x(a.size);
	for(int i = 0; i < a.size; i++)
	{
		if(rand()%2) x.set(i, a[i]);
		else x.set(i, b[i]);
	}
	return x;
}

//class defining meeple organisms (to borrow a term from the board game community)
class Meeple
{
	public:
		int depth;
		Bitset genes[2], prefs[2], newGenes[2], newPrefs[2], phen, phenPref;

		//initialize the expressed and preferred genes randomly
		Meeple(int theDepth)
		{
			depth = theDepth;
			newGenes[0] = genes[0] = randbits(depth);
			newGenes[1] = genes[1] = randbits(depth);
			newPrefs[0] = prefs[0] = randbits(depth);
			newPrefs[1] = prefs[1] = randbits(depth);
			phen = blend(genes[0], genes[1]);
			phenPref = blend(prefs[0], prefs[1]);
		}

		//compute value of another Meeple for reproduction
		int attraction(Meeple& x)
		{
			return (~(phenPref ^ x.phen)).count() + (~(x.phenPref ^ phen)).count();
		}

		//mix genes with another meeple (by pointer, so we can edit it) (THIS WAS CAUSING GENETIC DRIFT BY ACCIDENT!)
		void reproduceWith(Meeple& x)
		{
			//scramble existing genes (and preferences)
			newGenes[0] = blend(genes[0], genes[1]);
			newGenes[1] = (genes[0] ^ genes[1]) ^ newGenes[0];
			newPrefs[0] = blend(prefs[0], prefs[1]);
			newPrefs[1] = (prefs[0] ^ prefs[1]) ^ newPrefs[0];
			x.newGenes[0] = blend(x.genes[0], x.genes[1]);
			x.newGenes[1] = (x.genes[0] ^ x.genes[1]) ^ x.newGenes[0];
			x.newPrefs[0] = blend(x.prefs[0], x.prefs[1]);
			x.newPrefs[1] = (x.prefs[0] ^ x.prefs[1]) ^ x.newPrefs[0];

			//trade gene/preference chromosomes
			Bitset temp(depth);
			temp = newGenes[0];
			newGenes[0] = x.newGenes[0];
			x.newGenes[0] = temp;
			temp = newPrefs[0];
			newPrefs[0] = x.newPrefs[0];
			x.newPrefs[0] = temp;
		}

		//choose some genes we would like to alter or select towards
		Bitset request(bool restricted, int flipLim)
		{
			//which genes would we like to change
			Bitset out(depth);
			if(!restricted) out = phenPref & ~(newGenes[0] & newGenes[1]) | ~phenPref & (newGenes[0] | newGenes[1]);
			//potentially restrict ourselves to what we carry
			//genes we prefer which won't both be true and were posessed >0 times (and had different parity)
			//genes we don't prefer which won't both be false and were posessed <2 times (and had different parity)
			else out = (phenPref & ~(newGenes[0] & newGenes[1]) & (genes[0] | genes[1])
					| ~phenPref & (newGenes[0] | newGenes[1]) & ~(genes[0] & genes[1])) & ((genes[0] ^ genes[1]) ^ (newGenes[0] ^ newGenes[1]));

			//reduce the number of chosen bits if necessary
			Bitset temp(depth);
			while(out.count() > flipLim)
			{
				temp = out & randbits(depth);
				if(temp.count() >= flipLim)
					out = temp;
			}

			//return the chosen bits
			return out;
		}

		//accept a gene modification to the child state, aligning with the preference
		void grant(int geneToModify)
		{
			if(newGenes[0][geneToModify] != phenPref[geneToModify]) newGenes[0].set(geneToModify, phenPref[geneToModify]);
			else newGenes[1].set(geneToModify, phenPref[geneToModify]);
		}

		//become the predetermined child state
		void descend()
		{
			genes[0] = newGenes[0];
			genes[1] = newGenes[1];
			prefs[0] = newPrefs[0];
			prefs[1] = newPrefs[1];
			phen = blend(genes[0], genes[1]);
			phenPref = blend(prefs[0], prefs[1]);
		}

		string to_string()
		{
			stringstream out;
			out<<genes[0].to_ulong()<<" "<<genes[1].to_ulong()<<" "<<phen.to_ulong()<<" "
					<<prefs[0].to_ulong()<<" "<<prefs[1].to_ulong()<<" "<<phenPref.to_ulong()<<" ";
			return out.str();
		}
};

//define a tuple comparator prioritizing high third-index values
bool thirdComp(tuple<int,int,int> a, tuple<int,int,int> b)
{
	return get<2>(a) > get<2>(b);
}

//class defining a society
class Society
{
	public:
		vector<Meeple> meeples;
		int geneDepth;
		int popSize;
		bool restricted;
		int flipLim;
		Society(int theGeneDepth, int thePopSize, bool theRestricted, int theFlipLim)
		{
			geneDepth = theGeneDepth;
			popSize = thePopSize;
			restricted = theRestricted;
			flipLim = theFlipLim;
			for(int i = 0; i < popSize; i++) meeples.push_back(Meeple(geneDepth));
		}

		//compute transformation of the population by one generation,
		//returning a log of bit change count frequencies
		string generation()
		{
			//compute match values for each pair of meeples
			vector<tuple<int,int,int>> matches;
			for(int i = 0; i < popSize; i++)
			{
				for(int j = 0; j < popSize; j++)
				{
					if(i != j)
					{
						matches.push_back(make_tuple(i, j, meeples[i].attraction(meeples[j])));
					}
				}
			}

			//sort matches to optimize attraction and select matches accordingly
			random_shuffle(matches.begin(), matches.end());
			sort(matches.begin(), matches.end(), thirdComp);
			vector<bool> beenMatched (popSize, false);
			for(tuple<int,int,int> match : matches)
			{
				if(!beenMatched[get<0>(match)] && !beenMatched[get<1>(match)])
				{
					beenMatched[get<0>(match)] = beenMatched[get<1>(match)] = true;
					meeples[get<0>(match)].reproduceWith(meeples[get<1>(match)]);
				}
			}

			//if requests are allowed, take and grant requests
			if(flipLim > 0)
			{
				//generate random order for request satisfaction
				int order[popSize];
				for(int i = 0; i < popSize; i++) order[i] = i;
				random_shuffle(order, order + popSize);

				//take and satisfy requests from each meeple
				deque<int> requesting[geneDepth];
				Bitset request(geneDepth);
				for(int i : order)
				{
					request = meeples[i].request(restricted, flipLim);
					for(int j = 0; j < geneDepth; j++)
					{
						if(request[j])
						{
							//add meeple to the pile if they have the same request
							if(requesting[j].size() == 0 ||
									(meeples[requesting[j].front()].phenPref[j] ^ meeples[i].phenPref[j]) == 0)
							{
								requesting[j].push_back(i);
							}
							//satsify some requests otherwise
							else
							{
								meeples[requesting[j].front()].grant(j);
								meeples[i].grant(j);
								requesting[j].pop_front();
							}
						}
					}
				}
			}

			//create the successor generation
			//and count bits changed for each meeple (save to log)
			Bitset temp(geneDepth);
			int changeCount;
			vector<int> log;
			for(int i = 0; i < popSize; i++)
			{
				temp = meeples[i].phen;
				meeples[i].descend();
				changeCount = (temp ^ meeples[i].phen).count();
				while(log.size() <= changeCount) log.push_back(0);
				log[changeCount]++;
			}

			//build log string and return
			stringstream logStr;
			for(int l : log)
			{
				logStr << l << '\t';
			}
			return logStr.str();
		}

		string to_string()
		{
			stringstream out;
			for(Meeple meeple : meeples) out << meeple.to_string() << "\t";
			return out.str();
		}
};

//arguments: #generations, genome size, pop'n size, restricted (0-1), flip limit, seed, outfile
int main(int argc, const char* argv[])
{
	//save command-line arguments
	int numGenerations = atoi(argv[1]);
	int genomeDepth = atoi(argv[2]);
	int popSize = atoi(argv[3]);
	bool restricted = atoi(argv[4]) > 0;
	int flipLim = atoi(argv[5]);
	int seed = atoi(argv[6]);

	//seed the generator and run generation updates
	srand(seed);
	Society soc(genomeDepth, popSize, restricted, flipLim);
	stringstream outstream;
	outstream << soc.to_string();
	for(int i = 0; i < numGenerations; i++)
	{
		soc.generation();
		outstream << endl << soc.to_string();
	}

	//write output to file
	ofstream fout(argv[7]);
	fout << numGenerations << " " << genomeDepth << " " << popSize
			<< " " << int(restricted) << " " << flipLim << " " << seed << endl;
	fout << outstream.str() << endl;
	fout.close();
}