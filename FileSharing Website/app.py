import os
import random
import string
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret')

# DB (SQLite)
db_uri = os.getenv('SQLALCHEMY_DATABASE_URI', '').strip() or 'sqlite:///file_share.db'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXT = set(['txt','pdf','png','jpg','jpeg','gif','zip','rar','doc','docx','xls','xlsx'])

BASE_URL = os.getenv('BASE_URL','http://localhost:5000')

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    verify_code = db.Column(db.String(10), nullable=True)
    verify_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    saved_as = db.Column(db.String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    password_hash = db.Column(db.String(300), nullable=True)  # optional file password
    expiry_date = db.Column(db.DateTime, nullable=True)

with app.app_context():
    db.create_all()

# Helpers
def gen_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

# Routes
@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    fn = request.form.get('firstName','').strip()
    ln = request.form.get('lastName','').strip()
    email = request.form.get('email','').strip().lower()
    password = request.form.get('password','')
    if not (fn and ln and email and password):
        flash('All fields required', 'danger')
        return redirect(url_for('register'))
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'danger')
        return redirect(url_for('register'))

    user = User(first_name=fn, last_name=ln, email=email)
    user.set_password(password)
    code = gen_code(6)
    user.verify_code = code
    user.verify_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    db.session.add(user)
    db.session.commit()

    # Testing mode: print code to console and flash a demo message
    print(f'[TEST-OTP] Verification code for {email} is: {code}')
    flash(f'Registered (testing). Verification code printed to server console. Use it on verify page.', 'warning')
    session['pending_email'] = email
    return redirect(url_for('verify'))

@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'GET':
        pre = session.get('pending_email','')
        return render_template('verify.html', email=pre)
    email = request.form.get('email','').strip().lower()
    code = request.form.get('code','').strip()
    if not (email and code):
        flash('Email and code required', 'danger')
        return redirect(url_for('verify'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('No such user. Please register.', 'danger')
        return redirect(url_for('register'))
    if user.verified:
        flash('Already verified. Please login.', 'info')
        return redirect(url_for('login'))
    if user.verify_code != code:
        flash('Invalid verification code.', 'danger')
        return redirect(url_for('verify'))
    if user.verify_expiry and user.verify_expiry < datetime.datetime.utcnow():
        flash('Code expired. Register again.', 'danger')
        return redirect(url_for('register'))
    user.verified = True
    user.verify_code = None
    user.verify_expiry = None
    db.session.commit()
    flash('Email verified — account active! You can now login.', 'success')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email','').strip().lower()
    password = request.form.get('password','')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash('Invalid credentials', 'danger')
        return redirect(url_for('login'))
    if not user.verified:
        flash('Email not verified. Please verify first.', 'warning')
        session['pending_email'] = email
        return redirect(url_for('verify'))
    session['user_id'] = user.id
    flash('Login successful', 'success')
    return redirect(url_for('home'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    files = File.query.filter_by(user_id=user.id).order_by(File.uploaded_at.desc()).all()
    # filter out expired files (do not show)
    now = datetime.datetime.utcnow()
    files = [f for f in files if not f.expiry_date or f.expiry_date > now]
    return render_template('index.html', user=user, files=files)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('home'))
    f = request.files['file']
    if f.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('home'))
    if not allowed_file(f.filename):
        flash('File type not allowed', 'danger')
        return redirect(url_for('home'))
    file_password = request.form.get('file_password','').strip()
    expire_days = request.form.get('expire_days','').strip()
    try:
        expire_days = int(expire_days) if expire_days else None
    except:
        expire_days = None
    # save file
    filename = f.filename
    saved_as = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S_') + ''.join(random.choices(string.ascii_letters+string.digits, k=6)) + '_' + filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_as)
    f.save(filepath)
    expiry_date = None
    if expire_days and expire_days>0:
        expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=expire_days)
    file_entry = File(filename=filename, saved_as=saved_as, user_id=session['user_id'], password_hash=generate_password_hash(file_password) if file_password else None, expiry_date=expiry_date)
    db.session.add(file_entry)
    db.session.commit()
    flash('File uploaded', 'success')
    return redirect(url_for('home'))

@app.route('/file/<int:file_id>', methods=['GET','POST'])
def access_file(file_id):
    # if file has password, show form and verify; otherwise redirect to download
    file_entry = File.query.get(file_id)
    if not file_entry:
        flash('File not found', 'danger')
        return redirect(url_for('home'))
    # check expiry
    if file_entry.expiry_date and file_entry.expiry_date < datetime.datetime.utcnow():
        flash('File expired', 'danger')
        return redirect(url_for('home'))
    if file_entry.password_hash:
        if request.method == 'GET':
            return render_template('file_password.html', file=file_entry)
        pwd = request.form.get('password','')
        if not pwd or not check_password_hash(file_entry.password_hash, pwd):
            flash('Incorrect password', 'danger')
            return redirect(url_for('access_file', file_id=file_id))
        # correct password, send file
        return send_from_directory(app.config['UPLOAD_FOLDER'], file_entry.saved_as, as_attachment=True)
    else:
        return send_from_directory(app.config['UPLOAD_FOLDER'], file_entry.saved_as, as_attachment=True)

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    file_entry = File.query.get(file_id)
    if not file_entry or file_entry.user_id != session['user_id']:
        flash('File not found or permission denied', 'danger')
        return redirect(url_for('home'))
    # delete from disk and DB
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_entry.saved_as))
    except Exception as e:
        print('Delete file error:', e)
    db.session.delete(file_entry)
    db.session.commit()
    flash('File deleted', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
