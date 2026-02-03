# PiriHub Calendar Sync Setup

This repository includes automatic calendar synchronization with Airbnb listings using GitHub Actions.

## Setup Instructions

### 1. Push to GitHub

First, initialize and push your repository:

```bash
cd /Users/craighalliday/Desktop/repos/pirihub
git add .
git commit -m "Initial commit: PiriHub booking website with Airbnb calendar sync"
git branch -M main
git remote add origin https://github.com/craig8803/pirihub.git
git push -u origin main
```

### 2. Add Airbnb Calendar URLs as Secrets

Go to your GitHub repository settings and add these secrets:

**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:
- **AIRBNB_CASA_MATUTINA**: `https://www.airbnb.com/calendar/ical/[LIST_ID].ics?t=[TOKEN]&locale=pt`
- **AIRBNB_CASA_ATELIER**: `https://www.airbnb.com/calendar/ical/[LIST_ID].ics?t=[TOKEN]&locale=pt`
- **AIRBNB_CASA_DO_VALE**: `https://www.airbnb.com/calendar/ical/[LIST_ID].ics?t=[TOKEN]&locale=pt`
- **AIRBNB_CASA_DO_RIO**: `https://www.airbnb.com/calendar/ical/[LIST_ID].ics?t=[TOKEN]&locale=pt`

Replace `[LIST_ID]` and `[TOKEN]` with your actual Airbnb calendar URLs.

### 3. How It Works

**Automatic Sync:**
- GitHub Actions runs every 4 hours (configurable in `.github/workflows/sync-airbnb-calendar.yml`)
- Fetches Airbnb calendar data from all properties
- Blocks booked dates on the PiriHub calendar
- Blocked dates appear grayed out and cannot be selected

**Manual Trigger:**
- Go to Actions tab → Sync Airbnb Calendar → Run workflow

### 4. Blocked Dates Display

Blocked dates show as:
- Gray background with reduced opacity
- Non-clickable (cursor shows not-allowed)
- Users cannot select blocked dates for bookings

### 5. Example Calendar URL

Your Airbnb calendar URL looks like:
```
https://www.airbnb.com/calendar/ical/1053655926629770408.ics?t=d05ad6029a234a3cbc487fd753364610&locale=pt
```

Extract and secure it as a GitHub Secret.

## Files

- `.github/workflows/sync-airbnb-calendar.yml` - GitHub Actions workflow
- `sync_calendars.py` - Python script that syncs calendars
- `blocked_dates.json` - Generated file with blocked date ranges (auto-updated)
- `js/script.js` - Updated to read and apply blocked dates
- `css/styles.css` - Added `.blocked` class styling

## Testing Locally

To test the sync script locally:

```bash
pip install icalendar requests
AIRBNB_CASA_MATUTINA="[YOUR_URL]" python sync_calendars.py
```

This will generate `blocked_dates.json` with the blocked date ranges.
