from flask import Flask, render_template, redirect, logging, request, flash, url_for, jsonify, session
from flask_mysqldb import MySQL
from wtforms import Form, TextAreaField, StringField, PasswordField, FileField, IntegerField, SelectField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import os
from flask_mail import Mail, Message

UPLOAD_FOLDER = './static/img'
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# give app name to flask framework
app = Flask(__name__)
# configure the email
app.config['MAIL_SERVER'] = 'mail.supu.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ouremail'
app.config['MAIL_PASSWORD'] = 'ourpass'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
# config app root
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# config db
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'websupu'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.route('/')
def index():
	cur = mysql.connection.cursor()
	cur.execute("SELECT * FROM slide")
	slide = cur.fetchall()
	cur.close()

	cur2 = mysql.connection.cursor()
	cur2.execute("SELECT * FROM new")
	news = cur2.fetchall()
	cur2.close()

	cur3 = mysql.connection.cursor()
	cur3.execute("SELECT * FROM work")
	work = cur3.fetchall()
	cur3.close()

	cur4 = mysql.connection.cursor()
	cur4.execute("SELECT * FROM set_supu WHERE set_id = %s", [1])
	setting = cur4.fetchone()
	cur4.close()

	cur5 = mysql.connection.cursor()
	cur5.execute("SELECT * FROM set_supu WHERE set_id = %s", [2])
	data = cur5.fetchone()
	chart = data["adr"]
	cur5.close()

	return render_template('home.html', slides=slide, news=news, works=work, settings=setting, chart=chart)


def loging_required(p):
	@wraps(p)
	def wrap(*args, **kwargs):
		if 'loging' in session:
			return p(*args, **kwargs)
		else:
			flash('plase login', 'danger')
			return redirect('/login')
	return wrap


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		user = request.form["name"]
		password = request.form["pass"]
		if user == '':
			flash('field name must be fill', 'danger')
			return render_template('login.html')
		else:
			cur = mysql.connection.cursor()
			res = cur.execute('SELECT * FROM user WHERE u_username = %s ', [user])
			if res > 0:
				userdata = cur.fetchone()
				userpass = userdata['u_password']
				print(sha256_crypt.verify(password, userpass))
				if sha256_crypt.verify(password, userpass):
					session["loging"] = True
					session["uid"] = userdata["u_id"]
					session["ug"] = userdata["u_group"]
					flash('you login now', 'success')
					return redirect(url_for('admin'))
				else:
					flash('invalide password', 'danger')
					return render_template('login.html')
			else:
				flash('no user', 'danger')
				return render_template('login.html')
	return render_template('login.html')


@app.route('/logout', methods=["POST"])
@loging_required
def logout():
	session.clear()
	return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
@loging_required
def admin():
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	cur.close()
	cur = mysql.connection.cursor()
	cs = cur.execute("SELECT * FROM slide")
	slide = cur.fetchall()
	cur.close()

	cur2 = mysql.connection.cursor()
	cn = cur2.execute("SELECT * FROM new")
	news = cur2.fetchall()
	cur2.close()

	cur3 = mysql.connection.cursor()
	cw = cur3.execute("SELECT * FROM work")
	work = cur3.fetchall()
	cur3.close()

	cur4 = mysql.connection.cursor()
	cu = cur4.execute("SELECT * FROM user")
	user = cur4.fetchall()
	cur4.close()
	return render_template('admin.html', emailc=emailc, cs=cs, cn=cn, cw=cw, cu=cu)


class Addnew(Form):
	title = StringField('Title', [validators.length(min=20), validators.DataRequired()])
	text = TextAreaField('New text', [validators.length(min=30), validators.DataRequired()])


@app.route('/news')
@loging_required
def allnew():
	cur = mysql.connection.cursor()
	res = cur.execute("SELECT * FROM new")
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if res > 0:
		datanew = cur.fetchall()
		return render_template('news.html', allnews=datanew, emailc=emailc)
	else:
		return render_template('news.html', emailc=emailc)


@app.route('/add_new', methods=['GET', 'POST'])
@loging_required
def addnewweb():
	form = Addnew(request.form)
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.text.data
		
		cur = mysql.connection.cursor()
		cur.execute('INSERT INTO new(n_title, n_body) VALUES(%s, %s)', (title, body))
		mysql.connection.commit()
		cur.close()
		flash('news is added', 'success')
		return redirect(url_for('allnew'))
	return render_template('addnew.html', form=form, emailc=emailc)
	

class Addsilde(Form):
	text = TextAreaField('your describtion', [validators.length(min=10), validators.DataRequired()])


@app.route('/slide', methods=['GET'])
@loging_required
def allslide():
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	res = cur.execute("SELECT * FROM slide")
	if res > 0:
		dataslide = cur.fetchall()
		return render_template('slide.html', allslide=dataslide, emailc=emailc)
	else:
		return render_template('slide.html', emailc=emailc)


@app.route('/user')
@loging_required
def alluser():
	cur = mysql.connection.cursor()
	res = cur.execute("SELECT * FROM user")
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if res > 0:
		datauser = cur.fetchall()
		return render_template('user.html', alluser=datauser, count=res, emailc=emailc)
	else:
		return render_template('user.html', emailc=emailc)


