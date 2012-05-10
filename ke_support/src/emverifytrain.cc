/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */

/*
Author: Yan Ke
August 2004
*/

#include <assert.h>
#include <stdarg.h>
#include <string>
#include <vector>
#include <bitset>

using namespace std;

#define NF 32
	
class emverifytrainer {
private:
	/* vector of songs
	     vector of key pairs
	       pair of <original, recorded>
	 */
	vector<vector<unsigned int> > data;

	/* class labels.  1.0 = music,  0.0 = noise */
	vector<vector<float> > labels;

	float alpha1[NF];
	float alpha2[NF];
	float theta1;
	float theta2;
	
	float PYi1;
	float PYi0; 

	FILE * outfile;

	void readData(FILE * f) {
		unsigned int numsongs;
		fread(&numsongs, 4, 1, f);
		data.resize(numsongs);

		printf("Reading %d songs\n", numsongs);

		for (unsigned int i = 0; i < numsongs; i++) {
			unsigned int numkeys;
			fread(&numkeys, 4, 1, f);

			data[i].resize(numkeys);

			for (unsigned int j = 0; j < numkeys; j++)
				fread(&(data[i][j]), 4, 1, f);
		}
	}

	void initPriors() {
		printf("Initializing priors.\n");
		theta1 = 0.9;
		theta2 = 0.1;
		
		for (unsigned int i = 0; i < NF; i++) {
			alpha1[i] = 0.1;
			alpha2[i] = 0.5;
		}

		PYi1 = 0.50;
		PYi0 = 1 - PYi1;
	}

	void initClassLables() {
		printf("Initializing class labels.\n");
		labels.resize(data.size());
		
		for (unsigned int i = 0; i < data.size(); i++) {
			labels[i].resize(data[i].size());

			for (unsigned int j = 0; j < data[i].size(); j++) {
				//printf("    Data %d\n", j);
				bitset<NF> dist = data[i][j];

				float PXj_Yj1 = 1;
				float PXj_Yj0 = 1;
				for (unsigned int k = 0; k < NF; k++) {
					//printf("      Bit %d\n", k);
					PXj_Yj1 *= dist[k] ? alpha1[k] : (1.0 - alpha1[k]);
					PXj_Yj0 *= dist[k] ? alpha2[k] : (1.0 - alpha2[k]);
				}

				labels[i][j] = PXj_Yj1 * PYi1 /
					(PXj_Yj1 * PYi1 + PXj_Yj0 * PYi0);

				//printf("      Dist %d  Value %f\n", dist.count(), labels[i][j]);
			}
		}
	}
	
	void MStep() {
		// learn theta1 and theta2
		float theta1a = 0, theta1b = 0, theta2a = 0, theta2b = 0;

		for (unsigned int i = 0; i < labels.size(); i++) {
			for (unsigned int j = 0; j < labels[i].size() - 1; j++) {
				theta1a += labels[i][j] * labels[i][j+1];
				theta1b += labels[i][j] * (1.0 - labels[i][j+1]);

				theta2a += (1.0 - labels[i][j]) * labels[i][j+1];
				theta2b += (1.0 - labels[i][j]) * (1.0 - labels[i][j+1]);
			}
		}

		theta1 = theta1a / (theta1a + theta1b);
		theta2 = theta2a / (theta2a + theta2b);
	
		// learn alpha1k and alpha2k

		for (unsigned int i = 0; i < NF; i++) {
			alpha1[i] = 0;
			alpha2[i] = 0;
		}

		float county1 = 0;
		float county0 = 0;
		int totalcount = 0;
		for (unsigned int i = 0; i < labels.size(); i++) {
			for (unsigned int j = 0; j < labels[i].size(); j++) {
				bitset<NF> dist = data[i][j];
				for (unsigned int k = 0; k < NF; k++) {
					alpha1[k] += (dist[k] ? 1.0 : 0.0) * labels[i][j];
					alpha2[k] += (dist[k] ? 1.0 : 0.0) * (1.0 - labels[i][j]);
				}

				county1 += labels[i][j];
				county0 += 1.0 - labels[i][j];
				totalcount++;
			}
		}

		for (unsigned int i = 0; i < NF; i++) {
			alpha1[i] /= county1;
			alpha2[i] /= county0;
		}

		PYi1 = county1/totalcount;
		PYi0 = county0/totalcount;
		printf("  PY1: %f\tPY0: %f\n", PYi1, PYi0);
	}

