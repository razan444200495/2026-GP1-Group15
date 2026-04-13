from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.event import Event
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)


# ─── Access guard ─────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('You are not authorized to access the admin page.')
            return redirect(url_for('events.home'))
        return f(*args, **kwargs)
    return decorated


# ─── Admin dashboard ──────────────────────────────────────────────────────────

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Only fetch events entered manually by admin (source = "admin")
    admin_events = Event.query.filter_by(source='admin').order_by(Event.date.desc()).all()
    return render_template('admin/index.html', events=admin_events)


# ─── Admin profile ────────────────────────────────────────────────────────────

@admin_bp.route('/admin/profile')
@login_required
@admin_required
def profile():
    return render_template('admin/profile.html', user=current_user)


# ─── Add Event ────────────────────────────────────────────────────────────────

@admin_bp.route('/admin/add-event', methods=['GET', 'POST'])
@login_required
@admin_required
def add_event():
    errors = {}

    if request.method == 'POST':
        title         = request.form.get('title', '').strip()
        category      = request.form.get('category', '').strip()
        city          = request.form.get('city', '').strip()
        date_str      = request.form.get('date', '').strip()
        time_str      = request.form.get('time', '').strip()
        description   = request.form.get('description', '').strip()
        image         = request.form.get('image', '').strip()
        official_link = request.form.get('official_link', '').strip()
        price         = request.form.get('price', '').strip()
        location      = request.form.get('location', '').strip()
        end_date_str  = request.form.get('end_date', '').strip()

        # Required field validation
        required = {
            'title':       title,
            'category':    category,
            'city':        city,
            'date':        date_str,
            'time':        time_str,
            'description': description,
        }
        for field, value in required.items():
            if not value:
                errors[field] = f'{field.capitalize()} is required.'

        # Date parsing
        parsed_date = parsed_end_date = None
        if date_str and 'date' not in errors:
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                errors['date'] = 'Invalid date format (use YYYY-MM-DD).'

        if end_date_str:
            try:
                parsed_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors['end_date'] = 'Invalid end date format (use YYYY-MM-DD).'

        if not errors:
            event = Event(
                title=title,
                category=category,
                city=city,
                date=parsed_date,
                time=time_str,
                description=description,
                image=image or None,
                official_link=official_link or None,
                source='admin',          # always forced — never comes from the form
                price=price or None,
                location=location or None,
                end_date=parsed_end_date,
            )
            db.session.add(event)
            db.session.commit()
            flash('Event added successfully.')
            return redirect(url_for('admin.admin_dashboard'))

    return render_template(
        'admin/add_event.html',
        errors=errors,
        form_data=request.form if request.method == 'POST' else {}
    )
