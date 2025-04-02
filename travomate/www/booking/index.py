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

    # Fetch all areas
    areas = frappe.get_all(
        "Area",
        fields=["name", "area", "district"]
    )
    context.areas = areas

    # Fetch all guides
    guides = frappe.get_all(
        "Guide",
        fields=["name", "full_name", "email", "phone", "gender", "date_of_birth", "address", "nationality", "profile_picture", "language_spoken", "identification_document", "experience", "rating"]
    )
    context.guides = guides

    # Fetch all travel zones and their areas (from the child table)
    travel_zones = frappe.get_all(
        "Travel Zone",
        fields=["name", "guide", "district", "description"],
        # Fetch areas from the child table
        join="LEFT JOIN `tabTZ Areas` ON `tabTravel Zone`.name = `tabTZ Areas`.parent",
        # Group by travel zone to avoid duplicates
        group_by="name"
    )

    # Fetch areas for each travel zone
    for travel_zone in travel_zones:
        travel_zone["areas"] = frappe.get_all(
            "TZ Areas",  # Correct child table name
            filters={"parent": travel_zone["name"]},
            fields=["area"]
        )

    context.travel_zones = travel_zones

    return context

