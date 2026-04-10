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
        
        # Construct unsubscribe URL
        unsubscribe_url = f"http://192.168.31.174:8888/unsubscribe_confirm?email={recipient_email}"
        
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
