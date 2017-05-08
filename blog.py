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

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=True
    )

secret = "10ajwoc803nwW"


#  Universal functions*****************************************************
def render_strg(template, **params):
    """Renders output based upon template

    Args:
        template: Incoming HTML templace
        **params: any passed on parameters

    Returns:
        Calls render on the newly created object
    """
    t = jinja_env.get_template(template)
    return t.render(params)


def make_secure_val(val):
    """Creates a hash to be used as a cookie

    Args:
        val: A string value for hashing

    Returns:
        constructed val,hashedval
    """
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    """Checks an existing hash from a cookie to determine if valid

    Args:
        secure_val: val,hashedval object needing to be checked

    Returns:
        """
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


def make_salt(length=5):
    """Creates a random salt of a length that defaults to 5 char

    Args:
        Length: defaults at 5 but can be set longer

    Returns:
        String of random letters of length=X
    """
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    """Creates a password hash for secure DB storage   
    Args:
        name: name of user
        pw: password of user
        salt: Any previously defined salt(defaults to none)

    Returns:
        salt,hash
    """
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_username(username):
    """Checks if a new username is valid"""
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and USER_RE.match(username)


def valid_password(password):
    """Checks if a new password is valid"""
    PASS_RE = re.compile(r"^.{3,20}$")
    return password and PASS_RE.match(password)


def valid_pw(name, password, h):
    """Checks if incoming password is valid for a specific user"""
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


def login_required(func):
    """
    A decorator to confirm a user is logged in or redirect as needed.
    """
    def login(self, *args, **kwargs):
        # Redirect to login if user not logged in, else execute func.
        if not self.user:
            self.redirect("/")
        else:
            func(self, *args, **kwargs)
    return login


#  Blog and database classes **************************************************
class BlogHandler(webapp2.RequestHandler):
    """Basic blog functions which are imported into page classes"""
    def write(self, *a, **kw):
        """Simplifies the write function"""
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """Sends the render with template to the global function -line 25"""
        return render_strg(template, **params)

    def render(self, template, **kw):
        """Builds content and sends to render_str"""
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        """Sets a hashed tracking cookie for a user"""
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        """Checks if a cookie is valid"""
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        """Login function setting cookie and page redirect"""
        self.set_secure_cookie('user_id', str(user.key().id()))
        self.redirect('/welcome')

    def logout(self):
        """Logout function clears cookie and redirects to home"""
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/')

    def initialize(self, *a, **kw):
        """Used to check a users login status on every page"""
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


class User(db.Model):
    """Defines User database and gives it default functions"""
    """Sets the user DB"""
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        """Returns a user file found by id"""
        return User.get_by_id(uid)

    @classmethod
    def by_name(cls, name):
        """Returns a user file found by name"""
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        """Creates a pw hash and returns a built user structure"""
        pw_hash = make_pw_hash(name, pw)
        return User(name=name,
                    pw_hash=pw_hash,
                    email=email)

    @classmethod
    def login(cls, name, pw):
        """Checks if username and password are valid"""
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class Comment(db.Model):
    """defines a comments DB for posts
    Attr:
        postID: ID number of post comment is for
        commenter: user who wrote the comment
        comment: comment text
        created: date of comment creation
        CID: Comment KeyID held more accessible for templates
        """
    postID = db.StringProperty(required=True)
    commenter = db.StringProperty(required=True)
    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    CID = db.StringProperty()

    def render(self):
        """Formats text so that returns show in html reprint"""
        self._render_text = self.comment.replace('\n', '<br>')
        return render_strg("comment.html", p=self)


class Post(db.Model):
    """Defines user post database
    Attr:
        subject: Subject of post
        content: Post content
        created: Date of post creation
        poster: User who created post
        """
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    poster = db.StringProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    liked_by = db.ListProperty(str)
    perma_link = db.StringProperty()

    def render(self):
        """Formats text so that returns show in html reprint"""
        self._render_text = self.content.replace('\n', '<br>')
        return render_strg("post.html", p=self)


#  Blog page handlers**********************************************************
#  All blog pages that require a login have the if self.user checking for login

class BlogFront(BlogHandler):
    """Main blog page handler /blog"""
    @login_required
    def get(self):
        posts = Post.all().order('-created')
        self.render('blog.html', posts=posts)


