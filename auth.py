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

@auth_bp.route('logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('events.home'))