class AddUserForm(Form):
	name = StringField('Name', [validators.Length(min=3), validators.DataRequired()])
	username = StringField('UserName', [validators.Length(min=10), validators.DataRequired()])
	password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=8)])
	# group = IntegerField('function', [validators.AnyOf([0, 1])])


@app.route('/adduser', methods=['GET', 'POST'])
@loging_required
def adduser():
	form = AddUserForm(request.form)
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if request.method == 'POST' and form.validate():
		name = form.name.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
		cur = mysql.connection.cursor()
		cur.execute('INSERT INTO user(u_name, u_username, u_password, u_group) VALUES(%s, %s, %s, %s)', (name, username, password, 0))
		mysql.connection.commit()
		cur.close()

		flash('new user added', 'success')
		return redirect(url_for('alluser'))
	else:
		return render_template('adduser.html', form=form, emailc=emailc)


@app.route('/add_slide', methods=['GET', 'POST'])
@loging_required
def addsldweb():
	form = Addsilde(request.form)
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if request.method == 'POST' and form.validate():
		imag = request.files["img"].filename
		body = form.text.data
		place = os.path.join(APP_ROOT, 'static/img/')
		extn = imag.split(".")[1]
		if extn.lower() == 'png' or extn == 'jpg' or extn == 'jpeg':
			request.files["img"].save('/'.join([place, secure_filename(imag)]))
			cur = mysql.connection.cursor()
			cur.execute('INSERT INTO slide(s_img, s_text, s_group) VALUES(%s, %s, %s)', (imag, body, 1))
			mysql.connection.commit()
			cur.close()
			flash('slide element is added', 'success')
			return redirect(url_for('allslide'))
		else:
			flash('this extintion is not allowed', 'danger')
			return redirect(url_for('addsldweb'))
	return render_template('addslide.html', form=form, emailc=emailc)


@app.route('/ourwork', methods=['GET'])
@loging_required
def allwork():
	cur = mysql.connection.cursor()
	res = cur.execute("SELECT * FROM work")
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if res > 0:
		datawork = cur.fetchall()
		return render_template('ourwork.html', allwork=datawork, emailc=emailc)
	else:
		return render_template('ourwork.html', emailc=emailc)


class AddNewWork(Form):
	name = StringField('Title', [validators.Length(min=10), validators.DataRequired()])
	link = StringField('Link', [validators.Length(min=10), validators.URL(), validators.DataRequired()])
	type = SelectField('Type', choices=[('1', 'desgin'), ('2', 'develop')])


@app.route('/addwork', methods=['GET', 'POST'])
@loging_required
def addwkweb():
	form = AddNewWork(request.form)
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if request.method == 'POST' and form.validate():
		name = form.name.data
		link = form.link.data
		type = form.type.data
		if request.files['img']:
			file = request.files['img']
			filenameimg = file.filename
			extn = filenameimg.split('.')[1]
			place = os.path.join(APP_ROOT, 'static/img/')
			if not os.path.isdir(place):
				os.mkdir(place)

			if extn == 'png' or extn == 'jpg' or extn == 'jpeg':
				dist = '/'.join([place, secure_filename(filenameimg)])
				file.save(dist)

				cur = mysql.connection.cursor()
				cur.execute('INSERT INTO work(w_img, w_name, w_link, w_type) VALUES(%s, %s, %s)', (filenameimg, name, link, type))
				mysql.connection.commit()
				cur.close()
				flash('this work is added', 'success')
				return redirect(url_for('allwork'))
			else:
				flash('this extintion is not allowed', 'danger')
				return redirect(url_for('addsldweb'))

	return render_template('addwork.html', form=form, emailc=emailc)


class Addset(Form):
	country = StringField('Title', [validators.Length(min=1), validators.DataRequired()])
	face = StringField('Face', [validators.Length(min=1), validators.URL(), validators.DataRequired()])
	address = StringField('Address', [validators.Length(min=1), validators.DataRequired()])
	email = StringField('Email', [validators.Length(min=8), validators.Email(), validators.DataRequired()])
	telphone = StringField('Telphone', [validators.Length(min=11), validators.DataRequired()])
	chart = TextAreaField('Chart', [validators.DataRequired()])


