function [Q,SR] = gen_random_queries(IDs,Dur,Noise,Seed)
% [Q,SR] = gen_random_queries(IDs,Dur,Noise,Seed)
%    Generate a cell array of random queries for testing the
%    fingerprinter.  IDs is a cell array of ID strings to 
%    indicate the files.  Dur is the duration of the excerpt to 
%    randomly pull from the file.  Noise is a level of noise 
%    to add (0 => no noise).  Return Q as a cell array of 
%    waveforms, one for each entry in IDs, that can be passed to
%    eval_fprint.m. 
%    Optional Seed will initialize RNG to a fixed point.
% 2010-04-21 DAn Ellis dpwe@ee.columbia.edu

nIDs = length(IDs);

prepend = '';
postpend = '';

SR = 0;

if nargin > 3
  rns = RandStream.create('mt19937ar','seed',Seed);
  RandStream.setDefaultStream(rns);
end

for i = 1:length(IDs)
  
  id = IDs{i};
  fname = [prepend,id,postpend];
  [pth,nm,ext] = fileparts(fname);
  if strcmp(ext,'.mp3') == 1
    [d,sr] = mp3read(fname);
  else
    [d,sr] = wavread(fname);
  end
  if size(d,2) == 2
    % convert to mono if stereo
    d = mean(d,2);
  end
  % choose random excerpt
  ld = length(d);
  qlen = round(Dur * sr);
  sp = round((ld - qlen)*rand(1));
  Q{i} = d(sp + [1:qlen]) + Noise * randn(qlen,1);

  if SR == 0
    SR = sr;
  elseif SR ~= sr
    error(['File ',fname,' has sr ',num2str(sr),' not ', num2str(SR)]);
  end
  
end

  
