/*
Author: Yan Ke
August 2004
*/

#include <stdio.h>
#include <assert.h>

#include <iostream>
#include <map>
using namespace std;

// CSAPP Unix library header
#include "csapp.h"


#include "sigproc.h"
#include "keypointdb.h"
#include "directhash.h"
#include "util.h"
#include "verify.h"

/** Minimum ratio of (# Keys matched in a song) / (# Query keys) for
    a song to be considered for RANSAC verification. */
#define MMATCH2 0.5

/** Maximum umber of songs to return, if we decide to choose more than one. */
#define MAXNUMSONGS 3

/** Choose the top 1 song based on confidence score, out of list of songs.
    Assumes the lower the score, the better the confidence. */
map<unsigned int, vsong> chooseBestSong(map<unsigned int, vsong> & scores) {
        map<unsigned int, vsong> ret;

        unsigned int minf = 0;
        float minscore = INT_MAX;

        for (map<unsigned int, vsong>::iterator it = scores.begin();
             it != scores.end(); it++) {
                if (it->second.score < minscore) {
                        minf = it->first;
                        minscore = it->second.score;
                }
        }

        if (minscore != INT_MAX)
                ret[minf] = scores[minf];

        return ret;
}

/** Choose the top N songs based on confidence score, out of list of songs.
    Assumes the lower the score, the better the confidence. */
map<unsigned int, vsong> chooseBestNSongs(map<unsigned int, vsong> & scores, unsigned int n) {
      	map<unsigned int, vsong> ret;

	multimap<float, unsigned int> sortedscores;
	
	for (map<unsigned int, vsong>::iterator it = scores.begin();
	     it != scores.end(); it++) {
		sortedscores.insert(pair<float, unsigned int> (it->second.score, it->first));
	}

	unsigned int count = 0;
	for (map<float, unsigned int>::iterator it = sortedscores.begin();
	     it != sortedscores.end(); it++) {
		if (count < n)
			ret[it->second] = scores[it->second];
		count++;
	}

        return ret;
}

/** Prints number of keys matched per song, sorted by number of keys.
    Could be slow, so don't call too often. */
void printcountstats(map<unsigned int, float> & matches,
                     KeypointDB & kdb) {
        // map match score -> file id
        multimap<float, unsigned int> counts;
	for (map<unsigned int, float>::iterator it = matches.begin();
             it != matches.end(); ++it) {
                counts.insert(pair<float, unsigned int>(it->second, it->first));
        }

        for (multimap<float, unsigned int>::iterator it = counts.begin();
             it != counts.end(); ++it)
                printf("File %d: %f\t%s\n", it->second, it->first,
                       basename(kdb.getFileName(it->second)).c_str());
}

/** Prints number of keys matched per song, sorted by number of keys.
    Could be slow, so don't call too often. */
void printcountstats(map<unsigned int, vsong> & matches,
                     KeypointDB & kdb) {
        // map match score -> file id
        multimap<float, unsigned int> counts;

        for (map<unsigned int, vsong>::iterator it = matches.begin();
             it != matches.end(); ++it) {
                counts.insert(pair<float, unsigned int>(it->second.score, it->first));
        }

        for (multimap<float, unsigned int>::iterator it = counts.begin();
             it != counts.end(); ++it)
                printf("File %d: %f\t%s\n", it->second, it->first,
                       basename(kdb.getFileName(it->second)).c_str());

}

/** Converts little endian to big endian and vice versa. */
void swapendian(char * buf, int len) {
	char tmp;

	if (len == 4) {
		tmp = buf[0];
		buf[0] = buf[3];
		buf[3] = tmp;
		tmp = buf[2];
		buf[2] = buf[1];
		buf[1] = tmp;
	} else if (len == 2) {
		tmp = buf[1];
		buf[1] = buf[0];
		buf[0] = tmp;
	} else
		assert(false);
}

