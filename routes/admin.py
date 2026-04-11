from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__)

@admin_bp.route('/admin')
@login_required 
def admin_dashboard():
    if current_user.role != "admin":
        flash("you are not authorized to access the admin page. ")
        return redirect(url_for('events.home'))
    return render_template('admin.html')
