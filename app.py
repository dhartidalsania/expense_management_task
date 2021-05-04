from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import bcrypt
from sqlalchemy.sql import func

# app configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://gwusdzvivjcgsj:529e75c69af9bc4c6ba511cb86445aa4f165541bcb891e8a0d40afca101108df@ec2-18-206-20-102.compute-1.amazonaws.com:5432/d4klj2bchhlnec'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
app.secret_key = '(any string)'
db = SQLAlchemy(app)


# Database Models
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = bcrypt.encrypt(password)


class CategoryMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cat_name = db.Column(db.String(120))
    user_id = db.Column(db.String(120))

    def __init__(self, cat_name, user_id):
        self.cat_name = cat_name
        self.user_id = user_id


class ExpenseMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(120))
    cat_id = db.Column(db.Integer)
    desc = db.Column(db.String(255))
    amount = db.Column(db.Float(10, 2))

    def __init__(self, user_id, cat_id, desc, amount):
        self.user_id = user_id
        self.cat_id = cat_id
        self.desc = desc
        self.amount = amount


# APP LOGIC FOR LOGIN SCREEEN
@app.route('/')
@app.route('/login')
def login():
    if 'username' in session:
        name = session['username']
        return render_template('index.html', name=name)
    else:
        return render_template('login.html')

# APP LOGIC FOR LOGIN VERIFICATION


@app.route('/loginuser', methods=['POST'])
def loginuser():
    error = None
    if request.method == 'POST':
        if not db.session.query(users).filter(users.username == request.form['username']).count():
            error = 'Invalid username. Please try again!'
        else:
            userdata = db.session.query(users).filter(
                users.username == request.form['username']).all()
            for data in userdata:
                if bcrypt.verify(request.form['pass'], data.password):
                    session['username'] = data.username
                    session['email'] = data.email
                    return render_template('index.html', name=request.form['username'])
                else:
                    error = 'Invalid password. Please try again!'
                    return render_template('login.html', error=error)
        return render_template('login.html', error=error)


# APP LOGIC FOR REGISTRATION PAGE
@app.route('/register')
def signup():
    if 'username' in session:
        return render_template('index.html', name=session['username'])
    else:
        return render_template('register.html')

# APP LOGIC TO REGISTER NEW USER


@app.route('/registeruser', methods=['POST'])
def registeruser():
    if request.method == 'POST':
        error = None
        if not db.session.query(users).filter(users.email == request.form['email']).count():
            reg = users(
                request.form['email'], request.form['username'], request.form['pass'])
            db.session.add(reg)
            db.session.commit()
            session['username'] = request.form['username']
            session['email'] = request.form['email']
            return render_template('index.html', name=request.form['username'])
        else:
            error = 'Username already taken'
            return render_template('register.html', error=error)

# APP LOGIC FOR DASHBOARD PAGE


@app.route('/home')
@app.route('/dashboard')
def index():
    if 'username' in session:
        name = session['username']
        catdata = db.session.query(category_master).filter(
            category_master.user_id == session['username']).all()
        expdata = db.session.query(expense_master.cat_id, func.sum(expense_master.amount).label('total')).filter(
            expense_master.user_id == session['username']).group_by(expense_master.cat_id).all()
        return render_template('index.html', catdata=catdata, expdata=expdata, name=session['username'])
    else:
        error = 'Invalid request. Please enter username and password!'
        return render_template('login.html', error=error)

# APP LOGIC FOR ADD CATEGORY PAGE


@app.route('/category')
def category():
    if 'username' in session:
        error = None
        name = session['username']
        return render_template('category.html', name=name)
    else:
        error = 'Invalid request. Please enter username and password!'
        return render_template('login.html', error=error)

# APP LOGIC TO ADD OR EDIT CATEGORY


@app.route('/addcategory', methods=['POST'])
def addcategory():
    if request.method == 'POST':
        error = None
        if not request.form['cat_id']:
            cat = category_master(
                cat_name=request.form['validate_category'], user_id=session['username'])
            db.session.add(cat)
            db.session.commit()
            error = 'Category added successfully'
            name = session['username']
            return render_template('category.html', error=error, name=name)
        else:
            db.session.query(category_master).filter(category_master.id == request.form['cat_id']).update(
                {category_master.cat_name: request.form['validate_category']})
            db.session.commit()
            error = 'Category updated successfully'
            name = session['username']
            catdata = db.session.query(category_master).filter(
                category_master.user_id == session['username']).all()
            return render_template('viewcategory.html', error=error, name=name, catdata=catdata)
    return render_template('category.html', error=error)

