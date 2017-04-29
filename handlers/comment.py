from google.appengine.ext import db
import utils
import webapp2
from handlers.blog import BlogHandler
from models.user import User
from models.post import Post
from models.comment import Comment


class CommentPost(BlogHandler):
	"""Add comment to a post"""

	@utils.user_logged_in
	@utils.post_exists
	def post(self, post_id, post):

		current_user = self.user
		content = self.request.get('content')
		if content:
			c = Comment(user = current_user, post = post, content = content)
			c.put()
			post.comments_count += 1
			post.put()
			self.redirect('/blog/%s' % str(post.key().id()))
			c.put()


class CommentDelete(BlogHandler):

	@utils.user_logged_in
	@utils.comment_exists
	def post(self, comment_id, comment):
		post = comment.post

		# Check authorization, only author can delete comment
		if comment.user.name == self.user.name:
			comment.delete()
			post.comments_count -= 1
			post.put()
			self.render("permalink.html", post = post, logged_in = True)
			post.put()
			self.redirect('/blog/%s' % str(post.key().id()))
		else:
			error = "You cannot delete this comment"
			self.render("permalink.html", post = post, logged_in = True,
						comment_delete_error = error, this_comment = comment)

class CommentEdit(BlogHandler):

	@utils.user_logged_in
	@utils.comment_exists
	def get(self, comment_id, comment):
		# Check authorization, only author can edit comment
		if comment.user.name == self.user.name:
			self.render("editcomment.html", comment = comment,
						post = comment.post)
		else:
			error = "You cannot edit this comment"
			self.render("permalink.html", post = comment.post,
						logged_in = True, comment_delete_error = error,
						this_comment = comment)

	@utils.user_logged_in
	@utils.comment_exists
	def post(self, comment_id, comment):
		# Check authorization, only author can edit comment
		# Update comment
		if comment.user.name == self.user.name:
			comment.content = self.request.get('content')
			comment.put()
			self.redirect('/blog/%s' % str(comment.post.key().id()))
			comment.put()
		else:
			error = "You cannot edit this comment"
			self.render("permalink.html", post = comment.post,
				logged_in = True, comment_delete_error = error,
				this_comment = comment)