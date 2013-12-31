import web
import datetime
from multisort import multisort #doesn't HAVE to be in a separate file
import copy
import os
# All taken verbatim from 
# http://stackoverflow.com/questions/9272257/how-can-i-send-email-using-python?rq=1
# As are the contents of "email_notice()"
from email.header    import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib         import SMTP_SSL

##############
# THE COMMAND I NEED (IT APPEARS) TO PUSH THE DATABASE TO THE SITE:
#heroku pg:transfer -f postgres://localhost/alexloewi -t postgres://gmjfeaokrqybxu:rWV1ucM1sW-BMFTz4LNTMQsTVW@ec2-23-23-81-171.compute-1.amazonaws.com:5432/dk43q2hjo7pai
##############

#heroku config | grep HEROKU_POSTGRESQLHEROKU_POSTGRESQL_ORANGE_URL => postgres://gmjfeaokrqybxu:rWV1ucM1sW-BMFTz4LNTMQsTVW@ec2-23-23-81-171.compute-1.amazonaws.com:5432/dk43q2hjo7pai

# heroku pg:credentials DATABASE
# Connection info string:
#    "dbname=dk43q2hjo7pai host=ec2-23-23-81-171.compute-1.amazonaws.com port=5432 user=gmjfeaokrqybxu password=rWV1ucM1sW-BMFTz4LNTMQsTVW sslmode=require"

# HEROKU PRODUCTION

# Chooses the correct database connection based upon whether the db is local, and for development, or the actual site's db. Does so by testing the path of the current file.
if os.path.abspath("") == '/Users/alexloewi/Documents/Sites/heinz_reviewer':
	db = web.database(dbn='postgres',
					  user='alexloewi',
					  pw='dian4nao3',
					  db='alexloewi')
else:
	db = web.database(dbn='postgres',
					  db='dk43q2hjo7pai',
	 				  host='ec2-23-23-81-171.compute-1.amazonaws.com',
					  port=5432,
					  user='gmjfeaokrqybxu',
					  pw='rWV1ucM1sW-BMFTz4LNTMQsTVW',
					  sslmode='require')



# The number of passes before you're disabled for PASS_PENALTY
PASS_LIMIT = 5
# The number of days you're out, if you go over the pass limit
PASS_PENALTY = 14 #days
# Same, for accepting a review, then not returning it for more than a week.
DROP_LIMIT = 1
DROP_PENALTY = 14

URL = "young-wave-9997.herokuapp.com"


def users():
	"""Called to check login ids against active users at the login page."""
	return db.select('person')

def create_user(id):
	now = datetime.datetime.now()
	db.insert('person', id=id,
					   reviewed=0,
					   submitted=0,
					   passes=0,
					   dropped=0,
					   active_requests=0,
					   active_submissions=0,
					   started=now,
					   last_review=now,
					   enabled=True)
	
	
# The get_user_* set of functions are used in rendering an individual's dashboard. Each is necessary to pull a different kind of message (request, alert, etc.) of which the user may need to be informed. They tend to be simple single database calls to the relevant tables.

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

def get_user_alerts(id):
	alerts = list(db.where('alert', person=id))
	now = datetime.datetime.now()
	active = [a for a in alerts if a.reveal_if_after < now]
	return active

def get_user_finished(id):
	finished = list(db.where('finished', reviewer_id=id))
	return finished 

def get_user_feedback(id):
	fb = list(db.where('feedback', author=id, active=True))
	return fb



def email_notice(to_email, message, author=None, reviewer=None, 					
												 contact_email=None):
	""" The function that emails the relevant parties when an action is taken.
	
	Has messages for when a request for a review is sent out, for when a review request is accepted, for when a review is returned, for when a deadline is approaching, for when a reviewer could not be found, and for when rejecting or dropping too many reviews has resulted in a temporary suspension. Includes contact emails when necessary, and tries to include paper titles etc. so as to not be ambiguous about what has caused the email.
	"""

	login, password = 'heinz.phd.reviewer@gmail.com', 'phdpeerreview'

	# A notice to the reviewer that a review has been requested
	if message == "request":
		text = "Please log in to the <a href='"+URL+"""'>PhD Reviewer system</a> to respond to the request from """+author+""". If you have any questions, their email is  """+contact_email+""".
		<p>
		Many thanks from the entire PhD community,
		"""
		
		subject = "You have been requested to review a colleague's work"
	
	# A notice to the author that a request has been accepted
	if message == "accepted":
		text = """Your request for a review has been accepted by  """+reviewer+"""! Please send them a copy of your paper as soon as possible. Their email is """+contact_email+""" \n\nMany thanks from the entire PhD community,"""
		
		subject = "Your review request has been accepted!"

	# A notice to the author that a review has been completed
	if message == "returned":
		text = reviewer+""" has completed your review! Please log in to the PhD Review System to accept it."""
		
		subject = "Your review has been completed!"
		
	# A reminder that the requested return date is approaching
	if message == "deadline":
		text = """You have 24 hours remaining before a review is due. \nMany thanks from the entire PhD community,"""
		
		subject = "There is one day remaining on an active review deadline"
	
	# If a 'candidates' list runs dry on an assignment
	if message == "apology":
		text = """We're very sorry, no one was available to fill one of your reviewer spots. Please try again soon."""
		
		subject = "One reviewer spot could not be filled"
		
	# If you pass the PASS_LIMIT (or maybe other things too?)
	if message == "disabled":
		text = """We're very sorry, but you've rejected or dropped too many review requests. Your account will be disabled for """+author+""" days. Feel free to continue submitting papers as soon as you're back."""
		
		subject = "Account temporarily disabled"
	
	###########
	# The tag #
	###########	
	subject = "[PhDRvr] " + subject
	text = text + "\nSenator Heinz" + "\n" + URL
	
	
		# The code below is pulled straight from
