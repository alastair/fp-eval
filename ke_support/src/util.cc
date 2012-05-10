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
#include <set>

//#include "lshdisk.h"
#include "keypoint.h"
#include "util.h"
#include "search.h"

int keyschecked = 0;
int keysmatched = 0;


string basename(string fn) {
	size_t pos = fn.rfind("/");

	string ret = fn.substr(pos+1, 11);
			       
	//cout << "BASE: " << ret << endl;

	return ret;
}


void printcountstats(map<unsigned int, vector<Keypoint *> > & matches,
		     KeypointDB & kdb) {
        // map match count -> file id
        multimap<unsigned int, unsigned int> counts;
	map<unsigned int, set<Keypoint *> > uniquematches;
                                                            

	
	for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {                              
		set<Keypoint *> s;
		
		for (vector<Keypoint *>::iterator iv = it->second.begin();
		     iv != it->second.end(); iv++) {
			s.insert(*iv);
		}

		uniquematches[it->first] = s;
	}

        for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {
                counts.insert(pair<unsigned int, unsigned int>(it->second.size(), it->first));
        }
                                                                                                     
        for (multimap<unsigned int, unsigned int>::reverse_iterator it = counts.rbegin();
             it != counts.rend(); ++it)
                printf("File %d: %d\tunique: %d\t%s\n", it->second, it->first / 2,
		       uniquematches[it->second].size() / 2,
		       basename(kdb.getFileName(it->second)).c_str());
                                                                                                     
}

vector<Keypoint *> FindMatches(SearchStrategy * table, vector<Keypoint *> & qkeys, unsigned int dist)
{
        vector<Keypoint *> matches;
 
        vector<vector<Keypoint *> > neighbors = table->getNeighbors(qkeys, dist);
 
         
	printf("NOTE: filtering by max number of neighbors returned.\n");

        for (unsigned int i = 0; i < neighbors.size(); i++) {
		//if (neighbors[i].size() > 100)
		//	continue;

                for (unsigned int j = 0; j < neighbors[i].size(); j++) {
                        matches.push_back(qkeys[i]);
                        matches.push_back(neighbors[i][j]);
                }
        }
 
        return matches;
}


// returns file_id -> vector of keypoint matches
// odd items are query keypoints, even items are matched keypoints
map<unsigned int, vector<Keypoint *> > FilterMatches(vector<Keypoint *> & matches, unsigned int minmatches) {
                                                                                                     
        // map from file_id -> count
        map<unsigned int, unsigned int> filecounts;
                                                                                                     
        // map frrom file_id -> vector of keypoints
        map<unsigned int, vector<Keypoint *> > ret;
                                                                                                     
        for (unsigned int i = 1; i < matches.size(); i += 2) {
                filecounts[matches[i]->file_id]++;
        }
                                                                                                     
        for (unsigned int i = 0; i < matches.size(); i += 2) {
                if (filecounts[matches[i+1]->file_id] >= minmatches) {
                        //printf("added key %d, file %d\n", i, matches[i+1]->file_id);
                        ret[matches[i+1]->file_id].push_back(matches[i]);
                        ret[matches[i+1]->file_id].push_back(matches[i+1]);
                }
        }
                                                                                                     
        return ret;
}

// This function will only return one file with the maximum number of matches
// subject to the minmatches threshold
map<unsigned int, vector<Keypoint *> > FilterMatches2(map<unsigned int, vector<Keypoint *> > & matches, unsigned int minmatches) {
	
	unsigned int maxcount = minmatches;

        // map from file_id -> vector of keypoints
        map<unsigned int, vector<Keypoint *> > ret;
                                                                                                     
	for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
	     it != matches.end(); it++) {
		if (it->second.size() > maxcount)
			maxcount = it->second.size();
	}

	for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
	     it != matches.end(); it++) {
		if (it->second.size() == maxcount)
			ret.insert(*it);
	}
                                                                                                     
        return ret;
}


void printfiles(map<unsigned int, vector<Keypoint *> > & matches, KeypointDB * kdb) {
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
        }
}


