import frappe
from frappe import _

def get_context(context):
    """
    Fetch the logged-in guide's Travel Zones and pass them to the template context.
    """
    try:
        user_email = frappe.session.user

        if user_email == "Guest":
            frappe.throw("You must be logged in to view this page.")

        # Fetch the guide's record
        guide = frappe.get_all("Guide", filters={"email": user_email}, fields=["name"])
        context.guide = guide[0] if guide else {}

        if guide:
            # Fetch all Travel Zones for the guide with daily_rate included
            travel_zones = frappe.get_all("Travel Zone", 
                filters={"guide": guide[0].name}, 
                fields=["name", "state", "district", "description", "daily_rate"]
            )
            
            context.travel_zones = []
            for travel_zone in travel_zones:
                travel_zone_doc = frappe.get_doc("Travel Zone", travel_zone.name)
                areas = [row.area for row in travel_zone_doc.areas] if travel_zone_doc.areas else []
                context.travel_zones.append({
                    "name": travel_zone_doc.name,
                    "state": travel_zone_doc.state,
                    "district": travel_zone_doc.district,
                    "areas": areas,
                    "description": travel_zone_doc.description,
                    "daily_rate": travel_zone_doc.daily_rate,  # Added daily_rate
                    "booked_dates": [row.date for row in travel_zone_doc.booked_dates] if travel_zone_doc.booked_dates else []
                })
        else:
            context.travel_zones = []

        # Fetch all districts for the district dropdown
        context.districts = frappe.get_all("District", fields=["name", "district_name"])

    except Exception as e:
        frappe.logger().error(f"Error in get_context: {frappe.get_traceback()}")
        frappe.throw("An error occurred while fetching data. Please try again.")