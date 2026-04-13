from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.user import User
from extensions import db
from flask_login import login_user, login_required, logout_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for('admin.admin_dashboard'))
            return redirect(url_for('events.home'))

        flash('Invalid email or password')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('events.home'))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        # --- Validation ---
        errors = []

        if not fullname:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')

        if not errors:
            if User.query.filter_by(fullname=fullname).first():
                errors.append('This username is already taken.')

            if User.query.filter_by(email=email).first():
                errors.append('This email address is already registered.')

        if errors:
            return render_template(
                'signup.html',
                errors=errors,
                fullname=fullname,
                email=email,
            )

        # --- Create and save user ---
        new_user = User(fullname=fullname, email=email, role='user')
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return render_template(
                'signup.html',
                errors=['An unexpected error occurred. Please try again.'],
                fullname=fullname,
                email=email,
            )

        login_user(new_user)
        return redirect(url_for('events.home'))

    return render_template('signup.html', errors=[], fullname='', email='')
