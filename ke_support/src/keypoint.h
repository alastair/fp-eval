/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
May 2004
*/

#ifndef KEYPOINT_H
#define KEYPOINT_H

#include <vector>
using namespace std;

#define LDLEN 32


typedef struct s_Keypoint {

	unsigned int frame; ///< frame id

	unsigned int ld; ///< The 32 bit local descriptor


	unsigned int file_id; ///< File id that this keypoint belongs to.

	unsigned int keyid; ///< Global keypoint id

} Keypoint;
       

/** Calculate distance in descriptor space. */
unsigned int keyDist(unsigned int ld1, unsigned int ld2); 


vector<Keypoint *> readKeysFromFile(const char * fn);

/** Delete keys from memory. */
void DeleteKeys(vector<Keypoint *> & keys);

unsigned int charsToBits(unsigned char * ld);

/** write bits to disk (NOT packing bits to ints) */
void writebits2(unsigned int bits[], unsigned int nbits, char * fn);

/** write bits to disk (packing bits to ints) */
void writebits(unsigned int bits[], unsigned int nbits, char * fn);

vector<Keypoint *> bitsToKeys(unsigned int * bits, unsigned int nbits);

#endif
