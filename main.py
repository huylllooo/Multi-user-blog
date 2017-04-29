import webapp2
import utils

from models.user import User
from models.post import Post
from models.comment import Comment

from handlers.blog import BlogHandler, MainPage, BlogFront
from handlers.blogpost import PostPage, NewPost, EditPost, DeletePost, LikePost
from handlers.auth import Signup, Register, Login, Logout
from handlers.comment import CommentPost, CommentDelete, CommentEdit


app = webapp2.WSGIApplication([('/', MainPage),
							   ('/blog/?', BlogFront),
							   ('/blog/([0-9]+)', PostPage),
							   ('/blog/edit/([0-9]+)', EditPost),
							   ('/blog/delete/([0-9]+)', DeletePost),
							   ('/blog/like/([0-9]+)', LikePost),
							   ('/blog/comment/([0-9]+)', CommentPost),
							   ('/blog/comment/delete/([0-9]+)',CommentDelete),
							   ('/blog/comment/edit/([0-9]+)', CommentEdit),
							   ('/blog/newpost', NewPost),
							   ('/signup', Register),
							   ('/login', Login),
							   ('/logout', Logout)
							   ],
							  debug=True)
