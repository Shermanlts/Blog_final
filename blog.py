import os
import re
import random
import hashlib
import hmac
from string import letters
from time import sleep

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "Templates")
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=True
    )

secret = "10ajwoc803nwW"

#  Universal functions*****************************************************


#  Renders output based upon template
def render_strg(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


#  Creates a hash to be used as a cookie
def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


#  Checks an existing hash from a cookie to determine if valid
def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


#  Creates a random salt of a length that defaults to 5 char
def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


#  Creates a password hash for secure DB storage
def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


#  Checks if a new username is valid
def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and USER_RE.match(username)


#  Checks if a new password is valid
def valid_password(password):
    PASS_RE = re.compile(r"^.{3,20}$")
    return password and PASS_RE.match(password)


#  Checks if incoming password is valid for a specific user
def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


#  Blog and database classes **************************************************
#  Basic blog functions which are imported into page classes
class BlogHandler(webapp2.RequestHandler):
    # Simplifies the write function
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    # Sends the render with template to the global function -line 25
    def render_str(self, template, **params):
        return render_strg(template, **params)

    # Builds content and sends to render_str
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Sets a hashed tracking cookie for a user
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    # Checks if a cookie is valid
    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    # Login function setting cookie and page redirect
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))
        self.redirect('/welcome')

    # Logout function clears cookie and redirects to home
    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/')

    # Used to check a users login status on every page
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


#  Defines User database and gives it default functions
class User(db.Model):
    # Sets the user DB
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    # Checks if a uid is valid
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    # Checks if a name is valid
    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    # Creates a pw hash and returns a built user structure
    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return User(name=name,
                    pw_hash=pw_hash,
                    email=email)

    # Checks if username and password are valid
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


# defines a comments DB for posts
class Comment(db.Model):
    # Sets the comments DB
    postID = db.StringProperty(required=True)
    commenter = db.StringProperty(required=True)
    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    # CID is used to hold the keyID more accessible for template use
    CID = db.StringProperty()

    def render(self):
        self._render_text = self.comment.replace('\n', '<br>')
        return render_strg("comment.html", p=self)


#  Defines user post database
class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    poster = db.StringProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    perma_link = db.StringProperty()

    # Formats text so that returns show in html reprint
    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_strg("post.html", p=self)


#  Blog page handlers**********************************************************
#  All blog pages that require a login have the if self.user checking for login

# Main blog page handler /blog
class BlogFront(BlogHandler):
    def get(self):
        if self.user:
            posts = Post.all().order('-created')
            self.render('blog.html', posts=posts)
        else:
            self.redirect('/')


# Handles editing of posts "/edit/"
class CEditPost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Comment', int(post_id))
            c = db.get(key)
            comment = c.comment
            pid = c.postID
            self.render("edit.html", comment=comment, pid=pid)
        else:
            self.redirect('/')

    def post(self, post_id):
        comment = self.request.get('comment')
        if comment:
            key = db.Key.from_path('Comment', int(post_id))
            c = db.get(key)
            c.comment = comment
            c.put()
            sleep(1)
            self.redirect('/%s' % c.postID)
        else:
            error = "You must enter something!"
            self.render("edit.html", comment=comment,
                        error=error)


# Delete a post
class CDeletePost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Comment', int(post_id))
            comment = db.get(key)
            post = str(comment.postID)
            comment.delete()
            # redirect was happening before delete completed so sleep added
            sleep(1)
            self.redirect('/%s' % post)


# Delete a post
class DeletePost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id))
            post = db.get(key)
            post.delete()
            # redirect was happening before delete completed so sleep added
            sleep(1)
            self.redirect('/')


# Handles editing of posts "/edit/"
class EditPost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id))
            post = db.get(key)
            subject = post.subject
            content = post.content
            pid = post_id
            self.render("edit.html", subject=subject, content=content, pid=pid)
        else:
            self.redirect('/')

    def post(self, post_id):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            key = db.Key.from_path('Post', int(post_id))
            p = db.get(key)
            p.subject = subject
            p.content = content
            p.put()
            sleep(1)
            self.redirect(p.perma_link)
        else:
            error = "Subject and content, please!"
            self.render("edit.html", subject=subject, content=content,
                        error=error)


# Handles the "/Login" page
class Login(BlogHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            msg = 'Invalid login'
            self.render('login.html', error=msg)


# Logout function
class Logout(BlogHandler):
    def get(self):
        self.logout()


# Handles intro page "/"
class MainPage(BlogHandler):
    def get(self):
        if self.user:
            self.redirect('/blog')
        else:
            self.render("start.html")


# Handles new posts "/newpost"
class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect('/')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(subject=subject, content=content, poster=self.user.name)
            p.put()
            p.perma_link = '/%s' % str(p.key().id())
            p.put()
            self.redirect(p.perma_link)
        else:
            error = "Subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


# Handles permanent linked posts "/([0-9]+)"
class PostPage(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id))
            user = self.user.name
            post = db.get(key)
            posts = Comment.all().order('-created')
            if not post:
                self.error(404)
                return
            self.render("permalink.html", post=post, user=user, posts=posts)
        else:
            self.redirect('/')

    def post(self, post_id):
        if self.request.get('content'):
            key = db.Key.from_path('Post', int(post_id))
            user = self.user.name
            content = self.request.get('content')
            pid = db.get(key)
            if content:
                c = Comment(commenter=user, postID=post_id, comment=content)
                c.put()
                c.CID = '%s' % str(c.key().id())
                c.put()
                sleep(1)
                posts = Comment.all().order('-created')
                self.render("permalink.html", post=pid, user=user, posts=posts)
        elif self.request.get('cedit'):
            cedit = self.request.get('cedit')
        else:
            posts = Comment.all().order('-created')
            error = "You must enter something!"
            self.render("permalink.html", post=post_id, user=user,
                        posts=posts, error=error)


# Handles the singup page "/signup"
class Signup(BlogHandler):
    def get(self):
        self.render("signup.html")

    def post(self):
        errors = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')
        holder = dict(username=self.username)
        user_exists = User.by_name(self.username)

        if not valid_username(self.username):
            holder['name_err'] = "Not a valid username."
            errors = True
        elif user_exists:
            holder['name_err'] = "That user already exists."
            errors = True

        if not valid_password(self.password):
            holder['pass_err'] = "Not a valid password."
            errors = True
        elif self.password != self.verify:
            holder['pass_err'] = "Passwords do not match."

        if errors:
            self.render('signup.html', **holder)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
            self.login(u)
            self.redirect('/welcome')


# Handles the "/welcome" page. Users are sent there upon login/signup
class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render("welcome.html", name=self.user.name)
        else:
            self.redirect('/')

app = webapp2.WSGIApplication([("/", MainPage),
                               ("/blog", BlogFront),
                               ("/([0-9]+)", PostPage),
                               ("/newpost", NewPost),
                               ("/signup", Signup),
                               ("/delete/([0-9]+)", DeletePost),
                               ("/edit/([0-9]+)", EditPost),
                               ("/cedit/([0-9]+)", CEditPost),
                               ("/cdelete/([0-9]+)", CDeletePost),
                               ("/login", Login),
                               ("/welcome", Welcome),
                               ("/logout", Logout)
                               ],
                              debug=True)
