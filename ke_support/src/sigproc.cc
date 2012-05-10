/*
Author: Yan Ke
August 2004
*/

#include <complex>
#include <fftw3.h>
#include <stdio.h>
#include <assert.h>
#include <vector>
#include <bitset>

using namespace std;

#include "util.h"

#include "filters.h"

#include "sigproc.h"


// frames overlap 31/32
#define OVERLAP 32
// Tried 15/16 but doesn't work as well
// Not enough frames in 5 seconds of song
//#define OVERLAP 16

// number of samples in a frame
#define FRAMESIZE 2048

#define OVERLAPSAMPLES (FRAMESIZE/OVERLAP)

// expected original frequency of input wave file
#define OFREQ1 44100
#define OFREQ1MULT 8
#define OFREQ2 11025
#define OFREQ2MULT 2

// downsampled frequency
#define DFREQ 5513

// amount of time in a frame
#define FRAME_TLEN ((float) FRAMESIZE / (float) DFREQ)

// minimum and maximum frequency to consider
#define MINFREQ 300
#define MAXFREQ 2000

#define MINCOEF (FRAME_TLEN * MINFREQ)
//#define MAXCOEF (FRAME_TLEN * MAXFREQ)

// normalize power (volume) of a wave file.
// minimum and maximum rms to normalize from.
#define MINRMS 0.1
#define MAXRMS 3

// wave file header
// This header should be 44 bytes
typedef struct WavHeader_t {
	unsigned int RIFF; // "RIFF"
	unsigned int chunksize; // in bytes
	unsigned int WAVE; // "WAVE"

	unsigned int subchunk1id; // "fmt "
	unsigned int subchunk1size; // 16 for pcm
	unsigned short int audioformat; // PCM = 1 (no compression)
	unsigned short int nchannels; // 1 or 2
	unsigned int samplerate; // sample rate
	unsigned int byterate; // = sameplerate * nchannels * bitespersample / 8
	unsigned short int blockalign; // = nchannels * bitspersample / 8
	unsigned short int bitspersample; // 8 or 16

	unsigned int subchunk2id; // "data"
	unsigned int subchunk2size; // = nsamples * nchannels * bitspersample / 8
	
} WavHeader;

/** Read a wav file.  Convert to float of range [-1, 1], mono.
    Returns pointer to data, number of samples read, and sample frequency. */
float * wavread(char * fn, unsigned int * nsamples, unsigned int * freq) {
	assert(fn);
	assert(nsamples);
	assert(freq);

	FILE * f = fopen(fn, "rb");
	if (!f) return NULL;

	WavHeader header;

	fread(&header, sizeof(WavHeader), 1, f);

	if (header.RIFF != 0x46464952) {
		printf("Not a RIFF file.\n");
		return NULL;
	}

	if (header.WAVE != 0x45564157) {
		printf("Not a WAVE file.\n");
		return NULL;
	}

	if (header.subchunk1id != 0x20746d66) {
		printf("Incorrect format chunk id.\n");
		return NULL;
	}

	if (header.subchunk1size != 16) {
		printf("Incorrect WAVE chunk size - not PCM.\n");
		return NULL;
	}

	if (header.audioformat != 1) {
		printf("Unrecognized audio format - not PCM uncompressed.\n");
		return NULL;
	}

	if (header.subchunk2id != 0x61746164) {
		printf("Incorrect data chunk id.\n");
		return NULL;
	}


	if (header.bitspersample != 16) {
		printf("Sorry, I only know how to read 16 bits per sample wave files.\n");
		return NULL;
	}

	*nsamples = header.subchunk2size / (header.nchannels * header.bitspersample / 8);

	*freq = header.samplerate;

	printf("  Bytes: %d   Samples: %d   Time: %0.2fs\n  Channels: %d   Sample rate: %d   BitsPerSample: %d\n",
	       header.subchunk2size, *nsamples, (float) *nsamples / header.samplerate, header.nchannels, header.samplerate,
	       header.bitspersample);

	float * samples = (float *) malloc(sizeof(float) * *nsamples);

	unsigned int samplesleft = *nsamples;

	unsigned int BLOCKSIZE = 4096;

	while (samplesleft > 0) {
		short int block[BLOCKSIZE];
		unsigned int nread = fread(block, sizeof(short int),
					   MIN(BLOCKSIZE, samplesleft * header.nchannels), f);

		if (header.nchannels == 1) {
			for (unsigned int i = 0; i < nread; i++) {
				samples[*nsamples - samplesleft + i] = 
					(float) block[i] / (float) SHRT_MAX;
			}
			
		} else { // assume channels == 2
			for (unsigned int i = 0; i < nread; i += 2) {
				//printf("%d %d\n", block[i], block[i+1]);
				samples[*nsamples - samplesleft + i/2] = 
					((float) block[i] + block[i+1])
					/ ((float) SHRT_MAX * 2.0);
			}
		}

		samplesleft -= nread / header.nchannels;

	}

	/*
	for (unsigned int i = 1000000; i < 2000000; i += 100)
		printf("%f\n", samples[i]);
	*/

	fclose(f);

	return samples;
	
}

