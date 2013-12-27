import web
import datetime
from multisort import multisort #doesn't HAVE to be in a separate file
import copy
# All taken verbatim from 
# http://stackoverflow.com/questions/9272257/how-can-i-send-email-using-python?rq=1
# As are the contents of "email_notice()"
from email.header    import Header
from email.mime.text import MIMEText
from smtplib         import SMTP_SSL

#heroku config | grep HEROKU_POSTGRESQLHEROKU_POSTGRESQL_ORANGE_URL => postgres://gmjfeaokrqybxu:rWV1ucM1sW-BMFTz4LNTMQsTVW@ec2-23-23-81-171.compute-1.amazonaws.com:5432/dk43q2hjo7pai

# heroku pg:credentials DATABASE
# Connection info string:
#    "dbname=dk43q2hjo7pai host=ec2-23-23-81-171.compute-1.amazonaws.com port=5432 user=gmjfeaokrqybxu password=rWV1ucM1sW-BMFTz4LNTMQsTVW sslmode=require"

# HEROKU PRODUCTION
# db = web.database(dbname='dk43q2hjo7pai',
#  				   host='ec2-23-23-81-171.compute-1.amazonaws.com',
# 				   port=5432,
# 				   user='gmjfeaokrqybxu',
# 				   password='rWV1ucM1sW-BMFTz4LNTMQsTVW',
#				   sslmode='require')

# The number of passes before you're disabled for PASS_PENALTY
PASS_LIMIT = 5
# The number of days you're out, if you go over the pass limit
PASS_PENALTY = 14 #days


db = web.database(dbn='postgres',
					user='alexloewi',
					pw='dian4nao3',
					db='alexloewi')

def users():
	return db.select('person')

def create_user(id):
	now = datetime.datetime.now()
	db.insert('peron', id=id,
					   reviewed=0,
					   submitted=0,
					   passes=0,
					   dropped=0,
					   useful=0,
					   active_requests=0,
					   active_submissions=0,
					   started=now,
					   last_review=now)
	
def get_user_data(id):
	return db.where('person', id=id)[0]

def set_user_data(data):
	# Dunno WHY this call works -- just gotta trust stkx.
# http://stackoverflow.com/questions/13521890/error-with-update-with-web-py
	# Documentation, but it wasn't as useful:
	# http://webpy.org/docs/0.3/api#web.db
	db.update('person', where="id=$id", vars=data, **data)


def get_user_requests(id):
	'''Finds all active review requests assigned a particular reviewer.
	Called when the dashboard is rendered, to populate the request window.'''
	
	asmts = list(db.where('assignment', reviewer=id, accepted=False,
													 active=True))
	rqs = []
	for a in asmts:
		rqs.append(db.where('paper', id=a.paper)[0])
	return(rqs)


def email_notice(email, message, author=None, reviewer=None):
	""" The function that emails the relevant parties when an action is taken.
	
	
	"""

	login, password = 'heinz.phd.reviewer@gmail.com', 'phdpeerreview'

	# A notice to the reviewer that a review has been requested
	if message == "request":
		msg = """Please log in to the PhD Reviewer system to respond to the request from """+author+""".\n\nMany thanks from the entire PhD community,\nSenator Heinz
				"""
		subject = "You have been requested to review a colleague's work"
	
	# A notice to the author that a request has been accepted
	if message == "accepted":
		msg = """Your request for a review has been accepted by  """+reviewer+"""! Please send them a copy of your paper as soon as possible. \n\nMany thanks from the entire PhD community,\nSenator Heinz
				"""
		subject = "Your review request has been accepted!"

	# A notice to the author that a review has been completed
	if message == "returned":
		msg = reviewer+""" has completed your review! Please log in to the PhD 			 Review System to accept it. \n\nMany thanks from the entire PhD community,\nSenator Heinz
				"""
		subject = "Your review has been completed!"
		
	# A reminder that the requested return date is approaching
	if message == "deadline":
		msg = """Please log in to the PhD Reviewer system to respond to the request. \nMany thanks from the entire PhD community,\nSenator Heinz
				"""
		subject = "There is one day remaining on an active review deadline"
	
	# If a 'candidates' list runs dry on an assignment
	if message == "apology":
		msg = """We're very sorry, no one was available to fill one of your reviewer spots. Please try again soon. \nSenator Heinz"""
		
		subject = "One reviewer spot could not be filled"
		
	# If you pass the PASS_LIMIT (or maybe other things too?)
	if message == "disabled":
		msg = """We're very sorry, but you've rejected too many review requests. Your account will be disabled for """+author+""" days. Feel free to continue submitting papers as soon as you're back."""
		
		subject = "Account temporarily disabled"
	
	###########
	# The tag #
	###########	
	subject = "[PhDRvr] " + subject
	
	
		# The code below is pulled straight from
