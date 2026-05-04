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
    admin_events = Event.query.order_by(Event.start_date.desc()).all()
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
                start_date=parsed_date,
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
# ─── Edit Event ───────────────────────────────────────────────────────────────

@admin_bp.route('/admin/edit-event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    errors = {}

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        city = request.form.get('city', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        time_str = request.form.get('time', '').strip()
        description = request.form.get('description', '').strip()
        image = request.form.get('image', '').strip()
        official_link = request.form.get('official_link', '').strip()
        price = request.form.get('price', '').strip()
        location = request.form.get('location', '').strip()
        end_date_str = request.form.get('end_date', '').strip()

        required = {
            'title': title,
            'category': category,
            'city': city,
            'start_date': start_date_str,
            'time': time_str,
            'description': description,
        }

        for field, value in required.items():
            if not value:
                errors[field] = f'{field.replace("_", " ").capitalize()} is required.'

        parsed_start_date = parsed_end_date = None

        if start_date_str and 'start_date' not in errors:
            try:
                parsed_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors['start_date'] = 'Invalid start date format (use YYYY-MM-DD).'

        if end_date_str:
            try:
                parsed_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors['end_date'] = 'Invalid end date format (use YYYY-MM-DD).'

        if not errors:
            event.title = title
            event.category = category
            event.city = city
            event.start_date = parsed_start_date
            event.time = time_str
            event.description = description
            event.image = image or None
            event.official_link = official_link or None
            event.price = price or None
            event.location = location or None
            event.end_date = parsed_end_date

            db.session.commit()
            flash('Event updated successfully.')
            return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/edit_event.html', event=event, errors=errors)


# ─── Delete Event ─────────────────────────────────────────────────────────────

@admin_bp.route('/admin/delete-event/<int:event_id>', methods=['POST'])
@login_required
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)

    db.session.delete(event)
    db.session.commit()

    flash('Event deleted successfully.')
    return redirect(url_for('admin.admin_dashboard'))
