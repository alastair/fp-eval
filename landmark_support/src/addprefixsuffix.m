function Y = addprefixsuffix(X,P,S)
%   Apply prefix string P and suffix string S to every string in
%   cell array X, return new cell array Y.
% 2010-04-20 Dan Ellis dpwe@ee.columbia.edu

if nargin < 3
  S = '';
end

len = length(X);
for i = 1:len
  Y{i} = [P,X{i},S];
end
