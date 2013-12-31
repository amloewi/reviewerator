import web
import model
import json
import os

import datetime
import threading #for the refresh timer
        
urls = (
    '/', 					'login',		  # ugly
	'/users',				'users',
	'/dashboard/(.+)',		'show_dashboard',
	'/edit/(.+)', 			'edit_user',     
	'/create_user',			'create_user',
	'/submit',				'submit_request',
	'/respond/(.+)',		'respond',
	'/remove/(.+)',			'remove',
	'/finished',			'finish_review',
	'/feedback',			'feedback',
)

# PROBLEM is: now I gotta change all the ajax calls in the jquery too.
# school = "/cmu"
# urls = (school+urls[i] for i in range(len(urls)) if i%2==0)

render = web.template.render('templates')

# Do a sweep every so often (an hour, now) to flush old papers, pass on unresponded-to requests, and activate deactivated people
SWEEP_FREQUENCY = 60*60 #seconds
def sweep():
	threading.Timer(SWEEP_FREQUENCY, sweep).start()
	
	now = datetime.datetime.now()
	asmts = model.db.where('assignment', active=True, accepted=False)
	for a in asmts:
		# If it's been two days since the request was sent and nobody's
		# accepted it, mark it as a pass and send a new one.
		if a.assigned + datetime.timedelta(days=model.ACCEPTANCE_WINDOW) < now:
			model.reject_submission(a.reviewer, a.paper)
			
	papers = model.db.where('paper', active=True)
	for p in papers:
		# If the paper's been due for a week, even if reviews aren't in, 
		# it should be retired. (This allows for ... ?)
		# Also, if it's gotten all its reviews in.
		late = p.submitted + datetime.timedelta(days=p.timeline+7) < now
		if p.num_assigned_reviewers == p.num_completed_reviews or late:
			
			author = model.db.where('person', id=p.author)[0]
			model.increment(author, 'active_submissions', -1)
			p.active = False
			model.db.update('paper', where="id=$id", vars=p, **p)

		# ALSO, give a 'dropped' to the people who were a full week late.
		if late:
			asmts = model.db.where('assignment', paper=p.id)
			for a in asmts:
				rvr = model.db.where('person', id=a.reviewer)[0]
				# IF THEY'VE DROPPED TOO MANY -- DISABLE THEM.
				if rvr.dropped % model.DROP_LIMIT == model.DROP_LIMIT - 1:
					model.disable(rvr, model.DROP_PENALTY)
				# GOTTA be AFTER for the check to work right.
				increment(rvr, 'dropped')
				# NOW (and not before), dropped % limit == 0, which is Reset.
		
	people = model.db.where('person', enabled=False)
	for p in people:
		# If someone was disabled for too many rejections, is their time done?
		if p.disabled_until < now:
			p.enabled = True
			model.db.update('person', where="id=$id", vars=p, **p)

# Start the sweep
sweep()

class login:        
    def GET(self):
        return render.login()


class users:
	
	def GET(self):
		users = list(model.users())
		user_ids = [u['id'] for u in users]
		return json.dumps(user_ids)
			
			
class show_dashboard:
	
	def GET(self, id): 
		# AS THE FINAL STEP, THIS NEXT LINE SHOULD BE UNCOMMENTED.
		# DON'T GET THE ID FROM THE URL, BECAUSE IT SHOULDN'T BE THERE.
		# id = json.loads(web.data())['id']
		person   = model.get_user_data(id)
		requests = model.get_user_requests(id)
		alerts   = model.get_user_alerts(id)
		finished = model.get_user_finished(id)
		feedback = model.get_user_feedback(id)		
		return render.user_page(person, requests, alerts, finished, feedback)
		
		
class edit_user:

	def POST(self, id):
		# Expects an Array of name, year, email, etc.
		data = web.data()
		if data:
			data = json.loads(data)
			data = {d["name"]:d["value"] for d in data} #un-serializeArray
			model.set_user_data(data)
			
	def GET(self, id):
		person = model.get_user_data(id)
		return render.edit_profile(person)
		
		
class create_user:

	def POST(self):
		id = web.data()
		id = json.loads(id)
		model.create_user(id)


class submit_request:
		
	def POST(self):
		data = web.data()
		if data:
			data = json.loads(data)
			#data = {d["name"]:d["value"] for d in data}
			#print(data)
			model.process_submission(data)
		
		
class respond:
	
	def POST(self, rvr_id):
		
		data = web.data()
		# Is the conditional necessary?
		if data:
			data = json.loads(data)
			paper_id = data['id']
			if data['response'] == 'yes':
				model.accept_submission(rvr_id, paper_id)
			elif data['response'] == 'no':
				model.reject_submission(rvr_id, paper_id)
			else:
				pass
				# Error of some kind
				
class remove:
	
	def POST(self, table):
		id = json.loads(web.data())['id']
		# log.delete('exercise', where="id=$id", vars=locals())
		model.db.delete(table, where="id=$id", vars=locals())
		

class finish_review:
	
	def POST(self):
		# Things to do: 
		fin_id = json.loads(web.data())['id']
		model.process_finish(fin_id)
		
class feedback:
	
	def POST(self):
		data = json.loads(web.data())
		model.process_feedback(data['id'], data['score'])
		
		

app = web.application(urls, globals())

if __name__ == "__main__":
	# Gotta -- make some profiles
	#model.nuclear_option()
	# insert a few with known stats so that ... I can test if the submission
	# works right. What is there to test?
	alex = {
			"id":"alex",
			"name":"Alex",
			"submitted":3,
			"reviewed":3,
			"milestone":"None yet",
			"enabled":True,
			#"disabled_until": datetime.datetime.now() + datetime.timedelta(minutes=1),
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"active_submissions":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	shelly = {
			"id":"shelly",
			"name":"Shelly",
			"submitted":3,
			"reviewed":3,
			"milestone":"None yet",
			"enabled":True,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"active_submissions":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	paul = {
			"id":"paul",
			"name":"Paul",
			"submitted":3,
			"reviewed":3,
			"milestone":"2nd Paper",
			"enabled":True,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"active_submissions":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	clara = {
			"id":"clara",
			"name":"Clara",
			"submitted":3,
			"reviewed":3,
			"milestone":"2nd Paper",
			"enabled":True,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"active_submissions":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	
	local = '/Users/alexloewi/Documents/Sites/heinz_reviewer'
	if os.path.abspath("") == local:
		model.test_insert(alex)
		model.test_insert(shelly)
		model.test_insert(paul)
		model.test_insert(clara)
		
	app.run()
