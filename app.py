import os
import datetime as dt
from typing import List

import streamlit as st
from icalendar import Calendar, Event
import caldav


def week_range(date: dt.date) -> List[dt.date]:
    """Return a list of dates for the week containing ``date`` (Monday-Sunday)."""
    start = date - dt.timedelta(days=date.weekday())
    return [start + dt.timedelta(days=i) for i in range(7)]


def create_calendar(events: List[dict]) -> str:
    """Create an iCalendar string from event dictionaries."""
    cal = Calendar()
    cal.add("prodid", "-//Organiserv Streamlit//")
    cal.add("version", "2.0")
    for evt in events:
        e = Event()
        e.add("summary", evt["title"])
        e.add("dtstart", evt["start"])
        e.add("dtend", evt["end"])
        e.add("description", evt.get("description", ""))
        cal.add_component(e)
    return cal.to_ical().decode()


def push_to_icloud(ics: str) -> None:
    """Upload the provided ICS string to the user's primary iCloud calendar."""
    username = os.environ.get("ICLOUD_USER")
    password = os.environ.get("ICLOUD_PASS")
    if not username or not password:
        st.error("iCloud credentials are not set in environment variables.")
        return
    client = caldav.DAVClient(url="https://caldav.icloud.com/", username=username, password=password)
    principal = client.principal()
    calendars = principal.calendars()
    if not calendars:
        st.error("No calendars found for the provided iCloud account.")
        return
    cal = calendars[0]
    cal.add_event(ics)
    st.success("Calendar synced to iCloud!")


st.title("Weekly Planner")

if "events" not in st.session_state:
    st.session_state.events = []

selected_date = st.date_input("Select a date to view week", dt.date.today())
week_days = week_range(selected_date)

st.write("### Week Overview")
for day in week_days:
    st.write(day.strftime("%A %Y-%m-%d"))
    day_events = [e for e in st.session_state.events if e["start"].date() == day]
    for e in day_events:
        st.write(f"- {e['title']} ({e['start'].strftime('%H:%M')} - {e['end'].strftime('%H:%M')})")

with st.form("add_event"):
    st.write("### Add Event")
    title = st.text_input("Title")
    day = st.date_input("Day", selected_date)
    start_time = st.time_input("Start time", dt.time(9, 0))
    end_time = st.time_input("End time", dt.time(10, 0))
    description = st.text_area("Description")
    submitted = st.form_submit_button("Add")
    if submitted:
        start_dt = dt.datetime.combine(day, start_time)
        end_dt = dt.datetime.combine(day, end_time)
        st.session_state.events.append({
            "title": title,
            "start": start_dt,
            "end": end_dt,
            "description": description,
        })
        st.experimental_rerun()

if st.button("Sync to iCloud"):
    ics_data = create_calendar(st.session_state.events)
    push_to_icloud(ics_data)
