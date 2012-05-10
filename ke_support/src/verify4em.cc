/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */

/*
Author: Yan Ke
August 2004
*/

#include <assert.h>
#include <map>
#include <string>
#include <limits>
#include <bitset>

#include "verify.h"
#include "keypoint.h"
#include "util.h"

// ratio of frames in the query song that must overlap with the database song
#define MIN_FRAMES_RATIO 0.75

#define MIN_SCORE -1000
//#define MIN_SCORE -2100
//#define MIN_SCORE -500

// number of iterations to run RANSAC
#define RANSAC_NUMITER 500
//#define RANSAC_NUMITER 1000

#define WORST_SCORE 1000000

using namespace std;

// Read EM parameters from file.
emparams readEMParams(char * fn) {
	emparams p;
	
	FILE * f = fopen(fn, "rb");

	assert(f);

	unsigned int nf = 0;

	fread(&nf, 4, 1, f);

	assert(nf == NF);

	fread(p.alpha1, 4, NF, f);
	fread(p.alpha2, 4, NF, f);
	fread(&p.theta1, 4, 1, f);
	fread(&p.theta2, 4, 1, f);
	fread(&p.PYi1, 4, 1, f);
	fread(&p.PYi0, 4, 1, f);

	fclose(f);

	return p;
}

// find bit distances between query keys and database keys
vector<unsigned int> distData(vsong song, vector<Keypoint *> & qkeys, KeypointDB & kdb) {
	unsigned int len = MIN(song.query_frame_end - song.query_frame_start,
			       song.db_frame_end - song.db_frame_start);

	vector<unsigned int> data(len);

	for (unsigned int i = 0; i < len; i++) {
		//assert(song.db_key_start + i >= 0);
		//assert(song.db_key_start + i < kdb.numKeys());
		//assert(song.query_frame_start + i >= 0);
		//assert(song.query_frame_start + i < qkeys.size());

		data[i] = kdb.getKey(song.db_key_start + i)->ld ^
			qkeys[song.query_frame_start + i]->ld;
	}

	return data;
}

float MLRatioScore(unsigned int fid, vector<unsigned int> & data, emparams & params)  {
	float * alpha1 = params.alpha1;
	float * alpha2 = params.alpha2;
	float theta1 = params.theta1;
	float theta2 = params.theta2;
	float PYi1 = params.PYi1;
	float PYi0 = params.PYi0;

	// first set Y0 for each song
	bitset<NF> dist = data[0];
	
	float PXj_Yj1 = 1;
	float PXj_Yj0 = 1;
	for (unsigned int k = 0; k < NF; k++) {
		//printf("      Bit %d\n", k);
		PXj_Yj1 *= dist[k] ? alpha1[k] : (1.0 - alpha1[k]);
		PXj_Yj0 *= dist[k] ? alpha2[k] : (1.0 - alpha2[k]);
	}

	vector<float> labels(data.size());
	vector<float> oldlabels(data.size());

	labels[0] = PXj_Yj1 * PYi1 /
		(PXj_Yj1 * PYi1 + PXj_Yj0 * PYi0);

	
	// Now set Yj, j > 0	
	float oldnewdist = 0;
	unsigned int datasize = data.size();

	for (unsigned int j = 1; j < datasize; j++) {
		//printf("    Data %d\n", j);
		dist = data[j];
		
		PXj_Yj1 = 1;
		PXj_Yj0 = 1;
		for (unsigned int k = 0; k < NF; k++) {
			//printf("      Bit %d\n", k);
			PXj_Yj1 *= dist[k] ? alpha1[k] : (1.0 - alpha1[k]);
			PXj_Yj0 *= dist[k] ? alpha2[k] : (1.0 - alpha2[k]);
		}
		
		float PXjNYj1 = PXj_Yj1 * (theta1 * labels[j-1]
					   + theta2 * (1.0 - labels[j-1]));
		float PXjNYj0 = PXj_Yj0 * ((1.0 - theta1) * labels[j-1]
					   + (1.0 - theta2) * (1.0 - labels[j-1])) ;
		
		float term2 = theta1 * labels[j-1] + theta2 * (1.0 - labels[j-1]);
		
		labels[j] = PXj_Yj1 * term2 / (PXjNYj1 + PXjNYj0);
		
		//printf("  Data %d:  new y: %e  old y %e\n", j, labels[j], oldlabels[j]);
		//printf("    PXj_Yj1 %e   term2 %e   PXjNYj1 %e  PXjNYj0 %e\n", PXj_Yj1, term2, PXjNYj1, PXjNYj0);
		oldnewdist += fabs(labels[j] - oldlabels[j]);
		oldlabels[j] = labels[j];
	}
	

	/*
	float sumy = 0;
	int county = 0;
	for (unsigned int j = 1; j < data.size(); j++) {
		sumy += labels[j];
		if (labels[j] < 0.5)
			county++;
	}

	printf(" YOUT: fid %d: avg y: %f\t y < 0.5: %d\n", fid, sumy / (float) data.size(), county);
	*/

	// we've decided on the class labels for each frame (song or occlusion)
	// now we do ml ratio test
	// do logs
	
	float X_Y = 0, Y = 0, X_Y0 = 0;
	
	// ignore first frame intentionally

	for (unsigned int i = 1; i < datasize; i++) {
		bitset<NF> dist = data[i];
		
		for (unsigned int k = 0; k < NF; k++) {
			float PXj_Yj1 = dist[k] ? alpha1[k] : (1.0 - alpha1[k]);
			float PXj_Yj0 = dist[k] ? alpha2[k] : (1.0 - alpha2[k]);
			X_Y += log(PXj_Yj1 * labels[i] + PXj_Yj0 * (1.0 - labels[i]));
			
		}

		float PY_YP = theta1 * labels[i-1] + theta2 * (1.0 - labels[i-1]);

		Y += log(PY_YP * labels[i] + (1.0 - PY_YP) * (1.0 - labels[i]));
	}
	
	X_Y0 = data.size() * NF * log(0.5);

	
	float score = X_Y + Y - X_Y0;
	//float score = X_Y - X_Y0;


	//printf("X_Y %f\tY %f\t X_Y0 %f\n", X_Y, Y, X_Y0);
	return score;

}	
		  


