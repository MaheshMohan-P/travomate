import frappe
from frappe import _

def get_context(context):
    # Get the logged-in user's email
    user_email = frappe.session.user

    # Fetch the Traveler document linked to the logged-in user
    traveler = frappe.get_all(
        "Traveler",
        filters={"email": user_email},  # Filter by the logged-in user's email
        fields=["full_name", "email", "phone", "gender", "date_of_birth", "address", "nationality", "profile_picture", "emergency_contact"]
    )

    # Add the Traveler data to the context
    context.traveler = traveler[0] if traveler else {}