@app.route('/setting', methods=['GET', 'POST'])
@loging_required
def setting():
	cur = mysql.connection.cursor()
	cur.execute('SELECT * FROM set_supu where set_id = %s', [1])
	emailc = cur.execute("SELECT * FROM emai WHERE e_stat = %s", [0])
	res = cur.fetchone()
	form = Addset(request.form)
	form.address.data = res['adr']
	form.telphone.data = res['tel']
	form.email.data = res['email']
	form.country.data = res['cnt']
	form.face.data = res['face']
	cur1 = mysql.connection.cursor()
	cur1.execute('SELECT adr FROM set_supu where set_id = %s', [2])
	res1 = cur1.fetchone()

	form.chart.data = res1['adr']
	if request.method == 'POST' and form.validate():
		adr = request.form['address']
		tel = request.form['telphone']
		email = request.form['email']
		cnt = request.form['country']
		face = request.form['face']
		cur = mysql.connection.cursor()
		cur.execute('UPDATE set_supu SET tel = %s, adr = %s, cnt = %s, email = %s, face = %s WHERE set_id = %s', (tel, adr, cnt, email, face, 1))
		mysql.connection.commit()
		if request.form['chart'] != '':
			chart = request.form['chart']
			cur2.execute("UPDATE set_supu SET adr = %s WHERE set_id = %s", (chart, 2))
			mysql.connection.commit()
		cur.close()
		flash('saved', 'success')
		return redirect(url_for('setting'))
	cur1 = mysql.connection.cursor()
	cur1.execute('SELECT * FROM set_supu where set_id = %s', [2])
	resu = cur1.fetchone()
	chart = resu["adr"]
	cur1.close()
	return render_template('setting.html', form=form, chart=chart, emailc=emailc)


@app.route('/emailuser', methods=['POST'])
def emailuser():
	name = request.form['name']
	email = request.form['email']
	msg = request.form['msg']
	if name and email and msg:
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO email (e_name, e_email, e_msg) VALUES(	%s, %s, %s)", (name, email, msg))
		mysql.connection.commit()
		cur.close()
		return jsonify({'success': 'your message have been sent and we will mail you in short time'})

	return jsonify({'danger': 'you should full input please'})


@app.route('/remail', methods=['POST'])
@loging_required
def remail():
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s ORDER BY e_date DESC LIMIT 1", [0])
	if emailc > 0:
		emaildata = cur.fetchone()
		# msg = '<p> hi</p>'
		cur.close()
		return jsonify({'emailr': '<div class="pull-alert"><div class="alert alert-success pull-right"><button type="button" class="btn btn-default btn-circle btn-xl-alert btn-lateral btn-float-alert"><i class="glyphicon glyphicon-envelope"></i></button><hr class="hr-alert"><strong>'+ emaildata["e_name"] + '</strong></div></div>'})

	return jsonify({'emailr': '<p> hi</p>'})


@app.route('/allemail')
@loging_required
def allemailweb():
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	cur.execute('UPDATE set_supu SET  e_stat = %s WHERE e_stat = %s', (1, 1))
	mysql.connection.commit()
	if emailc > 0:
		emaildata = cur.fetchall()
		cur.close()
		return render_template('emailweb.html', allemail=emaildata, emailc=emailc)
	else:
		return render_template('emailweb.html', emailc=emailc)


class SendEmail(Form):
	subject = StringField('Subject', [validators.Length(min=10), validators.DataRequired()])
	to = StringField('Email', [validators.Length(min=10), validators.Email(), validators.DataRequired()])
	message = TextAreaField('Message', [validators.Length(min=5), validators.DataRequired()])


@app.route('/delete', methods=['POST'])
@loging_required
def deleteuser():
	id = request.form['id']
	datatable = request.form['table']
	cur = mysql.connection.cursor()
	if datatable == 'user':
		cur.execute('DELETE FROM user WHERE u_id = %s ', [id])
		mysql.connection.commit()
		cur.close()
		flash('user is deleted', 'success')
		return redirect(url_for('alluser'))
	elif datatable == 'new':
		cur.execute('DELETE FROM new WHERE n_id = %s', [id])
		mysql.connection.commit()
		cur.close()
		flash('new is deleted', 'success')
		return redirect(url_for('allnew'))
	elif datatable == 'email':
		cur.execute('DELETE FROM email WHERE e_id = %s', [id])
		mysql.connection.commit()
		cur.close()
		flash('email is deleted', 'success')
		return redirect(url_for('allemail'))
	elif datatable == 'slide':
		cur.execute('DELETE FROM slide WHERE s_id = %s', [id])
		mysql.connection.commit()
		cur.close()
		flash('element is deleted', 'success')
		return redirect(url_for('allslide'))
	elif datatable == 'work':
		cur.execute('DELETE FROM work WHERE w_id = %s', [id])
		mysql.connection.commit()
		cur.close()
		flash('element is deleted', 'success')
		return redirect(url_for('allwork'))
	else:
		flash('error', 'danger')
		return redirect(url_for('admin'))


@app.route('/send', methods=['GET', 'POST'])
@loging_required
def sendemail():
	form = SendEmail(request.form)
	cur = mysql.connection.cursor()
	emailc = cur.execute("SELECT * FROM email WHERE e_stat = %s", [0])
	if request.method == 'POST' and form.validate():
		to = form.email.data
		subject = form.subject.data
		message = form.message.data

		msg = Message(subject, sender='ouremail', recipients=[to])
		msg.body = message
		if mail.send(msg):
			flash('email is send', 'success')
			return redirect(url_for('allemail'))
		else:
			flash('email not send', 'danger')
			return redirect(url_for('allemail'))

	return render_template('sendemail.html', form=form, emailc=emailc)


if __name__ == '__main__':
	app.secret_key = 'secret'
	app.run(debug=True)