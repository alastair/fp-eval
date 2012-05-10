bin_PROGRAMS =  builddb codewav mrserver emalignsongs emverifytrain align

builddb_SOURCES = builddb.cc keypoint.cc keypoint.h keypointdb.cc keypointdb.h

dist_data_DATA = Doxyfile emparams3.bin boostdescr3.txt makekeys.sh

align_SOURCES = align.cc keypoint.cc keypoint.h keypointdb.h keypointdb.cc util.cc util.h verify2.cc search.h directhash.cc directhash.h

codewav_SOURCES = codewav.cc sigproc.h sigproc.cc util.h keypoint.h keypoint.cc filters.h filters.cc

mrserver_SOURCES = mrserver.cc sigproc.h sigproc.cc util.h keypoint.h keypoint.cc filters.h filters.cc csapp.cc csapp.h keypointdb.cc keypointdb.h directhash2.cc directhash.h util.cc verify4.cc verify4em.cc verify.h

emalignsongs_SOURCES = emalignsongs.cc keypoint.cc keypoint.h keypointdb.cc keypointdb.h util.cc util.h directhash.cc directhash.h verify2.cc verify.h

emverifytrain_SOURCES = emverifytrain.cc

AM_CXXFLAGS = -Wall -O3 -D _LARGEFILE_SOURCE

# Memory check, but slow
#CXXFLAGS += -DMALLOC_CHECK_=2

# Profiling
#CXXFLAGS += -pg

# No asserts
# AM_CXXFLAGS += -DNDEBUG

# Add electric fence
# AM_CXXFLAGS += -g
# AM_LDFLAGS = -lefence