// Filter length for the following filters.
#define FILTERLEN44 31
#define FILTERLEN11 17

/* Low pass filter for taking 44100Hz to 5512.5 Hz */
float lp_filter44[] = {
  -6.4796e-04, -1.4440e-03, -2.7023e-03, -4.4407e-03, -6.1915e-03, -6.9592e-03
, -5.3707e-03,  2.3907e-18,  1.0207e-02,  2.5522e-02,  4.5170e-02,  6.7289e-02
,  8.9180e-02,  1.0778e-01,  1.2027e-01,  1.2467e-01,  1.2027e-01,  1.0778e-01
,  8.9180e-02,  6.7289e-02,  4.5170e-02,  2.5522e-02,  1.0207e-02,  2.3907e-18
, -5.3707e-03, -6.9592e-03, -6.1915e-03, -4.4407e-03, -2.7023e-03, -1.4440e-03
, -6.4796e-04

};

/* Low pass filter for taking 11025Hz to 5512.5 Hz */
float lp_filter11[] = {
  -1.5619828e-18, -5.2391811e-03,  4.1925742e-18,  2.3211102e-02, -1.0543384e-17,
  -7.6105846e-02,  1.6894193e-17,  3.0769878e-01,  5.0087029e-01,  3.0769878e-01,
   1.6894193e-17, -7.6105846e-02, -1.0543384e-17,  2.3211102e-02,  4.1925742e-18,
  -5.2391811e-03, -1.5619828e-18
};

/* Convolve a sample with a filter at a point. */
inline float convpt(float * start, float * filter, unsigned int flen) {
	float sum = 0;

	for (unsigned int i = 0; i < flen; i++)
		sum += *(start + i) * filter[i];

	return sum;
}

/* Downsample from high sample rate to low sample rate (DFREQ). */
float * downsample(float * samples, unsigned int * nsamples, int freq) {

	unsigned int newnsamples, mult;

	if (freq == OFREQ1) {
		newnsamples = *nsamples / OFREQ1MULT - 3;
		mult = OFREQ1MULT;
	} else { // freq == OFREQ2 
		newnsamples = *nsamples / OFREQ2MULT - 9;
		mult = OFREQ2MULT;
	}

	float * newsamples = (float *) malloc(sizeof(float) * newnsamples);
	
	if (freq == OFREQ1)
		for (unsigned int i = 0; i < newnsamples; i++)
			newsamples[i] = convpt(samples + mult * i, lp_filter44, FILTERLEN44 );
	else
		for (unsigned int i = 0; i < newnsamples; i++)
			newsamples[i] = convpt(samples + mult * i, lp_filter11, FILTERLEN11);
	
	*nsamples = newnsamples;
	return newsamples;
}

/** normalize 10*RMS power to be 1.  10 is determined empirically
	from pop cd music.
*/
 
