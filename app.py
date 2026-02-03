#!/usr/bin/env python3
"""
PiriHub Backend Server
Handles booking requests, approvals, and Stripe payment processing
"""

import os
import json
import uuid
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import stripe
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'craig_halliday@mac.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_EMAIL = os.getenv('SMTP_EMAIL', 'craig_halliday@mac.com')

stripe.api_key = STRIPE_SECRET_KEY

# Pricing configuration
NIGHTLY_RATE_USD = 300
MIN_STAY_NIGHTS = 14
DEPOSIT_PERCENTAGE = 0.5  # 50%

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
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
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
            'status': 'pending',  # pending → approved → paid → confirmed
            'depositAmount': None,
            'totalAmount': None,
            'stripePaymentId': None,
        }
        
        # Calculate pricing
        total_usd = NIGHTLY_RATE_USD * nights
        deposit_usd = total_usd * DEPOSIT_PERCENTAGE
        
        booking['totalAmount'] = {
            'USD': total_usd,
            'deposit': deposit_usd
        }
        
        # Get exchange rate and convert to guest's currency
        exchange_rate = get_exchange_rate(booking['currency'])
        booking['totalAmount'][booking['currency']] = {
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
        <h2>Booking Request Received</h2>
        <p>Dear {booking['firstName']},</p>
        <p>Thank you for your interest in {HOUSES[booking['house']]['name']} at PiriHub!</p>
        <p><strong>Booking Details:</strong></p>
        <ul>
            <li>Property: {HOUSES[booking['house']]['name']}</li>
            <li>Check-in: {booking['startDate']}</li>
            <li>Check-out: {booking['endDate']}</li>
            <li>Duration: {booking['nights']} nights</li>
            <li>Guests: {booking['guests']}</li>
        </ul>
        <p>We will review your request and contact you within 24 hours with pricing and payment details.</p>
        <p>Best regards,<br>PiriHub Team</p>
        """
        
        send_email(booking['email'], 'Booking Request Received - PiriHub', guest_email_html)
        
        # Send admin notification with approval link
        admin_email_html = f"""
        <h2>New Booking Request</h2>
        <p><strong>Guest:</strong> {booking['firstName']} {booking['lastName']}</p>
        <p><strong>Email:</strong> {booking['email']}</p>
        <p><strong>Property:</strong> {HOUSES[booking['house']]['name']}</p>
        <p><strong>Dates:</strong> {booking['startDate']} to {booking['endDate']} ({booking['nights']} nights)</p>
        <p><strong>Guests:</strong> {booking['guests']}</p>
        <p><strong>Country:</strong> {booking['country']}</p>
        <p><strong>Phone:</strong> {booking['phone']}</p>
        {f'<p><strong>Notes:</strong> {booking["notes"]}</p>' if booking['notes'] else ''}
        <p><strong>Pricing (USD):</strong><br>
        Total: ${booking['totalAmount']['USD']:.2f']}<br>
        Deposit (50%): ${booking['totalAmount']['deposit']:.2f'}</p>
        <p>
            <a href="http://localhost:5000/admin/approve-booking/{booking['id']}" 
               style="background-color: #44a08d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
               Approve & Generate Payment Link
            </a>
        </p>
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

@app.route('/admin/approve-booking/<booking_id>', methods=['GET'])
def approve_booking(booking_id):
    """Generate Stripe payment link for approved booking."""
    try:
        bookings = load_bookings()
        booking = None
        
        for b in bookings['bookings']:
            if b['id'] == booking_id:
                booking = b
                break
        
        if not booking:
            return 'Booking not found', 404
        
        if booking['status'] != 'pending':
            return f'Booking already {booking["status"]}', 400
        
        # Create Stripe checkout session
        try:
            # Calculate deposit in USD cents
            deposit_cents = int(booking['totalAmount']['deposit'] * 100)
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{HOUSES[booking["house"]]["name"]} - Deposit',
                            'description': f'{booking["nights"]} nights ({booking["startDate"]} to {booking["endDate"]})',
                        },
                        'unit_amount': deposit_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://localhost:3000/booking-confirmed?session_id={CHECKOUT_SESSION_ID}',
                cancel_url='http://localhost:3000/booking-cancelled',
                customer_email=booking['email'],
                metadata={
                    'booking_id': booking_id,
                    'house': booking['house'],
                    'nights': booking['nights'],
                }
            )
            
            # Update booking with Stripe session ID
            booking['stripeSessionId'] = checkout_session.id
            booking['stripePaymentLink'] = checkout_session.url
            booking['status'] = 'approved'
            save_bookings(bookings)
            
            # Send payment link to guest
            payment_email_html = f"""
            <h2>Your Booking is Approved!</h2>
            <p>Dear {booking['firstName']},</p>
            <p>Great news! Your booking for {HOUSES[booking['house']]['name']} has been approved.</p>
            <p><strong>Booking Summary:</strong></p>
            <ul>
                <li>Property: {HOUSES[booking['house']]['name']}</li>
                <li>Check-in: {booking['startDate']}</li>
                <li>Check-out: {booking['endDate']}</li>
                <li>Duration: {booking['nights']} nights</li>
            </ul>
            <p><strong>Payment Required:</strong></p>
            <p>Deposit (50%): ${booking['totalAmount']['deposit']:.2f} USD</p>
            <p>Balance due on arrival: ${booking['totalAmount']['USD'] - booking['totalAmount']['deposit']:.2f} USD</p>
            <p>
                <a href="{checkout_session.url}" 
                   style="background-color: #44a08d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   Complete Payment
                </a>
            </p>
            <p>The payment link will expire in 24 hours.</p>
            <p>Best regards,<br>PiriHub Team</p>
            """
            
            send_email(booking['email'], 'Your Booking is Approved - Complete Payment', payment_email_html)
            
            return f"""
            <h2>Payment Link Generated</h2>
            <p>Booking ID: {booking_id}</p>
            <p><a href="{checkout_session.url}" target="_blank">Share this payment link with guest</a></p>
            <p><a href="mailto:{booking['email']}?subject=Your%20PiriHub%20Booking%20Approved&body=Payment%20link%3A%20{checkout_session.url}">Send via Email</a></p>
            """
        
        except stripe.error.StripeError as e:
            return f'Stripe error: {str(e)}', 500
            
    except Exception as e:
        print(f"Error approving booking: {e}")
        return f'Error: {str(e)}', 500

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook for payment confirmation."""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            return 'Invalid payload', 400
        except stripe.error.SignatureVerificationError:
            return 'Invalid signature', 400
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            booking_id = session['metadata'].get('booking_id')
            
            # Update booking status to paid
            bookings = load_bookings()
            for b in bookings['bookings']:
                if b['id'] == booking_id:
                    b['status'] = 'paid'
                    b['stripePaymentId'] = session['id']
                    b['paidAt'] = datetime.now().isoformat()
                    
                    # Send confirmation email
                    confirm_email_html = f"""
                    <h2>Payment Confirmed!</h2>
                    <p>Dear {b['firstName']},</p>
                    <p>Your payment has been processed successfully.</p>
                    <p><strong>Booking Confirmation:</strong></p>
                    <ul>
                        <li>Confirmation #: {b['id']}</li>
                        <li>Property: {HOUSES[b['house']]['name']}</li>
                        <li>Check-in: {b['startDate']}</li>
                        <li>Check-out: {b['endDate']}</li>
                    </ul>
                    <p>We look forward to hosting you!</p>
                    <p>Best regards,<br>PiriHub Team</p>
                    """
                    
                    send_email(b['email'], 'Booking Confirmed!', confirm_email_html)
                    save_bookings(bookings)
                    break
        
        return 'Webhook received', 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error processing webhook', 500

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings (admin only)."""
    # TODO: Add authentication
    bookings = load_bookings()
    return jsonify(bookings['bookings'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
