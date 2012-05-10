/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
May 2004
*/

#include <math.h>
#include <assert.h>

#include "keypoint.h"

#include <bitset>
using namespace std;


/** Find hamming distance between ld1 and ld2.
    Count the number of 1's in ld1 xor ld2. */
unsigned int keyDist(unsigned int ld1, unsigned int ld2) {
	/*
	unsigned int d = 0;

	unsigned int diff = ld1 ^ ld2;

	for (unsigned int i = 0; i < LDLEN; i++) {
		if ( diff %  2 == 1)
			d++;

		diff >>= 1;
	}

	return d;
	*/

	return (bitset<LDLEN>(ld1) ^ bitset<LDLEN>(ld2)).count();
}


void DeleteKeys(vector<Keypoint *> & keys)
{
	for (unsigned int i = 0; i < keys.size(); i++)
		delete(keys[i]);
}

unsigned int charsToBits(unsigned char * ld) {
	bitset<LDLEN> bits;

	for (unsigned int i = 0; i < LDLEN; i++) {
		bits.set(i, ld[i]);
	}

	return bits.to_ulong();
}

vector<Keypoint *> bitsToKeys(unsigned int * bits, unsigned int nbits) {
	vector<Keypoint *> keys (nbits);

	for (unsigned int i = 0; i < nbits; i++) {
		/* Allocate memory for the keypoint. */
		Keypoint * key = new Keypoint;

		key->file_id = 0;
		key->frame = i;
		key->keyid = 0;
		key->ld = bits[i];
		keys[i] = key;
	}

	return keys;
}

vector<Keypoint *> readKeysFromFile(const char * filename)
{
	assert(filename);
	bool packed = false;

	unsigned int num, ldlen;
	
	FILE * fp;
	vector<Keypoint *> keys;
	
	fp = fopen (filename, "rb");
	
	//printf("%s\n", filename);

	if (! fp) {
		fprintf(stderr, "Could not open file: %s\n", filename);
		exit(1);
	}         
	
	fread(&ldlen, 4, 1, fp);

	if (ldlen > 1000) {
		ldlen /= 1000;
		packed = true;
	}

	assert(ldlen == LDLEN);

	fread(&num, 4, 1, fp);

	// faster if we resize now
	keys.resize(num);

	for (unsigned int i = 0; i < num; i++) {
		/* Allocate memory for the keypoint. */
		Keypoint * key = new Keypoint;

		key->file_id = 0;
		key->frame = i;
		key->keyid = 0;

		if (packed) {
			if (fread(&(key->ld), 4, 1, fp) != 1) {
				fprintf(stderr, "Error reading from file %s\n",
					filename);
				exit(1);
			}
		} else {
			unsigned char ld[LDLEN];

			if (fread(ld, LDLEN, 1, fp) != 1) {
				fprintf(stderr, "Error reading from file %s\n",
					filename);
				exit(1);
			}

			key->ld = charsToBits(ld);
		}

		keys[i] = key;
	}
	
	fclose(fp);
	
	return keys;
}

void writebits2(unsigned int bits[], unsigned int nbits, char * fn) {
	assert(bits);
	
	FILE * f = fopen(fn, "wb");
	if (!f) {
		printf("Error: Can't open %s for writing.\n", fn);
		exit(1);
	}



	unsigned int t = 32;
	
	fwrite(&t, 4, 1, f);
	fwrite(&nbits, 4, 1, f);

	for (unsigned int i = 0; i < nbits; i++) {
		bitset<32> bt(bits[i]);

		for (unsigned int j = 0; j < t; j++) {
			unsigned char c = bt[j];
			
			fwrite(&c, 1, 1, f);
		}
	}

	fflush(f);
	fclose(f);
}

void writebits(unsigned int bits[], unsigned int nbits, char * fn) {
	FILE * f = fopen(fn, "wb");
	if (!f) {
		printf("Error: Can't open %s for writing.\n", fn);
		exit(1);
	}

	unsigned int t = 32000; // special case to represent packed bits
	
	fwrite(&t, 4, 1, f);
	fwrite(&nbits, 4, 1, f);

	for (unsigned int i = 0; i < nbits; i++) {
		fwrite(&(bits[i]), 4, 1, f);
	}

	fflush(f);
	fclose(f);
}
