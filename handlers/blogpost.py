from google.appengine.ext import db
import utils
import webapp2
from handlers.blog import BlogHandler
from models.user import User
from models.post import Post


class PostPage(BlogHandler):
	"""
	Render a specified post
	"""
	@utils.post_exists
	def get(self, post_id, post):

		if self.user:
			self.render("permalink.html", post = post, logged_in = True)
		else:
			self.render("permalink.html", post = post)


class NewPost(BlogHandler):
	"""
	Create a new post
	"""
	# Prompt non-user to login page
	def get(self):
		if self.user:
			self.render("newpost.html")
		else:
			self.redirect("/login")

	# Create a new page with input subject and content
	def post(self):
		if not self.user:
			self.redirect('/blog')

		current_user = self.user
		subject = self.request.get('subject')
		content = self.request.get('content')

		if subject and content:
			p = Post(parent = utils.blog_key(), subject = subject,
					content = content, likes_count = 0,
					comments_count = 0, user = current_user)
			p.put()
			self.redirect('/blog/%s' % str(p.key().id()))
		else:
			error = "subject and content, please!"
			self.render("newpost.html", subject=subject,
						content=content, error=error)



class EditPost(BlogHandler):
	"""
	Edit a post
	"""
	# Check authorization, only author can edit post
	@utils.user_logged_in
	@utils.post_exists
	def get(self, post_id, post):

		if self.user.name == post.user.name:
			self.render("editpost.html", post=post)
		else:
			error = "Cannot edit this post"
			self.render("permalink.html", post=post,
						logged_in = True, error = error)

	# Update post
	@utils.user_logged_in
	@utils.post_exists
	def post(self, post_id, post):
		subject = self.request.get('subject')
		content = self.request.get('content')

		if self.user.name == post.user.name:
			if subject and content:
				post.subject = subject
				post.content = content
				post.put()
				self.render("permalink.html", post = post, logged_in = True)
			else:
				error = "subject and content, please!"
				self.render("editpost.html", post=post, error = error)
		else:
			error = "Cannot edit this post"
			self.render("permalink.html", post=post,
						logged_in = True, error = error)

"""
Delete a post
"""
class DeletePost(BlogHandler):

	# Check authorization, only author can delete post
	@utils.user_logged_in
	@utils.post_exists
	def get(self, post_id, post):
		if self.user.name == post.user.name:
			subject = post.subject
			post.delete()
			self.render("post-deleted.html", subject = subject)
		else:
			error = "You cannot delete this post"
			self.render("permalink.html", post=post,
						logged_in = True, error = error)


##### Like related #####

class LikePost(BlogHandler):

	@utils.user_logged_in
	@utils.post_exists
	def get(self, post_id, post):

		if self.user.name == post.user.name:
			error = "You are trying to like your own post! ;)"
			self.render("permalink.html", post=post,
						logged_in = True, error = error)
		else:
			#check if user has liked this post or not
			if self.user.name in post.liked_users:
				liked = True
			else:
				liked = False
			if liked:
				post.liked_users.remove(self.user.name)
				post.put()
				self.redirect('/blog/%s' % str(post.key().id()))
			else:
				post.liked_users.append(self.user.name)
				post.put()
				self.redirect('/blog/%s' % str(post.key().id()))