from pprint import pprint

def multisort(x, fxns, reverse):
	"""A recursive function that sorts simultaneously on multiple,
		prioritized criteria. It sorts the whole list by the first
		criterion, then for each subset of elements with the same sorting value,
		it sorts THAT set by the SECOND criterion, etc. Useful for being
		able to break several kinds of ties of tiered importance.
	"""
	
	if fxns and len(x) > 1:
		# Sort the first bunch
		x = sorted(x, key=fxns[0], reverse=reverse[0])
		#print "x: \n", x
		# Find the places where the values change --
		# These will be the sublists
		values = [fxns[0](elem) for elem in x]
		#print "values: \n", values
		# Pre and post-pend values to diffs that handle the
		# edge cases when you're subsetting with the
		# start or end of the list. Necessary because the 'diffs' list comp.
		# only gives you values from the middle.
		diffs = [0]
		# Tells you the indices of spots when values change -- in other words,
		# where the cut-points should be for the sublists
		diffs += [i+1 for i in range(len(values)-1) if values[i]!=values[i+1]]
		diffs.append(len(x))
		#print "diffs: \n", diffs
		sublists = [x[diffs[j]:diffs[j+1]] for j in range(len(diffs)-1)]
		#print "sublists: \n", sublists
		f = fxns[1:]
		r = reverse[1:]         
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