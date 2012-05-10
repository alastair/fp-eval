/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */

/*
Author: Yan Ke
August 2004
*/

#include <assert.h>
#include <map>
#include <string>
#include <limits>

#include "verify.h"
#include "keypoint.h"
#include "util.h"

// ratio of frames in the query song that must overlap with the database song
#define MIN_FRAMES_RATIO 0.85
#define MIN_SCORE 8

// number of iterations to run RANSAC
#define RANSAC_NUMITER 500
 
#define WORST_SCORE 32

using namespace std;


// even indices are from query
// odd indices are from database
static vsong verify(vector<Keypoint *> & matches,
	     vector<Keypoint *> & qkeys,
	     KeypointDB & kdb) {

	vsong bestsong;

	bestsong.score = WORST_SCORE;

	unsigned int maxiter = MIN(RANSAC_NUMITER, matches.size() / 2);

	unsigned int i = 0;

	for (unsigned j = 0; j < maxiter; j++) {

	//for (unsigned int i = 0; i < matches.size(); i += 2) {
		unsigned int minframe = MIN(matches[i]->frame, matches[i+1]->frame);

		// find start key id in database
		unsigned int startkeyid = matches[i+1]->keyid - minframe;

		// frame from query
		unsigned int startframe = matches[i]->frame - minframe;

		unsigned int j = 0, tdist = 0;

		//printf("Start frame: %d   MinFrame: %d\n", startframe, minframe);

		// uses BER to calculate distances
		while (startkeyid + j < kdb.numKeys()
		       && startframe + j < qkeys.size()
		       && kdb.getKey(startkeyid + j)->file_id == matches[i+1]->file_id) {

			tdist += keyDist(qkeys[startframe + j]->ld,
					 kdb.getKey(startkeyid + j)->ld);
			j++;
		}

		float score = (float) tdist / (float) (j - 1);

		//printf("Iteration %d: Score %f  Aligned: %d  DF: %d  QF: %d\n",
		//       i, score, j, matches[i+1]->frame, matches[i]->frame);

		if (score < bestsong.score && j >= MIN_FRAMES_RATIO * (float) qkeys.size()) {
			//printf("Frame length: %d  Start frame: %d  Q keys size %d\n",
			//       j - 1, startframe, qkeys.size());

			bestsong.score = score;
			bestsong.db_frame_start = matches[i+1]->frame - minframe;
			bestsong.db_frame_end = bestsong.db_frame_start + j - 1;
			bestsong.query_frame_start = matches[i]->frame - minframe;
			bestsong.query_frame_end = bestsong.query_frame_start + j - 1;
			bestsong.db_key_start = startkeyid;
		}
		
		if (maxiter == RANSAC_NUMITER)
			i = (rand() % matches.size()) / 2 * 2;
		else
			i += 2;
	}

	return bestsong;
}

// matches[0, 2, 4, ...] contain keypoints from image 1 (query)
// matches[1, 3, 5, ...] contain keypoints from image 2 (target)
map<unsigned int, vsong > verify4(map<unsigned int, vector<Keypoint *> > & matches, vector<Keypoint *> & qkeys, KeypointDB & kdb) {
	map<unsigned int, vsong> scores;

	for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {

		//printf("Verifying file %d\n", it->first);
		vsong song = verify(it->second, qkeys, kdb);
		
		if (song.score < MIN_SCORE) {
			scores[it->first] = song;
		}
        }

	return scores;
}

