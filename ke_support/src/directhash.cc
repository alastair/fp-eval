/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
August 2004
*/

#define _FILE_OFFSET_BITS 64

#include <assert.h>

#include <algorithm>
#include <iostream>
#include <bitset>
using namespace std;

#include "directhash.h"

#include "util.h"

//#define KEYDIST0

DirectHash::DirectHash(KeypointDB * kdb) {
	this->kdb = kdb;

	unsigned int nkeys = kdb->numKeys();

	cout << "Building hash table of " << nkeys << " keys " << endl;

	hashtable.resize(nkeys);

	for (unsigned int i = 0; i < nkeys; i++) {
		Keypoint * k = kdb->getKey(i);
		hashtable.insert(MT::value_type(k->ld, k));
		if (i % 100000 == 0) {
			cout << ".";
			cout.flush();
		}
	}

	cout << endl;
}

vector<vector<Keypoint *> > DirectHash::getNeighbors(vector<Keypoint *> & keys,
						    unsigned int dist) {
	vector<vector<Keypoint *> > neighbors(keys.size());

	for (unsigned int i = 0; i < keys.size(); i++) {
		//cout << "Looking for ld: " << keys[i]->ld << endl;
		
		#ifdef KEYDIST0
		
		pair<MT::const_iterator, MT::const_iterator> bounds = hashtable.equal_range(keys[i]->ld);
		
		for (MT::const_iterator it = bounds.first; it != bounds.second; it++) {
			neighbors[i].push_back(it->second);
			//cout << "  Found: " << it->second->ld << endl;

			keysmatched++;
			keyschecked++;
		}

		#else
		pair<MT::const_iterator, MT::const_iterator> bounds
			= hashtable.equal_range(keys[i]->ld);
		for (MT::const_iterator it = bounds.first; it != bounds.second; it++)
			neighbors[i].push_back(it->second);
		
		bitset<LDLEN> bits(keys[i]->ld);
		for (int j = 0; j < LDLEN; j++) {
			bits.flip(j);
			unsigned int ld = bits.to_ulong();

			bounds = hashtable.equal_range(ld);

			for (MT::const_iterator it = bounds.first; it != bounds.second; it++)
				neighbors[i].push_back(it->second);

			bits.flip(j);
		}
		


		if (i % 1000 == 0) {
			printf(".");
			fflush(stdout);
			
		} 
		#endif
		
	}

	//cout << endl;
	
	return neighbors;
}