#stackoverflow.com/questions/9272257/how-can-i-send-email-using-python?rq=1

	#msg = MIMEMultipart('alternative') # for html
	msg = MIMEText(text, 'html', _charset='utf-8')
	msg['Subject'] = Header(subject, 'utf-8')
	msg['From'] = login
	msg['To'] = to_email

	# send it via gmail        WHY 465 ?
	s = SMTP_SSL('smtp.gmail.com', 465, timeout=10)
	s.set_debuglevel(0)
	try:
	    s.login(login, password)
	    s.sendmail(msg['From'], msg['To'], msg.as_string())
	finally:
	    s.quit()

				
def increment(record, field, value=1, table='person'):
	"""Takes a database record. Increments the 'field' attribute by 'value.'"""
	record[field] += value
	db.update(table, where="id=$id", vars=record, **record)

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


def assign_reviewer(paper, kind, rejected=''):	
	""" Finds a reviewer when a new paper is submitted, or a review is refused.
	
	Probably the most complex function in the site, although the most opaque computations likely occur in 'multisort,' which this only calls. Sorts reviewers by seniority, active review request load, the difference between their submission and review counts (to push new reviews towards people who have contributed less than they've received) and by last completed review. This entire process is necessary each time a reviewer is needed because each of these attributes may change after the original review is assigned, and so the best NEXT candidate may be different than they were at the original submission.
	"""
	# Choose reviewers, based on the ratio AND CURRENT LOAD
	rvrs = list(db.where('person', enabled=True))
	rejected = rejected.split()
	# Can't review your own paper, and don't want to reassign
	# to people who have already rejected it
	rvrs = [r for r in rvrs if
	 			r.id != paper['author'] and r.id not in rejected]
	
	if rvrs:
		# Split by seniority
		kinds = ['jr', 'sr']
		features = [["None yet", "1st Paper"],
					["2nd Paper", "Proposal"]]
		n = len(kinds)
		
		rdict = {k:[] for k in kinds}
		# For each reviewer
		for r in rvrs:
			# Look at all the kinds available
			for i in range(n):
				# If the rvr's milestone falls into that category,
				if r.milestone in features[i]:
					# Sort them accordingly.
					rdict[kinds[i]].append(r)
		# Do the multi-parameter prioritized sort.
		# fxns is (are) defined immediately above this function.
		# This results in one multi-sorted list for each seniority level.
		lists = [multisort(rdict[k], fxns, rev) for k in kinds]
		
		timeline = datetime.timedelta(days=int(paper['timeline']))
		due = timeline + paper['submitted']
		
		asmt = {"paper": 		paper['id'],
				"accepted":		False,
				"completed":	False,
				"active":		True,
				"rejected":		' '.join(rejected),
				"assigned":		datetime.datetime.now(),
				"due":			due}

		# A list of seniority lists, sorted by 'kind'
		candidates = [ [p.id for p in lists[i]] for i in range(n)]
		# Everyone is a candidate for a reviewer -- we're looking for the BEST
		# match, but that's relative. So, put the seniority lists themselves
		# in order, starting with the desired seniority, but following with the
		# rest in order (looping when you get to most senior). This will 
		# reliably find the BEST match.
		sorted_candidates = []
		ix = kinds.index(kind)
		for j in range(ix,n)+range(ix):
			sorted_candidates += candidates[j]
		# The first person from the all-encompassing list
		asmt["reviewer"] = sorted_candidates[0]
		selected = db.where('person', id=asmt['reviewer'])[0] #the rvr OBJECT
		increment(selected, 'active_requests')
		
		asmt["kind"] 		   = kind
		asmt['rvr_expertise']  = selected.expertise
		asmt['rvr_year'] 	   = selected.year
		asmt['rvr_milestone']  = selected.milestone
		asmt['active'] 	   	   = True
		
		author = db.where('person', id=paper['author'])[0]
		email_notice(selected.email, 'request', author=author.name,
												contact_email=author.email)		
		db.insert('assignment', **asmt)
				
	else:
		# Nobody was available -- apologize
		author = db.where('person', id=paper.author)[0]
		email_notice(author.email, "apology")

