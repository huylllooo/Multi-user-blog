from google.appengine.ext import db
from models.user import User
from models.post import Post

"""
Comment class
store comment
"""
class Comment(db.Model):

	user = db.ReferenceProperty(User, required = True,
								collection_name='comments')
	post = db.ReferenceProperty(Post, required = True,
								collection_name='comments')
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)