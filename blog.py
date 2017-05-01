import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), "Templates")
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=True
    )

secret = "10ajwoc803nwW"


# def make_cookie(self, uid):
#     h = hashlib.sha256(uid + secret).hexdigest()
#     return '%|%' % (uid, h)

# def check_cookie(self, cookie):
#     uid = cookie.split('|')[0]
#     if cookie == self.make_cookie(uid):
#         if user.check_id(uid):
#             return uid
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # def salt(self, length):
    #     alph = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    #     chars = []
    #     for i in range(length):
    #         chars.append(random.choice(alph))
    #     return "".join(chars)

    # def make_hash(self, name, pw, salt):
    #     if not salt:
    #         salt = salt(8)
    #     h = hashlib.sha256(name + pw + salt).hexdigest()
    #     return '%s,%s' % (salt, h)

    # def validate(self, name, pw, h):
    #     salt = h.split(',')[0]
    #     return h == hash(name, pw, salt)

    # def clear_cookie(self):
    #     self.response.headers.add_header(
    #         'Set-Cookie',
    #         '')

    # def set_cookie(self, uid):
    #     self.response.headers.add_header(
    #         'Set-Cookie',
    #         self.make_cookie(uid))

    # def logout(self):
    #     self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')


def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


def users_key(group='default'):
    return db.Key.from_path('users', group)


class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid)

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent=users_key(),
                    name=name,
                    pw_hash=pw_hash,
                    email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p=self)


class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('blog.html', posts=posts)


class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id))
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)


class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(subject = subject, content = content)
            p.put()
            self.redirect('/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)


class MainPage(BlogHandler):
    def get(self):
        self.render("start.html")


# def valid_username(username):
#     USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
#     return username and USER_RE.match(username)


# def valid_password(password):
#     PASS_RE = re.compile(r"^.{3,20}$")
#     return password and PASS_RE.match(password)


# class Signup(BlogHandler):
#     def get(self):
#         self.render("signup.html")

#     def post(self):
#         errors = False
#         self.username = self.request.get('username')
#         self.password = self.request.get('password')
#         self.verify = self.request.get('verify')
#         holder = dict(username=self.username)
#         u = user.check_name(self.username)

#         if not valid_username(self.username):
#             holder['name_err'] = "Not a valid username."
#             errors = True
#         elif u:
#             holder['name_err'] = "That user already exists."
#             errors = True

#         if not valid_password(self.password):
#             holder['pass_err'] = "Not a valid password."
#             errors = True
#         elif self.password != self.verify:
#             holder['pass_err'] = "Passwords do not match."

#         if errors:
#             self.render('signup.html', **holder)
#         else:
#             h = make_hash(self.username, self.password)
#             nu = user(name=self.username, pw_hash=h)
#             nu.put()


# class Login(BlogHandler):
#     def get(self):
#         self.render("login.html")


# class PostPage(BlogHandler):
#     def get(self):
#         self.render("blog.html")


# class NewPost(BlogHandler):
#     def get(self):
#         self.render("newpost.html")


class Blog(BlogHandler):
    def get(self):
        self.render("logout.html")


app = webapp2.WSGIApplication([("/", MainPage),
                               ("/blog", BlogFront),
                               ("/([0-9]+)", PostPage),
                               ("/newpost", NewPost),
                               # ("/signup", Signup),
                               # ("/login", Login),
                               ],
                              debug=True)
