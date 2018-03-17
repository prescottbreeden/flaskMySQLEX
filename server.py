from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector
import hashlib, re, os, binascii
app = Flask(__name__)
mysql = MySQLConnector(app, 'practice_mydb')
app.secret_key = 'lkajsdhflkja'
salt = binascii.b2a_hex(os.urandom(15))
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')



@app.route('/')
def index():
	if 'user_id' not in session:
		session['status'] = 'guest'
	else:
		session['status'] = 'logged_in'
	return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
	errors = [] #create empty array for errors 
	user_fname = request.form['first_name'].capitalize()
	user_lname = request.form['last_name'].capitalize()
	user_email = request.form['email'].lower()
	user_password = request.form['password']
	user_cpassword = request.form['cpassword']

	#email validation
	if 'user_id' in session:
		errors.append('Please log out before registering a new user')
	if len(user_fname) < 1:
		errors.append('First name cannot be blank')
	if len(user_lname) < 1:
		errors.append('Last name cannot be blank')
	if len(user_email) < 1:
		errors.append('Email cannot be blank')
	if not EMAIL_REGEX.match(user_email):
		errors.append('Invalid Email Address')

	#password validation
	if user_password != user_cpassword:
		errors.append('Passwords do not match')
	if(len(user_password)<6 or len(user_password)>12):
		errors.append('passwords must be between 6 and 12 characters long')
	user_password = hashlib.md5(user_password).hexdigest() + salt
	if len(errors) > 0:
		for error in errors:
			flash(error)
		return redirect('/')

	#add user to database
	data = { 
		'first_name':user_fname, 
		'last_name':user_lname, 
		'email':user_email, 
		'user_password':user_password,
		'salt': salt
		}
	query = "INSERT INTO users (first_name, last_name, email, password, salt) "
	query += "VALUES (:first_name, :last_name, :email, :user_password, :salt)"	
	mysql.query_db(query, data)

	#grab new user back from server and activate session
	query = "SELECT * FROM users WHERE email = '{}'".format(user_email)
	new_user = mysql.query_db(query)

	if new_user != []:
		session['user_id'] = new_user[0]['id']
		session['user_name'] = '{} {}'.format(new_user[0]['first_name'], new_user[0]['last_name'])
		session['user_email'] = new_user[0]['email']
		session['welcome'] = 'Welcome {}!'.format(session['user_name'])
		print("User {} has logged in".format(session['user_id']))
	else:
		print('oh no... we suck again!')
	return redirect('/')

@app.route('/login', methods=['POST'])
def login():
	errors = []
	if len(request.form['email']) < 1:
		errors.append('Please enter an email to log in')
	if len(request.form['password']) < 1:
		errors.append('Please enter a password to log in')
	user_email = request.form['email']
	user_password = request.form['password']
	hashed_password = hashlib.md5(user_password).hexdigest()
	if len(errors) > 0:
		for error in errors:
			flash(error)
		return redirect('/')
	query = "SELECT * FROM users WHERE email = :user_email"
	data = {
		'user_email': user_email,
		'password': hashed_password,
	}
	email_validate = mysql.query_db(query, data)
	if email_validate != []:
		if hashed_password + email_validate[0]['salt'] == email_validate[0]['password']:
			session['user_id'] = email_validate[0]['id']
			session['user_name'] = '{} {}'.format(email_validate[0]['first_name'], email_validate[0]['last_name'])
			session['user_email'] = email_validate[0]['email']
			session['welcome'] = 'Welcome {}!'.format(session['user_name'])
			query = 'SELECT * '
			query += 'FROM posts '
			query += 'INNER JOIN users '
			query += 'ON posts.user_id = users.id '
			query += 'ORDER BY posts.created_at '
			session['recent_posts'] = mysql.query_db(query)
			print("User {} has logged in".format(session['user_id']))
		else:
			flash('incorrect password')
	else:
		flash('Email not found')
	return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
	session.clear()
	print('session cleared')
	return redirect('/')