// even indices are from query
// odd indices are from database
static vsong verify(vector<Keypoint *> & matches,
	     vector<Keypoint *> & qkeys,
	     KeypointDB & kdb, emparams & params, unsigned int fid) {

	vsong bestsong;

	bestsong.score = WORST_SCORE;

	unsigned int maxiter = MIN(RANSAC_NUMITER, matches.size() / 2);

	unsigned int i = 0;

	unsigned int kdbnumkeys = kdb.numKeys();
	unsigned int qkeyssize = qkeys.size();

	for (unsigned j = 0; j < maxiter; j++) {

	//for (unsigned int i = 0; i < matches.size(); i += 2) {
		unsigned int minframe = MIN(matches[i]->frame, matches[i+1]->frame);

		// find start key id in database
		unsigned int startkeyid = matches[i+1]->keyid - minframe;

		// frame from query
		unsigned int startframe = matches[i]->frame - minframe;

		unsigned int j = 0, tdist = 0;

		//printf("Start frame: %d   MinFrame: %d\n", startframe, minframe);

		while (startkeyid + j < kdbnumkeys
		       && startframe + j < qkeyssize
		       && kdb.getKey(startkeyid + j)->file_id == matches[i+1]->file_id) {

			tdist += keyDist(qkeys[startframe + j]->ld,
					 kdb.getKey(startkeyid + j)->ld);
			j++;
		}

		float score = (float) tdist / (float) (j - 1);

		//printf("Iteration %d: Score %f  Aligned: %d  DF: %d  QF: %d\n",
		//       i, score, j, matches[i+1]->frame, matches[i]->frame);

		if (score < bestsong.score && j >= MIN_FRAMES_RATIO * (float) qkeyssize) {
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

	if (bestsong.score != WORST_SCORE) {
		vector<unsigned int> distances = distData(bestsong, qkeys, kdb);
		bestsong.score = - MLRatioScore(fid, distances, params);
	
	}

	return bestsong;
}

// matches[0, 2, 4, ...] contain keypoints from image 1 (query)
// matches[1, 3, 5, ...] contain keypoints from image 2 (target)
map<unsigned int, vsong > verify4em(map<unsigned int, vector<Keypoint *> > & matches, vector<Keypoint *> & qkeys,
				    KeypointDB & kdb, emparams & params) {
	map<unsigned int, vsong> scores;

	for (map<unsigned int, vector<Keypoint *> >::iterator it = matches.begin();
             it != matches.end(); ++it) {

		//printf("Verifying file %d\n", it->first);
		vsong song = verify(it->second, qkeys, kdb, params, it->first);
		//printf("MLRatioTest Score for file %d: %f\n", it->first, song.score);
			
		if (song.score < MIN_SCORE) {
			scores[it->first] = song;
		}
        }

	return scores;
}

