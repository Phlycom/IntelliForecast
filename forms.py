from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    SelectField, DateField, IntegerField, FloatField, FileField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    submit = SubmitField('Add Product')


class SalesEntryForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    quantity = IntegerField('Quantity Sold', validators=[DataRequired()])
    revenue = FloatField('Revenue', validators=[DataRequired()])
    submit = SubmitField('Add Sales Record')


class UploadForm(FlaskForm):
    file = FileField('Upload CSV/Excel', validators=[DataRequired()])
    submit = SubmitField('Upload')