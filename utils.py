import os
import re
import random
import hashlib
import hmac
from string import letters
from functools import wraps
from google.appengine.ext import db
from models.comment import Comment

import jinja2

##### Template rendering #####
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
							   autoescape = True)

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

##### Accounts and Security #####
secret = 'sjgpi09343p*&Nlseur'
def make_salt(length = 5):
	return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split(',')[0]
	return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
	return db.Key.from_path('users', group)

def make_secure_val(val):
	return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val

##### Blog post related #####

def blog_key(name = 'default'):
	return db.Key.from_path('blogs', name)

def comment_exists(f):
	@wraps(f)
	def check_comment(self, comment_id):
		comment = Comment.get_by_id(int(comment_id))
		if comment:
			return f(self, comment_id, comment)
		else:
			self.error(404)
			return

	return check_comment

def user_logged_in(f):
	@wraps(f)
	def check_logged_in(self, something_id):
		if not self.user:
			self.redirect('/login')
			return
		else:
			return f(self, something_id)

	return check_logged_in

def post_exists(f):
	@wraps(f)
	def check_post(self, post_id):
		key = db.Key.from_path('Post', int(post_id), parent=blog_key())
		post = db.get(key)
		if post:
			return f(self, post_id, post)
		else:
			self.error(404)
			return

	return check_post

##### Sign up, Log in, Log out#####

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
	return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
	return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
	return not email or EMAIL_RE.match(email)