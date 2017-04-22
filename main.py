import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'sjgpi09343p*&Nlseur'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

"""
Handle generic stuff
"""
class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class MainPage(BlogHandler):
    def get(self):
        posts = greetings = Post.all().order('-created')
        self.render('front.html', posts = posts)


##### Accounts and Security #####

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

"""
User class
"""

class User(db.Model):

    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


##### Blog post related #####

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

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
    likes_count = db.IntegerProperty(required = True)
    liked_users = db.StringListProperty()

    # post's comments
    comments_count = db.IntegerProperty(required = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

"""
Render blog's frontpage
"""
class BlogFront(BlogHandler):

	# get 10 lastest post
    def get(self):
        posts = greetings = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts)

"""
Render a specified post
"""
class PostPage(BlogHandler):

    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        if self.user:
        	self.render("permalink.html", post = post, logged_in = True)
        else:
        	self.render("permalink.html", post = post)

"""
Create a new post
"""
class NewPost(BlogHandler):

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
            p = Post(parent = blog_key(), subject = subject,
            		content = content, likes_count = 0,
            		comments_count = 0, user = current_user)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject,
            			content=content, error=error)

"""
Edit a post
"""
class EditPost(BlogHandler):

	# Check authorization, only author can edit post
    def get(self, post_id):
        if not self.user:
            self.redirect('/blog')

    	key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        if self.user.name == post.user.name:
        	self.render("editpost.html", post=post)
        else:
        	error = "Cannot edit this post"
        	self.render("permalink.html", post=post,
        				logged_in = True, error = error)

    # Update post
    def post(self, post_id):
        if not self.user:
            self.redirect('/blog')

    	key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return

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
    def get(self, post_id):
        if not self.user:
            self.redirect('/blog')

    	key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
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
    def get(self, post_id):
        if not self.user:
            self.redirect('/blog')

    	key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return

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
		        post.likes_count -= 1
		        post.put()
		        self.redirect('/blog/%s' % str(post.key().id()))
	        else:
	        	post.liked_users.append(self.user.name)
		        post.likes_count += 1
		        post.put()
		        self.redirect('/blog/%s' % str(post.key().id()))


###### Comment related #####

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

class CommentPost(BlogHandler):
	"""Add comment to a post"""

	def post(self, post_id):
		if not self.user:
			self.redirect('/login')
			return

		key = db.Key.from_path('Post', int(post_id), parent=blog_key())
		post = db.get(key)

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
	def post(self, comment_id):
		# Prompt non-user to login page
		if not self.user:
			self.redirect('/login')
			return

		comment = Comment.get_by_id(int(comment_id))
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

	def get(self, comment_id):
		comment = Comment.get_by_id(int(comment_id))
		# Prompt non-user to login page
		# Check authorization, only author can edit comment
		if not self.user:
			self.redirect('/login')
		else:
			if comment.user.name == self.user.name:
				self.render("editcomment.html", comment = comment,
							post = comment.post)
			else:
				error = "You cannot edit this comment"
				self.render("permalink.html", post = comment.post,
							logged_in = True, comment_delete_error = error,
							this_comment = comment)

	def post(self, comment_id):
		comment = Comment.get_by_id(int(comment_id))
		# Prompt non-user to login page
		# Check authorization, only author can edit comment
		# Update comment
		if not self.user:
			self.redirect('/login')
		else:
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

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/blog')

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/signup')

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
