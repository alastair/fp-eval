/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
August 2004
*/

#define _FILE_OFFSET_BITS 64

#include <assert.h>
#include <string>
#include <iostream>
#include <bitset>

#include "keypointdb.h"

using namespace std;

#define HEADERSIZE 1024

#define MAX_FN_LEN 255
#define FL_REC_SIZE 256

#define NUM_RECS_OFFSET 8

#define KEY_REC_SIZE 12
/*
Files list file structure:
Bytes
[0, 3]   Magic number (ASCII).
[4, 7]   Version number (ASCII).
[8, 11]  Number of records (files) in list (unsigned int)


1024     Start of the first record.

Record:
[0]   Number of bytes in file name (unsigned int).
[1 - ] Start of file name (ASCII).

Note:

A record is 256 bytes
*/

/*
Keys list file structure:
Bytes
[0, 3]   Magic number (ASCII).
[4, 7]   Version number (ASCII).
[8, 11]  Number of records (keypoints) in list (unsigned int)

1024     Start of the first record.

Record:
[0, 3]   frame number (unsigned int)
[4, 7]   local descriptor (unsigned int)
[8, 11]  file id (unsigned int


Note:
The size of a record is 4 * 3 = 12
*/

KeypointDB::KeypointDB(char * files_dbn, char * keys_dbn) {
	assert(files_dbn);
	assert(keys_dbn);

	FILE * fl_fid = fopen(files_dbn, "rb");
	
	if (!fl_fid) {
		fprintf(stderr, "Error opening %s for reading.\n", files_dbn);
		exit(1);
	}


	// Check headers

	char hdr[5] = {0};

	// check filelist file type
	fread(hdr, 4, 1, fl_fid);

	if (strcmp(hdr, "FLDB") != 0) {
		fprintf(stderr, "%s is not a file list db.  Unrecognized format.\n", files_dbn);
		exit(1);
	}

	// check version number
	fread(hdr, 4, 1, fl_fid);

	if (strcmp(hdr, "0001") != 0) {
		fprintf(stderr, "Unrecognized file version number in %s. \n", files_dbn);
		exit(1);
	}

	unsigned int numfiles;
	fread(&numfiles, 4, 1, fl_fid);
	
	fseeko(fl_fid, (long long) HEADERSIZE, SEEK_SET);

	files.resize(numfiles);

	for (unsigned int i = 0; i < numfiles; i++) {
		unsigned char buf[257] = {0};

		fread(buf, 1, 256, fl_fid);

		files[i] = (char *) (buf + 1);
	}
	
	fclose(fl_fid);
	
	/////////////////////////////////////////////////////
	FILE * keys_fid = fopen(keys_dbn, "rb");

	if (!keys_fid) {
		fprintf(stderr, "Error opening %s for reading.\n", keys_dbn);
		exit(1);
	}
	// check keypoints file type
	fread(hdr, 4, 1, keys_fid);

	if (strcmp(hdr, "KPDB") != 0) {
		fprintf(stderr, "%s is not a keys list db.  Unrecognized format.\n", keys_dbn);
		exit(1);
	}

	// check version number
	fread(hdr, 4, 1, keys_fid);

	if (strcmp(hdr, "0001") != 0) {
		fprintf(stderr, "Unrecognized file version number in %s. \n", keys_dbn);
		exit(1);
	}

	unsigned int numkeys;

	fread(&numkeys, 4, 1, keys_fid);

	keys.resize(numkeys);
	
	fseeko(keys_fid, (long long) HEADERSIZE, SEEK_SET);

	printf("Reading keypoint database\n");
	for (unsigned int i = 0; i < numkeys; i++) {
		Keypoint * key = new Keypoint;
		fread(&(key->frame), 4, 1, keys_fid);
		fread(&(key->ld), 4, 1, keys_fid);
		fread(&(key->file_id), 4, 1, keys_fid);
		key->keyid = i;
		keys[i] = key;
		if (i % 100000 == 0) {
			printf(".");
			fflush(stdout);
		}
	}

	printf("\n");

	fclose(keys_fid);

	printf("%d files and %d keys read from db's.\n", numfiles, numkeys);
}


