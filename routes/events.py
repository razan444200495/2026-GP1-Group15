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

    # Search by title or description
    # Search
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

    # Filter by category
    if category:
        query = query.filter(Event.category == category)

    # Filter by available date
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

    if ratings_count > 0:
        average_rating = sum(r.value for r in ratings) / ratings_count
    else:
        average_rating = 0

    reviews = Review.query.filter_by(event_id=event_id).order_by(Review.created_at.desc()).all()

    current_user_rating = None
    current_user_review = None

    if current_user.is_authenticated:
        current_user_rating = Rating.query.filter_by(
            user_id=current_user.user_id,
            event_id=event_id
        ).first()

        current_user_review = Review.query.filter_by(
            user_id=current_user.user_id,
            event_id=event_id
        ).first()

    return render_template(
        "event_details.html",
        event=event,
        average_rating=average_rating,
        ratings_count=ratings_count,
        reviews=reviews,
        current_user_rating=current_user_rating,
        current_user_review=current_user_review
    )


@events_bp.route("/events/<int:event_id>/rate", methods=["POST"])
def rate_event(event_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to rate events.", "error")
        return redirect(url_for("auth.login"))

    Event.query.get_or_404(event_id)

    rating_value = request.form.get("rating")

    if not rating_value:
        flash("Please select a rating.", "error")
        return redirect(url_for("events.event_details", event_id=event_id))

    try:
        rating_value = int(rating_value)
    except ValueError:
        flash("Invalid rating value.", "error")
        return redirect(url_for("events.event_details", event_id=event_id))

    if rating_value < 1 or rating_value > 5:
        flash("Rating must be between 1 and 5.", "error")
        return redirect(url_for("events.event_details", event_id=event_id))

    existing_rating = Rating.query.filter_by(
        user_id=current_user.user_id,
        event_id=event_id
    ).first()

    if existing_rating:
        existing_rating.value = rating_value
        flash("Your rating has been updated.", "success")
    else:
        new_rating = Rating(
            user_id=current_user.user_id,
            event_id=event_id,
            value=rating_value
        )
        db.session.add(new_rating)
        flash("Thank you for rating this event.", "success")

    db.session.commit()

    return redirect(url_for("events.event_details", event_id=event_id))


@events_bp.route("/events/<int:event_id>/reviews", methods=["POST"])
def write_review(event_id):
    if not current_user.is_authenticated:
        flash("You must be logged in to write reviews.", "error")
        return redirect(url_for("auth.login"))

    Event.query.get_or_404(event_id)

    content = request.form.get("review", "").strip()

    if not content:
        flash("Review cannot be empty.", "error")
        return redirect(url_for("events.event_details", event_id=event_id))

    existing_review = Review.query.filter_by(
        user_id=current_user.user_id,
        event_id=event_id
    ).first()

    if existing_review:
        existing_review.content = content
        flash("Your review has been updated.", "success")
    else:
        new_review = Review(
            user_id=current_user.user_id,
            event_id=event_id,
            content=content
        )
        db.session.add(new_review)
        flash("Your review has been submitted.", "success")

    db.session.commit()

    return redirect(url_for("events.event_details", event_id=event_id))
