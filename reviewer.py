import web
import model
import json

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

# Do a sweep every so often to flush old papers and activate remoted people


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
			data = {d["name"]:d["value"] for d in data}
			print(data)
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
	#model.nuclear_option()
	model.test_insert(alex)
	model.test_insert(shelly)
	model.test_insert(paul)
	model.test_insert(clara)
	app.run()
