from pprint import pprint

def multisort(x, fxns, reverse):
	"""Recursively sorts simultaneously on multiple, prioritized criteria.
	
	This function sorts the whole list 'x' by the first criterion (i.e., the 'key' function 0 passed in 'fxns'), then for each subset of elements with the same sorting value, it sorts THAT set by the SECOND criterion (fxns[1]), etc. Useful for being able to break several kinds of ties of tiered importance.
	"""
	
	# If there are criteria left for sorting (or elements to sort),
	if fxns and len(x) > 1:
		# Sort the first bunch, by the first criterion.
		x = sorted(x, key=fxns[0], reverse=reverse[0])
		# Find the places where the values change 
		# Each same-valued chunk will be a sublist
		values = [fxns[0](elem) for elem in x]
		# Pre and post-pend values to diffs that handle the
		# edge cases.
		diffs = [0]
		# Tells you the indices of spots when values change -- in other words,
		# where the cut-points should be for the sublists
		diffs += [i+1 for i in range(len(values)-1) if values[i]!=values[i+1]]
		# The second edge-case
		diffs.append(len(x))
		# Makes a sublist for each set of elements with the SAME value, under
		# the current sorting criterion. Each will be sorted by the NEXT 	
		# criterion, in the next level of recursion.
		sublists = [x[diffs[j]:diffs[j+1]] for j in range(len(diffs)-1)]
		f = fxns[1:] # pass the remaining criteria
		r = reverse[1:] # and the remaining arguments for sort as/des-cending.
		# Flattens the results from the next recursive call.         
		return [elem for sl in sublists for elem in multisort(sl, f, r)]
	else:
		return(x)

if __name__ == '__main__':
	x = [(1,1),
		 (1,2),
		 (1,3),
		 (2,1),
		 (2,2),
		 (2,3),
		]
			
	def nth(n):
		def f(x):
			return x[n]
		return f
		
	keys = [nth(i) for i in range(2)]
	order= [True, False]#, True]
	
	print "The results: "
	pprint(multisort(x, keys, order))