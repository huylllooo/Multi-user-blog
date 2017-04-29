from google.appengine.ext import db
from models.user import User

import utils

"""
Post class
store blog post's info
"""
class Post(db.Model):

	# basic info
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	user = db.ReferenceProperty(User, required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)

	# post's likes
	liked_users = db.StringListProperty()

	@property
	def likes(self):
		return len(self.liked_users)

	# post's comments
	comments_count = db.IntegerProperty(required = True)


	def render(self):
		self._render_text = self.content.replace('\n', '<br>')
		return utils.render_str("post.html", p = self)