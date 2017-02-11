import os
import re
import random
import hashlib
import hmac
import string

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'Templates')
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    autoescape=True
    )

secret = 'monkey'


# def render_str(template, **params):
#    t = jinja_env.get_template(template)
#    return t.render(params)


# def make_secure(val):
#    return '%|%' % (val, hmac.new(secret, val).hexdigest())


# def check_secure(secure_val):
#    val = secure_val.split('|')[0]
#    if secure_val == make_secure(val):
#        return val


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **kw):
        t = jinja_env.get_template(template)
        return t.render(kw)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(BlogHandler):
    def get(self):
        self.render('welcome.html')


class Signup(BlogHandler):
    def get(self):
        self.render('signup.html')


class login(BlogHandler):
    def get(self):
        self.render('login.html')


class PostPage(BlogHandler):
    def get(self):
        self.render('blog.html')


class NewPost(BlogHandler):
    def get(self):
        self.render('newpost.html')


class logout(BlogHandler):
    def get(self):
        self.render('logout.html')

app = webapp2.WSGIApplication([('/?', MainPage),
                               ('/([0-9]+', PostPage),
                               ('/newpost', NewPost),
                               ('/signup', Signup),
                               ('/login', login),
                               ('/logout', logout),
                               ],
                              debug=True)
