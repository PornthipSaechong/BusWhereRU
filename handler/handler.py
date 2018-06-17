import webapp2
import jinja2

import os,datetime
from google.appengine.api import users
from database.user import User


path = 'templates'

env = jinja2.Environment(loader=jinja2.FileSystemLoader(path), 
	autoescape=True)

def to_time(value):
    return (value+datetime.timedelta(hours=8)).strftime("%Y-%m-%d|%H:%M:%S")

env.filters['to_time'] = to_time

import logging
import hmac

secret_key = "&*GdkJDFy.fz&J9w"

class Handler(webapp2.RequestHandler):

	def write(self,*a,**kw):
		self.response.headers['Content-Type'] = 'application/json' 
		self.response.out.write(*a,**kw)

	def render(self,template_html,*a,**kw):
		template = env.get_template(template_html)
		self.response.write(template.render(*a,**kw))

	def login_user(self, user):
		self.set_secure_cookie('user_id', str(user.key.id()))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
		    'Set-Cookie',
		    '%s=%s; Path=/' % (name, cookie_val))

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		logging.info(uid)
		self.user = uid and User.by_id(int(uid))

		
def make_secure_val(val):
	return '%s|%s' % (val, hmac.new(secret_key, val).hexdigest())

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val