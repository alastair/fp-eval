#!/bin/sh

echo "Need to modify this file before running."
exit

# Remove the 2 lines above
# Change the 2 lines below

DESC=~/audiokeys/haitsma_retrieve/boostextdescr.txt
PROG=~/audiokeys/haitsma_retrieve/codewav

### Do not modify after this line

if [ $# -ne 2 ]
then
  echo "Usage: $0 wavelist.txt keysdir"
  exit
fi

if [ ! -d $2 ]
then
  mkdir $2
fi

for i in `cat $1`
do
  #n=$2/`basename $i | cut -c1-11`.key
  n=$2/`basename $i`.key
  if [ ! -f $n ]
  then
    $PROG $DESC $i $n
  fi
done