@app.route('/friends', methods=['POST'])
def add_friends():
	query = "INSERT INTO friends (first_name, last_name, occupation) VALUES (:first_name,:last_name,:occupation)"
	data = {
		'first_name': request.form['first_name'],
		'last_name': request.form['last_name'],
		'occupation': request.form['occupation']
		}
	mysql.query_db(query, data)
	return redirect('/database')

@app.route('/database')
def database_of_friends():
	friends = mysql.query_db("SELECT * FROM friends")
	if 'first_name' not in session:
		session['first_name'] = 'first name'
	if 'last_name' not in session:
		session['last_name'] = 'last name'
	if 'occupation' not in session:
		session['occupation'] = 'occupation'
	return render_template('database.html', all_friends=friends)

@app.route('/update_friend/<friend_id>', methods=['POST'])
def button_click(friend_id):
	session['friend_id'] = friend_id
	query = "SELECT * from friends where id = {}".format(friend_id)
	result = mysql.query_db(query)

	#change session variable names!!
	session['first_name'] = result[0]['first_name']
	session['last_name'] = result[0]['last_name']
	session['occupation'] = result[0]['occupation'] 
	return redirect('/database')

@app.route('/update', methods=["POST"])
def update():

	query = "UPDATE friends "
	query += "SET first_name = :first_name, last_name = :last_name, occupation = :occupation, "
	query += "updated_at = NOW() WHERE id = :id"
	data = {
		'first_name': request.form['first_name'],
		'last_name': request.form['last_name'],
		'occupation': request.form['occupation'],
		'id': request.form['id']
		}
	mysql.query_db(query, data)
	session['first_name'] = ''
	session['last_name'] = ''
	session['occupation'] = ''
	return redirect('/database')

@app.route('/remove_friend/<friend_id>', methods=['POST'])
def delete(friend_id):

	query = "DELETE FROM friends WHERE id = :id"
	data = {'id': friend_id}
	mysql.query_db(query, data)
	return redirect('/database')

@app.route('/wall')
def wall():
	if 'user_id' not in session:
		return redirect('/')

	# Get user id from session
	id = session['user_id']

	# Get user info by id from database
	query = "SELECT * FROM users WHERE id = {}".format(id)
	user_data = mysql.query_db(query) 

	# Get all posts
	query = "SELECT posts.id, "
	query += "CONCAT_WS(' ', users.first_name, users.last_name) AS user_name, "
	query += "DATE_FORMAT(posts.created_at, '%M %D, %Y %H:%i:%s') AS time, posts.content "
	query += "FROM posts "
	query += "JOIN users "
	query += "ON users.id = posts.user_id "
	query += "ORDER BY posts.created_at DESC"
	posts = mysql.query_db(query)

	# Get all the comments
	query = "SELECT comments.post_id AS parent_id, "
	query += "CONCAT_WS(' ', users.first_name, users.last_name) AS user_name, "
	query += "DATE_FORMAT(comments.created_at, '%M %D, %Y %H:%i:%s') AS time, comments.content "
	query += "FROM comments "
	query += "JOIN posts "
	query += "ON post_id = comments.post_id "
	query += "JOIN users "
	query += "ON users.id = comments.user_id "
	query += "ORDER BY comments.created_at ASC"
	comments = mysql.query_db(query)

	return render_template('wall.html', user_info=user_data, all_posts=posts, all_comments=comments)


@app.route('/post', methods=['POST'])
def post():

	if (request.form['type'] == 'post'):
		data = {
			'user_id': session['user_id'],
			'post': request.form['text']
			}
		query = "INSERT INTO posts (user_id, content) "
		query += "VALUES (:user_id, :post)"
		mysql.query_db(query, data)

	# If the message is a comment, insert comment record into the comments table.
	elif (request.form['type'] == 'comment'):
		data = {
			'post_id': request.form['parent'],
			'user_id': session['user_id'],
			'comment': request.form['text']
			}
		query = "INSERT INTO comments (post_id, user_id, content) "
		query += "VALUES (:post_id, :user_id, :comment)"
		mysql.query_db(query, data)


	return redirect('/wall')


app.run(debug=True)