#stackoverflow.com/questions/9272257/how-can-i-send-email-using-python?rq=1
	
	msg = MIMEText(msg, _charset='utf-8')
	msg['Subject'] = Header(subject, 'utf-8')
	msg['From'] = login
	msg['To'] = email

	# send it via gmail        WHY 465 ?
	s = SMTP_SSL('smtp.gmail.com', 465, timeout=10)
	s.set_debuglevel(0)
	try:
	    s.login(login, password)
	    s.sendmail(msg['From'], msg['To'], msg.as_string())
	finally:
	    s.quit()


# def request_review(paper, reviewer, kind):
# 	"""Send a request to a person. Takes the person object and paper dict.
# 	
# 	Either they already exist, or you can call them right before. It's cleaner than having a toggle for 'just a name, or the whole thing?'
# 	"""
# 	
# 	email_notice(reviewer.email, 'request', author=paper['author'])
# 	increment(reviewer, 'active_requests')
# 	# Is that really ALL? This should probably just be written directly
# 	# into the places it's used, cause there are only two.

						
def increment(person, field, value=1):
	"""Takes the person OBJECT. Increments their 'field' attribute by one. """
	person[field] += value
	set_user_data(person)

# The functions used in multisort -- the priorities for choosing a 
# reviewer
def request_count(r):
	return r.active_requests
	
def submit_diff(r):
	return r.submitted - r.reviewed
	
def recent_review(r):
	return r.last_review

# Whether each of the functions should be sorted in reverse or not
rev  = [False,         True,        False]
fxns = [request_count, submit_diff, recent_review]


def process_submission(paper):
	'''Called when a review request is submitted. Increments the 
	number of reviews requested in the reviewer\'s profile, then 
	selects two (currently) reviewers for them, and files the submission.
	It will be called up when they log in. 
	And this emails the chosen reviewers, to let them know.
	'''
	
	# Choose reviewers, based on the ratio AND CURRENT LOAD
	rvrs = list(db.where('person', enabled=True))
	print [r.id for r in rvrs]
	if rvrs:
		# Can't review your own paper
		rvrs = [r for r in list(rvrs) if r.id != paper['author']]
		
		########################### Should only need to change this part.
		# Split by seniority
		kinds = ['jr', 'sr']
		features = [["None yet", "1st Paper"],
					["2nd Paper", "Proposal"]]
		n = len(kinds)
		###########################
		
		rdict = {k:[] for k in kinds}
		# For each reviewer
		for r in rvrs:
			# Look at all the kinds available
			for i in range(n):
				# If the rvr's milestone falls into that category,
				if r.milestone in features[i]:
					# Sort them accordingly.
					rdict[kinds[i]].append(r)
		print rdict
		# Do the multi-parameter prioritized sort
		# fxns is (are) defined immediately above
		lists = [multisort(rdict[k], fxns, rev) for k in kinds]
		
		# Have to insert it to GET an id
		paper['active'] = True
		paper_id = db.insert('paper', **paper)
		
		asmt = {"paper": 		paper_id,
				"accepted":		False,
				"completed":	False,
				"active":		True}

		asmts = [copy.copy(asmt) for i in range(n)]
		for i, a in enumerate(asmts):
			# Just the names, from the corresponding list
			candidates = [p.id for p in lists[i]]
			print candidates
			# Cycle through the other candidates, and stick them on the end
			# as backups, even though they're a different 'kind.' 
			# This could theoretically result in someone having to reject
			# something multiple times, but to avoid that seems 
			# complicated and unnecessary. Better to make sure a reviewer
			# is gotten from SOMEwhere.
			for j in range(i+1,n)+range(i):
				candidates += [p.id for p in lists[j]] 
			# The first person from the corresponding list
			a["reviewer"] = candidates[0]
			# One quoteless non comma seperated string, for easy splitting.
			# Needs to be this way cause it's stored in sql.
			selected = lists[i][0] #the rvr OBJECT
			candidates = " ".join(candidates[1:])
			a["candidates"]    = candidates
			a["kind"] 		   = kinds[i]
			a['rvr_expertise'] = selected.expertise
			a['rvr_year'] 	   = selected.year
			a['rvr_milestone'] = selected.milestone
			a['active'] 	   = True
						
			email_notice(selected.email, 'request', author=paper['author'])
			increment(selected, 'active_requests')
			
			db.insert('assignment', **a)
		
		# Notch one up for the submitter
		author = db.where('person', id=paper['author'])[0]
		increment(author, 'submitted')
		increment(author, 'active_submissions')
		
	else:
		# nobody's signed up -- hope that's an error
		print "never got here"
	

def accept_submission(rvr_id, paper_id):
	# Get the submission itself
	paper = db.where('paper', id=paper_id)[0]
	author = db.where('person', id=paper.author)[0]
	rvr = get_user_data(rvr_id)
	
	asmts = [a for a in db.where('assignment', paper=paper.id)]
	for a in asmts:
		if a.reviewer == rvr_id:
			a['accepted'] = True
			db.update('assignment', where="id=$id", vars=a, **a)
			break	 		
	
	#	email the author
	email_notice(author.email, 'accepted', reviewer=rvr.name)
	
	# 	set a reminder with the deadline
	alert_td = datetime.timedelta(days=paper.timeline-1)
	due_td = datetime.timedelta(days=paper.timeline)	
	now = datetime.datetime.now()
	reminder = {'person': rvr.id, 
				'message': "DUE SOON: You have a review for "\
							+author.name+" due in 1 day!",
				'reveal_if_after':now+alert_td}
	db.insert('alert', **reminder)
	#	make a 'finish' object
	finished = {'paper_id':	   		paper.id,
				'reviewer_id': 		rvr.id,
				'author_id':   		author.id,
				'reviewer_name': 	rvr.name,				
				'author_name': 		author.name,
				'due':				now+due_td,
				'title':	   		paper.title,}
	db.insert('finished', **finished)
	
	
