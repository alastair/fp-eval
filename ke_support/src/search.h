/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
June 2004

*/


#ifndef SEARCH_H
#define SEARCH_H

#include <vector>

#include "keypoint.h"


class SearchStrategy {
public:
	virtual vector<vector<Keypoint *> > getNeighbors(vector<Keypoint *> & keys,
						 unsigned int dist) = 0;

	virtual ~SearchStrategy() {};

	//vector<unsigned int> getNumKeys();
};



#endif
