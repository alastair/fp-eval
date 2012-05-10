/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
June 2004

*/


#ifndef DIRECTHASH_H
#define DIRECTHASH_H

#include "search.h"

#define _FILE_OFFSET_BITS 64

#include <vector>
#include <set>

using namespace std;

// hashmap is an SGI extension, so we must use this
#include <ext/hash_map>
using namespace __gnu_cxx;

#include "keypoint.h"
#include "keypointdb.h"

// typedef hash_multimap<unsigned int, Keypoint *, hash<unsigned int>, equal_to<unsigned int> > MT;
typedef hash_multimap<unsigned int, Keypoint *> MT;

class DirectHash : public SearchStrategy {
private:

	KeypointDB * kdb;

	MT hashtable;
public:


	/** Create new hash table. */
	DirectHash(KeypointDB * kdb);


	/** Get neighbors of list of keypoints.
	    This function optimizes to minimize seek time.
	*/
	vector<vector<Keypoint *> > getNeighbors(vector<Keypoint *> & keys,
						 unsigned int dist);
};



#endif
