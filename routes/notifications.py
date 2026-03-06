from flask import Blueprint, render_template, g, redirect, url_for, jsonify, request
from models import db, Notification, DiseaseOutbreak, Farm, AnimalType
from sqlalchemy import desc
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__)

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r

@notifications_bp.route('/notifications')
def index():
    """Show all notifications"""
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Get user's notifications
    notifications = Notification.query.filter_by(
        user_id=g.user.id
    ).order_by(desc(Notification.created_at)).all()
    
    # Mark all as read
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True
    
    db.session.commit()
    
    return render_template('notifications.html', notifications=notifications)

@notifications_bp.route('/notifications/api/check-new')
def check_new():
    """API endpoint to check for new notifications"""
    if not g.user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Count unread notifications
    unread_count = Notification.query.filter_by(
        user_id=g.user.id,
        is_read=False
    ).count()
    
    return jsonify({
        'unread_count': unread_count
    })

@notifications_bp.route('/notifications/scan-outbreaks', methods=['POST'])
def scan_outbreaks():
    """Scan for new disease outbreaks and create notifications"""
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Get user's farm details
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    if not farm or not farm.latitude or not farm.longitude:
        return jsonify({'error': 'Farm location not set'}), 400
    
    # Get recent outbreaks (in the past week) in user's state
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    recent_outbreaks = DiseaseOutbreak.query.filter(
        DiseaseOutbreak.state == farm.state,
        DiseaseOutbreak.is_active == True,
        DiseaseOutbreak.reported_at >= cutoff_date
    ).all()
    
    new_notification_count = 0
    
    # Check each outbreak and create notification if within range
    for outbreak in recent_outbreaks:
        if outbreak.latitude and outbreak.longitude:
            distance = haversine(
                farm.longitude, farm.latitude,
                outbreak.longitude, outbreak.latitude
            )
            
            # Check if within 50km
            if distance <= 50:
                # Check if we already have a notification for this outbreak
                existing = Notification.query.filter_by(
                    user_id=g.user.id,
                    notification_type='disease_alert',
                    related_disease=outbreak.disease_name
                ).first()
                
                if not existing:
                    # Create a new notification
                    notification = Notification(
                        user_id=g.user.id,
                        title=f"Disease Alert: {outbreak.disease_name}",
                        message=f"A {outbreak.disease_name} outbreak has been reported {distance:.1f}km from your farm in {outbreak.district}. Take precautions to protect your animals.",
                        notification_type='disease_alert',
                        is_read=False,
                        related_disease=outbreak.disease_name,
                        distance_km=distance
                    )
                    db.session.add(notification)
                    new_notification_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_notifications': new_notification_count
    }) 