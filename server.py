from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector
app = Flask(__name__)
mysql = MySQLConnector(app, 'practice_mydb')
app.secret_key = 'lkajsdhflkja'

@app.route('/')
def index():
	friends = mysql.query_db("SELECT * FROM friends")
	return render_template('index.html', all_friends=friends)

@app.route('/friends', methods=['POST'])
def add_friends():

	query = "INSERT INTO friends (first_name, last_name, occupation) VALUES (:first_name,:last_name,:occupation)"

	data = {
		'first_name': request.form['first_name'],
		'last_name': request.form['last_name'],
		'occupation': request.form['occupation']
		}

	mysql.query_db(query, data)
	return redirect('/')

@app.route('/database')
def database_of_friends():
	friends = mysql.query_db("SELECT * FROM friends")

	if 'first_name' not in session:
		session['first_name'] = 'empty'
	if 'last_name' not in session:
		session['last_name'] = 'empty'
	if 'occupation' not in session:
		session['occupation'] = 'empty'

	return render_template('database.html', all_friends=friends)

@app.route('/update_friend/<friend_id>', methods=['POST'])
def button_click(friend_id):
	session['friend_id'] = friend_id

	query = "SELECT * from friends where id = {}".format(friend_id)
	result = mysql.query_db(query)
	session['first_name'] = result[0]['first_name']
	session['last_name'] = result[0]['last_name']
	session['occupation'] = result[0]['occupation'] 

	return redirect('/database')

@app.route('/update', methods=["POST"])
def update():

	query = "UPDATE friends SET first_name = :first_name, last_name = :last_name, occupation = :occupation, updated_at = NOW() WHERE id = :id"
	data = {
		'first_name': request.form['first_name'],
		'last_name': request.form['last_name'],
		'occupation': request.form['occupation'],
		'id': request.form['id']
		}
	mysql.query_db(query, data)

	session['first_name'] = data['first_name']
	session['last_name'] = data['last_name']
	session['occupation'] = data['occupation']


	return redirect('/database')


app.run(debug=True)