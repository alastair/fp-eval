/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
May 2004
*/

#ifndef UTIL_H
#define UTIL_H
#include <math.h>

#include <vector>
#include <map>
using namespace std;

#include "search.h"

#include "keypointdb.h"

#define MAX(x, y) ((x) > (y) ? (x) : (y))
#define MIN(x, y) ((x) < (y) ? (x) : (y))

void printcountstats(map<unsigned int, vector<Keypoint *> > & matches, KeypointDB & kdb);

vector<Keypoint *> FindMatches(SearchStrategy * lshtable, vector<Keypoint *> & qkeys, unsigned int dist);

// returns file_id -> vector of keypoint matches
// odd items are query keypoints, even items are matched keypoints
map<unsigned int, vector<Keypoint *> > FilterMatches(vector<Keypoint *> & matches, unsigned int minmatches);

map<unsigned int, vector<Keypoint *> > FilterMatches2(map<unsigned int, vector<Keypoint *> > & matches, unsigned int minmatches);

void printfiles(map<unsigned int, vector<Keypoint *> > & matches, KeypointDB * kdb);

string basename(string nm);

extern int keyschecked;
extern int keysmatched;

#endif
