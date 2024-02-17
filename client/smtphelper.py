import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def smtp_send(server, user, password, recipient, subject, body):

    # Email and password for authentication
    sender_email = f'{user}@{server}'
    sender_password = password
    
    # Recipient email address
    recipient_email = recipient
    
    # SMTP server details
    smtp_server = server
    smtp_port = 25  # Default port for TLS connection
    
    # Create a message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    
    # Add body to email
    body = body
    message.attach(MIMEText(body, 'plain'))
    
    # Establish a connection to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Secure the connection
    server.login(sender_email, sender_password)
    
    # Send the email
    server.sendmail(sender_email, recipient_email, message.as_string())
    
    # Close the connection
    server.quit()
