from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, SalesRecord
from forms import RegistrationForm, LoginForm, ProductForm, SalesEntryForm, UploadForm
import pandas as pd

main = Blueprint('main', __name__)

# --- Authentication Routes ---
@main.route('/')
def home():
    return render_template('base.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# --- Dashboard (FIXED) ---
@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# --- Product Routes ---
@main.route('/products')
@login_required
def list_products():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('products.html', products=products)

@main.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data, category=form.category.data, user_id=current_user.id)
        db.session.add(product)
        db.session.commit()
        flash('Product added!', 'success')
        return redirect(url_for('main.list_products'))
    return render_template('add_product.html', form=form)

# --- Sales Routes ---
@main.route('/sales/add', methods=['GET', 'POST'])
@login_required
def add_sales():
    form = SalesEntryForm()
    products = Product.query.filter_by(user_id=current_user.id).all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    if form.validate_on_submit():
        record = SalesRecord(
            product_id=form.product_id.data,
            date=form.date.data,
            quantity=form.quantity.data,
            revenue=form.revenue.data,
            user_id=current_user.id
        )
        db.session.add(record)
        db.session.commit()
        flash('Sales record added!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('add_sales.html', form=form)

@main.route('/sales/upload', methods=['GET', 'POST'])
@login_required
def upload_sales():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        required_cols = ['product_name', 'date', 'quantity', 'revenue']
        if not all(col in df.columns for col in required_cols):
            flash('File must contain columns: product_name, date, quantity, revenue', 'danger')
            return redirect(url_for('main.upload_sales'))

        for _, row in df.iterrows():
            product = Product.query.filter_by(name=row['product_name'], user_id=current_user.id).first()
            if not product:
                product = Product(name=row['product_name'], category='Imported', user_id=current_user.id)
                db.session.add(product)
                db.session.flush()

            try:
                record_date = pd.to_datetime(row['date']).date()
            except:
                flash(f'Invalid date format in row: {row.to_dict()}', 'danger')
                continue

            record = SalesRecord(
                product_id=product.id,
                date=record_date,
                quantity=int(row['quantity']),
                revenue=float(row['revenue']),
                user_id=current_user.id
            )
            db.session.add(record)
        db.session.commit()
        flash('Sales data uploaded successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('upload_sales.html', form=form)