/** Reads in wave samples from the socket.  Convert to float [-1.0, 1.0] representation. */
float * ReadFromSocket(int connfd, unsigned int * nsamples,
		       unsigned int * freq) {
	char buf[MAXLINE];
	rio_t rio;

	Rio_readinitb(&rio, connfd);
	
	Rio_readnb(&rio, buf, 8);
	swapendian(buf, 4);
	int nbytes = * ((int *) buf);
	printf("Byte length: %d\n", nbytes);

	*nsamples = nbytes / 2;

	swapendian(buf + 4, 4);
	*freq = * ((int *) (buf + 4));
	printf("Sample rate: %d\n", *freq);
	
	float * samples = (float *) malloc (sizeof(float) * *nsamples);

	int count = 0;
	int size = 1;

	printf("Reading %d samples...\n", *nsamples);

	while (nbytes > 0 && size > 0) {
		size = Rio_readnb(&rio, buf, MIN(MAXLINE, nbytes));

                if (size < 0) {
			printf("Error in reading...\n");
			continue;
		}
		
		//printf("Read %d bytes\n", size);

		for (int i = 0; i < size; i += 2) {
			samples[count + i/2] = (float) (buf[i] * 256 + (buf[i+1] & 0xff))
				/ (float) SHRT_MAX;
		
		}

		count += size / 2;
		nbytes -= size;
		
		//printf("%d bytes left,  at sample %d\n", nbytes, count);
	}

	return samples;
}

/** Strips out directory info and extension from a file name. */
string basename2(string fn) {
	if (fn.substr(fn.size() - 4) == ".key")
		fn = fn.substr(0, fn.size() - 4);
	
	if (fn.substr(fn.size() - 4) == ".wav")
		fn = fn.substr(0, fn.size() - 4);
	
	size_t pos = fn.rfind("/");
	

	string ret = fn.substr(pos+1);
			       
	//cout << "BASE: " << ret << endl;

	return ret;
}

/** Write an integer to the socket, in big endian format. */
void writeInt(int connfd, int data) {
	char buf[4];
	memcpy(buf, &data, 4);
	swapendian(buf, 4);
	Rio_writen(connfd, buf, 4);
}


/** Write song information to the socket, in the following format.

Data written

Bytes  DataType  Descr
4      int       Number of songs

for each song:
11     char      cddb id, underscore, track #.  Example "1234567A_08"
4      int       db start frame
4      int       db end frame
4      int       query start frame
4      int       query end frame
4      int       string length
x      char      string

*/

void writeResults(map<unsigned int, vsong> & scores, KeypointDB & kdb,
		  int connfd) {

	char buf[MAXLINE];

	int numsongs = scores.size();
	
	printf("Writing %d songs.\n", scores.size());

	writeInt(connfd, numsongs);

	if (! scores.empty()) {
		multimap<float, unsigned int> sortedscores;
		
		for (map<unsigned int, vsong>::iterator it = scores.begin();
		     it != scores.end(); it++) {
			sortedscores.insert(pair<float, unsigned int> (it->second.score, it->first));
		}

		for (map<float, unsigned int>::iterator it = sortedscores.begin();
		     it != sortedscores.end(); it++) {
			//printf("  Writing song id: %d\n", it->second);
			memcpy(buf, basename(kdb.getFileName(it->second)).c_str(), 11);
			Rio_writen(connfd, buf, 11);

			vsong song = scores[it->second];
			writeInt(connfd, song.db_frame_start);
			writeInt(connfd, song.db_frame_end);
			writeInt(connfd, song.query_frame_start);
			writeInt(connfd, song.query_frame_end);

			/*
			printf("  DBS: %d   DBE: %d  QS: %d  QE: %d\n",
			       song.db_frame_start, song.db_frame_end, song.query_frame_start,
			       song.query_frame_end);
			*/

			char scorebuf[MAXLINE];
			sprintf(scorebuf, "%0.2f ", it->first);

			//string name = string(scorebuf) + basename2(kdb.getFileName(it->second));
			string name = basename2(kdb.getFileName(it->second));
 
			int namelen = name.size();
			writeInt(connfd, namelen);

			memcpy(buf, name.c_str(), namelen);
			Rio_writen(connfd, buf, namelen);
		}
	}
}

