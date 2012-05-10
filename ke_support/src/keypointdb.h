/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
May 2004
*/

#ifndef KEYPOINTDB_H
#define KEYPOINTDB_H

#define _FILE_OFFSET_BITS 64


#include "keypoint.h"

class KeypointDB {
private:
	vector<Keypoint *> keys;
	vector<string> files;
public:
	KeypointDB(char * keyslist_fn, char * files_dbn, char * keys_dbn);
	KeypointDB(char * files_dbn, char * keys_dbn);
	KeypointDB(string afile);
	~KeypointDB();

	Keypoint * getKey(unsigned int keyid);

	string getFileName(unsigned int fileid);


	unsigned int numKeys();
	unsigned int numFiles();

	void printStats();
};

#endif