# APP LOGIC FOR VIEW CATEGORY PAGE


@app.route('/view-category')
def viewcategory():
    if 'username' in session:
        catdata = db.session.query(category_master).filter(
            category_master.user_id == session['username']).all()
        name = session['username']
        return render_template('viewcategory.html', catdata=catdata, name=name)
    else:
        error = 'Invalid request. Please enter username and password!'
        return render_template('login.html', error=error)

# APP LOGIC FOR EDIT CATEGORY PAGE


@app.route('/editcategory/<cat_id>')
def editcategory(cat_id):
    catData = db.session.query(category_master).filter(
        category_master.id == cat_id).all()
    return render_template('category.html', catData=catData, name=session['username'])

# APP LOGIC TO DELETE A CATEGORY


@app.route('/deletecategory/<cat_id>')
def delcategory(cat_id):
    db.session.query(category_master).filter(
        category_master.id == cat_id).delete()
    db.session.commit()
    error = 'Category Deleted successfully'
    catdata = db.session.query(category_master).filter(
        category_master.user_id == session['username']).all()
    return render_template('viewcategory.html', error=error, name=session['username'], catdata=catdata)

# APP LOGIC FOR ADD EXPENSE PAGE


@app.route('/add-expense')
def addexpense():
    if 'username' in session:
        catdata = db.session.query(category_master).filter(
            category_master.user_id == session['username']).all()
        name = session['username']
        return render_template('addexpense.html', catdata=catdata, name=name)
    else:
        error = 'Invalid request. Please enter username and password!'
        return render_template('login.html', error=error)

# APP LOGIC TO ADD OR UPDATE EXPENSE


@app.route('/addexpense', methods=['POST'])
def addnewexpense():
    if request.method == 'POST':
        error = None
        if not request.form['exp_id']:
            exp = expense_master(session['username'], request.form['validate_category'],
                                 request.form['validate_description'], request.form['validate_amount'])
            db.session.add(exp)
            db.session.commit()
            error = 'Expense Added successfully'
            name = session['username']
            return render_template('addexpense.html', error=error, name=name)
        else:
            db.session.query(expense_master).filter(expense_master.id == request.form['exp_id']).update(
                {expense_master.cat_id: request.form['validate_category'], expense_master.desc: request.form['validate_description'], expense_master.amount: request.form['validate_amount']})
            db.session.commit()
            error = 'Expense Updated successfully'
            expdata = expense_master.query.join(category_master, expense_master.cat_id == category_master.id).add_columns(
                expense_master.id, expense_master.desc, expense_master.amount, category_master.cat_name).filter(expense_master.user_id == session['username']).all()
            name = session['username']
            return render_template('viewexpense.html', expdata=expdata, name=name, error=error)

# APP LOGIC FOR VIEW EXPENSE PAGE


@app.route('/view-expense')
def viewexpense():
    if 'username' in session:
        expdata = expense_master.query.join(category_master, expense_master.cat_id == category_master.id).add_columns(
            expense_master.id, expense_master.desc, expense_master.amount, category_master.cat_name).filter(expense_master.user_id == session['username']).all()
        name = session['username']
        return render_template('viewexpense.html', expdata=expdata, name=name)
    else:
        error = 'Invalid request. Please enter username and password!'
        return render_template('login.html', error=error)

# APP LOGIC FOR EDIT EXPENSE PAGE


@app.route('/editexpense/<exp_id>')
def editexpense(exp_id):
    expdata = db.session.query(expense_master).filter(
        expense_master.id == exp_id).all()
    catdata = db.session.query(category_master).filter(
        category_master.user_id == session['username']).all()
    return render_template('addexpense.html', expdata=expdata, name=session['username'], catdata=catdata)

# APP LOGIC TO DELETE AN EXPENSE


@app.route('/deleteexpense/<exp_id>')
def deleteexpense(exp_id):
    db.session.query(expense_master).filter(
        expense_master.id == exp_id).delete()
    db.session.commit()
    error = 'Expense Deleted successfully'
    expdata = expense_master.query.join(category_master, expense_master.cat_id == category_master.id).add_columns(
        expense_master.id, expense_master.desc, expense_master.amount, category_master.cat_name).filter(expense_master.user_id == session['username']).all()
    return render_template('viewexpense.html', error=error, name=session['username'], expdata=expdata)

# APP LOGIC FOR SIGNOUT


@app.route('/signout')
def signout():
    session.pop('username', None)
    session.pop('email', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    db.create_all()
    app.run()
