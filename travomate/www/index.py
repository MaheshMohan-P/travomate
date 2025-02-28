import frappe

def get_context(context):
    """
    Context processor for dashboard redirection.
    """
    context.no_cache = 1
    user = frappe.session.user

    if user == 'Guest':
        return
    elif user == 'Administrator':
        frappe.local.flags.redirect_location = "/app"
        raise frappe.Redirect
    else:
        # Check the user's role
        user_role = frappe.db.get_value("User", user, "role_profile_name")
        if user_role == "Traveler":
            frappe.local.flags.redirect_location = "/traveler_dash"
            raise frappe.Redirect
        elif user_role == "Guide":
            frappe.local.flags.redirect_location = "/guide_dash"
            raise frappe.Redirect
        else:
            frappe.local.flags.redirect_location = "/login"
            raise frappe.Redirect

def get_routes():
    """
    Define the routes for the application.
    """
    return [
        {
            "path": "/traveler_dash",
            "template": "traveler_dash",  # Path to the traveler dashboard in www folder
            "context": get_context
        },
        {
            "path": "/guide_dash",
            "template": "guide_dash",  # Path to the guide dashboard in www folder
            "context": get_context
        }
    ]