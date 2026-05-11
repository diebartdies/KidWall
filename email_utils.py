import smtplib
import os
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

SMTP_HOST = os.getenv('SMTP_HOST', 'mailout.easymail.ca')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER)
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'


def send_email(to_email: str, subject: str, body_html: str) -> None:
    """Generic email sender."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    msg.attach(MIMEText(body_html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())


def send_alert_email(
    to_email: str,
    recipient_name: str,
    child_name: str,
    message: str,
    school_name: str = "the school",
) -> None:
    """Send an urgent alert email to a parent or emergency contact."""
    subject = f"🚨 Urgent – {child_name} – ColePago Alert"
    body_html = f"""
    <p>Hello {recipient_name},</p>
    <p>You are receiving this message because <strong>{child_name}</strong>'s
    school (<em>{school_name}</em>) needs to reach you urgently.</p>
    <blockquote style="border-left:4px solid #e53935;padding:8px 16px;
    background:#fff3f3;margin:16px 0;">
      {message}
    </blockquote>
    <p>Please contact the school as soon as possible.</p>
    <br><p>— ColePago School Communication System</p>
    """
    send_email(to_email, subject, body_html)


def send_temp_password_email(to_email: str, name: str, temp_password: str) -> None:
    subject = 'ColePago – Password Reset'
    body_html = f"""
    <p>Hello {name},</p>
    <p>We received a request to reset your password.</p>
    <p>Your temporary password is:</p>
    <h2 style="letter-spacing:4px;">{temp_password}</h2>
    <p><strong>This password expires in 2 hours.</strong><br>
    You will be required to change it on next login.</p>
    <p>If you did not request this, please ignore this email.</p>
    <br><p>— ColePago Team</p>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    msg.attach(MIMEText(body_html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())