	void EStep() {
		for (unsigned int i = 0; i < data.size(); i++) {
			// first set Y0 for each song
			bitset<NF> dist = data[i][0];
			
			float PXj_Yj1 = 1;
			float PXj_Yj0 = 1;
			for (unsigned int k = 0; k < NF; k++) {
				//printf("      Bit %d\n", k);
				PXj_Yj1 *= dist[k] ? alpha1[k] : (1.0 - alpha1[k]);
				PXj_Yj0 *= dist[k] ? alpha2[k] : (1.0 - alpha2[k]);
			}
			labels[i][0] = PXj_Yj1 * PYi1 /
				(PXj_Yj1 * PYi1 + PXj_Yj0 * PYi0);
			
			// Now set Yj, j > 0
			for (unsigned int j = 1; j < data[i].size(); j++) {
                                //printf("    Data %d\n", j);
				dist = data[i][j];

				PXj_Yj1 = 1;
				PXj_Yj0 = 1;
				for (unsigned int k = 0; k < NF; k++) {
					//printf("      Bit %d\n", k);
					PXj_Yj1 *= dist[k] ? alpha1[k] : (1.0 - alpha1[k]);
					PXj_Yj0 *= dist[k] ? alpha2[k] : (1.0 - alpha2[k]);
				}

				float PXjNYj1 = PXj_Yj1 * (theta1 * labels[i][j-1]
							   + theta2 * (1.0 - labels[i][j-1]));
				float PXjNYj0 = PXj_Yj0 * ((1.0 - theta1) * labels[i][j-1]
							   + (1.0 - theta2) * (1.0 - labels[i][j-1])) ;

				labels[i][j] = PXj_Yj1 * (theta1 * labels[i][j-1] + theta2 * (1.0 - labels[i][j-1]))
					/ (PXjNYj1 + PXjNYj0);
			}
		}	
	}

	void printParams() {
		printf("  Theta 1: %f\tTheta2: %f\n", theta1, theta2);
		float alpha1sum = 0, alpha2sum = 0;
		for (unsigned int i = 0; i < NF; i++) {
			printf("  %d Alpha1: %f\tAlpha2: %f\n", i, log(alpha1[i]), log(alpha2[i]));
			//printf("  Alpha2 %d: %f\n", i, alpha2[i]);
			alpha1sum += alpha1[i];
			alpha2sum += alpha2[i];
		}

		printf("  Alpha 1 sum: %f\tAlpha 2 sum: %f\n", alpha1sum, alpha2sum);

	}

	void writeParams() {
		printf("Writing learned parameters to file.\n");

		unsigned int nf = NF;
		fwrite(&nf, 4, 1, outfile);

		fwrite(alpha1, 4, NF, outfile);
		fwrite(alpha2, 4, NF, outfile);
		fwrite(&theta1, 4, 1, outfile);
		fwrite(&theta2, 4, 1, outfile);
		fwrite(&PYi1, 4, 1, outfile);
		fwrite(&PYi0, 4, 1, outfile);
	}

public:

	emverifytrainer(FILE * f, FILE * f2) {
		readData(f);
		initPriors();
		initClassLables();
		outfile = f2;
	}

	void run(unsigned int numiter) {
		for (unsigned int i = 0; i < numiter; i++) {
			printf("******* Iteration %d **********\n", i);
			MStep();
			printParams();
			EStep();
		}

		writeParams();
	}

};

int main(int argc, char * argv[])
{
        if (argc != 3 ) {
                printf("Usage: %s keypointpairs.kpr paramout.bin\n", argv[0]);
                return -1;
        }

	FILE * f = fopen(argv[1], "rb");
	assert(f);
	
	FILE * f2 = fopen(argv[2], "wb");
	assert(f2);

	emverifytrainer et(f, f2);

	et.run(40);

	fclose(f);

	fflush(f2);
	fclose(f2);
}
