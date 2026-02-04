#!/usr/bin/env python3
"""
PiriHub Backend Server
Handles booking requests and email notifications
"""

import os
import json
import uuid
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'craig_halliday@mac.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'craig_halliday@mac.com')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'false').lower() == 'true'
SMTP_USE_SSL = os.getenv('SMTP_USE_SSL', 'true').lower() == 'true'

# Pricing configuration
NIGHTLY_RATE_USD = 300
MIN_STAY_NIGHTS = 14

BOOKINGS_FILE = 'bookings.json'

# House price reference
HOUSES = {
    'casa-matutina': {'name': 'Casa Matutina', 'rate': NIGHTLY_RATE_USD},
    'atelier': {'name': 'Atelier', 'rate': NIGHTLY_RATE_USD},
    'casa-sol': {'name': 'Casa Sol', 'rate': NIGHTLY_RATE_USD},
    'mini-casa': {'name': 'Mini Casa', 'rate': NIGHTLY_RATE_USD},
}

def load_bookings():
    """Load bookings from JSON file."""
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as f:
            return json.load(f)
    return {'bookings': []}

def save_bookings(data):
    """Save bookings to JSON file."""
    with open(BOOKINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_exchange_rate(currency_code):
    """Get USD to target currency exchange rate."""
    if currency_code == 'USD':
        return 1.0
    
    try:
        # Using exchangerate-api.com free tier
        response = requests.get(
            f'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data['rates'].get(currency_code, 1.0)
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
    
    return 1.0  # Fallback to 1:1 if API fails

def send_email(to_email, subject, html_content):
    """Send email via SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_EMAIL
        msg['To'] = to_email
        
        msg.attach(MIMEText(html_content, 'html'))
        
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/api/submit-booking', methods=['POST'])
def submit_booking():
    """Handle booking request submission."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'country', 'phone', 
                          'guests', 'startDate', 'endDate', 'house']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Calculate stay duration
        start = datetime.fromisoformat(data['startDate'])
        end = datetime.fromisoformat(data['endDate'])
        nights = (end - start).days
        
        if nights < MIN_STAY_NIGHTS:
            return jsonify({
                'error': f'Minimum stay is {MIN_STAY_NIGHTS} nights'
            }), 400
        
        # Create booking object
        booking = {
            'id': str(uuid.uuid4()),
            'createdAt': datetime.now().isoformat(),
            'firstName': data['firstName'],
            'lastName': data['lastName'],
            'email': data['email'],
            'country': data['country'],
            'phone': data['phone'],
            'guests': data['guests'],
            'startDate': data['startDate'],
            'endDate': data['endDate'],
            'house': data['house'],
            'nights': nights,
            'notes': data.get('notes', ''),
            'currency': data.get('currency', 'USD'),
            'status': 'pending',  # pending → approved → paid
        }
        
        # Calculate pricing
        total_usd = NIGHTLY_RATE_USD * nights
        deposit_usd = total_usd * 0.5  # 50% deposit

        booking['pricing'] = {
            'totalUSD': total_usd,
            'depositUSD': deposit_usd,
        }
        
        # Get exchange rate and convert to guest's currency
        exchange_rate = get_exchange_rate(booking['currency'])
        booking['pricing'][booking['currency']] = {
            'total': round(total_usd * exchange_rate, 2),
            'deposit': round(deposit_usd * exchange_rate, 2),
            'exchangeRate': exchange_rate,
            'rateDate': datetime.now().isoformat()
        }
        
        # Save booking
        bookings = load_bookings()
        bookings['bookings'].append(booking)
        save_bookings(bookings)
        
        # Send confirmation email to guest
        guest_email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Booking Request Received</h2>
            <p>Dear {booking['firstName']},</p>
            <p>Thank you for your interest in {HOUSES[booking['house']]['name']} at PiriHub!</p>
            <p><strong>Booking Details:</strong></p>
            <ul>
                <li><strong>Property:</strong> {HOUSES[booking['house']]['name']}</li>
                <li><strong>Check-in:</strong> {booking['startDate']}</li>
                <li><strong>Check-out:</strong> {booking['endDate']}</li>
                <li><strong>Duration:</strong> {booking['nights']} nights</li>
                <li><strong>Guests:</strong> {booking['guests']}</li>
                <li><strong>Booking ID:</strong> {booking['id']}</li>
            </ul>
            <p><strong>Pricing:</strong></p>
            <ul>
                <li>Nightly Rate: ${NIGHTLY_RATE_USD} USD</li>
                <li>Total (USD): ${booking['pricing']['totalUSD']:.2f}</li>
                <li>Deposit (50%): ${booking['pricing']['depositUSD']:.2f}</li>
            </ul>
            <p>We will review your request and contact you within 24 hours with payment options.</p>
            <p>Best regards,<br><strong>PiriHub Team</strong></p>
        </body>
        </html>
        """
        
        send_email(booking['email'], 'Booking Request Received - PiriHub', guest_email_html)
        
        # Send admin notification
        admin_email_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>New Booking Request</h2>
            <p><strong>Booking ID:</strong> {booking['id']}</p>
            <p><strong>Guest:</strong> {booking['firstName']} {booking['lastName']}</p>
            <p><strong>Email:</strong> {booking['email']}</p>
            <p><strong>Phone:</strong> {booking['phone']}</p>
            <p><strong>Country:</strong> {booking['country']}</p>
            <p><strong>Property:</strong> {HOUSES[booking['house']]['name']}</p>
            <p><strong>Dates:</strong> {booking['startDate']} to {booking['endDate']} ({booking['nights']} nights)</p>
            <p><strong>Guests:</strong> {booking['guests']}</p>
            {f'<p><strong>Notes:</strong> {booking["notes"]}</p>' if booking['notes'] else ''}
            <p><strong>Pricing (USD):</strong></p>
            <ul>
                <li>Total: ${booking['pricing']['totalUSD']:.2f}</li>
                <li>Deposit (50%): ${booking['pricing']['depositUSD']:.2f}</li>
                <li>Balance Due: ${booking['pricing']['totalUSD'] - booking['pricing']['depositUSD']:.2f}</li>
            </ul>
        </body>
        </html>
        """
        
        send_email(ADMIN_EMAIL, f'New Booking Request - {booking["firstName"]} {booking["lastName"]}', admin_email_html)
        
        return jsonify({
            'success': True,
            'bookingId': booking['id'],
            'message': 'Booking request submitted successfully'
        }), 201
        
    except Exception as e:
        print(f"Error submitting booking: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings (for admin dashboard)."""
    # TODO: Add authentication
    bookings = load_bookings()
    return jsonify(bookings['bookings'])

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get a specific booking."""
    bookings = load_bookings()
    for booking in bookings['bookings']:
        if booking['id'] == booking_id:
            return jsonify(booking)
    return jsonify({'error': 'Booking not found'}), 404

@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    """Handle review submission with booking verification."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['bookingId', 'reviewerName', 'rating', 'comment', 'house']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify booking exists
        bookings = load_bookings()
        booking = None
        for b in bookings['bookings']:
            if b['id'] == data['bookingId']:
                booking = b
                break
        
        if not booking:
            return jsonify({'error': 'Invalid booking ID'}), 404
        
        # Verify booking is for the correct house
        if booking['house'] != data['house']:
            return jsonify({'error': 'Booking ID does not match this property'}), 400
        
        # Check if booking has already been used for a review
        if booking.get('reviewed'):
            return jsonify({'error': 'A review has already been submitted for this booking'}), 400
        
        # Create review object
        review = {
            'id': str(uuid.uuid4()),
            'bookingId': data['bookingId'],
            'house': data['house'],
            'reviewerName': data['reviewerName'],
            'rating': int(data['rating']),
            'comment': data['comment'],
            'createdAt': datetime.now().isoformat(),
            'verified': True  # Verified through booking ID
        }
        
        # Save review (you'll need to create reviews.json similar to bookings.json)
        reviews_file = 'reviews.json'
        if os.path.exists(reviews_file):
            with open(reviews_file, 'r') as f:
                reviews_data = json.load(f)
        else:
            reviews_data = {'reviews': []}
        
        reviews_data['reviews'].append(review)
        
        with open(reviews_file, 'w') as f:
            json.dump(reviews_data, f, indent=2)
        
        # Mark booking as reviewed
        booking['reviewed'] = True
        save_bookings(bookings)
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'reviewId': review['id']
        }), 201
        
    except Exception as e:
        print(f"Error submitting review: {e}")
        return jsonify({'error': 'Failed to submit review'}), 500

@app.route('/api/reviews/<house_id>', methods=['GET'])
def get_reviews(house_id):
    """Get all verified reviews for a specific house."""
    try:
        reviews_file = 'reviews.json'
        if os.path.exists(reviews_file):
            with open(reviews_file, 'r') as f:
                reviews_data = json.load(f)
        else:
            reviews_data = {'reviews': []}
        
        # Filter reviews for the specific house
        house_reviews = [r for r in reviews_data['reviews'] if r['house'] == house_id]
        
        # Sort by most recent first
        house_reviews.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        return jsonify({'reviews': house_reviews}), 200
        
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return jsonify({'error': 'Failed to fetch reviews'}), 500

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, port=5001)
