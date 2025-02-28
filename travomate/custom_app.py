import frappe
from frappe.utils.password import update_password

@frappe.whitelist(allow_guest=True)
def sign_up(**kwargs):
    """
    Custom signup method to save user details and create a user in ERPNext.
    """
    try:
        # Extract data from the frontend
        email = kwargs.get("email")
        password = kwargs.get("password")
        role = kwargs.get("role_profile")  # Get the selected role
        
        # Validate required fields
        if not all([email, password, role]):
            frappe.throw("Please fill all required fields.")

        # Validate the role
        if role not in ["Traveler", "Guide"]:
            frappe.throw("Invalid role selected.")
        
        # Check if the Role Profile exists
        if not frappe.db.exists("Role Profile", role):
            frappe.throw(f"Role Profile '{role}' does not exist. Please create it first.")

        # Check if the email already exists
        if frappe.db.exists("User", email):
            frappe.throw("User with this email already exists.")

        # Create a new user
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": email.split("@")[0],  # Use email prefix as first name
            "send_welcome_email": 0,  # Disable welcome email
            "user_type": "Website User",
            "role_profile_name": role  # Assign the selected role
        })
        user.insert(ignore_permissions=True)

        # Set the user's password
        update_password(user.name, password)

        # Commit changes to the database
        frappe.db.commit()

        if role == "Traveler":
            traveler = frappe.get_doc({
                "doctype": "Traveler",
                "user": user.name,  # Link to the User record
                "email": email,
            })
            traveler.insert(ignore_permissions=True)
        elif role == "Guide":
            guide = frappe.get_doc({
                "doctype": "Guide",
                "user": user.name,  # Link to the User record
                "email": email,
            })
            guide.insert(ignore_permissions=True)

        # Commit changes to the database
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Signup successful! Please log in.",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Signup Error")
        frappe.throw(f"An error occurred: {str(e)}")

@frappe.whitelist(allow_guest=True)
def on_session_creation(login_manager):
    """
    Redirect users to their respective dashboards after login.
    """
    user = login_manager.user
    print("\n\n\n\n user : ", user)

    # Redirect only for non-admin users
    if user != "Administrator":
        # Check the user's role
        user_role = frappe.db.get_value("User", user, "role_profile_name")
        if user_role == "Traveler":
            frappe.local.response["home_page"] = "/traveler_dash"
        elif user_role == "Guide":
            frappe.local.response["home_page"] = "/guide_dash"
        else:
            frappe.local.response["home_page"] = "/login"  # Fallback for users without a role

def route_user(bootinfo):
    """
    Define the initial route for users based on their role.
    """
    print("\n\ngfgfgfhghgf")
    user = frappe.session.user

    # Redirect only for non-admin users
    if user != "Administrator":
        # Check the user's role
        user_role = frappe.db.get_value("User", user, "role_profile_name")
        if user_role == "Traveler":
            bootinfo.route_to = "/traveler_dash"
        elif user_role == "Guide":
            bootinfo.route_to = "/guide_dash"
        else:
            bootinfo.route_to = "/login"  # Fallback for users without a role
    else:
        bootinfo.route_to = "/app"


@frappe.whitelist()
def update_traveler_profile(**kwargs):
    """
    Update Traveler profile details.
    """
    try:
        # Extract data from the frontend
        user = frappe.session.user  # Get the logged-in user
        full_name = kwargs.get("full_name")
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        gender = kwargs.get("gender")
        date_of_birth = kwargs.get("date_of_birth")
        address = kwargs.get("address")
        nationality = kwargs.get("nationality")
        emergency_contact = kwargs.get("emergency_contact")
        profile_picture = kwargs.get("profile_picture")  # Handle file upload separately

        # Validate required fields
        if not all([full_name, email, phone, gender, date_of_birth, address, nationality, emergency_contact]):
            frappe.throw("Please fill all required fields.")

        # Get the Traveler document linked to the user
        traveler = frappe.get_doc("Traveler", {"email": user})  # Filter by email
        if not traveler:
            frappe.throw("Traveler profile not found.")

        # Update Traveler details
        traveler.update({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "gender": gender,
            "date_of_birth": date_of_birth,
            "address": address,
            "nationality": nationality,
            "emergency_contact": emergency_contact,
        })

        # Handle profile picture upload
        if profile_picture:
            # Save the file and attach it to the Traveler document
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": profile_picture.filename,
                "attached_to_doctype": "Traveler",
                "attached_to_name": traveler.name,
                "content": profile_picture.read(),
            })
            file_doc.insert(ignore_permissions=True)
            traveler.profile_picture = file_doc.file_url

        traveler.save(ignore_permissions=True)

        # Commit changes to the database
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Traveler profile updated successfully!",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Traveler Profile Update Error")
        frappe.throw(f"An error occurred: {str(e)}")

@frappe.whitelist()
def update_guide_profile(**kwargs):
    """
    Update Guide profile details.
    """
    try:
        # Extract data from the frontend
        user = frappe.session.user  # Get the logged-in user
        full_name = kwargs.get("full_name")
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        gender = kwargs.get("gender")
        date_of_birth = kwargs.get("date_of_birth")
        address = kwargs.get("address")
        nationality = kwargs.get("nationality")
        language_spoken = kwargs.get("language_spoken")
        profile_picture = kwargs.get("profile_picture")  # Handle file upload separately
        identification_document = kwargs.get("identification_document")  # Handle file upload separately

        # Validate required fields
        if not all([full_name, email, phone, gender, date_of_birth, address, nationality, language_spoken]):
            frappe.throw("Please fill all required fields.")

        # Get the Guide document linked to the user
        guide = frappe.get_doc("Guide", {"email": user})  # Filter by email
        if not guide:
            frappe.throw("Guide profile not found.")

        # Update Guide details
        guide.update({
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "gender": gender,
            "date_of_birth": date_of_birth,
            "address": address,
            "nationality": nationality,
            "language_spoken": language_spoken,
        })

        # Handle profile picture upload
        if profile_picture:
            # Save the file and attach it to the Guide document
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": profile_picture.filename,
                "attached_to_doctype": "Guide",
                "attached_to_name": guide.name,
                "content": profile_picture.read(),
            })
            file_doc.insert(ignore_permissions=True)
            guide.profile_picture = file_doc.file_url

        # Handle identification document upload
        if identification_document:
            # Save the file and attach it to the Guide document
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": identification_document.filename,
                "attached_to_doctype": "Guide",
                "attached_to_name": guide.name,
                "content": identification_document.read(),
            })
            file_doc.insert(ignore_permissions=True)
            guide.identification_document = file_doc.file_url

        guide.save(ignore_permissions=True)

        # Commit changes to the database
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Guide profile updated successfully!",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Guide Profile Update Error")
        frappe.throw(f"An error occurred: {str(e)}")