void normpower(float * samples, unsigned int nsamples) {
	double squares = 0;

	for (unsigned int i = 0; i < nsamples; i++) {
		//printf(" sample %d: %f\n", i, samples[i]);

		squares += samples[i] * samples[i];
	}

	// we don't want to normalize by the real rms, because excessive clipping will occurr
	float rms = sqrt(squares / (double) nsamples) * 10;

	printf("10*RMS: %f\n", rms);

	if (rms < MINRMS)
		rms = MINRMS;
	if (rms > MAXRMS)
		rms = MAXRMS;

	for (unsigned int i = 0; i < nsamples; i++) {
		samples[i] /= rms;

		samples[i] = MIN(samples[i], 1);
		samples[i] = MAX(samples[i], -1);

	}

}

/** Compute windowed fft of samples using the FFTW3 library.
	Convert to bands.
 */
float ** wdft(float * samples, unsigned int nsamples, unsigned int * nframes) {
	nsamples = (nsamples / OVERLAPSAMPLES) * OVERLAPSAMPLES;
	*nframes = (nsamples - FRAMESIZE) / OVERLAPSAMPLES;

	float ** frames = (float **) malloc(sizeof(float *) * *nframes);

	//printf("nframes: %d\n", *nframes);

	for (unsigned int i = 0; i < *nframes; i++) {
		frames[i] = (float *) malloc(sizeof(float) * NBANDS);
	}
	fftw_plan p;
	fftw_complex * out;
	double * in;
	in = (double *) fftw_malloc(sizeof(double) * FRAMESIZE);
	out = (fftw_complex *) fftw_malloc(sizeof(fftw_complex) * (FRAMESIZE/2 + 1));
	
	// in destroyed when line executed
	p = fftw_plan_dft_r2c_1d(FRAMESIZE, in, out, FFTW_ESTIMATE); // FFTW_ESTIMATE or FFTW_MEASURE


	float base = exp(log((float) MAXFREQ / (float) MINFREQ) / (float) NBANDS);

	for (unsigned int i = 0; i < *nframes; i++) {
		for (unsigned int j = 0; j < FRAMESIZE; j++)
			in[j] = samples[i * OVERLAPSAMPLES + j];

		fftw_execute(p);
		

		//printf("mincoef %f\n", MINCOEF);

		for (unsigned int k = 0; k < FRAMESIZE / 2 + 1; k++) {
			out[k][0] /= (float) FRAMESIZE / 2.0;
			out[k][1] /= (float) FRAMESIZE / 2.0;
			//printf("P Frame %d  C%d: %e\n", i, k, out[k][0] * out[k][0] + out[k][1] * out[k][1]);

		}


		// compute bands
		for (unsigned int j = 0; j < NBANDS; j++) {
			unsigned int start = (unsigned int) ((pow(base, (float) j) - 1.0) * MINCOEF);
			unsigned int end = (unsigned int) ((pow(base, (float) j+1.0f) - 1.0) * MINCOEF);
			
			//printf("band %d  start %d end %d\n", j,
			//       start+1, end+1);

			frames[i][j] = 0;


			// WARNING: We're double counting the last one here.
			// this bug is to match matlab's implementation bug in power2band.m
			for (unsigned int k = start + (unsigned int) MINCOEF; k <= end + (unsigned int) MINCOEF; k++) {
				//out[k][0] /= (float) FRAMESIZE / 2.0;
				//out[k][1] /= (float) FRAMESIZE / 2.0;
				frames[i][j] +=  out[k][0] * out[k][0] + out[k][1] * out[k][1];
				//printf("P:% d %d %e\n", i, k,  (out[k][0] * out[k][0] + out[k][1] * out[k][1]));
			}

			// WARNING: if we change the k<=end to k<end above, we need to change the following line
			frames[i][j] /= (float) (end - start + 1);
			
			//printf("Frame %d Band %d: %f\n", i, j, frames[i][j] * 1000); 
		}
		
	}
	
	fftw_destroy_plan(p);
	
	fftw_free(in);
	fftw_free(out);

	return frames;
}

