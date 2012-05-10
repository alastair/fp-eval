function N = record_hashes(H)
% N = record_hashes(H)
%   Record the set of hashes that are rows of H in persistent
%   database.
%   Format of H rows are 3 columns:
%   <song id> <start time index> <hash>
% song ID is 24 bit
% time index is 8 bit
%   (1s basic resolution out to 256s)
% Hash is 20 bit = 1M slots
% N returns the actual number of hashes saved (excluding table overflows).
%
% 2008-12-24 Dan Ellis dpwe@ee.columbia.edu

% This version uses an in-memory global with one row per hash
% value, and a series of song ID / time ID entries per hash

global HashTable HashTableCounts

%if exist('HashTable','var') == 0 || length(HashTable) == 0
%   clear_hashtable;
%end

maxnentries = size(HashTable,1);

nhash = size(H,1);

N = 0;

TIMESIZE = 16384;

for i=1:nhash
  song = H(i,1);
  toffs = mod(round(H(i,2)), TIMESIZE);
  hash = 1+H(i,3);  % avoid problems with hash == 0
  htcol = HashTable(:,hash);
  nentries =  HashTableCounts(hash) + 1;
  if nentries <= maxnentries
	% put entry in next available slot
	r = nentries;
  else
    % choose a slot at random; will only be stored if it falls into
    % the first maxnentries slots (whereupon it will replace an older 
    % value).  This approach guarantees that all values we try to store
    % under this hash will have an equal chance of being retained.
    r = ceil(nentries*rand(1));
  end
  if r <= maxnentries
    hashval = int32(song*TIMESIZE + toffs);
%    disp(num2str(floor(double(hashval)/TIMESIZE)));
    HashTable(r,hash) = hashval;
    N = N+1;
  end
HashTableCounts(hash) = nentries;
end
