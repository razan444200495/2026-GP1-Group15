from flask import Blueprint, render_template
from models.event import Event

events_bp = Blueprint("events", __name__)


@events_bp.route("/")
def home():
    events = Event.query.limit(6).all()
    return render_template("index.html", events=events)


@events_bp.route("/events")
def events_page():
    events = Event.query.all()
    return render_template("events.html", events=events)


@events_bp.route("/events/<int:event_id>")
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("event_details.html", event=event)
