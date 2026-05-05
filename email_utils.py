import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv('SMTP_HOST', 'mailout.easymail.ca')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER)
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'


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
