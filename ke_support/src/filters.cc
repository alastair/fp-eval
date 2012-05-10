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

#include "filters.h"
#include "util.h"

Filter::Filter(unsigned int id, float threshold, float weight) {
	this->id = id;
	this->threshold = threshold;
	this->weight = weight;

	float time_rate = 1.5;
		
	unsigned int t = 1;
	vector<unsigned int> time_lengths;

	       
	while (t < KEYWIDTH) {
		time_lengths.push_back(t);
		t = MAX((unsigned int)round(time_rate * t)
			+ ((unsigned int) round(t * time_rate) % 2),
			t + 1);
	}

	//for (unsigned int i = 0; i < time_lengths.size(); i++)
	//	printf("Time Lengths %d %d\n", i, time_lengths[i]);
		
	unsigned int filter_count = 0;

	for (wt = 1; wt <= time_lengths.size(); wt++) {
		for (wb = 1; wb <= NBANDS; wb++) {
			for (first_band = 1; first_band <= NBANDS - wb + 1;
			     first_band++) {
				unsigned int time = time_lengths[wt-1];
				filter_count++;

				if (filter_count == id) {
					wt = time_lengths[wt-1];
					filter_type = 1;
					return;
				}

				if (time > 1) {
					filter_count++;
					if (filter_count == id) {
						wt = time_lengths[wt-1];
						filter_type = 2;
						return;
					}
				}
					
				if (wb > 1) {
					filter_count++;
					if (filter_count == id) {
						wt = time_lengths[wt-1];
						filter_type = 3;
						return;
					}
				}

				if (time > 1 && wb > 1) {
					filter_count++;
					if (filter_count == id) {
						wt = time_lengths[wt-1];
						filter_type = 4;
						return;
					}
				}
				
				if (time > 3) {
					filter_count++;
					if (filter_count == id) {
						wt = time_lengths[wt-1];
						filter_type = 5;
						return;
					}
				}
				
				if (wb > 3) {
					filter_count++;
					if (filter_count == id) {
						wt = time_lengths[wt-1];
						filter_type = 6;
						return;
					}
				}

			} // for first_band
		} // for wb
	} // for wt
}



vector<Filter> readFilters(char * fn) {
	FILE * f = fopen(fn, "rb");

	if (!f) {
		printf("Error reading descriptor file.\n");
		exit(1);
	}

	unsigned int ftid;
	float thresh;
	float weight;

	vector<Filter> filters;

	while (fscanf(f, "%d %f %f", &ftid, &thresh, &weight) == 3) {
		filters.push_back(Filter(ftid, thresh, weight));
		/*
		Filter ft = filters[filters.size() - 1];
		printf("ID: %d   wt: %d  wb: %d fb: %d type: %d\n",
		       ft.id, ft.wt, ft.wb, ft.first_band, ft.filter_type);
		*/
	}

	printf("Read %d filters.\n", filters.size());

	fclose(f);

	return filters;
}
