/*
Author: Yan Ke
August 2004
*/

#include <stdio.h>
#include <assert.h>

using namespace std;

#include "sigproc.h"
#include "keypoint.h"

int main(int argc, char * argv[]) {
  
	if (argc != 4) {
		printf("Usage: %s descriptors.txt recording.wav outbits.keys\n", argv[0]);
		return 0;
	}

	char * descrfn = argv[1];
	char * wavfn = argv[2];
	char * outfn = argv[3];
	
	vector<Filter> filters = readFilters(descrfn);

       	printf ("Reading %s...\n", wavfn);
	unsigned int nsamples = 0, freq = 0;
	float * samples = wavread(wavfn, &nsamples, &freq);

	if (!samples) {
		printf("Error reading wave file.\n");
		return 0;
	}

	unsigned int nbits;
	unsigned int * bits = wav2bits(filters, samples, nsamples, freq, &nbits);

	free(samples);

	printf("Writing %d keys...\n", nbits);

	writebits(bits, nbits, outfn);

	free(bits);

	return 0;  
  
}



