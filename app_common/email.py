from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading


def send_template_email(subject, template_name, context, recipient_list):
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)
    from_email = settings.EMAIL_HOST_USER
    
    def send_email():
        try:
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
            print("Email sent successfully.")
        except Exception as e:
            print(f"Failed to send email: {e}")

    # Use threading to send the email asynchronously
    email_thread = threading.Thread(target=send_email)
    email_thread.start()
    