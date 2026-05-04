from datetime import date, timedelta

from flask import Blueprint, render_template, request
from sqlalchemy import or_
from flask_login import current_user
from models.search import Search

from extensions import db
from models.event import Event


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
    return render_template("event_details.html", event=event)