/** Compute "integral image" of banded power. */
void integralimage(float ** frames, unsigned int nframes) {
	for (unsigned int y = 1; y < nframes; y++) {
		frames[y][0] += frames[y-1][0];
	}

	for (unsigned int x = 1; x < NBANDS; x++) {
		frames[0][x] += frames[0][x-1];
	}

	for (unsigned int y = 1; y < nframes; y++) {
		for (unsigned int x = 1; x < NBANDS; x++) {
			frames[y][x] += frames[y-1][x] + frames[y][x-1] - frames[y-1][x-1];
		}
	}
}

/** Convert bands to bits, using the supplied filters. */
unsigned int * computebits(vector<Filter> & f, float ** frames, unsigned int nframes,
			   unsigned int * nbits) {

	unsigned int first_time = KEYWIDTH / 2 + 1;
	unsigned int last_time = nframes - KEYWIDTH / 2;

	*nbits = last_time - first_time + 1;

	unsigned int * bits = (unsigned int *) malloc(sizeof(unsigned int) * *nbits);
       
	for (unsigned int t2 = first_time; t2 <= last_time; t2++) {
		bitset<32> bt;

		for (unsigned int i = 0; i < f.size(); i++) {
			// we subtract 1 from t1 and b1 because we use integral images
		
			unsigned int t1 = (unsigned int) ((float) t2 - f[i].wt / 2.0 - 1);
			unsigned int t3 = (unsigned int) ((float) t2 + f[i].wt / 2.0 - 1);
			unsigned int b1 = f[i].first_band;
			unsigned int b2 = (unsigned int) round((float) b1 + f[i].wb / 2.0) - 1;
			unsigned int b3 = b1 + f[i].wb - 1;
			b1--;

			
			unsigned int t_1q = (t1 + t2) / 2; // one quarter time 
			unsigned int t_3q = t_1q + (t3 - t1 + 1) / 2; // three quarter time
			unsigned int b_1q = (b1 + b2) / 2; // one quarter band
			unsigned int b_3q = b_1q + (b3 - b1) / 2; // three quarter band

			
			/*
			printf("t1 %d  t2 %d  t3 %d  b1 %d  b2 %d  b3 %d\n",
			       t1, t2, t3, b1, b2, b3);
			*/
			float X = 0;
			
			// we should check from t1 > 0, but in practice, this doesn't happen
			// we subtract 1 from everything because this came from matlab where indices start from 1
			switch (f[i].filter_type) {
			case 1: { // total energy
				if (b1 > 0)
					X = frames[t3-1][b3-1] - frames[t3-1][b1-1]
						- frames[t1-1][b3-1] + frames[t1-1][b1-1];
				else
					X = frames[t3-1][b3-1] - frames[t1-1][b3-1];
				break;
			}
			case 2: { // energy difference over time
				if (b1 > 0)
					X = frames[t1-1][b1-1] - 2*frames[t2-2][b1-1]
						+ frames[t3-1][b1-1] - frames[t1-1][b3-1]
						+ 2*frames[t2-2][b3-1] - frames[t3-1][b3-1];
				else
					X = - frames[t1-1][b3-1] + 2*frames[t2-2][b3-1]
						- frames[t3-1][b3-1];
				break;
			
			}
			case 3: { // energy difference over bands
				if (b1 > 0)
					X = frames[t1-1][b1-1] - frames[t3-1][b1-1]
						- 2*frames[t1-1][b2-1] + 2*frames[t3-1][b2-1]
						+ frames[t1-1][b3-1] - frames[t3-1][b3-1];
				else
					X = -2*frames[t1-1][b2-1] + 2*frames[t3-1][b2-1]
						+ frames[t1-1][b3-1] - frames[t3-1][b3-1];
				break;	
			}
			case 4: {
				// energy difference over time and bands
				if (b1 > 0)
					X = frames[t1-1][b1-1] - 2*frames[t2-2][b1-1]
						+ frames[t3-1][b1-1] - 2*frames[t1-1][b2-1]
						+ 4*frames[t2-2][b2-1] - 2*frames[t3-1][b2-1]
						+ frames[t1-1][b3-1] - 2*frames[t2-2][b3-1]
						+ frames[t3-1][b3-1];
				else
					X = -2*frames[t1-1][b2-1] + 4*frames[t2-2][b2-1]
						- 2*frames[t3-1][b2-1] + frames[t1-1][b3-1]
						- 2*frames[t2-2][b3-1] + frames[t3-1][b3-1];
				break;	
			}
			case 5: { // time peak
				if (b1 > 0)
					X = -frames[t1-1][b1-1] + 2*frames[t_1q-1][b1-1]
						- 2*frames[t_3q-1][b1-1] + frames[t3-1][b1-1]
						+ frames[t1-1][b3-1] - 2*frames[t_1q-1][b3-1]
						+ 2*frames[t_3q-1][b3-1] - frames[t3-1][b3-1];
				else
					X = frames[t1-1][b3-1] - 2*frames[t_1q-1][b3-1]
						+ 2*frames[t_3q-1][b3-1] - frames[t3-1][b3-1];
						
				break;
			}
			case 6: { // band beak
				if (b1 > 0)
					X = -frames[t1-1][b1-1] + frames[t3-1][b1-1]
						+ 2*frames[t1-1][b_1q-1] - 2*frames[t3-1][b_1q-1]
						- 2*frames[t1-1][b_3q-1] + 2*frames[t3-1][b_3q-1]
						+ frames[t1-1][b3-1] - frames[t3-1][b3-1];
				else
					X = + 2*frames[t1-1][b_1q-1] - 2*frames[t3-1][b_1q-1]
						- 2*frames[t1-1][b_3q-1] + 2*frames[t3-1][b_3q-1]
						+ frames[t1-1][b3-1] - frames[t3-1][b3-1];

				break;
			}
			}

			bt[i] = X > f[i].threshold;

			//printf("Frame %d Bits: %d %f %f %d\n", t2 - 1, i, X, f[i].threshold, bt[i] ? 1 : 0);

		}

		bits[t2 - first_time] = bt.to_ulong();

	}

	return bits;
}

