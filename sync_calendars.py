#!/usr/bin/env python3
"""
Sync Airbnb calendar to PiriHub blocked dates.
Reads iCal feeds and generates JSON with blocked date ranges.
"""

import os
import json
from datetime import datetime
from icalendar import Calendar
import requests

# House configurations
HOUSES = {
    'casa-matutina': os.getenv('AIRBNB_CASA_MATUTINA'),
    'casa-atelier': os.getenv('AIRBNB_CASA_ATELIER'),
    'casa-do-vale': os.getenv('AIRBNB_CASA_DO_VALE'),
    'casa-do-rio': os.getenv('AIRBNB_CASA_DO_RIO'),
}

def fetch_airbnb_calendar(ical_url):
    """Fetch and parse Airbnb iCal feed."""
    if not ical_url:
        return []
    
    try:
        response = requests.get(ical_url, timeout=10)
        response.raise_for_status()
        cal = Calendar.from_ical(response.content)
        return cal.walk('VEVENT')
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return []

def extract_blocked_dates(events):
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
                    'title': summary[:50]  # Limit title length
                })
        except Exception as e:
            print(f"Error processing event: {e}")
            continue
    
    return blocked

def sync_all_calendars():
    """Sync all house calendars and save to JSON."""
    all_blocked = {}
    
    for house_id, ical_url in HOUSES.items():
        print(f"Syncing {house_id}...")
        
        if not ical_url:
            print(f"  No calendar URL for {house_id}")
            all_blocked[house_id] = []
            continue
        
        events = fetch_airbnb_calendar(ical_url)
        blocked_dates = extract_blocked_dates(events)
        all_blocked[house_id] = blocked_dates
        
        print(f"  Found {len(blocked_dates)} blocked date ranges")
    
    # Save to JSON
    output_file = 'blocked_dates.json'
    with open(output_file, 'w') as f:
        json.dump(all_blocked, f, indent=2)
    
    print(f"\nSaved blocked dates to {output_file}")
    print(json.dumps(all_blocked, indent=2))

if __name__ == '__main__':
    sync_all_calendars()