/** Main loop.

Accepts incoming connections.
Reads wave.
Convert to bits.
Queries database.
Write results.

Repeat.

*/

void mainloop(vector<Filter> filters, KeypointDB & kdb, SearchStrategy * search,
	      int port, emparams & params) {

        int listenfd;

	printf("Listening on port %d\n", port);
		listenfd = Open_listenfd(port);

	while (true) {
		struct sockaddr_in clientaddr;
		int clientlen = sizeof(clientaddr);

		printf("Waiting for connection...\n");

		int connfd = Accept(listenfd, (SA *)&clientaddr, &clientlen);
		printf("Connection established to %s:%d on fd %d\n",
		       inet_ntoa(clientaddr.sin_addr), clientaddr.sin_port,
		       connfd);

		unsigned int nsamples = 0, freq = 0;
		float * samples = ReadFromSocket(connfd, &nsamples, &freq);

		if (samples == NULL) {
			printf("Invalid packet received.\n");
			Close(connfd);
			continue;
		} else {
			printf("Read %d samples at %d sample rate\n",
			       nsamples, freq);
		}

		unsigned int nbits;
		unsigned int * bits = wav2bits(filters, samples, nsamples,
					       freq, &nbits);
		free(samples);
	
		vector<Keypoint *> qkeys = bitsToKeys(bits, nbits);
		free(bits);

		vector<Keypoint *> rkeys = FindMatches(search, qkeys, 0);
		map<unsigned int, vector<Keypoint *> > fkeys
			= FilterMatches(rkeys, (int) (MMATCH2 * qkeys.size()));
                 
                cout << "After min matches..." << endl;
 
                //printcountstats(fkeys, kdb);
                 

		//map<unsigned int, vsong> scores = verify4(fkeys, qkeys, kdb);
                //cout << "After BER verfication..." << endl;
 		//printcountstats(scores, kdb);
	
		map<unsigned int, vsong> scoresem = verify4em(fkeys, qkeys, kdb, params);
		cout << "After EM verfication..." << endl;
 		printcountstats(scoresem, kdb);
		

		//scores = chooseBestNSongs(scoresem, MAXNUMSONGS);
		
		map<unsigned int, vsong> scores = chooseBestSong(scoresem);

		DeleteKeys(qkeys);

		printf("Writing results...\n");

		writeResults(scores, kdb, connfd);

		Close(connfd);
	}
}


int main(int argc, char * argv[]) {
  
	if (argc != 6 && argc != 5) {
		printf("Usage: %s descriptors.txt db.fdb db.kdb emparams.bin [port]\n", argv[0]);
		return 0;
	}

	char * descrfn = argv[1];
	char * fdbfn = argv[2];
	char * kdbfn = argv[3];
	char * emparamfn =argv[4];
	
	int port = 2000;

/* test code for char[2] -> short int conversion
	for (short int i = SHRT_MIN; i < SHRT_MAX; i++) {
		char * buf = (char* )&i;
		float b = (float) (buf[1] * 256 + (buf[0] & 0xff)) / (float) SHRT_MAX;
		float c = (float) i / (float) SHRT_MAX;
		if (fabs(b - c) > 0.00001)
			printf("%d %f %f\n", i, b , c);
	}

	return 0;
*/	

	if (argc == 6)
		port = atoi(argv[5]);

	emparams params = readEMParams(emparamfn);

	vector<Filter> filters = readFilters(descrfn);
	
	if (filters.size() == 0) {
		printf("Error reading descriptors.\n");
		return 0;
	}

	// Reads in the keypoint database from disk. 
	KeypointDB kdb(fdbfn, kdbfn);

	// Builds a hash table from the keypoints
	DirectHash table(&kdb);
	SearchStrategy * search = &table;

	mainloop(filters, kdb, search, port, params);
       
	return 0;  
  
}



