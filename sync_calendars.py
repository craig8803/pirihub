#!/usr/bin/env python3
"""
Sync Airbnb and Booking.com calendars to PiriHub blocked dates.
Reads iCal feeds and generates JSON with blocked date ranges.
"""

import os
import json
from datetime import datetime
from icalendar import Calendar
import requests

# House configurations - Airbnb
AIRBNB_HOUSES = {
    'casa-matutina': os.getenv('AIRBNB_CASA_MATUTINA'),
    'atelier': os.getenv('AIRBNB_ATELIER'),
    'casa-sol': os.getenv('AIRBNB_CASA_SOL'),
    'mini-casa': os.getenv('AIRBNB_MINI_CASA'),
}

# House configurations - Booking.com
BOOKING_HOUSES = {
    'casa-matutina': os.getenv('BOOKING_CASA_MATUTINA'),
    'atelier': os.getenv('BOOKING_ATELIER'),
    'casa-sol': os.getenv('BOOKING_CASA_SOL'),
    'mini-casa': os.getenv('BOOKING_MINI_CASA'),
}

def fetch_calendar(ical_url, source_name):
    """Fetch and parse iCal feed."""
    if not ical_url:
        return []
    
    try:
        response = requests.get(ical_url, timeout=10)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        events = cal.walk('VEVENT')
        print(f"  Fetched {len(events)} events from {source_name}")
        return events
    except Exception as e:
        print(f"  Error fetching {source_name} calendar: {e}")
        return []

def extract_blocked_dates(events, source_name):
    """Extract blocked date ranges from calendar events."""
    blocked = []
    
    for event in events:
        try:
            summary = str(event.get('summary', ''))
            dtstart = event.get('dtstart')
            dtend = event.get('dtend')
            
            if dtstart and dtend:
                start_date = dtstart.dt
                end_date = dtend.dt
                
                # Convert to date objects if they're datetime
                if hasattr(start_date, 'date'):
                    start_date = start_date.date()
                if hasattr(end_date, 'date'):
                    end_date = end_date.date()
                
                blocked.append({
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'title': f"{source_name}: {summary[:30]}"
                })
        except Exception as e:
            print(f"  Error processing event: {e}")
            continue
    
    return blocked

def merge_blocked_dates(airbnb_dates, booking_dates):
    """Merge blocked dates from multiple sources."""
    all_dates = airbnb_dates + booking_dates
    # Sort by start date
    all_dates.sort(key=lambda x: x['start'])
    return all_dates

def sync_all_calendars():
    """Sync all house calendars from all sources and save to JSON."""
    all_blocked = {}
    
    for house_id in ['casa-matutina', 'atelier', 'casa-sol', 'mini-casa']:
        print(f"\nSyncing {house_id}...")
        
        # Fetch from Airbnb
        airbnb_url = AIRBNB_HOUSES.get(house_id)
        airbnb_events = fetch_calendar(airbnb_url, 'Airbnb') if airbnb_url else []
        airbnb_blocked = extract_blocked_dates(airbnb_events, 'Airbnb')
        
        # Fetch from Booking.com
        booking_url = BOOKING_HOUSES.get(house_id)
        booking_events = fetch_calendar(booking_url, 'Booking.com') if booking_url else []
        booking_blocked = extract_blocked_dates(booking_events, 'Booking.com')
        
        # Merge all blocked dates
        merged_blocked = merge_blocked_dates(airbnb_blocked, booking_blocked)
        all_blocked[house_id] = merged_blocked
        
        print(f"  Total blocked ranges: {len(merged_blocked)} (Airbnb: {len(airbnb_blocked)}, Booking: {len(booking_blocked)})")
    
    # Save to JSON
    output_file = 'blocked_dates.json'
    with open(output_file, 'w') as f:
        json.dump(all_blocked, f, indent=2)
    
    print(f"\nSaved blocked dates to {output_file}")

if __name__ == '__main__':
    sync_all_calendars()
