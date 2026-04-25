import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# EMAIL CONFIGURATION
# ==========================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_aqi_alert(recipient_email, city, aqi, status, recommendation):
    """
    Sends an email alert to the user when AQI exceeds the threshold.
    """
    try:
        subject = f"⚠️ Air Quality Alert: {city}"
        
        # Determine color for the email (optional HTML styling)
        color = "#ef4444" if aqi > 200 else "#f97316"
        
        # Construct unsubscribe URL - using a dynamic base if possible, otherwise default
        host = os.getenv("BACKEND_URL", "http://localhost:8888")
        unsubscribe_url = f"{host}/unsubscribe?email={recipient_email}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
                <div style="background-color: {color}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">Air Quality Alert</h1>
                </div>
                <div style="padding: 20px;">
                    <p>Hello,</p>
                    <p>The current Air Quality Index (AQI) in <b>{city}</b> has reached an unhealthy level.</p>
                    
                    <div style="background: #f4f4f4; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <span style="font-size: 40px; font-weight: bold; color: {color};">{aqi}</span><br>
                        <span style="font-size: 18px; font-weight: bold;">{status}</span>
                    </div>
                    
                    <p><b>Health Recommendation:</b></p>
                    <p>{recommendation}</p>
                    
                    <div style="border-top: 1px solid #eee; margin-top: 30px; padding-top: 15px; text-align: center; font-size: 11px; color: #888;">
                        <p>Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>This is an automated alert from your Personal AQI Health Assistant.</p>
                        <p><a href="{unsubscribe_url}" style="color: #64748b; text-decoration: underline;">Stop receiving these alerts (Unsubscribe)</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        print(f"Alert email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_current_aqi_email(recipient_email, city, city_data):
    """
    Sends an immediate email with the current AQI details upon subscription or manual trigger.
    """
    try:
        aqi = city_data['aqi']
        category = city_data['category']
        health_message = city_data['health_message']
        
        subject = f"🔔 AQInsight: Immediate AQI Update for {city}"
        
        # Color matching
        color = "#10b981" # Good
        if aqi > 300: color = "#7f1d1d" # Severe
        elif aqi > 200: color = "#ef4444" # Very Poor/Poor
        elif aqi > 100: color = "#f97316" # Moderate
        elif aqi > 50: color = "#eab308" # Satisfactory
        
        host = os.getenv("BACKEND_URL", "http://localhost:8888")
        unsubscribe_url = f"{host}/unsubscribe?email={recipient_email}"
        
        body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background-color: {color}; color: white; padding: 30px; text-align: center;">
                    <h2 style="margin: 0;">Current Air Quality in {city}</h2>
                    <p style="opacity: 0.9; margin-top: 5px;">Alerts successfully enabled!</p>
                </div>
                <div style="padding: 30px; text-align: center;">
                    <div style="display: inline-block; background: #f1f5f9; padding: 20px 40px; border-radius: 12px;">
                        <span style="font-size: 48px; font-weight: 800; color: {color};">{aqi}</span><br>
                        <span style="font-size: 20px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">{category}</span>
                    </div>
                    
                    <div style="margin-top: 25px; padding: 20px; background: #fffbeb; border-left: 4px solid #f59e0b; text-align: left;">
                        <p style="margin: 0; font-weight: 600; color: #92400e;">Health Advice:</p>
                        <p style="margin: 5px 0 0 0; color: #b45309;">{health_message}</p>
                    </div>

                    <p style="margin-top: 30px; font-size: 14px; color: #64748b;">
                        You will receive an automated update email every hour as long as these alerts are enabled.
                    </p>
                    
                    <div style="margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 12px; color: #94a3b8;">
                        <p>Tracked City: {city} | Time: {datetime.datetime.now().strftime('%H:%M')}</p>
                        <p><a href="{unsubscribe_url}" style="color: #3b82f6; text-decoration: none;">Disable these alerts</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        print(f"Immediate AQI email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send immediate email: {e}")
        return False

def send_welcome_email(recipient_email, recipient_name):
    """
    Sends a welcome email to new users after successful signup.
    """
    try:
        subject = "Welcome to AQInsight! 🌬️"
        
        body = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background-color: #3b82f6; color: white; padding: 40px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 28px;">Welcome, {recipient_name}!</h1>
                    <p style="font-size: 16px; opacity: 0.9;">Thank you for joining the AQInsight community.</p>
                </div>
                <div style="padding: 30px; border-bottom: 1px solid #e2e8f0;">
                    <p style="font-size: 16px;">We're excited to help you monitor and manage the air quality in your surroundings.</p>
                    <p>With <b>AQInsight</b>, you can:</p>
                    <ul style="padding-left: 20px;">
                        <li>Track real-time AQI and pollutants (PM2.5, CO, etc.)</li>
                        <li>Explore air quality across the globe using our interactive map</li>
                        <li>Receive automated health alerts for your favorite cities</li>
                        <li>Get personalized AI predictions for tomorrow's air quality</li>
                    </ul>
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:5000" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Explore Dashboard</a>
                    </div>
                </div>
                <div style="padding: 20px; text-align: center; background: #f1f5f9; color: #64748b; font-size: 13px;">
                    <p>© {datetime.datetime.now().year} AQInsight. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        print(f"Welcome email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {e}")
        return False

# Test function (Internal use only)
if __name__ == "__main__":
    # Test send (will fail without valid credentials)
    # send_aqi_alert("test@example.com", "London", 150, "Unhealthy", "Stay indoors.")
    pass
