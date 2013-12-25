import web
import model
import json

import datetime
        
urls = (
    '/', 					'login',		  # ugly
	'/users',				'users',
	'/dashboard/(.+)',		'show_dashboard',
	'/edit/(.+)', 			'edit_user',     
	'/create_user',			'create_user',
	'/submit',				'submit_request',
	'/respond/(.+)',		'respond',
)

# PROBLEM is: now I gotta change all the ajax calls in the jquery too.
# school = "/cmu"
# urls = (school+urls[i] for i in range(len(urls)) if i%2==0)

render = web.template.render('templates')

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
		# It gets 'login' from the (.*) regex.
		person = model.get_user_data(id)
		requests  = model.get_user_requests(id)
		#alerts   = model.get_user_alerts(id)
		#finished = model.get_user_finished(id)
		#feedback = model.get_user_feedback(id)		
		return render.user_page(person, requests) #, alerts, finished, feedback)
		
		
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
		return render.edit_profile(id, person)
		
		
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
			data['active'] = 1
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

app = web.application(urls, globals())

if __name__ == "__main__":
	# Gotta -- make some profiles
	#model.nuclear_option()
	# insert a few with known stats so that ... I can test if the submission
	# works right. What is there to test?
	alex = {
			"login":"alex",
			"submitted":3,
			"reviewed":3,
			"milestone":"None yet",
			"enabled":1,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	shelly = {
			"login":"shelly",
			"submitted":3,
			"reviewed":3,
			"milestone":"None yet",
			"enabled":1,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	paul = {
			"login":"paul",
			"submitted":3,
			"reviewed":3,
			"milestone":"2nd Paper",
			"enabled":1,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	clara = {
			"login":"clara",
			"submitted":3,
			"reviewed":3,
			"milestone":"2nd Paper",
			"enabled":1,
			"passes":0,
			"dropped":0,
			"active_requests":0,
			"email":"amloewi@gmail.com",
			"last_review":datetime.datetime.now()
	}
	#model.nuclear_option()
	model.test_insert(alex)
	model.test_insert(shelly)
	model.test_insert(paul)
	model.test_insert(clara)
	app.run()
