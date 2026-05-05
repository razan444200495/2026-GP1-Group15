from datetime import date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import or_
from flask_login import current_user
from models.search import Search

from extensions import db
from models.event import Event
from models.rating import Rating
from models.review import Review


events_bp = Blueprint("events", __name__)


@events_bp.route("/")
def home():
    events = Event.query.limit(6).all()
    return render_template("index.html", events=events)


@events_bp.route("/events")
def events_page():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    date_filter = request.args.get("date_filter", "").strip()

    query = Event.query

    if search:
        words = [w for w in search.lower().split() if len(w) > 2]

        conditions = []
        for w in words:
             conditions.append(Event.title.ilike(f"%{w}%"))
             conditions.append(Event.description.ilike(f"%{w}%"))
             conditions.append(Event.category.ilike(f"%{w}%"))

        query = query.filter(or_(*conditions))

        if current_user.is_authenticated:
            new_search = Search(
                user_id=current_user.user_id,
                keyword=search
            )
            db.session.add(new_search)
            db.session.commit()

    if category:
        query = query.filter(Event.category == category)

    today = date.today()

    if date_filter == "today":
        query = query.filter(
            Event.start_date <= today,
            or_(Event.end_date == None, Event.end_date >= today)
        )

    elif date_filter == "tomorrow":
        tomorrow = today + timedelta(days=1)
        query = query.filter(
            Event.start_date <= tomorrow,
            or_(Event.end_date == None, Event.end_date >= tomorrow)
        )

    elif date_filter == "this_week":
        week_end = today + timedelta(days=7)
        query = query.filter(
            Event.start_date <= week_end,
            or_(Event.end_date == None, Event.end_date >= today)
        )

    events = query.all()

    categories = db.session.query(Event.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template(
        "events.html",
        events=events,
        categories=categories,
        selected_search=search,
        selected_category=category,
        selected_date_filter=date_filter
    )


@events_bp.route("/events/<int:event_id>")
def event_details(event_id):
    event = Event.query.get_or_404(event_id)

    ratings = Rating.query.filter_by(event_id=event_id).all()
    ratings_count = len(ratings)
    average_rating = round(sum(r.value for r in ratings) / ratings_count, 1) if ratings_count > 0 else None

    current_user_rating = None
    if current_user.is_authenticated:
        existing = Rating.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()
        if existing:
            current_user_rating = existing.value

    reviews = Review.query.filter_by(event_id=event_id).order_by(Review.created_at.desc()).all()

    return render_template(
        "event_details.html",
        event=event,
        average_rating=average_rating,
        ratings_count=ratings_count,
        current_user_rating=current_user_rating,
        reviews=reviews,
    )


@events_bp.route("/events/<int:event_id>/rate", methods=["POST"])
def rate_event(event_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to rate an event.", "warning")
        return redirect(url_for("events.event_details", event_id=event_id))

    Event.query.get_or_404(event_id)

    try:
        value = int(request.form.get("rating", 0))
    except ValueError:
        value = 0

    if value < 1 or value > 5:
        flash("Rating must be between 1 and 5.", "danger")
        return redirect(url_for("events.event_details", event_id=event_id))

    existing = Rating.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()
    if existing:
        existing.value = value
        flash("Your rating has been updated.", "success")
    else:
        db.session.add(Rating(user_id=current_user.user_id, event_id=event_id, value=value))
        flash("Thank you for rating this event!", "success")

    db.session.commit()
    return redirect(url_for("events.event_details", event_id=event_id))


@events_bp.route("/events/<int:event_id>/reviews", methods=["POST"])
def submit_review(event_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to write a review.", "warning")
        return redirect(url_for("events.event_details", event_id=event_id))

    Event.query.get_or_404(event_id)
    content = request.form.get("content", "").strip()

    if not content:
        flash("Review cannot be empty.", "danger")
        return redirect(url_for("events.event_details", event_id=event_id))

    existing = Review.query.filter_by(user_id=current_user.user_id, event_id=event_id).first()
    if existing:
        existing.content = content
        flash("Your review has been updated.", "success")
    else:
        db.session.add(Review(user_id=current_user.user_id, event_id=event_id, content=content))
        flash("Your review has been submitted!", "success")

    db.session.commit()
    return redirect(url_for("events.event_details", event_id=event_id))