def process_submission(paper):
	'''Called when a review request is sent out. Sends review requests.
	
	Increments the number of reviews requested in the reviewer\'s profile, then 
	selects two (currently) reviewers for them, and files the submission.
	It will be called up when they log in. 
	And this emails the chosen reviewers, to let them know.
	'''

	# Have to insert it to GET an id
	paper['active'] = True
	paper['submitted'] = datetime.datetime.now()
	rvrs = ['jr', 'sr']
	paper['num_assigned_reviewers'] = len(rvrs)
	paper['num_completed_reviews'] = 0	
	paper_id = db.insert('paper', **paper)
	paper['id'] = paper_id
	for r in rvrs:
		assign_reviewer(paper, r)
	
	# Notch one up for the submitter
	author = db.where('person', id=paper['author'])[0]
	increment(author, 'submitted')
	increment(author, 'active_submissions')


def accept_submission(rvr_id, paper_id):
	""" Called when someone accepts a review request.
	
	Sends the necessary parties emails, sets up due-date alerts for 24 hours before it's due, and makes the 'finished' object for when the reviewer is done.
	"""
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
	email_notice(author.email, 'accepted', reviewer=rvr.name,
										   contact_email=rvr.email)
	
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


def disable(person, penalty):
	""" Used on a person who has rejected or dropped too many jobs.
	
	Renders their profile inactive for the amount of penalty time that is passed, and sends them an email saying so. 
	"""
	# Cut and pasted from where it was in 'reject_submission'
	back = datetime.datetime.now() + datetime.timedelta(days=PASS_PENALTY)
	person.enabled = False
	person.disabled_until = back
	db.update('person', where="id=$id", vars=person, **person)
	email_notice(person.email, 'disabled', author=str(PASS_PENALTY))
	
	
def reject_submission(rvr_id, paper_id):
	""" Does the necessary housekeeping when someone refuses a review request.
	
	This includes giving them a 'pass,' checking to see if they should be disabled as a result, putting to rest their assignment, and generating a new one.
	"""
	# notch up the 'passes' for the rejector
	paper = db.where('paper', id=paper_id)[0]
	rvr = db.where('person', id=rvr_id)[0]
	
	# Take the person out if they 'pass' too many requests.
	rvr = db.where('person', id=rvr_id)[0]
	# If you're ONE BELOW the limit (but have one more coming), you're out.
	# mod is used (%) to preserve the true count, rather than resetting it.
	if rvr.passes % PASS_LIMIT == PASS_LIMIT - 1:
		disable(rvr, PASS_PENALTY)
		
	# Do these AFTER the test
	increment(rvr, 'passes')
	increment(rvr, 'active_requests', -1) #i.e. decrement
	
	# Assumes the same person will not be reviewering the same paper twice --
	# should be safe though.
	asmt = db.where('assignment', paper=paper.id, reviewer=rvr.id)[0]
	asmt.accepted = False
	asmt.active = False
	db.update('assignment', where="id=$id", vars=asmt, **asmt)
	
	rejected = rvr_id + " " + asmt.rejected
	assign_reviewer(paper, asmt.kind, rejected)
	
	
def process_finish(fin_id):
	""" Called when someone signals that they are done with a review.
	
	Does a large amount of housekeeping. Active requests need to be decremented, emails need to be sent, both reviewer and author are toggled or involved in some way or another. The assignment needs to be retired, the paper needs to be marked as having a finished review ... the pending alerts need to be deleted, as does the now obsolete 'finished' object. The review itself is submitted, and a feedback survey is sent to the author. But, it doesn't seem like there's a useful way to factor any of those things out. This doesn't do anything complicated -- it just does a lot.
	"""
	
	finish = db.where('finished', id=fin_id)[0]
	reviewer = db.where('person', id=finish.reviewer_id)[0]
	author = db.where('person', id=finish.author_id)[0]
	paper = db.where('paper', id=finish.paper_id)[0]
	increment(paper, 'num_completed_reviews', 1, table="paper")
	increment(reviewer, 'active_requests', -1)
	increment(reviewer, 'reviewed')
	email_notice(author.email, 'returned', reviewer=reviewer.name)
	db.delete('finished', where="id=$id", vars=finish)
	
	# Since they've finished, they don't need to be alerted.
	alerts = db.where('alert', paper=finish.paper_id)
	for a in alerts:
		db.delete('alert', where="id=$id", vars=a)
	
	# Log the old assignment as finished.
	asmt = db.where('assignment', paper=finish.paper_id,
								  reviewer=finish.reviewer_id)[0]
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
	""" The function that responds to a satisfaction survey being submitted.
	
	Deactivates the survey, and logs the 'feedback' object, along with the score that the review was given (1-7) and any notes that were written with it.
	"""
	fb = db.where('feedback', id=id)[0]
	fb.active = False
	fb.score = score
	db.update('feedback', where="id=$id", vars=fb, **fb)




	
def test_insert(person):
	db.insert('person', **person)



###############

# remove the names from urls (LAST step -- hard to test that way)

# html emails ... include the url in them ... gmail does it automatically, but does anybody else?

##############


