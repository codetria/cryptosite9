from flask import *
from sqlalchemy import ForeignKey
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, UserMixin, login_required, login_user, logout_user, LoginManager
from datetime import datetime
from functools import wraps
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'crptosite'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('GLOBAL_EXCHANGE_DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app=app)

class Users(UserMixin, db.Model):
            id  = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(30), nullable=False, unique=True)
            email = db.Column(db.String(100), nullable=False, unique=True)
            password = db.Column(db.String(1000), nullable=False)
            package = db.Column(db.Text, nullable=False)
            purchased = db.Column(db.Boolean, default=False)


class Coin(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     package_name = db.Column(db.String(20), nullable=False)
     current_price = db.Column(db.Float)
     purchase_price = db.Column(db.Float)


with app.app_context():
     db.create_all()

@login_manager.user_loader
def load_user(user_id):
     return Users.query.get(int(user_id))


def admin_only(f):
     @wraps(f)
     def decorated_func(*args, **kwargs):
          if current_user.id != 1:
               return abort(403)
          return f(*args, **kwargs)
     return decorated_func



@app.route('/')
def home():
    package1 = Coin(
         package_name='package1',
         current_price=1.2,
         purchase_price=1
    )
    package2 = Coin(
          package_name='package2',
          current_price=5.2,
          purchase_price=5
     )
    package3 = Coin(
         package_name='package3',
         current_price=11.2,
         purchase_price=10
    )
    db.session.add(package1)
    db.session.add(package2)
    db.session.add(package3)
    db.session.commit()
    return render_template('index.html', logged_in=current_user.is_authenticated)


@app.route('/about')
def about():
    return render_template('about.html', logged_in=current_user.is_authenticated)


@app.route('/reg')
def reg():
    error = request.args.get('error')
    return render_template('reg.html', error=error)


@app.route('/dashboard')
@login_required
def dashboard():
     user_id = request.args.get('ll')
     user = Users.query.filter_by(id=user_id).first()
     to_laod_json = None
     price = None
     if user.package == 'package1':
          to_laod_json = './static/package1.json'
          coin = Coin.query.filter_by(id=1).first()
          price = coin.current_price
     elif user.package == 'package2':
           to_laod_json = './static/package2.json'
           coin = Coin.query.filter_by(id=2).first()
           price = coin.current_price
     else:
           to_laod_json = './static/package3.json'
           coin = Coin.query.filter_by(id=3).first()
           price = coin.current_price

     with open(to_laod_json, 'r') as file:
          data = json.load(file)

     time_data = [item['time'] for item in data['package_data']]
     price_data = [item['price'] for item in data['package_data']]
     
         
     return render_template('dashboard.html', user=user,
                             logged_in=current_user.is_authenticated,
                               current_user=current_user,
                               price_data=price_data,
                               time_data=time_data,
                               data='.'+to_laod_json,
                               price=price)


@app.route('/signup',  methods=['POST'])
def signup():
     all_users = Users.query.all()
     if request.method == 'POST':
          username = request.form.get('username')
          email = request.form.get('email')
          package = request.form.get('package')
          password = request.form.get('password')
          verify_email = Users.query.filter_by(email=email).first()
          verify_username = Users.query.filter_by(username=username).first()
          if verify_email in  all_users:
               error = 'This email is already being used'
               return redirect(url_for('reg', error=error))
          else:
               if verify_username in all_users:
                    error = 'This username is already being used'
                    return redirect(url_for('reg', error=error))
               else:
                    hashed_password = generate_password_hash(password,'pbkdf2:sha256', salt_length=8)
                    new_user = Users(
                         username=username,
                         email=email,
                         package=package,
                         password=hashed_password
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    verify_username2 = Users.query.filter_by(username=username).first()
                    ll = verify_username2.id
                    login_user(verify_username2)
                    return redirect(url_for('dashboard', logged_in=current_user.is_authenticated, ll=ll))
               

@app.route('/login', methods=['POST'])
def login():
     all_users = Users.query.all()
     if request.method == 'POST':
          username = request.form.get('username')
          password = request.form.get('password')
          verify_username = Users.query.filter_by(username=username).first()
          if verify_username in all_users:
               unhashed_psw = check_password_hash(verify_username.password, password)
               if unhashed_psw:
                    ll = verify_username.id
                    login_user(verify_username)
                    return redirect(url_for('dashboard', logged_in=current_user.is_authenticated, ll=ll))
               else:
                    error = 'Invalid Password'
                    return redirect(url_for('reg', error=error))
          else:
               error = 'Username does not exist'
               return redirect(url_for('reg', error=error))
          

@app.route('/admin_panel', methods=['POST', 'GET'])
@login_required
@admin_only
def admin_panel():
     all_coins = Coin.query.all()
     if request.method == 'POST':
          to_update_json = None
          package = request.form.get('package')
          new_price = request.form.get('price')
          if package == 'package1':
               to_update_json = './static/package1.json'
               to_update_package = Coin.query.filter_by(id=1).first()
               to_update_package.current_price = new_price
               db.session.commit()
          elif package == 'package2':
               to_update_json = './static/package2.json'
               to_update_package = Coin.query.filter_by(id=2).first()
               to_update_package.current_price = new_price
               db.session.commit()
          else:
               to_update_json = './static/package3.json'
               to_update_package = Coin.query.filter_by(id=3).first()
               to_update_package.current_price = new_price
               db.session.commit()

          with open(to_update_json, 'r') as file:
               data = json.load(file)
          
          current_date = datetime.now()
          data["package_data"].append({"price": float(new_price), "time": current_date.strftime('%d %b, %I %p')}) 

          with open(to_update_json, 'w') as file:
               json.dump(data, file, indent=4)
          
          return redirect(url_for('admin_panel', logged_in=current_user.is_authenticated, ll=current_user.id))
     return render_template('admin_panel.html')

               
@app.route('/logout')
def logout():
     logout_user()
     return redirect(url_for('home'))

@app.route('/contact')
def contact():
    return render_template('contact.html', logged_in=current_user.is_authenticated)


if __name__ == '__main__':
    app.run(debug=True)