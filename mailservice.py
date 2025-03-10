from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import os


load_dotenv()

def email_confirmation(email, code):
    
    subject = "Verification Code Halloween Spotter"
    body = f"Welcome to Halloween Spotting. \n Your Verification code is: {code} \n\n Please enter within the next 5 min"
    sender = "halloweenspotter@gmail.com"
    recipients = email
    password = os.getenv('MAILPASSWORD')
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipients
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

    
def email_password_reset(email, code):
    
    subject = "Password Reset"
    body = f"\n\nPassword Reset \n\n Your Verification code is: {code} \n\n Please enter within the next 5 min\n\n Please contact Admin if you did not ask for a reset"
    sender = "halloweenspotter@gmail.com"
    recipients = email
    password = os.getenv('MAILPASSWORD')
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipients
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")
