# Blog_final

<h1>Udacity Full Stack Developer Blog section final</h1>
<h2>Written by R. Sherman</h2>


<h3>Description</h3>
<p>The purpose of this project is to show completed knowledge of backend programming knowledge folowing the guidelines of the Udacity Full Stack Developer Course</p>
<p>The project is intended to be uploaded and run on the Google App Engine system and is coded appropriately for that.</p>

<h3>Files/Folders</h3>
<h4>Readme.md</h4>
<p>This file which give instructions on the app and it's uses</p>
<br>
<h4>app.yaml</h4>
<p>Instruction file used for uploading to the Google App Engine</p>
<br>
<h4>blog.py</h4>
<p>Main program running the blog written in Python with the Jinja2 plugin used</p>
<br>
<h4>/static/main.css</h4>
<p>CSS file for HTML code
<br>
<h4>/Templates/blog.html</h4>
<p>Webpage that shows blog posts once logged in</p>
<br>
<h4>/Templates/blog_template.html</h4>
<p>Main blog template that all other pages pull from</p>
<br>
<h4>/Templates/cedit.html</h4>
<p>Page used to edit comments</p>
<br>
<h4>/Templates/comment.html</h4>
<p>Page used to format comments</p>
<br>
<h4>/Templates/edit.html</h4>
<p>Page used to edit posts</p>
<br>
<h4>/Templates/login.html</h4>
<p>Login webpage</p>
<br>
<h4>/Templates/logout.html</h4>
<p>Logout webpage</p>
<h4>/Templates/newpost.html</h4>
<p>Page used for new posts</p>
<br>
<h4>/Templates/permalink.html</h4>
<p>Page used when linking to a single post</p>
<br>
<h4>/Templates/post.html</h4>
<p>Html used to format post display</p>
<br>
<h4>/Templates/signup.html</h4>
<p>Signup page for site</p>
<br>
<h4>/Templates/start.html</h4>
<p>Initial un-logged in landing page</p>
<br>
<h4>/Templates/welcome.html</h4>
<p>Welcome page used when logging in</p>


<h3>Implementation</h3>
<p>To start with you will need to install the Google App engine which can be downloaded and installed at https://cloud.google.com/appengine/docs/standard/python/download</p>
<p>Once installed you can run the app on your local machine by running command <i>dev_appserver.py app.yaml</i></p>
<p>This will allow you to view the app at web address localhost:8080</p>
<br>
<p>Once you are happy with the app you can use the gcloud command system to upload the app to the web. You will need to setup a Gcloud project to upload to first</p>
<p>Gcloud is constantly updating so be sure and check the API documentation before attempting an upload</p>

<h3>Notes</h3>
<p>This program was written to run with Python 2.7 and may not work using other versions of Python</p>