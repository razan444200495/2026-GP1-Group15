import json
import os
from models.event import Event
from extensions import db


def load_events_to_database():
    file_path = os.path.join("data", "events.json")

    with open(file_path, "r", encoding="utf-8") as file:
        events = json.load(file)

    for item in events:
        existing_event = Event.query.filter_by(
            title=item.get("title", "No Title")
        ).first()

        if not existing_event:
            event = Event(
                title=item.get("title", "No Title"),
                category=item.get("category", "General"),
                city=item.get("city", "Riyadh"),
                date=str(item.get("date", "")),
                time=str(item.get("time", "")),
                description=item.get("description", ""),
                image=item.get("image", ""),
                official_link=item.get("official_link", ""),
                source=item.get("source", "GoSaudis"),
                price=item.get("price", ""),
                location=item.get("location", ""),
                end_date=str(item.get("end_date", ""))
            )
            db.session.add(event)

    db.session.commit()
    print("Events inserted successfully")