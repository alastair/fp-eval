/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
May 2004
*/

#ifndef VERIFY_H
#define VERIFY_H

#include <map>
#include <vector>
#include "keypoint.h"
#include "keypointdb.h"

using namespace std;

typedef struct vsong_t {
	float score;
	
	unsigned int db_frame_start;
	unsigned int db_frame_end;
	unsigned int db_key_start;

	unsigned int query_frame_start;
	unsigned int query_frame_end;

} vsong;

#define NF 32

typedef struct emparams_t {
	float alpha1[NF];
	float alpha2[NF];
	float theta1;
	float theta2;
	float PYi1;
	float PYi0;
} emparams;


map<unsigned int, vsong> verify4(map<unsigned int, vector<Keypoint *> > & keys,
                                  vector<Keypoint *> & query, KeypointDB & kdb);

map<unsigned int, vsong> verify4em(map<unsigned int, vector<Keypoint *> > & keys,
				   vector<Keypoint *> & query, KeypointDB & kdb,
				   emparams & params);
emparams readEMParams(char * fn);

#endif
