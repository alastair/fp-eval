/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
Author: Yan Ke
August 2004
*/

#define _FILE_OFFSET_BITS 64


#include <assert.h>
#include <iostream>
#include "keypointdb.h"

using namespace std;

/** Builds filelist db and keypoints db from individual files */
int main(int argc, char * argv[])
{
        if (argc != 4 ) {
                printf("Usage: %s fileslist.txt db.fdb db.kdb\n", argv[0]);
                return -1;
        }

	char * keyslist = argv[1];
	char * fl_dbfn = argv[2];
	char * keys_dbfn = argv[3];

	KeypointDB kdb(keyslist, fl_dbfn, keys_dbfn);

        return 0;

}
