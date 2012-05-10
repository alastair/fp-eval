function [S,R] = eval_fprint(Q,SR,T)
% [S,R] = eval_fprint(Q,SR,T)
%    Evaluate the fingerprinting system over a set of queries.
%    Q is a cell array of query waveforms, each at sampling rate
%    SR.  T is the ground-truth track indices that should be 
%    returned (0 => not found).  Return S as the proportion of
%    queries correctly identified.  R is a matrix of actual 
%    top-hit results, with 4 columns: track_id nmatch t_offs total_match,
%    as returned by match_query
% 2010-04-21 DAn Ellis dpwe@ee.columbia.edu

nq = length(Q);
s = 0;

for i = 1:nq
  r = match_query(Q{i},SR);
  R(i,:) = r(1,:);
end

if nargin > 2
  S = mean(R(:,1)==T');
else
  S = 0;
end


  