KeypointDB::KeypointDB(char * keyslist_fn, char * files_dbn, char * keys_dbn) {
	assert(keyslist_fn);
	assert(files_dbn);
	assert(keys_dbn);


	FILE * fkeys = fopen(keyslist_fn, "rb");

        if (!fkeys) {
                fprintf(stderr, "Can't open %s\n", keyslist_fn);
		exit(1);        
	}

	FILE * keys_fid = fopen(keys_dbn, "w+");

	if (!keys_fid) {
		fprintf(stderr, "Error opening %s for writing.\n", keys_dbn);
		exit(1);
	}

	vector<string> filenames;

	/////////////////////////////////////////
	// Write keys list
	char * hdr2 = "KPDB0001";
	fwrite(hdr2, strlen(hdr2), 1, keys_fid);

	fseeko(keys_fid, (long long) HEADERSIZE, SEEK_SET);

	char aline[2048];

	unsigned int numkeys = 0;
        while (fscanf(fkeys, "%s", aline) == 1) {
		cout << "Reading " << aline << endl;
		
                vector<Keypoint *> tkeys = readKeysFromFile(aline);

		for (vector<Keypoint *>::iterator it = tkeys.begin();
		     it != tkeys.end(); it++) {
			
			fwrite(&((*it)->frame), 4, 1, keys_fid);
			fwrite(&((*it)->ld), 4, 1, keys_fid);
			
			(*it)->file_id = filenames.size();
			fwrite(&((*it)->file_id), 4, 1, keys_fid);
		}

		numkeys += tkeys.size();

		DeleteKeys(tkeys);

		filenames.push_back(aline);
        }


	fseeko(keys_fid, (long long) NUM_RECS_OFFSET, SEEK_SET);
	fwrite(&numkeys, 4, 1, keys_fid);

	fflush(keys_fid);
	fclose(keys_fid);

	fclose(fkeys);
	

	/////////////////////////////////////////////
	// Write files list

	FILE * fl_fid = fopen(files_dbn, "w+");
	
	if (!fl_fid) {
		fprintf(stderr, "Error opening %s for writing.\n", files_dbn);
		exit(1);
	}

	// Initialize headers.

	char * hdr = "FLDB0001";
	fwrite(hdr, strlen(hdr), 1, fl_fid);


	fseeko(fl_fid, (long long) HEADERSIZE, SEEK_SET);

	for (vector<string>::iterator it = filenames.begin();
	     it != filenames.end(); it++) {

		unsigned char buf[256] = {0};
                buf[0] = it->size();
		memcpy(buf + 1, it->c_str(), buf[0]);


		fwrite(buf, 1, 256, fl_fid);
        }


	fseeko(fl_fid, (long long) NUM_RECS_OFFSET, SEEK_SET);
	
	unsigned int numfiles = filenames.size();

	fwrite(&numfiles, 4, 1, fl_fid);

	fflush(fl_fid);
	fclose(fl_fid);


	cout << "Wrote " << filenames.size() << " files and " << numkeys << " keys." << endl;
	

}

KeypointDB::KeypointDB(string afile) {
	keys = readKeysFromFile(afile.c_str());

	
	for (unsigned int i = 0; i < keys.size(); i++)
		keys[i]->keyid = i;

	files.push_back(afile);
}

KeypointDB::~KeypointDB() {
	DeleteKeys(keys);
}

Keypoint * KeypointDB::getKey(unsigned int keyid) {
	assert(keyid < keys.size());

	return keys[keyid];
}

string KeypointDB::getFileName(unsigned int fileid) {
	
	assert(fileid < files.size());

	return files[fileid];
}

unsigned int KeypointDB::numFiles() {
	return files.size();
}

unsigned int KeypointDB::numKeys() {
	return keys.size();
}

void KeypointDB::printStats() {
	unsigned int counts[LDLEN] = {0};

	for (unsigned int i = 0; i < keys.size(); i++) {
		bitset<LDLEN> bits(keys[i]->ld);
		
		for (unsigned int j = 0; j < LDLEN; j++) {
			counts[j] += bits[j] ? 1 : 0;
		}

	}

	cout << "Bit stats out of " << keys.size() << " keys." << endl;
	for (unsigned int i = 0; i < LDLEN; i++)
		cout << "Bit " << i << ": " << counts[i] << "  ("
		     << (float) counts[i] / keys.size() << ")" << endl;
}
