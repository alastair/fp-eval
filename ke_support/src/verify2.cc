/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
August 2004
*/

#include <assert.h>
#include <map>
#include <string>
#include <limits>

#include "keypoint.h"
#include "util.h"

#define MIN_INLIER_PAIRS 5
#define RANSAC_NUMITER 1000

// 1 + x, 1 - x factor
#define SPEED_RANGE 0.01

#define NUM_FRAME_D 0

#define MIN_INLIER_RATIO 0.001

#define MIN_FRAMES 20

using namespace std;

bool pointsConsistent(Keypoint * i1, Keypoint * j1,
		      Keypoint * i2, Keypoint * j2) {

	// check if frame distances are approximately the same
	float f1 = (int) i2->frame - (int) i1->frame;
	float f2 = (int) j2->frame - (int) j1->frame;

	float scale = f1 / f2;

	// check if speed is within 10% speed change
	// also check for scale < 0 (mirroring)
	if (scale > 1.0 + SPEED_RANGE || scale < 1.0 - SPEED_RANGE)
		return false;

	//printf(" scale: %f   i1=%u i2=%u   j1=%u j2=%u\n", scale, i1->frame, i2->frame, j1->frame, j2->frame);


	return true;
}

void calcTransform(Keypoint * i1, Keypoint * j1,
		   Keypoint * i2, Keypoint * j2,
		   int * start, int * offset, float * scale) {


	unsigned int istart = MIN(i1->frame, i2->frame);
	unsigned int iend = MAX(i1->frame, i2->frame);

	unsigned int jstart = MIN(j1->frame, j2->frame);
	unsigned int jend = MAX(j1->frame, j2->frame);

	*start = istart;
	*offset = jstart - istart;

	float ilen = iend - istart;
	float jlen = jend - jstart;

	*scale = jlen / ilen;

	
}


vector<Keypoint *> getinliers(int start, int offset, float scale, vector<Keypoint *> & matches) {
	vector<Keypoint *> ret;

	for (unsigned int i = 0; i < matches.size(); i += 2) {
		Keypoint * k1 = matches[i];
		Keypoint * k2 = matches[i + 1];

		int len = (int) (scale * ((int) k1->frame - start));

		int target = start + offset + len;

		if (abs((int) k2->frame - target) <= NUM_FRAME_D) {
			// is inlier
			ret.push_back(k1);
			ret.push_back(k2);
		}
	}

	return ret;
}

vector<Keypoint *> verify(vector<Keypoint *> & matches) {
	vector<Keypoint *> ret;

        //printf("Number of matches found: %d\n", matches.size());
 
        // number of iterations of RANSAC
        for (unsigned int i = 0; i < RANSAC_NUMITER; i++) {
 
                //printf("  Iteration %d\n", i);
 
                // choose three points - even numbers, so they're from query image
                unsigned int i1 = (rand() % (matches.size() / 2)) * 2;
                unsigned int i2 = (rand() % (matches.size() / 2)) * 2;
              
                // make sure they're not the same points
                if (i1 == i2)
                        continue;
		
		if (!pointsConsistent(matches[i1], matches[i1+1],
				      matches[i2], matches[i2+1]))
			continue;

		int start;
		int offset;
		float scale;

		calcTransform(matches[i1], matches[i1+1],
			      matches[i2], matches[i2+1],
			      &start, &offset, &scale);


		vector<Keypoint *> inliers = getinliers(start, offset, scale, matches);

		/*
		printf("Transform: %d  Start %d\tOffset %d\tScale %f\t# Inliers %d\n",
		       i, start, offset, scale, inliers.size() / 2);
		*/

		if (inliers.size() > ret.size() && inliers.size() > matches.size() * MIN_INLIER_RATIO) {
		    ret = inliers;
		    //printf("%f %f\n", (float) inliers.size(), (float) matches.size() * MIN_INLIER_RATIO);
		}
		
	}

	return ret;
}

//WARNING assumes key ids are in order, per file
vector<Keypoint *> fillin(vector<Keypoint *> & inliers,
			  vector<Keypoint *> & qkeys,
			  KeypointDB & kdb, unsigned int keydist) {
	/*
	vector<Keypoint *> query;
	vector<Keypoint *> target;

	for (vector<Keypoint *>::iterator it = inliers.begin();
	     it != inliers.end(); it += 2) {
		query.push_back(*it);
		target.push_back(*(it + 1));
	}
	*/

	unsigned int minkey = UINT_MAX;
	unsigned int maxkey = 0;

	unsigned int minframe = 0, maxframe = 0;

	vector<Keypoint *> ret;

	for (unsigned int i = 1; i < inliers.size(); i += 2) {
		
		if (maxkey < inliers[i]->keyid) {
			maxkey = inliers[i]->keyid;
			maxframe = inliers[i - 1]->frame;
		}

		if (minkey > inliers[i]->keyid) {
			minkey = inliers[i]->keyid;
			minframe = inliers[i - 1]->frame;
		}
	}

	
	printf("Min key:   %d  Max key:   %d   Length: %d\n",
	       minkey, maxkey, maxkey - minkey);
	printf("Min frame: %d  Max frame: %d   Length: %d\n",
	       minframe, maxframe, maxframe - minframe);
	

	assert(maxframe < qkeys.size());


	for (unsigned int i = minkey - minframe, j = 0;
	     j < qkeys.size(); i++, j++) {
		
		if (i < 0 || i >= kdb.numKeys())
			continue;

		Keypoint * k1 = kdb.getKey(i);
		Keypoint * k2 = qkeys[j];
		
		if (keyDist(k1->ld, k2->ld) <= keydist) {
			ret.push_back(k2);
			ret.push_back(k1);
		}
		
	}

	printf("  Original Length: %d,  Original keys: %d,  New keys: %d\n",
	       maxkey - minkey + 1, inliers.size() / 2, ret.size() / 2);

	return ret;
	
	/*
	if (maxkey - minkey > MIN_FRAMES)
		return inliers;
	else
		return empty;
	*/
}


// matches[0, 2, 4, ...] contain keypoints from image 1 (query)
// matches[1, 3, 5, ...] contain keypoints from image 2 (target)
map<unsigned int, vector<Keypoint *> > verify2(map<unsigned int, vector<Keypoint *> > & matches, vector<Keypoint *> & qkeys, KeypointDB & kdb, unsigned int keydist) {
	map<unsigned int, vector<Keypoint *> > vkeys;

	for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {
         
                 
                printf("Verifying with RANSAC on file %d\n", it->first);
 
                vector<Keypoint *> inliers =  verify(it->second);
		
                if (inliers.size() >= 2*MIN_INLIER_PAIRS) {
			//printf("Checking file %d\n", it->first);

			vector<Keypoint *> ret = fillin(inliers, qkeys, kdb, keydist);
			if (ret.size() > 0)
				vkeys[it->first] = ret;
		}
                 
        }
 


	return vkeys;
}

