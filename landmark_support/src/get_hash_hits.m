function R = get_hash_hits(H)
% R = get_hash_hits(H)
%    Return values from song hash table for particular hashes
%    Each element of H is a <(20 bit) hash value>
%    Each row of R is a hit in format:
%    <song id> <start time index> <hash>
%    If H is a 2 column matrix, the first element is taken as a
%    time base which is subtracted from the start time index for
%    the retrieved hashes.
%    If H is a 3 column matrix, the first element is taken as a
%    songID and discarded.
% 2008-12-29 Dan Ellis dpwe@ee.columbia.edu

if size(H,2) == 3
  H = H(:,[2 3]);
end

if min(size(H))==1
  H = [zeros(length(H),1),H(:)];
end

global HashTable HashTableCounts
nhtcols = size(HashTable,1);

TIMESIZE=16384;

Rsize = 1000;  % preallocate
R = zeros(Rsize,3);
Rmax = 0;

for i = 1:length(H)
  hash = H(i,2);
  htime = double(H(i,1));
  nentries = min(nhtcols,HashTableCounts(hash+1));
  htcol = double(HashTable(1:nentries,hash+1));
  songs = floor(htcol/TIMESIZE);
  times = round(htcol-songs*TIMESIZE);
  if Rmax+nentries > Rsize
    R = [R;zeros(Rsize,3)];
    Rsize = size(R,1);
  end
  dtimes = times-htime;
  R(Rmax+[1:nentries],:) = [songs, dtimes, repmat(double(hash),nentries,1)];
  Rmax = Rmax + nentries;
end

R = R(1:Rmax,:);
