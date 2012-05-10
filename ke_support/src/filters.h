/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
May 2004
*/

#ifndef FILTERS_H
#define FILTERS_H

#include <vector>

using namespace std;

/// number of frames in time
#define KEYWIDTH 100

/// number of bands to divide the signal (log step)
#define NBANDS 33
		
class Filter {
public:
	unsigned int id; //< filter id
	unsigned int wt; //< time width
	unsigned int first_band; //< first band
	unsigned int wb; //< band width
	unsigned int filter_type; //< filter type
	
	float threshold; //< threshold for filter
	float weight; //< filter weight
	
	/// Constructs a new filter with id.
	Filter(unsigned int id, float threshold, float weight);

};

/// Reads a list of filters from file fn.
vector<Filter> readFilters(char * fn);

#endif
