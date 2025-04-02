import frappe
from frappe import _

def get_context(context):
    # Get the logged-in user's email
    user_email = frappe.session.user

    # Ensure the user is logged in
    if user_email == "Guest":
        frappe.throw("You must be logged in to access this page.")

    # Fetch all districts
    districts = frappe.get_all(
        "District",
        fields=["name"]
    )
    context.districts = districts

    # Fetch all areas (optional, if needed for preloading)
    areas = frappe.get_all(
        "Area",
        fields=["name", "area", "district"]
    )
    context.areas = areas

    # Fetch all guides (optional, if needed for preloading)
    guides = frappe.get_all(
        "Guide",
        fields=["full_name", "email", "phone", "gender", "date_of_birth", "address", "nationality", "profile_picture", "language_spoken", "identification_document", "experience", "rating"]
    )
    context.guides = guides

    # Fetch all travel zones (optional, if needed for preloading)
    travel_zones = frappe.get_all(
        "Travel Zone",
        fields=["name", "guide", "district", "description"],
        # Fetch areas from the child table
        join="LEFT JOIN `tabTravel Zone Area` ON `tabTravel Zone`.name = `tabTravel Zone Area`.parent"
    )
    context.travel_zones = travel_zones