unsigned int * wav2bits(vector<Filter> & filters, float * samples,
			unsigned int nsamples, unsigned int freq,
			unsigned int * nbits) {

	if (freq != OFREQ1 && freq != OFREQ2 && freq != DFREQ) {
		printf("Error: I only support 44100Hz or 11025Hz or 5513Hz samples rates.\n");
		return 0;
	}

	float * dsamples;

	if (freq == OFREQ1 || freq == OFREQ2) {
		printf("Downsampling to 5512.5 KHz...\n");
		dsamples = downsample(samples, &nsamples, freq);
	} else {
		dsamples = (float *) malloc(sizeof (float) * nsamples);
		memcpy(dsamples, samples, sizeof(float) * nsamples);
	}

	printf("  Got %d samples.\n", nsamples);
	// dsamples now at 5512.5 Hz sample rate
	
	printf("Normalizing power...\n");
	normpower(dsamples, nsamples);

	printf("Calculating windows DFT's...\n");

	//for (unsigned int i = 1000; i < 030; i++)
	//	printf("D Sample %d: %f\n", i, dsamples[i]);
	

	unsigned int nframes;
	float ** frames = wdft(dsamples, nsamples, &nframes);
	free(dsamples);

	printf("Computing integral image on %d frames...\n", nframes);
	integralimage(frames, nframes);
	
	printf("Computing bit descriptors...\n");
	unsigned int * bits = computebits(filters, frames, nframes, nbits);

	printf("  Got %d descriptors.\n", *nbits);

	for (unsigned int i = 0; i < nframes; i++)
		free(frames[i]);

	free(frames);

	return bits;
}

