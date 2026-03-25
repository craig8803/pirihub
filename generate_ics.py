#!/usr/bin/env python3
"""
Generate iCal (.ics) feeds from PiriHub website bookings.
Only approved/paid bookings are included so that Airbnb and Booking.com
can import these feeds to block dates that are already taken.
"""

import json
import os
from datetime import datetime, date
from icalendar import Calendar, Event

BOOKINGS_FILE = 'bookings.json'
OUTPUT_DIR = 'cal'
CONFIRMED_STATUSES = {'approved', 'paid'}

HOUSES = {
    'casa-matutina': 'Casa Matutina',
    'atelier': 'Atelier',
    'casa-sol': 'Casa Sol',
    'mini-casa': 'Mini Casa',
}


def load_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return []
    with open(BOOKINGS_FILE) as f:
        data = json.load(f)
    return data.get('bookings', [])


def generate_ics_for_house(house_id, house_name, bookings):
    cal = Calendar()
    cal.add('prodid', f'-//PiriHub//{house_name}//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', f'{house_name} - PiriHub Bookings')

    confirmed = [
        b for b in bookings
        if b.get('house') == house_id and b.get('status') in CONFIRMED_STATUSES
    ]

    for booking in confirmed:
        event = Event()
        event.add('uid', booking['id'])
        event.add('summary', f'Booked - {house_name}')
        event.add('dtstart', date.fromisoformat(booking['startDate']))
        event.add('dtend', date.fromisoformat(booking['endDate']))
        event.add('dtstamp', datetime.now())
        cal.add_component(event)

    return cal.to_ical(), len(confirmed)


def generate_all():
    bookings = load_bookings()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for house_id, house_name in HOUSES.items():
        ics_content, count = generate_ics_for_house(house_id, house_name, bookings)
        output_path = os.path.join(OUTPUT_DIR, f'{house_id}.ics')
        with open(output_path, 'wb') as f:
            f.write(ics_content)
        print(f"  {house_name}: {count} confirmed booking(s) → {output_path}")


if __name__ == '__main__':
    print("Generating iCal feeds from website bookings...")
    generate_all()
    print("Done.")
