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

##############
# THE COMMAND I NEED (IT APPEARS) TO STICK THE DATABASE UP
#heroku pg:transfer -f postgres://localhost/alexloewi -t postgres://gmjfeaokrqybxu:rWV1ucM1sW-BMFTz4LNTMQsTVW@ec2-23-23-81-171.compute-1.amazonaws.com:5432/dk43q2hjo7pai
##############

#heroku config | grep HEROKU_POSTGRESQLHEROKU_POSTGRESQL_ORANGE_URL => postgres://gmjfeaokrqybxu:rWV1ucM1sW-BMFTz4LNTMQsTVW@ec2-23-23-81-171.compute-1.amazonaws.com:5432/dk43q2hjo7pai

# heroku pg:credentials DATABASE
# Connection info string:
#    "dbname=dk43q2hjo7pai host=ec2-23-23-81-171.compute-1.amazonaws.com port=5432 user=gmjfeaokrqybxu password=rWV1ucM1sW-BMFTz4LNTMQsTVW sslmode=require"

# HEROKU PRODUCTION
db = web.database(dbn='postgres',
				   db='dk43q2hjo7pai',
 				   host='ec2-23-23-81-171.compute-1.amazonaws.com',
				   port=5432,
				   user='gmjfeaokrqybxu',
				   pw='rWV1ucM1sW-BMFTz4LNTMQsTVW',
				   sslmode='require')

# db = web.database(dbn='postgres',
# 					user='alexloewi',
# 					pw='dian4nao3',
# 					db='alexloewi')

# The number of passes before you're disabled for PASS_PENALTY
PASS_LIMIT = 5
# The number of days you're out, if you go over the pass limit
PASS_PENALTY = 14 #days

URL = "young-wave-9997.herokuapp.com"


def users():
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
	
	
	"""

	login, password = 'heinz.phd.reviewer@gmail.com', 'phdpeerreview'

	# A notice to the reviewer that a review has been requested
	if message == "request":
		msg = """Please log in to the PhD Reviewer system to respond to the request from """+author+""". If you have any questions, their email is  """+contact_email+""".\n\nMany thanks from the entire PhD community,"""
		
		subject = "You have been requested to review a colleague's work"
	
	# A notice to the author that a request has been accepted
	if message == "accepted":
		msg = """Your request for a review has been accepted by  """+reviewer+"""! Please send them a copy of your paper as soon as possible. Their email is """+contact_email+""" \n\nMany thanks from the entire PhD community,"""
		
		subject = "Your review request has been accepted!"

	# A notice to the author that a review has been completed
	if message == "returned":
		msg = reviewer+""" has completed your review! Please log in to the PhD Review System to accept it."""
		
		subject = "Your review has been completed!"
		
	# A reminder that the requested return date is approaching
	if message == "deadline":
		msg = """You have 24 hours remaining before a review is due. \nMany thanks from the entire PhD community,"""
		
		subject = "There is one day remaining on an active review deadline"
	
	# If a 'candidates' list runs dry on an assignment
	if message == "apology":
		msg = """We're very sorry, no one was available to fill one of your reviewer spots. Please try again soon."""
		
		subject = "One reviewer spot could not be filled"
		
	# If you pass the PASS_LIMIT (or maybe other things too?)
	if message == "disabled":
		msg = """We're very sorry, but you've rejected too many review requests. Your account will be disabled for """+author+""" days. Feel free to continue submitting papers as soon as you're back."""
		
		subject = "Account temporarily disabled"
	
	###########
	# The tag #
	###########	
	subject = "[PhDRvr] " + subject
	msg = msg + "\nSenator Heinz" + "\n" + URL
	
	
		# The code below is pulled straight from
#stackoverflow.com/questions/9272257/how-can-i-send-email-using-python?rq=1
	
	msg = MIMEText(msg, _charset='utf-8')
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


def assign_reviewer(paper, kind, rejected=''):	

	# Choose reviewers, based on the ratio AND CURRENT LOAD
	rvrs = list(db.where('person', enabled=True))
	rejected = rejected.split()
	# Can't review your own paper, and don't want to reassign
	# to people who have already rejected it
	rvrs = [r for r in rvrs if
	 			r.id != paper['author'] and r.id not in rejected]
	
	if rvrs:
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
		# Do the multi-parameter prioritized sort
		# fxns is (are) defined immediately above
		lists = [multisort(rdict[k], fxns, rev) for k in kinds]
		
		asmt = {"paper": 		paper['id'],
				"accepted":		False,
				"completed":	False,
				"active":		True,
				"rejected":		''}
				# add 'kind'?

		#asmts = [copy.copy(asmt) for i in range(n)]
		#for i, a in enumerate(asmts):
		
		# A list of lists, sorted by 'kind'
		candidates = [ [p.id for p in lists[i]] for i in range(n)]
		# Go through EVERYBODY. In order, but maybe only 'later' 
		# ones are THERE
		sorted_candidates = []
		ix = kinds.index(kind)
		for j in range(ix,n)+range(ix):
			sorted_candidates += candidates[j] #[p.id for p in lists[j]] 
		# The first person from the corresponding list
		asmt["reviewer"] = sorted_candidates[0]
		selected = db.where('person', id=asmt['reviewer'])[0] #the rvr OBJECT
		#candidates = " ".join(candidates[1:])
		
		asmt["kind"] 		   = kind
		asmt['rvr_expertise']  = selected.expertise
		asmt['rvr_year'] 	   = selected.year
		asmt['rvr_milestone']  = selected.milestone
		asmt['active'] 	   	   = True
		
		author = db.where('person', id=paper['author'])[0]
		email_notice(selected.email, 'request', author=author.name,
												contact_email=author.email)
		increment(selected, 'active_requests')
		
		db.insert('assignment', **asmt)
				
	else:
		# Nobody was available -- apologize
		author = db.where('person', id=paper.author)[0]
		email_notice(author.email, "apology")

def process_submission(paper):
	'''Called when a review request is submitted. Increments the 
	number of reviews requested in the reviewer\'s profile, then 
	selects two (currently) reviewers for them, and files the submission.
	It will be called up when they log in. 
	And this emails the chosen reviewers, to let them know.
	'''

	# Have to insert it to GET an id
	paper['active'] = True
	paper_id = db.insert('paper', **paper)
	paper['id'] = paper_id
	assign_reviewer(paper, 'jr')
	assign_reviewer(paper, 'sr')
	
	# Notch one up for the submitter
	author = db.where('person', id=paper['author'])[0]
	increment(author, 'submitted')
	increment(author, 'active_submissions')


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
	
	rejected = rvr_id + " " + asmt.rejected
	assign_reviewer(paper, asmt.kind, rejected)
	
	
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




	
def test_insert(person):
	db.insert('person', **person)



###############

# remove the names from urls (LAST step -- hard to test that way)

# html emails ... include the url in them ... 

##############


