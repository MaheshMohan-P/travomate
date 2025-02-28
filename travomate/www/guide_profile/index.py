import frappe
from frappe import _

def get_context(context):
    # Get the logged-in user's email
    user_email = frappe.session.user

    # Fetch the Guide document linked to the logged-in user
    guide = frappe.get_all(
        "Guide",
        filters={"email": user_email},  # Filter by the logged-in user's email
        fields=["full_name", "email", "phone", "gender", "date_of_birth", "address", "nationality", "profile_picture", "language_spoken", "identification_document"]
    )

    # Add the Guide data to the context
    context.guide = guide[0] if guide else {}