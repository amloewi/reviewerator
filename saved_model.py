import web
import datetime
# All taken verbatim from 
# http://stackoverflow.com/questions/9272257/how-can-i-send-email-using-python?rq=1
# As are the contents of "email_request_notice()"
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

DEVELOPMENT = True	


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
	
	r1 = list(db.where('submission', active=1, assigned_reviewer_1=login))
	r2 = list(db.where('submission', active=1, assigned_reviewer_2=login))
	return(r1+r2)

def email_notice(email, message, author=None, reviewer=None):

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

	subject = "[PhdRvr] " + subject
	
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


def process_submission(data):
	'''Called when a review request is submitted. Increments the 
	number of reviews requested in the reviewer\'s profile, then 
	selects two (currently) reviewers for them, and files the submission.
	It will be called up when the log in. 
	And this SHOULD EMAIL them.
	'''
	
	# Notch one up for the submitter
	author = db.where('reviewer', login=data['author'])[0]
	new_value = author.submitted+1
	db.update('reviewer', where="login=$login", 	
				vars={"login":data['author']}, submitted=new_value)
	
	# Choose reviewers, based on the ratio AND CURRENT LOAD
	rvrs = db.where('reviewer', enabled=1)
	if rvrs:
		# Can't review your own paper
		rvrs = [r for r in list(rvrs) if r.login != data['author']]
		
		# Split by seniority
		rdict = {"jr":[], "sr":[]}
		for r in rvrs:
			if r.milestone == "None yet" or r.milestone == "1st Paper":
				rdict['jr'].append(r)
			else: # "2nd Paper" or "Proposal"
				rdict['sr'].append(r)
		
		
		#
		# THE NEW PLAN: Get a COMPLETE ordering of the reviewers.
		# FOr each subset, find the first, lop em off, do the rest. 
		# Or actually -- it could all br done at once. 
		# Send these lists with the submission, to fill in no-takes.
		#
		
		# Sorty by active requests
		jr_sort_load = sorted(rdict['jr'], key=lambda r: r.active_requests)
		sr_sort_load = sorted(rdict['sr'], key=lambda r: r.active_requests)
	
		# Take those with the lowest number of active requests
		jr_low_load = [r for r in jr_sort_load
					if r.active_requests == jr_sort_load[0].active_requests]
		sr_low_load = [r for r in sr_sort_load
					if r.active_requests == sr_sort_load[0].active_requests]
	
		# Sort the lowest-load reviewers by their submit/review ratio
		jr_sort_diff = sorted(jr_low_load, 
								key=lambda r:r.submitted-r.reviewed,
								reverse=True)
		sr_sort_diff = sorted(sr_low_load, 
								key=lambda r:r.submitted-r.reviewed,
								reverse=True)
	
		# The maximum ratio among the low-load reviewers
		maxjr = jr_sort_diff[0]
		maxjrdiff = maxjr.submitted-maxjr.reviewed
		maxsr = sr_sort_diff[0]
		maxsrdiff = maxsr.submitted-maxsr.reviewed
	
		# The low-load reviewers who have that ratio
		maxjrs = [r for r in jr_sort_diff
		 			   if (r.submitted-r.reviewed)==maxjrdiff]
		maxsrs = [r for r in sr_sort_diff 
					   if (r.submitted-r.reviewed)==maxsrdiff]
	
		# The login of the max-score low-load reviewer
		# who hasn't reviewed in longest
		rvr1 = sorted(maxjrs, key=lambda r: r.last_review)[0]
		rvr2 = sorted(maxsrs, key=lambda r: r.last_review)[0]
		
		# Let the selected reviewers know
		if not DEVELOPMENT:
			email_notice(rvr1.email, "request", author=data['author'])
			email_notice(rvr2.email, "request", author=data['author'])

		data["assigned_reviewer_1"] = rvr1.login
		data["assigned_reviewer_2"] = rvr2.login
		
		# Notch one up for the reviewers
		r1 = db.where('reviewer', login=rvr1.login)[0]
		new_value = r1.active_requests+1
		db.update('reviewer', where="login=$login", 	
							  vars={"login":rvr1.login},
							  active_requests=new_value)
		r2 = db.where('reviewer', login=rvr2.login)[0]
		new_value = r2.active_requests+1
		db.update('reviewer', where="login=$login", 	
							  vars={"login":rvr2.login},
							  active_requests=new_value)
					
		print("rvr1: "+rvr1.login)
		print("rvr2: "+rvr2.login)

		db.insert('submission', **data)
		
	else:
		# nobody's signed up -- hope that's an error
		print "never got here"
	

	
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
