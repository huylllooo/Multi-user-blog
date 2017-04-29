from google.appengine.ext import db
import utils
import webapp2
from models.user import User
from models.post import Post

"""
Handle generic stuff
"""
class BlogHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		params['user'] = self.user
		return utils.render_str(template, **params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self, name, val):
		cookie_val = utils.make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and utils.check_secure_val(cookie_val)

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and User.by_id(int(uid))

class MainPage(BlogHandler):
	def get(self):
		posts = greetings = Post.all().order('-created')
		self.render('front.html', posts = posts)

"""
Render blog's frontpage
"""
class BlogFront(BlogHandler):

	# get 10 lastest post
	def get(self):
		posts = greetings = db.GqlQuery("select * from Post order by created desc limit 10")
		self.render('front.html', posts = posts)