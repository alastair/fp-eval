/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */

/*
Author: Yan Ke
August 2004
*/

#include <assert.h>
#include <stdarg.h>
#include <iostream>
#include <map>
#include <string>

//#include "linsearch.h"
//#include "lshdisk.h"
#include "directhash.h"

#include "keypoint.h"
#include "util.h"

using namespace std;


map<unsigned int, vector<Keypoint *> > verify(map<unsigned int, vector<Keypoint *> > & keys);
map<unsigned int, vector<Keypoint *> > verify2(map<unsigned int, vector<Keypoint *> > & keys,
					       vector<Keypoint *> & query, KeypointDB & kdb,
					       unsigned int keydist);

// for flipping bits
#define MMATCH 0.005
#define MMATCH2 0.1

// for not flipping bits
//#define MMATCH 0.08

//#define MMATCH 0.05
//#define MMATCH2 0.4

// out of 32 bits
#define KEYDIST 8



void countmatches(map<unsigned int, vector<Keypoint *> > & matches, KeypointDB * kdb,
                  int & nummatched, int & truepos, int & falsepos,
                  char * qfn) {
        // map match count -> file id
        multimap<unsigned int, unsigned int> counts;
                                                                                                  
        for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {
                counts.insert(pair<unsigned int, unsigned int>(it->second.size(), it->first));
        }
                                                                                                  
        for (multimap<unsigned int, unsigned int>::reverse_iterator it = counts.rbegin();
             it != counts.rend(); ++it) {
                string fn = kdb->getFileName(it->second);
                cout << "CandidateFile " << it->second << ": " << fn << endl;
                                                                                                  
                nummatched++;

		
		if (basename(fn) == basename(string(qfn)))
                        truepos++;
                else {
                        falsepos++;
                        cout << "  FP: " << fn << endl;
                }
        }
}

void printmatches(map<unsigned int, vector<Keypoint *> > & matches,
		     KeypointDB & kdb) {
	
        for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {
		string fn = basename(kdb.getFileName(it->first));

		unsigned int minkey = UINT_MAX;
		unsigned int maxkey = 0;
		
		unsigned int minframe = 0, maxframe = 0;

		vector<Keypoint *> inliers = it->second;

		float dist = 0;

		for (unsigned int i = 1; i < inliers.size(); i += 2) {
			dist += keyDist(inliers[i]->ld, inliers[i-1]->ld);

			if (maxkey < inliers[i]->frame) {
				maxkey = inliers[i]->frame;
				maxframe = inliers[i - 1]->frame;
			}
			
			if (minkey > inliers[i]->frame) {
				minkey = inliers[i]->frame;
				minframe = inliers[i - 1]->frame;
			}
		}

		printf("RM: %s OS: %d OE: %d OL: %d    RS: %d RE: %d RL: %d   N: %d  AvgD: %f\n",
		       fn.c_str(), minkey, maxkey, maxkey - minkey + 1,
		       minframe, maxframe, maxframe - minframe + 1, inliers.size() / 2,
		       dist / (float) inliers.size() * 2.0);
        }
}


map<string, string> readKeysList(char * fn) {
	map<string, string> ret;

	printf("Reading %s\n", fn);

	FILE * f = fopen(fn, "rb");
	assert(f);

	char aline[2048];

        while (fscanf(f, "%s", aline) == 1) {
		string a = string(aline);
		ret[basename(a)] = a;
	}

	return ret;
}


int main(int argc, char * argv[])
{
        if (argc != 3 ) {
                printf("Usage: %s origs.txt recorded.txt\n", argv[0]);
                return -1;
        }

	map<string, string> origslist = readKeysList(argv[1]);
	map<string, string> recslist = readKeysList(argv[2]);
		
	printf("MMATCH: %f\n", MMATCH);

	for (map<string, string>::iterator it = recslist.begin(); 
	     it != recslist.end(); it++) {

		cout << "Aligning " << it->first << endl;

		if (origslist.find(it->first) == origslist.end()) {
			cout << "WARNING: Could not find recording in original songs." << endl;
			continue;
		}

 		KeypointDB kdb(origslist[it->first]);

		DirectHash table(&kdb);

		SearchStrategy * search = &table;

		cout << "Reading recorded keys from " << it->second.c_str() << endl;

		vector<Keypoint *> qkeys = readKeysFromFile(it->second.c_str());

		cout << "Searching on " << qkeys.size() << " keys." << endl;

		vector<Keypoint *> rkeys = FindMatches(search, qkeys, KEYDIST);


		map<unsigned int, vector<Keypoint *> > fkeys = FilterMatches(rkeys, (int) (MMATCH2 * qkeys.size()));
		
		cout << "After min matches..." << endl;

		printcountstats(fkeys, kdb);
		
		// map<unsigned int, vector<Keypoint *> > vkeys = verify(fkeys);
		map<unsigned int, vector<Keypoint *> > vkeys = verify2(fkeys, qkeys, kdb, KEYDIST);

		vkeys = FilterMatches2(vkeys, (int) (MMATCH * qkeys.size()));

		if (vkeys.size() == 0) {
			cout << "WARNING: Verification failed. " << endl;
		}

		cout << "After verfication... " << endl;

		printcountstats(vkeys, kdb);

		printf("\n");
		
		//printfiles(fkeys, &kdb);
		//printf("\n");

		cout << "Searched keys: " << keyschecked << "    matched_keys: " << keysmatched << endl;
		
		printmatches(vkeys, kdb);

		// keep this line at end of loop
		DeleteKeys(qkeys);
                        
	}

        return 0;

}


