#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cmath>
#include <thread>
#include <chrono>
using namespace std;

//define constants
#define NUM_TRIALS 100
#define LOG_PREFIX ".\\reduced\\"
#define LOG_SUFFIX ".txt"

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

//save the means of two vectors and their correlation coefficient in three other vectors
//(we assume v1 and v2 describe bivariate data and are the same length)
void pushMeansAndR(vector<float> v1, vector<float> v2, vector<float> &m1, vector<float> &m2, vector<float> &r)
{
	float mean1 = 0, mean2 = 0, std1 = 0, std2 = 0, corCoeff = 0;
	int len = v1.size();

	//compute means
	for(int i = 0; i < len; i++)
	{
		mean1 += v1[i];
		mean2 += v2[i];
	}
	mean1 /= len;
	mean2 /= len;

	//compute standard deviations
	for(int i = 0; i < len; i++)
	{
		std1 += pow(v1[i] - mean1, 2);
		std2 += pow(v2[i] - mean2, 2);
	}
	std1 /= len - 1;
	std2 /= len - 1;
	std1 = sqrt(std1);
	std2 = sqrt(std2);

	//compute correlation coefficient from z-score products
	if(std1 > 0 && std2 > 0)
	{
		for(int i = 0; i < len; i++)
		{
			corCoeff += (v1[i] - mean1) * (v2[i] - mean2);
		}
		corCoeff /= (len - 1) * std1 * std2;
	}
	//set error flags if we would have undefined r
	else if(std1 > 0) corCoeff = 2;
	else if(std2 > 0) corCoeff = 3;
	else corCoeff = 4;

	//store means and r-value
	m1.push_back(mean1);
	m2.push_back(mean2);
	r.push_back(corCoeff);
	return;
}


//get data from a specified log file and reduce it to the following:
// in each generation of a run, give the mean "expressed" homozygosity ratio,
// mean "preferential" homozygosity ratio,
// and their correlation coefficient in that generation
int main(int argc, const char* argv[])
{
	//determine which file we should open and declare variables
	ifstream fin;
	int numGenerations, genomeDepth, popSize, restricted, flipLim, seed;
	Bitset genes[2], phen, prefs[2], phenPref;
	vector<float> homozGenes, homozPrefs;
	vector<float> geneMeans, prefMeans, corrs;
	stringstream sout;

	//loop trials to read
	for(int i = 1; i <= NUM_TRIALS; i++)
	{
		//prepare the file
		//cout << string(".\\data\\") + argv[1] + + "_" + to_string(i) + ".txt" << endl;
		//return 0;
		fin.open(string(".\\data\\") + argv[1] + + "_" + to_string(i) + ".txt");

		//read the trial configuration and prep bitset sizes
		fin >> numGenerations >> genomeDepth >> popSize >> restricted >> flipLim >> seed;
		genes[0].size = genes[1].size = phen.size = prefs[0].size = prefs[1].size = phenPref.size = genomeDepth;
		geneMeans = vector<float>();
		prefMeans = vector<float>();
		corrs = vector<float>();

		//loop reading individuals and storing their homozygosity ratios
		for(int j = 0; j <= numGenerations; j++)
		{
			//build vectors of homozygosities
			homozGenes = vector<float>();
			homozPrefs = vector<float>();
			for(int k = 0; k < popSize; k++)
			{
				fin >> genes[0].bits >> genes[1].bits >> phen.bits >> prefs[0].bits >> prefs[1].bits >> phenPref.bits;
				homozGenes.push_back((~(genes[0] ^ genes[1])).count() / float(genomeDepth));
				homozPrefs.push_back((~(prefs[0] ^ prefs[1])).count() / float(genomeDepth));
			}

			//push the means and correlation
			pushMeansAndR(homozGenes, homozPrefs, geneMeans, prefMeans, corrs);
		}

		//write summary statistics to output stream
		for(int j = 0; j <= numGenerations; j++)
		{
			sout << geneMeans[j] << " " << prefMeans[j] << " " << corrs[j] << '\t';
		}
		sout << endl;

		//close the file
		fin.close();
	}

	//write output stream to output file
	ofstream fout(LOG_PREFIX + string(argv[1]) + LOG_SUFFIX);
	fout << sout.str();
	fout.close();
}