class CEditPost(BlogHandler):
    """Handles editing of posts "/edit/"""
    @login_required
    def get(self, post_id):
        key = db.Key.from_path('Comment', int(post_id))
        c = db.get(key)
        if c:
            comment = c.comment
            pid = c.postID
            self.render("cedit.html", comment=comment, pid=pid)
        else:
            self.redirect('/blog')

    @login_required
    def post(self, post_id):
        comment = self.request.get('comment')
        if comment:
            key = db.Key.from_path('Comment', int(post_id))
            c = db.get(key)
            if c:
                c.comment = comment
                c.put()
                sleep(1)
                self.redirect('/%s' % c.postID)
            else:
                self.redirect('/blog')
        else:
            error = "You must enter something!"
            self.render("cedit.html", comment=comment,
                        error=error)


class CDeletePost(BlogHandler):
    """Delete a Comment"""
    @login_required
    def get(self, post_id):
        key = db.Key.from_path('Comment', int(post_id))
        comment = db.get(key)
        if comment.commenter == self.user.name:
            post = str(comment.postID)
            comment.delete()
        else:
            self.redirect('/blog')
        """redirect was happening before delete completed so sleep added"""
        sleep(1)
        self.redirect('/%s' % post)


class DeletePost(BlogHandler):
    """Delete a post"""
    @login_required
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id))
        post = db.get(key)
        if post and (self.user.name == post.poster):
            post.delete()
        """redirect was happening before delete completed so sleep added"""
        sleep(1)
        self.redirect('/')


class EditPost(BlogHandler):
    """Handles editing of posts "/edit/"""
    @login_required
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id))
        post = db.get(key)
        if post:
            subject = post.subject
            content = post.content
            pid = post_id
            self.render("edit.html", subject=subject, content=content, pid=pid)
        else:
            self.redirect('/blog')

    @login_required
    def post(self, post_id):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            key = db.Key.from_path('Post', int(post_id))
            p = db.get(key)
            if p and (self.user.name == p.poster):
                p.subject = subject
                p.content = content
                p.put()
                sleep(1)
                self.redirect(p.perma_link)
            else:
                self.redirect('/blog')
        else:
            error = "Subject and content, please!"
            self.render("edit.html", subject=subject, content=content,
                        error=error)


class Login(BlogHandler):
    """Handles the "/Login" page"""
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


class Logout(BlogHandler):
    """Logout function"""
    def get(self):
        self.logout()


class MainPage(BlogHandler):
    """Handles intro page "/"""
    def get(self):
        if self.user:
            self.redirect('/blog')
        else:
            self.render("start.html")


class NewPost(BlogHandler):
    """Handles new posts "/newpost"""
    @login_required
    def get(self):
        self.render("newpost.html")

    @login_required
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


class PostPage(BlogHandler):
    """Handles permanent linked posts "/([0-9]+)"""
    @login_required
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id))
        user = self.user.name
        post = db.get(key)
        posts = Comment.all().filter('postID =', post_id).order('-created')
        likes = 0
        liked = False
        for people in post.liked_by:
            likes += 1
            if people == user:
                liked = True
        if not post:
            self.error(404)
            return
        self.render("permalink.html", post=post, user=user, posts=posts,
                    likes=str(likes), liked=liked)

    @login_required
    def post(self, post_id):
        """used for new comments"""
        key = db.Key.from_path('Post', int(post_id))
        user = self.user.name
        if self.request.get('comment'):
            comment = self.request.get('comment')
            c = Comment(commenter=user, postID=post_id, comment=comment)
            c.put()
            c.CID = '%s' % str(c.key().id())
            c.put()
            sleep(1)
            self.redirect('/%s' % post_id)
        elif self.request.get('like'):
            p = db.get(key)
            if self.user.name != p.poster:
                if self.user.name not in p.liked_by:
                    p.liked_by.append(user)
                    p.put()
                    sleep(1)
                self.redirect(p.perma_link)
        else:
            posts = Comment.all().filter('postID =', post_id).order('-created')
            user = self.user.name
            error = "You must enter something!"
            self.render("permalink.html", post=post_id, user=user,
                        posts=posts, error=error)


class Signup(BlogHandler):
    """Handles the singup page "/signup"""
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


class Welcome(BlogHandler):
    """Handles the "/welcome" page. Users are sent there upon login/signup"""
    @login_required
    def get(self):
        self.render("welcome.html", name=self.user.name)

"""Below tells the application which function to send a specific web address"""
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