def reject_submission(rvr_id, paper_id):
	# notch up the 'passes' for the rejector
	paper = db.where('paper', id=paper_id)[0]
	rvr = db.where('person', id=rvr_id)[0]
	increment(rvr, 'passes')
	increment(rvr, 'active_requests', -1) #i.e. decrement
	
	# Take the person out if they 'pass' too many requests.
	rvr = db.where('person', id=rvr_id)[0]
	if rvr.passes > PASS_LIMIT:
		back = datetime.datetime.now() + datetime.timedelta(days=PASS_PENALTY)
		rvr.enabled = False
		rvr.disabled_until = back
		db.update('person', where="id=$id", vars=rvr, **rvr)
		email_notice(rvr.email, 'disabled', author=str(PASS_PENALTY))
	
	asmt = db.where('assignment', paper=paper.id, reviewer=rvr.id)[0]	
	asmt.accepted = False
	asmt.active = False
	db.update('assignment', where="id=$id", vars=asmt, **asmt)
	
	candidates = asmt.candidates.split()
	new = next_reviewer(asmt)
	if candidates:
		new.reviewer = candidates[0]
		new.candidates = candidates[1:]
		db.insert('assignment', **new)
		email_notice(rvr.email, 'request', author=paper.author)
		increment(rvr, 'active_requests')
	
		# BACK WHEN I WAS DOING THE ACTIVE/NOT TABLE SCHEME
		# log.delete('exercise', where="id=$id", vars=locals())
		# db.delete('assignment', where="id=$id", vars=asmt, **asmt)
		# db.insert('finished_assignment', asmt)
			
	else:
		# Nobody was left ... tell the author.
		author = db.where('person', id=paper.author)[0]
		email_notice(author.email, "apology")
	
	
def get_user_alerts(id):
	alerts = list(db.where('alert', person=id))
	now = datetime.datetime.now()
	active = [a for a in alerts if a.reveal_if_after < now]
	return active


def get_user_finished(id):
	finished = list(db.where('finished', reviewer_id=id))
	return finished 
		
	
def process_finish(fin_id):
	finish = db.where('finished', id=fin_id)[0]
	reviewer = db.where('person', id=finish.reviewer_id)[0]
	author = db.where('person', id=finish.author_id)[0]
	increment(author, 'active_submissions', -1)
	increment(reviewer, 'active_requests', -1)
	increment(reviewer, 'reviewed')
	email_notice(author.email, 'returned', reviewer=reviewer.name)
	db.delete('finished', where="id=$id", vars=finish)
	
	# Log the old assignment as finished.
	asmt = db.where('assignment', paper=finish.paper_id,
								  reviewer=finish.reviewer_id)[0]
	#db.delete('assignment', where="id=$id", vars=asmt)
	#db.insert('finished_assignment', **asmt)
	asmt.completed = True
	asmt.active = False
	db.update('assignment', where="id=$id", vars=asmt, **asmt)
	# Make a 'review' object (which will maybe later have an attachment)
	now = datetime.datetime.now()
	review = {'reviewer': reviewer.id,
			  'author':   author.id,
			  'title':	  finish.title,
			  'reviewer_expertise': reviewer.expertise,
			  'review': None,
			  'returned': now,
			  'on_time': now < finish.due}
	review_id = db.insert('review', **review)
	# create and send a satisfaction survey to the author	
	feedback = {'paper_id':   		finish.paper_id,
			    'review_id':  		review_id,
			    'author':			author.id,
			    'title':			finish.title,
			    'author_name': 		author.name,
				'active':			True}
	db.insert('feedback', **feedback)			

def process_feedback(id, score):
	fb = db.where('feedback', id=id)[0]
	#db.delete('feedback', where="id=$id", vars=fb)
	fb.active = False
	fb.score = score
	#db.insert('finished_feedback', **fb)
	db.update('feedback', where="id=$id", vars=fb, **fb)


def get_user_feedback(id):
	fb = list(db.where('feedback', author=id, active=True))
	return fb
	
	
def test_insert(person):
	db.insert('person', **person)



###############

# OR just make everything 'active' or not. AT WORST: 10 reviews a day,
# 100 years -- 10*365*100 = 365,000. 

# I.e. don't have inherited tables. ALSO: check the necessity of ... all kindsa fields, 'accepted' and 'finished' and 'active' and etc. There's a lot.

# add all the desired reviewer attributes to ... 'finished'. 

# remove the names from urls (LAST step -- hard to test that way)

##############










