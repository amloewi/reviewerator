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
	
def get_user_data(person):
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
	
	rqs = list(db.where('assignment', reviewer=id))	
	return(rqs)


def email_notice(email, message, author=None, reviewer=None):
	""" The function that emails the relevant parties when an action is taken.
	
	
	"""

	login, password = 'heinz.phd.reviewer@gmail.com', 'phdpeerreview'

	# A notice to the reviewer that a review has been requested
	if message == "request":
		msg = """Please log in to the PhD Reviewer system to respond to the request from """+author+""".\nMany thanks from the entire PhD community,\nDoctor Heinz
				"""
		subject = "You have been requested to review a colleague's work"
	
	# A notice to the author that a request has been accepted
	if message == "accepted":
		msg = """Your request for a review has been accepted by """+reviewer+"""! Please send them a copy of your paper as soon as possible. \nMany thanks from the entire PhD community,\nDoctor Heinz
				"""
		subject = "Your review request has been accepted!"

	# A notice to the author that a review has been completed
	if message == "returned":
		msg = reviewer+"""has completed your review! Please log in to the PhD 			 Review System to accept it. \nMany thanks from the entire PhD community,\nDoctor Heinz
				"""
		subject = "Your review has been completed!"
		
	# A reminder that the requested return date is approaching
	if message == "deadline":
		msg = """Please log in to the PhD Reviewer system to respond to the request. \nMany thanks from the entire PhD community,\nDoctor Heinz
				"""
		subject = "There is one day remaining on an active review deadline"

	subject = "[PhDRvr] " + subject
	
	if message == "apology":
		msg = """We're very sorry, no one was available to fill one of your reviewer spots. Please try again soon. \nDoctor Heinz"""
		
		subject = "One reviewer spot could not be filled"
	
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


def request_review(reviewer, paper, kind):
	"""Send a request to a person. Takes the person and paper OBJECTS.
	
	Either they already exist, or you can call them right before. It's cleaner than having a toggle for 'just a name, or the whole thing?'
	"""
	
	email_notice(reviewer.email, 'request', author=paper.author)
	increment(reviewer, 'active_requests')
	# Is that really ALL?


						
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
	rvrs = db.where('person', enabled=1)
	if rvrs:
		# Can't review your own paper
		rvrs = [r for r in list(rvrs) if r.id != paper['author']]
		
		########################### Should only need to change this part.
		# Split by seniority
		kinds = ['jr', 'sr']
		features = [["None yet", "1st Paper"],
					["2nd Paper", "Proposal"]]
		###########################
		
		rdict = {k:[] for k in kinds}
		# For each reviewer
		for r in rvrs:
			# Look at all the kinds available
			for i in range(len(kinds)):
				# If the rvr's milestone falls into that category,
				if r.milestone in features[i]:
					# Sort them accordingly.
					rdict[kinds[i]].append(r)
				
		# Do the multi-parameter prioritized sort
		# fxns is (are) defined immediately above
		lists = [multisort(rdict[k], fxns, rev) for k in kinds]
		
		asmt = {"paper": 		paper.id,
				"accepted":		0,
				"completed":	0}

		n = len(kinds)
		asmts = [copy.copy(asmt) for i in range(n)]
		for i, a in enumerate(asmts):
			# Just the names, from the corresponding list
			candidates = [p.id for p in lists[i]]
			# Cycle through the other candidates, and stick them on the end
			# as backups, even though they're a different 'kind.' 
			# This could theoretically result in someone having to reject
			# something multiple times, but to avoid that seems 
			# complicated and unnecessary.
			for j in range(i+1,n)+range(i):
				candidates += [p.id for p in lists[j]] 
			# The first person from the corresponding list
			a["reviewer"] = candidates[0]
			# One quoteless non comma seperated string, for easy splitting.
			# Needs to be this way cause it's stored in sql.
			candidates = " ".join(candidates[1:])
			a["candidates"] = candidates
			a["kind"] = kinds[i]
			
			request_review(paper, lists[i][0])
			db.insert('assignments', **a)
		
		# Notch one up for the submitter
		author = db.where('person', id=paper['author'])[0]
		increment(author, 'submitted')
		increment(author, 'active_submissions')
		# And toss in the paper.
		db.insert('paper', **paper)
		
	else:
		# nobody's signed up -- hope that's an error
		print "never got here"
	

def accept_submission(rvr_id, paper_id):
	# Get the submission itself
	paper = db.where('paper', paper_id=paper_id)[0]
	author = db.where('person', id=paper.author)[0]
	rvr = get_user_data(rvr_id)
	
	asmts = [a for a in db.where('assignment', paper=paper.id)]
	for a in asmts:
		if a.reviewer == rvr_id:
			a['accepted'] = 1
			db.update('assignment', where="id=$id" vars=a, **a)
			break	 		
	
	#	email the author
	email_notice(author.email, 'accepted', reviewer=rvr.name)
	
	# 	set a reminder with the deadline
	td = datetime.timedelta(days=paper.timeline-1)
	now = datetime.datetime.now()
	reminder = {'recipient': rvr.id, 
				'message': "You have a review for "\
							+author.name+" due in 1 day!",
				'reveal_if_after':now+td}
	db.insert('alert', **reminder)
	#	make a 'finish' object
	finished = {'reviewer': rvr.id,
				'requester': author.id
				}
	db.insert('finished', **finished)
	

	
def reject_submission(rvr_id, paper_id):
	# notch up the 'passes' for the rejector
	paper = db.where('paper', id=paper_id)[0]
	rvr = db.where('person', id=rvr_id)[0]
	increment(rvr, 'passes')
	increment(rvr, 'active_requests', -1) #i.e. decrement
	
	asmt = db.where('assignment', paper=paper.id, reviewer=rvr.id)[0]	
	new = copy.copy(asmt)
	
	asmt.accepted = 0
	candidates = asmt.candidates.split()
	if candidates:
		new.reviewer = candidates[0]
		new.candidates = candidates[1:]
		db.insert('assignment', **new)
		request_review(rvr, paper, asmt.kind)
	
		# SYNTAX?
		# log.delete('exercise', where="id=$id", vars=locals())
		db.delete('assignment', where="id=$id", vars=asmt, **asmt)
		db.insert('finished_assignment', asmt)
			
	else:
		#NObody was left ... tell the author.
		author = db.where('person', id=paper.author)[0]
		email_notice(author.email, "apology")
		print 'only got here!'
	
	
	
	
	
	
def test_insert(person):
	db.insert('person', **person)

def nuclear_option():
	for table in ["reviewer", "submission", "review", "review_review"]:
		try:
			db.query('DROP TABLE '+table+';')
		except:
			pass
	#db.query('DROP TABLE submission;')
	#db.query('DROP TABLE review;')
	#db.query('DROP TABLE review_review;')
