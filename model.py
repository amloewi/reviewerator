import web
import datetime
from multisort import multisort #doesn't HAVE to be in a separate file
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

DEVELOPMENT = False


db = web.database(dbn='postgres',
					user='alexloewi',
					pw='dian4nao3',
					db='alexloewi')

def users():
	return db.select('reviewer')

def create_user(login):
	now = datetime.datetime.now()
	db.insert('reviewer', login=login,
						  reviewed=0,
						  submitted=0,
						  passes=0,
						  dropped=0,
						  useful=0,
						  active_requests=0,
						  active_submissions=0,
						  started=now,
						  last_review=now)
	
def get_user_data(login):
	return db.where('reviewer', login=login)[0]

def set_user_data(data):
	# Dunno WHY this call works -- just gotta trust stkx.
# http://stackoverflow.com/questions/13521890/error-with-update-with-web-py
	# Documentation, but it wasn't as useful:
	# http://webpy.org/docs/0.3/api#web.db
	db.update('reviewer', where="login=$login", vars=data, **data)

def get_user_requests(login):
	'''Finds all active review requests assigned a particular reviewer.
	Called when the dashboard is rendered, to populate the request window.'''
	
	# 'nobody' is used because it's apparently hard to select by something
	# with a None (NULL) value.
	r1 = list(db.where('submission', active=1, assigned_reviewer_1=login, 
												reviewer_1='nobody'))
	r2 = list(db.where('submission', active=1, assigned_reviewer_2=login,
												reviewer_2='nobody'))
												
	# BUT -- THIS WILL APPEAR FOR THEM, EVEN IF THEY REJECTED IT.										
	
	return(r1+r2)


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





def request_review(submission, rvrs, kind, name_only):
	"""

	Used in 'process_submission' and 'reject_submission'
	"""
	print 'IN REQUEST REVIEW'
	# Take the first, pass the list with the request -- keeping the 
	# first person on it is a way to tell which list they came from
	if name_only:
		r = db.where('reviewer', login=rvrs[0])[0]
		print rvrs
	else:
		r = rvrs[0]
		rvrs = [str(r.login) for r in rvrs]
		print rvrs
	
	# Stick these lists on the submission itself, to
	# move through as people 'pass'
	# and as a string, cause it's stored in SQL
	submission[kind+'_list'] = str(rvrs).replace("'","")[1:-1]
	print "HELLO! ", str(rvrs[1:-1])
		
	# Let the selected reviewers know
	if not DEVELOPMENT:
		email_notice(r.email, "request", author=submission['login'])

	num = "1" if kind == "jr" else "2"
	submission["assigned_reviewer_"+num] = r.login
	
	# Notch one up for the reviewers
	increment(r, 'active_requests')





						
def increment(rvr, field, name_only=False):
	if name_only:
		rvr = db.where('reviewer', login=rvr)[0]
	rvr[field] += 1
	set_user_data(rvr)

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


def process_submission(data):
	'''Called when a review request is submitted. Increments the 
	number of reviews requested in the reviewer\'s profile, then 
	selects two (currently) reviewers for them, and files the submission.
	It will be called up when they log in. 
	And this emails the chosen reviewers, to let them know.
	'''
	
	# Notch one up for the submitter
	increment(data['login'], 'submitted', name_only=True)
	
	# Choose reviewers, based on the ratio AND CURRENT LOAD
	rvrs = db.where('reviewer', enabled=1)
	if rvrs:
		# Can't review your own paper
		rvrs = [r for r in list(rvrs) if r.login != data['login']]
		
		# Split by seniority
		rdict = {"jr":[], "sr":[]}
		for r in rvrs:
			if r.milestone == "None yet" or r.milestone == "1st Paper":
				rdict['jr'].append(r)
			else: # "2nd Paper" or "Proposal"
				rdict['sr'].append(r)
		
		# Do the multi-parameter prioritized sort
		# fxns is (are) defined immediately above
		jr_list = multisort(rdict['jr'], fxns, rev)
		sr_list = multisort(rdict['sr'], fxns, rev)
		
		request_review(data, jr_list, 'jr', name_only=False)
		request_review(data, sr_list, 'sr', name_only=False)
	
		data['reviewer_1'] = 'nobody'
		data['reviewer_2'] = 'nobody'
		db.insert('submission', **data)
		
	else:
		# nobody's signed up -- hope that's an error
		print "never got here"
	

def accept_submission(name, ID):
	# Get the submission itself
	request = db.where('submission', ID=ID)[0]
	author = db.where('reviewer', login=request['login'])[0]
	rvr = get_user_data(name)
	
	# Give the review to that reviewer FIRST OR SECOND?
	# (I'd like this to be more general, later)
	if rvr.milestone == "None yet" or rvr.milestone == "1st Paper":
		num = "1"
	else:
		num = "2"
	
	request['reviewer_'+num] = rvr.login
	db.update('submission', where="login=$login", vars=request, **request)
	#	log an 'active' for them
	increment(rvr, 'active_requests')
	#	email the author
	email_notice(author.email, 'accepted', reviewer=rvr['name'])
	# 	set a reminder with the deadline
	td = datetime.timedelta(days=request.timeline-1)
	now = datetime.datetime.now()
	reminder = {'recipient': rvr.login, 
				'message': "You have a review for "\
							+author.name+" due in 1 day!",
				'reveal_if_after':now+td}
	db.insert('alert', **reminder)
	#	make a 'finish' object
	finished = {'reviewer': rvr.login,
				'requester': author.login
				}
	db.insert('finished', **finished)

	# alert the author (also an alert?)	
	# else?
	

	
def reject_submission(name, ID):
	# notch up the 'passes' for the rejector
	print 'was this called at all?'
	increment(name, 'passes', name_only=True)
	# get the lists ... BUT WHICH ONE!?!
	request = db.where('submission', ID=ID)[0]
	next_jr = request.jr_list.split()
	next_sr = request.sr_list.split()
	print "next_jr", next_jr
	print "next_sr", next_sr

	if next_jr[0] and name == next_jr[0]:
		print 'in jr!'
		if len(next_jr) > 1:
			request_review(next_jr[1], next_jr[1:], 'jr', name_only=True)
		elif len(next_sr) > 1:
			request_review(next_sr[1], next_sr[1:], 'sr', name_only=True)
	elif next_sr and name == next_sr[0]:
		print 'in sr!'
		if len(next_sr) > 1:
			request_review(next_sr[1], next_sr[1:], 'sr', name_only=True)
		elif len(next_sr) > 1:
			request_review(next_jr[1], next_jr[1:], 'jr', name_only=True)
	else:
		#NObody was left ... tell the author.
		author = db.where('reviewer', login=request.login)[0]
		email_notice(author.email, "apology")
		print 'only got here!'
		
	
	
	
def test_insert(person):
	db.insert('reviewer', **person)

def nuclear_option():
	for table in ["reviewer", "submission", "review", "review_review"]:
		try:
			db.query('DROP TABLE '+table+';')
		except:
			pass
	#db.query('DROP TABLE submission;')
	#db.query('DROP TABLE review;')
	#db.query('DROP TABLE review_review;')
