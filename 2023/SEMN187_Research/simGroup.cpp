#include <iostream>
#include <fstream>
#include <cstdlib>
using namespace std;

//arguments: #generations, genome size, pop'n size, restricted (0-1), flip limit, min seed, max seed
int main(int argc, const char* argv[])
{
	//save command-line arguments
	int minSeed = atoi(argv[6]);
	int maxSeed = atoi(argv[7]);

	//loop command construction
	string cmd = "";
	for(int i = minSeed; i <= maxSeed; i++)
	{
		cmd = string(".\\doSim.exe ")+argv[1]+" "+argv[2]+" "+argv[3]+" "+argv[4]+" "+argv[5]+" "+to_string(i)+" ";
		cmd += string(".\\data\\")+argv[1]+"_"+argv[2]+"_"+argv[3]+"_"+argv[4]+"_"+argv[5]+"_"+to_string(i)+".txt";
		system(cmd.c_str());
	}
	
}
//powershell "[console]::beep(440,1000)"