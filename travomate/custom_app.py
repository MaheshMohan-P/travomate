import frappe
from frappe.utils.password import update_password
from frappe.utils import flt, getdate, now_datetime, nowdate
from datetime import datetime, timedelta

@frappe.whitelist(allow_guest=True)
def sign_up(**kwargs):
    try:
        # Log incoming data
        frappe.logger().info(f"Incoming data: {kwargs}")

        # Extract data
        full_name = kwargs.get("full_name")
        email = kwargs.get("email")
        password = kwargs.get("password")
        role = kwargs.get("role_profile")

        # Log extracted data
        frappe.logger().info(f"Extracted data - Full Name: {full_name}, Email: {email}, Role: {role}")

        # Validate required fields
        if not all([full_name, email, password, role]):
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
            "first_name": full_name,
            "send_welcome_email": 0,
            "user_type": "Website User",
            "role_profile_name": role
        })
        user.insert(ignore_permissions=True)

        # Set the user's password
        update_password(user.name, password)

        # Commit changes
        frappe.db.commit()

        # Create Traveler or Guide document
        if role == "Traveler":
            traveler = frappe.get_doc({
                "doctype": "Traveler",
                "user": user.name,
                "email": email,
                "full_name": full_name,
            })
            traveler.insert(ignore_permissions=True)
        elif role == "Guide":
            guide = frappe.get_doc({
                "doctype": "Guide",
                "user": user.name,
                "email": email,
                "full_name": full_name,
            })
            guide.insert(ignore_permissions=True)

        # Commit changes
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Signup successful! Please log in.",
            "redirect_url": "/login"
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

@frappe.whitelist(allow_guest=False, methods=['PATCH'])
def update_traveler_profile(**kwargs):
    """
    Update Traveler profile details and corresponding User details.
    Only updates fields that are provided in the request.
    """
    try:
        # Get the logged-in user's email
        user_email = frappe.session.user

        # Ensure the user is logged in
        if user_email == "Guest":
            frappe.throw("You must be logged in to update your profile.")

        # Ensure the user has the Traveler role
        if "Traveler" not in frappe.get_roles(user_email):
            frappe.throw("You do not have permission to update a Traveler profile.")

        # Extract data from the frontend
        full_name = kwargs.get("full_name")  # Corresponds to first_name in User
        phone = kwargs.get("phone")
        gender = kwargs.get("gender")
        date_of_birth = kwargs.get("date_of_birth")
        address = kwargs.get("address")
        nationality = kwargs.get("nationality")
        emergency_contact = kwargs.get("emergency_contact")
        profile_picture = kwargs.get("profile_picture")  # Handle file upload separately

        # Update the User doctype (first_name)
        user = frappe.get_doc("User", user_email)
        if not user:
            frappe.throw("User not found.")

        if full_name:  # Update first_name in User if full_name is provided
            user.first_name = full_name
            user.save(ignore_permissions=True)

        # Update the Traveler doctype
        traveler = frappe.get_doc("Traveler", {"email": user_email})
        if not traveler:
            frappe.throw("Traveler profile not found.")

        # Update only the fields that are provided
        if full_name:
            traveler.full_name = full_name
        if phone:
            traveler.phone = phone
        if gender:
            traveler.gender = gender
        if date_of_birth:
            traveler.date_of_birth = date_of_birth
        if address:
            traveler.address = address
        if nationality:
            traveler.nationality = nationality
        if emergency_contact:
            traveler.emergency_contact = emergency_contact

        if frappe.request.files:
            if "profile_picture" in frappe.request.files:
                file = frappe.request.files["profile_picture"]
                file_doc = frappe.utils.file_manager.save_file(
                    file.filename,
                    file.read(),
                    "Traveler",
                    traveler.name,
                    is_private=0,
                )
                traveler.profile_picture = file_doc.file_url  # Store file URL in Traveler Doctype

        # Save the updated Traveler document
        traveler.save(ignore_permissions=True)

        # Commit changes to the database
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Traveler profile updated successfully!",
        }

    except Exception as e:
        # Log the error for debugging
        frappe.logger().error(f"Error updating Traveler profile: {frappe.get_traceback()}")
        frappe.throw("An error occurred while updating the profile. Please try again.")


@frappe.whitelist(allow_guest=False, methods=['PATCH'])
def update_guide_profile(**kwargs):
    """
    Update Guide profile details and corresponding User details.
    Only updates fields that are provided in the request.
    """
    try:
        # Get the logged-in user's email
        user_email = frappe.session.user

        # Ensure the user is logged in
        if user_email == "Guest":
            frappe.throw("You must be logged in to update your profile.")

        # Ensure the user has the Guide role
        if "Guide" not in frappe.get_roles(user_email):
            frappe.throw("You do not have permission to update a Guide profile.")

        # Extract data from the frontend
        full_name = kwargs.get("full_name")  # Corresponds to first_name in User
        phone = kwargs.get("phone")
        gender = kwargs.get("gender")
        date_of_birth = kwargs.get("date_of_birth")
        address = kwargs.get("address")
        nationality = kwargs.get("nationality")
        language_spoken = kwargs.get("language_spoken")
        profile_picture = kwargs.get("profile_picture")  # Handle file upload separately
        identification_document = kwargs.get("identification_document")  # Handle file upload separately

        # Update the User doctype (first_name)
        user = frappe.get_doc("User", user_email)
        if not user:
            frappe.throw("User not found.")

        if full_name:  # Update first_name in User if full_name is provided
            user.first_name = full_name
            user.save(ignore_permissions=True)

        # Update the Guide doctype
        guide = frappe.get_doc("Guide", {"email": user_email})
        if not guide:
            frappe.throw("Guide profile not found.")

        # Update only the fields that are provided
        if full_name:
            guide.full_name = full_name
        if phone:
            guide.phone = phone
        if gender:
            guide.gender = gender
        if date_of_birth:
            guide.date_of_birth = date_of_birth
        if address:
            guide.address = address
        if nationality:
            guide.nationality = nationality
        if language_spoken:
            guide.language_spoken = language_spoken

        if frappe.request.files:
            if "profile_picture" in frappe.request.files:
                file = frappe.request.files["profile_picture"]
                file_doc = frappe.utils.file_manager.save_file(
                    file.filename,
                    file.read(),
                    "Guide",
                    guide.name,
                    is_private=0,
                )
                guide.profile_picture = file_doc.file_url  # Store file URL in Guide Doctype

            if "identification_document" in frappe.request.files:
                file = frappe.request.files["identification_document"]
                file_doc = frappe.utils.file_manager.save_file(
                    file.filename,
                    file.read(),
                    "Guide",
                    guide.name,
                    is_private=0,
                )
                guide.identification_document = file_doc.file_url  # Store file URL in Guide Doctype

        # Save the updated Guide document
        guide.save(ignore_permissions=True)

        # Commit changes to the database
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Guide profile updated successfully!",
        }

    except Exception as e:
        # Log the error for debugging
        frappe.logger().error(f"Error updating Guide profile: {frappe.get_traceback()}")
        frappe.throw("An error occurred while updating the profile. Please try again.")

@frappe.whitelist(methods=['GET'])
def check_existing_travel_zone(district):
    """
    Check if the guide already has a travel zone in the specified district
    """
    try:
        user_email = frappe.session.user
        if user_email == "Guest":
            frappe.throw("You must be logged in to check travel zones.")

        guide = frappe.get_value("Guide", {"email": user_email}, "name")
        if not guide:
            frappe.throw("Guide profile not found.")

        # Check for existing travel zone in this district
        existing_zones = frappe.get_all("Travel Zone",
            filters={
                "guide": guide,
                "district": district
            },
            fields=["name"]
        )

        return {
            "exists": len(existing_zones) > 0,
            "count": len(existing_zones)
        }

    except Exception as e:
        frappe.logger().error(f"Error in check_existing_travel_zone: {frappe.get_traceback()}")
        frappe.throw(f"An error occurred while checking travel zones: {str(e)}")

@frappe.whitelist(methods=['POST'])
def save_travel_zone(**kwargs):
    """
    Save a new Travel Zone for the logged-in guide.
    """
    try:
        frappe.logger().info("save_travel_zone called")
        user_email = frappe.session.user

        # Ensure the user is logged in
        if user_email == "Guest":
            frappe.throw("You must be logged in to save a travel zone.")

        # Extract and validate data
        district = kwargs.get("district")
        areas = kwargs.get("areas")
        description = kwargs.get("description", "")
        daily_rate = kwargs.get("daily_rate")

        # Validate required fields
        if not district:
            frappe.throw("District is required.")
        if not areas or not isinstance(areas, list) or len(areas) == 0:
            frappe.throw("Please select at least one area.")
        if not daily_rate or float(daily_rate) <= 0:
            frappe.throw("Please enter a valid daily rate.")

        # Fetch the guide's name
        guide = frappe.get_value("Guide", {"email": user_email}, "name")
        if not guide:
            frappe.throw("Guide profile not found.")

        # Check for existing travel zone in this district (double-check)
        existing_zones = frappe.get_all("Travel Zone",
            filters={
                "guide": guide,
                "district": district
            },
            fields=["name"]
        )
        if existing_zones:
            frappe.throw("You already have a travel zone in this district. Please edit your existing zone.")

        # Create a new Travel Zone
        travel_zone_doc = frappe.get_doc({
            "doctype": "Travel Zone",
            "guide": guide,
            "district": district,
            "description": description,
            "daily_rate": daily_rate
        })

        # Add areas to the child table
        for area in areas:
            travel_zone_doc.append("areas", {"area": area})

        # Save the Travel Zone
        travel_zone_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Travel Zone saved successfully!",
        }

    except Exception as e:
        frappe.logger().error(f"Error in save_travel_zone: {frappe.get_traceback()}")
        frappe.throw(f"An error occurred while saving the Travel Zone: {str(e)}")

# @frappe.whitelist(methods=['PATCH'])
# def update_travel_zone(name, **kwargs):
#     """
#     Update an existing Travel Zone record.
#     """
#     try:
#         frappe.logger().info("update_travel_zone called with name: {} and kwargs: {}".format(name, kwargs))
#         user_email = frappe.session.user

#         if user_email == "Guest":
#             frappe.throw("You must be logged in to update a travel zone.")

#         # Fetch the existing Travel Zone
#         travel_zone = frappe.get_doc("Travel Zone", name)
#         if not travel_zone:
#             frappe.throw("Travel Zone not found.")

#         # Check if the logged-in user is the owner of the Travel Zone
#         guide = frappe.get_value("Guide", {"email": user_email}, "name")
#         if travel_zone.guide != guide:
#             frappe.throw("You do not have permission to update this Travel Zone.")

#         # Extract and validate data
#         district = kwargs.get("district")
#         areas = kwargs.get("areas")  # List of areas (from the frontend)
#         description = kwargs.get("description")

#         if not all([district, areas, description]):
#             frappe.throw("Please fill all required fields.")

#         if not isinstance(areas, list) or len(areas) == 0:
#             frappe.throw("Please select at least one area.")

#         # Validate that the areas exist in the Area doctype
#         for area in areas:
#             if not frappe.db.exists("Area", area):
#                 frappe.throw(f"Area '{area}' does not exist in the system.")

#         # Update the Travel Zone
#         travel_zone.update({
#             "district": district,
#             "description": description,
#         })
#         # Clear existing areas in the child table
#         travel_zone.set("areas", [])
#         # Add new areas to the child table
#         for area in areas:
#             travel_zone.append("areas", {"area": area})
#         travel_zone.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Travel Zone updated successfully!",
#         }

#     except Exception as e:
#         frappe.logger().error(f"Error in update_travel_zone: {frappe.get_traceback()}")
#         frappe.throw(f"An error occurred while updating the Travel Zone: {str(e)}")
        
@frappe.whitelist(methods=['GET'])
def get_travel_zone(name=None):
    try:
        user_email = frappe.session.user
        if user_email == "Guest":
            frappe.throw("You must be logged in to fetch travel zone details.")

        guide = frappe.get_value("Guide", {"email": user_email}, "name")
        if not guide:
            frappe.throw("Guide profile not found.")

        filters = {"guide": guide}
        if name:
            filters["name"] = name

        travel_zone = frappe.get_all("Travel Zone", filters=filters, fields=["*"], limit=1)
        if travel_zone:
            travel_zone_doc = frappe.get_doc("Travel Zone", travel_zone[0].name)
            areas = [row.area for row in travel_zone_doc.areas] if travel_zone_doc.areas else []
            frappe.logger().info(f"Fetched areas: {areas}")  # Debugging log
            return {
                "status": "success",
                "data": {
                    "district": travel_zone_doc.district,
                    "areas": areas,  # Fetch areas as a list
                    "description": travel_zone_doc.description,
                },
            }
        else:
            return {
                "status": "success",
                "data": None,
                "message": "No travel zone found for this guide.",
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching Travel Zone")
        frappe.throw("An error occurred while fetching the Travel Zone. Please try again.")

@frappe.whitelist(methods=['DELETE'])
def delete_travel_zone(name):
    """
    Delete a Travel Zone record.
    """
    try:
        frappe.logger().info(f"delete_travel_zone called with name: {name}")
        user_email = frappe.session.user

        # Ensure the user is logged in
        if user_email == "Guest":
            frappe.throw("You must be logged in to delete a travel zone.")

        # Fetch the Travel Zone
        travel_zone = frappe.get_doc("Travel Zone", name)
        if not travel_zone:
            frappe.throw("Travel Zone not found.")

        # Check if the logged-in user is the owner of the Travel Zone
        guide = frappe.get_value("Guide", {"email": user_email}, "name")
        if travel_zone.guide != guide:
            frappe.throw("You do not have permission to delete this Travel Zone.")

        # Delete the Travel Zone
        frappe.delete_doc("Travel Zone", name, ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Travel Zone deleted successfully!",
        }

    except Exception as e:
        frappe.logger().error(f"Error in delete_travel_zone: {frappe.get_traceback()}")
        frappe.throw(f"An error occurred while deleting the Travel Zone: {str(e)}")

# @frappe.whitelist(allow_guest=False, methods=['GET'])
# def get_guides_by_district(district):
#     """
#     Fetch guides and their Travel Zones for a given district.
#     """
#     try:
#         # Fetch Travel Zones linked to the selected district
#         travel_zones = frappe.get_all(
#             "Travel Zone",
#             filters={"district": district},
#             fields=["name", "guide", "district", "description"]
#         )

#         if not travel_zones:
#             return {
#                 "status": "success",
#                 "guides": [],
#                 "message": "No guides found for the selected district."
#             }

#         # Fetch guide details for each Travel Zone
#         guides = []
#         for zone in travel_zones:
#             guide = frappe.get_doc("Guide", zone.guide)
#             guides.append({
#                 "guide_name": guide.full_name,
#                 "experience": guide.experience,
#                 "language_spoken": guide.language_spoken,
#                 "rating": guide.rating,
#                 "travel_zone": zone.description,
#                 "district": zone.district
#             })

#         return {
#             "status": "success",
#             "guides": guides
#         }
#     except Exception as e:
#         frappe.logger().error(f"Error fetching guides: {frappe.get_traceback()}")
#         return {
#             "status": "error",
#             "message": "An error occurred while fetching guides. Please try again."
#         }

@frappe.whitelist(allow_guest=False, methods=['GET'])
def get_guides_by_district(district):
    """
    Fetch guides and their Travel Zones for a given district.
    """
    try:
        if not district:
            return {
                "status": "error",
                "message": "District is required."
            }

        # Fetch Travel Zones linked to the selected district
        travel_zones = frappe.get_all(
            "Travel Zone",
            filters={"district": district},
            fields=["name", "guide", "district", "description"],
            limit=50  # Limit the number of results for performance
        )

        if not travel_zones:
            return {
                "status": "success",
                "guides": [],
                "message": "No guides found for the selected district."
            }

        # Fetch guide details for each Travel Zone
        guides = []
        for zone in travel_zones:
            guide = frappe.get_doc("Guide", zone.guide)
            guides.append({
                "guide_name": guide.full_name,
                "experience": guide.experience,
                "language_spoken": guide.language_spoken,
                "rating": guide.rating,
                "travel_zone": zone.description,
                "district": zone.district
            })

        return {
            "status": "success",
            "guides": guides
        }
    except Exception as e:
        frappe.logger().error(f"Error fetching guides: {frappe.get_traceback()}")
        return {
            "status": "error",
            "message": "An error occurred while fetching guides. Please try again."
        }

# @frappe.whitelist()
# def get_guide_details(guide):
#     """
#     Fetch guide details, including areas from the TZ Areas child table.
#     """
#     if not guide:
#         frappe.throw("Guide is required.")

#     # Fetch guide details
#     guide_details = frappe.get_doc("Guide", guide).as_dict()

#     # Fetch travel zones for the guide
#     travel_zones = frappe.get_all(
#         "Travel Zone",
#         filters={"guide": guide},
#         fields=["name", "district", "description"]
#     )

#     # Fetch areas for each travel zone from the TZ Areas child table
#     for travel_zone in travel_zones:
#         travel_zone["areas"] = frappe.get_all(
#             "TZ Areas",  # Correct child table name
#             filters={"parent": travel_zone["name"]},
#             fields=["area"]
#         )

#     # Add travel zones and areas to guide details
#     guide_details["travel_zones"] = travel_zones

#     return {
#         "status": "success",
#         "data": guide_details
#     }

@frappe.whitelist(allow_guest=False, methods=['GET'])
def get_guides_by_district_booking(district, start_date=None, end_date=None, page=1, page_size=10):
    """
    Fetch guides for a given district, along with their availability for booking.
    """
    try:
        if not district:
            return {
                "status": "error",
                "message": "District is required."
            }

        # Calculate start and end for pagination
        start = (page - 1) * page_size
        end = start + page_size

        # Fetch guides and their travel zones for the district
        guides = frappe.db.sql("""
            SELECT g.name AS guide_id, g.full_name AS guide_name, g.experience, g.language_spoken, g.rating,
                   tz.description AS travel_zone, tz.district
            FROM `tabGuide` g
            JOIN `tabTravel Zone` tz ON tz.guide = g.name
            WHERE tz.district = %s
            LIMIT %s, %s
        """, (district, start, page_size), as_dict=True)

        if not guides:
            return {
                "status": "success",
                "guides": [],
                "message": "No guides found for the selected district."
            }

        # If start_date and end_date are provided, check guide availability
        if start_date and end_date:
            for guide in guides:
                # Check if the guide has any CONFIRMED bookings for these dates
                overlapping_bookings = frappe.db.sql("""
                    SELECT name
                    FROM `tabBooking`
                    WHERE guide = %s
                    AND start_date <= %s
                    AND end_date >= %s
                    AND status = 'Confirmed'
                """, (guide["guide_id"], end_date, start_date), as_dict=True)

                guide["available"] = not bool(overlapping_bookings)

        return {
            "status": "success",
            "guides": guides
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching guides for booking")
        return {
            "status": "error",
            "message": "An error occurred while fetching guides for booking. Please try again."
        }

@frappe.whitelist()
def get_guide_details(guide):
    """Fetch guide details, including daily rates from the TZ Areas child table."""
    try:
        if not guide:
            return {"status": "error", "message": "Guide is required."}

        if not frappe.db.exists("Guide", guide):
            return {"status": "error", "message": "Guide not found."}

        guide_details = frappe.get_doc("Guide", guide).as_dict()

        # Fetch travel zones with daily rates
        travel_zones = frappe.get_all(
            "Travel Zone",
            filters={"guide": guide},
            fields=["name", "district", "description", "daily_rate"]
        )

        # Fetch areas for each travel zone
        for travel_zone in travel_zones:
            travel_zone["areas"] = frappe.get_all(
                "TZ Areas",
                filters={"parent": travel_zone["name"]},
                fields=["area"]
            )
            # Ensure daily_rate is properly formatted
            travel_zone["daily_rate"] = flt(travel_zone.get("daily_rate", 0))

        guide_details["travel_zones"] = travel_zones

        return {
            "status": "success",
            "data": guide_details
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching guide details")
        return {"status": "error", "message": str(e)}
    
@frappe.whitelist(allow_guest=False)
def create_booking(**kwargs):
    """
    Create a new booking with proper success/error messaging
    Returns:
        dict: {
            "status": "success"|"error",
            "message": str,
            "booking_id": str (if successful),
            "booking_details": dict (if successful),
            "pricing_details": dict (if successful)
        }
    """
    try:
        # Parse the incoming data with strict validation
        booking_data = frappe._dict(kwargs)
        
        # Validate required fields with more detailed messages
        required_fields = [
            ('traveler', 'Traveler information is required'),
            ('guide', 'Guide selection is required'),
            ('start_date', 'Start date is required'),
            ('end_date', 'End date is required'),
            ('district', 'District selection is required'),
            ('area', 'Area selection is required')
        ]
        
        missing_fields = []
        for field, message in required_fields:
            if not booking_data.get(field):
                missing_fields.append(message)
        
        if missing_fields:
            frappe.response['http_status_code'] = 400
            return {
                "status": "error",
                "message": " ".join(missing_fields)
            }

        # Get the daily rate from the guide's travel zone for this district
        daily_rate = 0
        try:
            travel_zone = frappe.get_all(
                "Travel Zone",
                filters={
                    "guide": booking_data.guide,
                    "district": booking_data.district
                },
                fields=["daily_rate"],
                limit=1
            )
            
            if travel_zone and travel_zone[0].get("daily_rate"):
                daily_rate = flt(travel_zone[0].get("daily_rate"))
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Failed to fetch daily rate")
            daily_rate = 0

        # Calculate total amount
        total_amount = 0
        try:
            start_date = getdate(booking_data.start_date)
            end_date = getdate(booking_data.end_date)
            num_days = (end_date - start_date).days + 1
            total_amount = daily_rate * num_days
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Failed to calculate total amount")
            total_amount = 0

        # Validate and parse fellow travelers with better error handling
        fellow_travelers = []
        if booking_data.get('fellow_travelers'):
            try:
                fellow_travelers = frappe.parse_json(booking_data.fellow_travelers)
                if not isinstance(fellow_travelers, list):
                    frappe.response['http_status_code'] = 400
                    return {
                        "status": "error",
                        "message": "Fellow travelers data should be a list"
                    }
                
                # Validate each traveler's data
                for i, traveler in enumerate(fellow_travelers, 1):
                    if not isinstance(traveler, dict):
                        raise ValueError(f"Traveler #{i} is not a valid object")
                    if not traveler.get('full_name'):
                        raise ValueError(f"Traveler #{i} is missing full name")
                    if not traveler.get('age') or not str(traveler.get('age')).isdigit():
                        raise ValueError(f"Traveler #{i} has invalid age")
                    
            except ValueError as e:
                frappe.response['http_status_code'] = 400
                return {
                    "status": "error",
                    "message": f"Invalid fellow travelers data: {str(e)}"
                }
            except Exception as e:
                frappe.response['http_status_code'] = 400
                return {
                    "status": "error",
                    "message": "Failed to process fellow travelers data"
                }

        # Validate dates with more comprehensive checks
        try:
            start_date = getdate(booking_data.start_date)
            end_date = getdate(booking_data.end_date)
            today = getdate(nowdate())
            
            if start_date < today:
                frappe.response['http_status_code'] = 400
                return {
                    "status": "error",
                    "message": "Start date cannot be in the past"
                }
                
            if start_date > end_date:
                frappe.response['http_status_code'] = 400
                return {
                    "status": "error", 
                    "message": "End date must be after start date"
                }
                
            if (end_date - start_date).days > 30:  # Example: Limit booking to 30 days max
                frappe.response['http_status_code'] = 400
                return {
                    "status": "error",
                    "message": "Booking duration cannot exceed 30 days"
                }
                
        except Exception as e:
            frappe.response['http_status_code'] = 400
            return {
                "status": "error",
                "message": "Invalid date format. Please use YYYY-MM-DD format"
            }

        # Enhanced guide availability check
        try:
            overlapping_bookings = frappe.get_all("Booking", 
                filters={
                    "guide": booking_data.guide,
                    "start_date": ["<=", end_date],
                    "end_date": [">=", start_date],
                    "status": ["in", ["Confirmed", "Pending"]],
                    "name": ["!=", booking_data.get("name", "")]
                },
                fields=["name", "start_date", "end_date", "status"],
                limit=1
            )

            if overlapping_bookings:
                frappe.response['http_status_code'] = 409
                conflict = overlapping_bookings[0]
                return {
                    "status": "error",
                    "message": f"Guide is already booked from {conflict.start_date} to {conflict.end_date}",
                    "conflict_details": conflict
                }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Guide Availability Check Failed")
            frappe.response['http_status_code'] = 500
            return {
                "status": "error",
                "message": "Could not verify guide availability"
            }

        # Create booking document with transaction handling
        try:
            booking = frappe.get_doc({
                "doctype": "Booking",
                "traveler": booking_data.traveler,
                "guide": booking_data.guide,
                "start_date": start_date,
                "end_date": end_date,
                "daily_rate": daily_rate,  # Add daily rate to booking
                "total_amount": total_amount,  # Add calculated total amount
                "num_travelers": booking_data.get('num_travelers', 1),
                "notes": booking_data.get('notes', ''),
                "district": booking_data.district,
                "area": booking_data.area,
                "status": "Pending",
                "payment_status": "Unpaid"
            })

            # Add fellow travelers if provided
            if fellow_travelers:
                for traveler in fellow_travelers:
                    booking.append("fellow_travelers", {
                        "full_name": traveler.get('full_name'),
                        "age": int(traveler.get('age')),
                        "gender": traveler.get('gender', 'Other'),
                        "relation": traveler.get('relation', 'Other'),
                        "contact_number": traveler.get('contact_number', '')
                    })

            booking.insert(ignore_permissions=True)
            
            # Send notification to guide
            send_booking_notification(booking)
            
            frappe.db.commit()

            return {
                "status": "success",
                "message": "🎉 Your booking request has been submitted!",
                "booking_id": booking.name,
                "booking_details": {
                    "reference": booking.name,
                    "guide": booking.guide,
                    "traveler": booking.traveler,
                    "dates": f"{booking.start_date} to {booking.end_date}",
                    "num_travelers": booking.num_travelers,
                    "status": booking.status,
                    "district": booking.district,
                    "area": booking.area
                },
                "pricing_details": {
                    "daily_rate": daily_rate,
                    "total_amount": total_amount,
                    "num_days": (end_date - start_date).days + 1
                }
            }

        # except frappe.DuplicateEntryError:
        #     frappe.response['http_status_code'] = 409
        #     return {
        #         "status": "error",
        #         "message": "This booking already exists"
        #     }
            
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), "Booking Creation Failed")
            frappe.response['http_status_code'] = 500
            return {
                "status": "error",
                "message": "Failed to create booking. Please try again."
            }

    except Exception as e:
        frappe.response['http_status_code'] = 500
        frappe.log_error(frappe.get_traceback(), "Booking API Error")
        return {
            "status": "error",
            "message": "An unexpected error occurred. Please try again later."
        }

def send_booking_notification(booking):
    """Send notification to guide about new booking request"""
    try:
        guide_email = frappe.db.get_value("Guide", booking.guide, "email")
        traveler_name = frappe.db.get_value("Traveler", booking.traveler, "full_name")
        
        if guide_email:
            subject = f"New Booking Request from {traveler_name}"
            message = f"""
                <p>You have a new booking request from {traveler_name}:</p>
                <ul>
                    <li>Dates: {booking.start_date} to {booking.end_date}</li>
                    <li>Location: {booking.district}, {booking.area}</li>
                    <li>Number of travelers: {booking.num_travelers}</li>
                    <li>Daily Rate: {frappe.format(booking.daily_rate, 'Currency')}</li>
                    <li>Total Amount: {frappe.format(booking.total_amount, 'Currency')}</li>
                </ul>
                <p>Please review this request in your dashboard.</p>
            """
            
            frappe.sendmail(
                recipients=[guide_email],
                subject=subject,
                message=message,
                now=True
            )
            
            # Create system notification
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": frappe.db.get_value("Guide", booking.guide, "user"),
                "type": "Alert",
                "document_type": "Booking",
                "document_name": booking.name,
                "from_user": frappe.session.user
            }).insert(ignore_permissions=True)
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to send booking notification")
    
# @frappe.whitelist()
# def check_guide_availability(guide, start_date, end_date):
#     """
#     Check if the guide is available for the requested dates.
#     """
#     try:
#         # Convert string dates to datetime objects
#         start_date = datetime.strptime(start_date, "%Y-%m-%d")
#         end_date = datetime.strptime(end_date, "%Y-%m-%d")

#         # Check for overlapping bookings
#         bookings = frappe.get_all("Booking", filters={
#             "guide": guide,
#             "start_date": ["<=", end_date],
#             "end_date": [">=", start_date],
#             "status": ["!=", "Cancelled"]  # Ignore cancelled bookings
#         })

#         if bookings:
#             return {
#                 "status": "unavailable",
#                 "message": "Guide is not available for the selected dates.",
#                 "conflicting_bookings": bookings
#             }
#         else:
#             return {
#                 "status": "available",
#                 "message": "Guide is available for the selected dates."
#             }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Error checking guide availability")
#         return {
#             "status": "error",
#             "message": "An error occurred while checking availability."
#         }
        
@frappe.whitelist()
def get_traveler_for_user(user):
    try:
        # Fetch the Traveler record linked to the user
        traveler = frappe.get_value("Traveler", {"user": user}, "name")
        if traveler:
            return {"status": "success", "traveler": traveler}
        else:
            return {"status": "error", "message": "No traveler found for the user."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching traveler for user")
        return {"status": "error", "message": "An error occurred while fetching traveler."}

@frappe.whitelist()
def get_guide_for_user(user):
    try:
        # Fetch the Guide record linked to the user
        guide = frappe.get_value("Guide", {"email": user}, "name")
        if guide:
            return {"status": "success", "guide": guide}
        else:
            return {"status": "error", "message": "No guide found for the user."}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching guide for user")
        return {"status": "error", "message": "An error occurred while fetching guide."}

@frappe.whitelist()
def update_booking_status(booking_id, status):
    """Update booking status with additional validation"""
    try:
        if not booking_id or not status:
            return {"status": "error", "message": "Missing required parameters"}

        if status not in ["Confirmed", "Cancelled"]:
            return {"status": "error", "message": "Invalid status"}

        booking = frappe.get_doc("Booking", booking_id)
        if not booking:
            return {"status": "error", "message": "Booking not found"}

        # Prevent modifying non-pending bookings
        if booking.status != "Pending":
            return {
                "status": "error", 
                "message": f"Cannot modify a {booking.status} booking"
            }

        # Update status
        booking.status = status
        booking.save(ignore_permissions=True)

        # If confirming, cancel overlapping pending bookings
        if status == "Confirmed":
            overlapping = frappe.get_all("Booking",
                filters={
                    "guide": booking.guide,
                    "start_date": ["<=", booking.end_date],
                    "end_date": [">=", booking.start_date],
                    "status": "Pending",
                    "name": ["!=", booking.name]
                },
                pluck="name"
            )

            for booking_id in overlapping:
                frappe.db.set_value("Booking", booking_id, "status", "Cancelled")

        frappe.db.commit()

        # Send notification to traveler
        if frappe.db.exists("Notification Settings", booking.traveler):
            notify_traveler(booking_id, status)

        return {"status": "success", "message": f"Booking {status.lower()} successfully"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Error in update_booking_status")
        return {"status": "error", "message": str(e)}

def notify_traveler(booking_id, status):
    """Send notification to traveler about booking status change"""
    try:
        booking = frappe.get_doc("Booking", booking_id)
        traveler = frappe.get_doc("Traveler", booking.traveler)
        
        subject = f"Your booking has been {status.lower()}"
        message = f"""
            <p>Your booking with {booking.guide} for {booking.start_date} to {booking.end_date} 
            has been <strong>{status.lower()}</strong>.</p>
            
            <p>Booking Reference: {booking.name}</p>
            
            {f"<p>Reason: {booking.rejection_reason}</p>" if status == "Cancelled" and booking.rejection_reason else ""}
        """

        frappe.sendmail(
            recipients=[traveler.email],
            subject=subject,
            message=message,
            now=True
        )
        
        # Create system notification
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": subject,
            "for_user": traveler.user,
            "type": "Alert",
            "document_type": "Booking",
            "document_name": booking.name,
            "from_user": frappe.session.user
        }).insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to send booking notification")

@frappe.whitelist()
def reject_booking_with_reason(booking_id, reason):
    """Reject booking with a specific reason"""
    try:
        if not booking_id:
            return {"status": "error", "message": "Booking ID required"}

        booking = frappe.get_doc("Booking", booking_id)
        if not booking:
            return {"status": "error", "message": "Booking not found"}

        booking.status = "Cancelled"
        booking.rejection_reason = reason
        booking.save(ignore_permissions=True)
        frappe.db.commit()

        notify_traveler(booking_id, "Cancelled")
        
        return {"status": "success", "message": "Booking rejected successfully"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Error in reject_booking_with_reason")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_booking_requests(guide):
    """
    Fetch booking requests for the logged-in guide without area field
    """
    try:
        if not guide:
            return {
                "status": "error",
                "message": "Guide is required."
            }

        bookings = frappe.get_all("Booking", 
            filters={
                "guide": guide,
                "status": ["in", ["Pending", "Confirmed", "Cancelled"]]
            }, 
            fields=["name", "traveler", "start_date", "end_date", 
                   "num_travelers", "notes", "status", "district"]
        )

        return {
            "status": "success",
            "bookings": bookings
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching booking requests")
        return {
            "status": "error",
            "message": "An error occurred while fetching booking requests. Please try again."
        }

@frappe.whitelist()
def get_fellow_travelers_for_bookings(booking_ids):
    """
    Fetch fellow travelers through Booking doctype (parent-child relationship)
    """
    try:
        if not booking_ids:
            return {"status": "error", "message": "Booking IDs required"}
            
        if isinstance(booking_ids, str):
            booking_ids = frappe.parse_json(booking_ids)

        fellow_travelers = {}
        
        for booking_id in booking_ids:
            # Get the booking document
            booking = frappe.get_doc("Booking", booking_id)
            
            # Initialize empty list for this booking
            travelers = []
            
            # Access fellow travelers through the booking document
            if hasattr(booking, 'fellow_travelers'):
                for traveler in booking.fellow_travelers:
                    travelers.append({
                        'full_name': traveler.full_name,
                        'age': traveler.age,
                        'gender': traveler.gender,
                        'relation': traveler.relation,
                        'contact_number': traveler.contact_number
                    })
            
            fellow_travelers[booking_id] = travelers

        return {
            "status": "success",
            "fellow_travelers": fellow_travelers
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error fetching fellow travelers")
        return {
            "status": "error",
            "message": str(e)
        }
    
@frappe.whitelist()
def get_traveler_bookings(traveler_email):
    try:
        traveler_name = frappe.db.get_value("Traveler", {"email": traveler_email}, "name")
        if not traveler_name:
            return {"status": "error", "message": "Traveler not found"}

        bookings = frappe.get_all("Booking",
            filters={"traveler": traveler_name},
            fields=["name", "guide", "start_date", "end_date", 
                   "num_travelers", "notes", "status", "district", "area",
                   "rejection_reason", "traveler", "is_reviewable", "review_link",
                   "payment_status", "total_amount"],
            order_by="start_date desc"
        )

        today = frappe.utils.getdate(frappe.utils.nowdate())
        
        for booking in bookings:
            booking["guide_name"] = frappe.db.get_value("Guide", booking["guide"], "full_name")
            
            # Auto-mark as reviewable if completed in last 7 days
            if booking.status == "Completed" and not booking.review_link:
                # Ensure end_date is a date object
                end_date = frappe.utils.getdate(booking.end_date) if booking.end_date else None
                if end_date:
                    days_passed = (today - end_date).days
                    if days_passed <= 7:
                        frappe.db.set_value("Booking", booking.name, "is_reviewable", 1)
                        booking.is_reviewable = 1

        return {"status": "success", "bookings": bookings}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Booking fetch error")
        return {"status": "error", "message": str(e)}
 
@frappe.whitelist()
def submit_review(booking_id, rating, review_text=""):
    """Submit a review for a completed trip and update guide's average rating"""
    try:
        # Validate booking and rating
        booking = frappe.get_doc("Booking", booking_id)
        if booking.status != "Completed":
            return {"status": "error", "message": "Only completed trips can be reviewed"}
            
        rating = float(rating)
        if rating < 1 or rating > 5:
            return {"status": "error", "message": "Rating must be between 1 and 5"}
            
        # Check if review already exists for this booking
        if frappe.db.exists("Review", {"booking": booking_id}):
            return {"status": "error", "message": "Review already submitted for this booking"}

        # Get current guide rating data
        guide = frappe.get_doc("Guide", booking.guide)
        current_rating = guide.rating or 0
        total_reviews = frappe.db.count("Review", {"guide": booking.guide, "docstatus": 0})
        
        # Calculate new average rating (weighted average)
        if total_reviews > 0:
            new_rating = ((current_rating * total_reviews) + rating) / (total_reviews + 1)
        else:
            new_rating = rating  # First review

        # Create review with correct field name (review_text instead of comment)
        review = frappe.get_doc({
            "doctype": "Review",
            "booking": booking.name,
            "traveler": booking.traveler,
            "traveler_name": frappe.db.get_value("Traveler", booking.traveler, "full_name"),
            "guide": booking.guide,
            "guide_name": guide.full_name,
            "rating": rating,
            "review_text": review_text,  # Using correct field name
            "review_date": frappe.utils.nowdate(),
            "trip_date": booking.start_date  # Added trip date from booking
        }).insert(ignore_permissions=True)
        
        # Update booking
        frappe.db.set_value("Booking", booking.name, {
            "is_reviewable": 0,
            "review_link": review.name
        })
        
        # Update guide with new rating and review count
        frappe.db.set_value("Guide", booking.guide, {
            "rating": round(new_rating, 1),
            "total_reviews": total_reviews + 1,
            "last_review_date": frappe.utils.nowdate()
        })
        
        # Return success with additional data
        return {
            "status": "success", 
            "review_id": review.name,
            "new_rating": round(new_rating, 1),
            "total_reviews": total_reviews + 1,
            "guide_name": guide.full_name
        }
        
    except Exception as e:
        frappe.log_error(
            title="Review submission failed",
            message=f"Booking: {booking_id}\nError: {str(e)}\nTraceback: {frappe.get_traceback()}"
        )
        return {"status": "error", "message": f"Error submitting review: {str(e)}"}
    
@frappe.whitelist()
def get_guide_bookings(guide_email):
    """Get all bookings for a guide"""
    try:
        guide_name = frappe.db.get_value("Guide", {"email": guide_email}, "name")
        if not guide_name:
            return {"status": "error", "message": "Guide not found"}

        bookings = frappe.get_all("Booking",
            filters={"guide": guide_name},
            fields=["name", "traveler", "start_date", "end_date", 
                   "num_travelers", "notes", "status", "district", "area",
                   "rejection_reason", "is_reviewable", "review_link",
                   "payment_status", "total_amount"],
            order_by="start_date desc"
        )

        # Add traveler names
        for booking in bookings:
            booking["traveler_name"] = frappe.db.get_value("Traveler", booking["traveler"], "full_name")

        return {"status": "success", "bookings": bookings}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Guide bookings fetch error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_guide_reviews(guide_email):
    """Get all reviews for a guide using correct field names from doctype"""
    try:
        if not guide_email:
            frappe.log_error("No guide email provided", "get_guide_reviews")
            return {"status": "error", "message": "Guide email is required"}

        # Get guide document
        guide = frappe.get_doc("Guide", {"email": guide_email})
        if not guide:
            return {"status": "error", "message": "Guide not found"}

        # Get reviews with exact field names from doctype
        reviews = frappe.get_all("Review",
            filters={"guide": guide.name},
            fields=[
                "name",
                "traveler",
                "traveler_name",
                "guide",
                "guide_name",
                "rating",
                "review_text",  # Correct field name from doctype
                "review_date",
                "booking",
                "trip_date",
                "guide_reply",
                "reply_date"
            ],
            order_by="review_date desc"
        )

        return {
            "status": "success",
            "reviews": reviews,
            "guide_name": guide.full_name
        }

    except Exception as e:
        frappe.log_error(
            title="Failed to fetch guide reviews",
            message=f"Guide Email: {guide_email}\nError: {str(e)}\nTraceback: {frappe.get_traceback()}"
        )
        return {
            "status": "error", 
            "message": f"Error loading reviews: {str(e)}"
        }

@frappe.whitelist()
def submit_review_reply(review_id, reply):
    """Submit a guide's reply to a review"""
    try:
        if not review_id or not reply:
            return {"status": "error", "message": "Review ID and reply are required"}

        review = frappe.get_doc("Review", review_id)
        review.guide_reply = reply
        review.reply_date = frappe.utils.nowdate()
        review.save(ignore_permissions=True)
        
        return {"status": "success", "message": "Reply submitted successfully"}
        
    except Exception as e:
        frappe.log_error(
            title="Failed to submit review reply",
            message=f"Review ID: {review_id}\nError: {str(e)}\nTraceback: {frappe.get_traceback()}"
        )
        return {"status": "error", "message": f"Error submitting reply: {str(e)}"}

# @frappe.whitelist()
# def submit_guide_reply(review_id, reply_text):
#     try:
#         review = frappe.get_doc("Review", review_id)
        
#         # Validate guide ownership
#         if frappe.session.user != frappe.db.get_value("Guide", review.guide, "user"):
#             frappe.throw("You can only reply to your own reviews")
        
#         review.guide_reply = reply_text
#         review.reply_date = frappe.utils.now_datetime()
#         review.save(ignore_permissions=True)
        
#         return {"status": "success"}
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Guide Reply Failed")
#         return {"status": "error", "message": str(e)}
    
# @frappe.whitelist(allow_guest=True)
# def payment_webhook():
#     try:
#         payload = frappe.request.get_json()
        
#         if payload.get("event") == "payment.captured":
#             booking_id = payload.get("payload").get("payment").get("notes", {}).get("booking")
            
#             payment = frappe.new_doc("Payment")
#             payment.update({
#                 "booking": booking_id,
#                 "status": "Completed",
#                 "transaction_id": payload.get("payload").get("payment").get("id"),
#                 "payment_gateway_response": frappe.as_json(payload),
#                 "receipt_url": payload.get("payload").get("payment").get("receipt"),
#                 "capture_status": "Captured",
#                 "captured_amount": payload.get("payload").get("payment").get("amount")/100,
#                 "capture_date": now_datetime()
#             })
#             payment.insert(ignore_permissions=True)
#             payment.submit()
            
#             return {"status": "success"}
    
#     except Exception as e:
#         frappe.log_error("Payment Webhook Failed", str(e))
#         return {"status": "error"}
    
# @frappe.whitelist()
# def get_booking_payment_details(booking_id):
#     try:
#         booking = frappe.get_doc("Booking", booking_id)
        
#         if booking.status != "Confirmed":
#             frappe.throw("Only confirmed bookings can be paid for")
            
#         return {
#             "status": "success",
#             "booking": {
#                 "name": booking.name,
#                 "guide_name": frappe.db.get_value("Guide", booking.guide, "full_name"),
#                 "start_date": booking.start_date.strftime("%d %b %Y"),
#                 "end_date": booking.end_date.strftime("%d %b %Y"),
#                 "total_amount": booking.total_amount
#             }
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Payment Details Error")
#         return {"status": "error", "message": str(e)}

# @frappe.whitelist()
# def initiate_payment(booking_id, payment_method):
#     try:
#         booking = frappe.get_doc("Booking", booking_id)
        
#         # Create Payment Request
#         pr = frappe.new_doc("Payment Request")
#         pr.update({
#             "reference_doctype": "Booking",
#             "reference_name": booking.name,
#             "subject": f"Payment for Booking {booking.name}",
#             "grand_total": booking.total_amount,
#             "payment_gateway": "Razorpay" if payment_method == "razorpay" else "UPI",
#             "email_to": frappe.db.get_value("Traveler", booking.traveler, "email")
#         })
#         pr.insert(ignore_permissions=True)
        
#         return {
#             "status": "success",
#             "payment_url": pr.get_payment_url()
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Payment Initiation Failed")
#         return {"status": "error", "message": str(e)}
    
# @frappe.whitelist()
# def mark_as_paid(booking_id, amount, method, details=None):
#     """Mark a booking as paid and create payment record"""
#     try:
#         # Standardize payment method first
#         method = method.strip().title()  # Converts "card" → "Card", "upi" → "Upi"
        
#         # Manually handle special cases
#         if method.lower() == "upi":
#             method = "UPI"
#         elif method.lower() in ["bank", "bank transfer"]:
#             method = "Bank Transfer"
        
#         # Validate payment method
#         valid_methods = ["Card", "UPI", "Bank Transfer", "Cash"]
#         if method not in valid_methods:
#             frappe.throw(f'Payment Method must be one of: {", ".join(valid_methods)}')

#         # Rest of your existing code...
#         payment = frappe.new_doc("Payment")
#         payment.update({
#             # ...
#             "payment_method": method,  # Use the standardized value
#             # ...
#         })

#         # Update method-specific checks to use standardized values
#         if method == "Card":
#             payment.update({
#                 "card_last_4": details.get("cardNumber", "")[-4:] if details else None,
#                 "card_type": "Credit/Debit"
#             })
#         elif method == "UPI":  # Now uppercase
#             payment.update({
#                 "upi_id": details.get("upiId") if details else None
#             })
#         elif method == "Bank Transfer":  # Full name
#             payment.update({
#                 "bank_reference": details.get("transactionRef") if details else None
#             })

#         payment.insert(ignore_permissions=True)
#         payment.submit()

#         # Update booking status
#         frappe.db.set_value("Booking", booking.name, {
#             "payment_status": "Paid",
#             "payment_reference": payment.name
#         })

#         # Send payment confirmation email
#         send_payment_confirmation(booking, payment)

#         return {
#             "status": "success",
#             "message": "Payment recorded successfully",
#             "payment_id": payment.name
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Payment Processing Error")
#         frappe.db.rollback()
#         return {
#             "status": "error",
#             "message": str(e)
#         }

# def send_payment_confirmation(booking, payment):
#     """Send payment confirmation email to traveler"""
#     try:
#         traveler = frappe.get_doc("Traveler", booking.traveler)
#         guide = frappe.get_doc("Guide", booking.guide)

#         subject = f"Payment Confirmation for Booking {booking.name}"
        
#         message = f"""
#             <p>Dear {traveler.full_name},</p>
            
#             <p>We have successfully received your payment of <strong>₹{payment.amount}</strong> 
#             for your booking with {guide.full_name}.</p>
            
#             <p><strong>Booking Details:</strong></p>
#             <ul>
#                 <li>Booking Reference: {booking.name}</li>
#                 <li>Dates: {booking.start_date} to {booking.end_date}</li>
#                 <li>Location: {booking.district}, {booking.area}</li>
#                 <li>Payment Method: {payment.payment_method}</li>
#                 <li>Payment Date: {payment.payment_date}</li>
#             </ul>
            
#             <p>Thank you for using Travomate!</p>
#         """

#         frappe.sendmail(
#             recipients=[traveler.email],
#             subject=subject,
#             message=message,
#             now=True
#         )

#         # Also notify guide
#         if frappe.db.exists("Notification Settings", guide.name):
#             guide_message = f"""
#                 <p>Payment received for booking {booking.name} from {traveler.full_name}.</p>
#                 <p>Amount: ₹{payment.amount}</p>
#                 <p>Payment Method: {payment.payment_method}</p>
#             """
#             frappe.sendmail(
#                 recipients=[guide.email],
#                 subject=f"Payment Received for Booking {booking.name}",
#                 message=guide_message,
#                 now=True
#             )

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Failed to send payment confirmation")

@frappe.whitelist()
def create_travel_payment(booking=None, amount=0, payment_method="Cash", payment_details=None):
    """Create a Travel Payment record (all fields optional)"""
    try:
        # Standardize and validate payment method
        valid_methods = ["Card", "UPI", "Bank Transfer", "Cash"]
        
        # Convert to title case and handle special cases
        payment_method = payment_method.strip().title()  # "card" -> "Card", "upi" -> "Upi"
        if payment_method.lower() == "upi":
            payment_method = "UPI"
        elif payment_method.lower() in ["bank", "bank transfer"]:
            payment_method = "Bank Transfer"
            
        # Validate against allowed methods
        if payment_method not in valid_methods:
            frappe.throw(f'Payment Method must be one of: {", ".join(valid_methods)}')

        # Validate amount
        if not isinstance(amount, (int, float)) or float(amount) <= 0:
            frappe.throw("Amount must be a positive number")

        payment = frappe.new_doc("Travel Payment")
        
        # Convert stringified JSON if needed
        if isinstance(payment_details, str):
            try:
                payment_details = frappe.parse_json(payment_details)
            except:
                payment_details = None
        
        # Set basic fields
        payment.update({
            "booking": booking,
            "amount": flt(amount),
            "payment_method": payment_method,  # Use standardized value
            "status": "Completed"
        })
        
        # Set method-specific details with standardized comparisons
        if payment_method == "Card" and payment_details:
            card_last_4 = str(payment_details.get("card_last_4", "")).strip()
            if len(card_last_4) >= 4:
                payment.card_reference = card_last_4[-4:]
            if payment_details.get("card_name"):
                payment.card_reference = f"{payment.card_reference or ''} ({payment_details['card_name']})".strip()
                
        elif payment_method == "UPI" and payment_details:
            payment.upi_id = str(payment_details.get("upi_id", "")).strip()
            
        elif payment_method == "Bank Transfer" and payment_details:
            payment.bank_reference = str(payment_details.get("bank_reference", "")).strip()
        
        payment.insert(ignore_permissions=True)
        payment.submit()
        
        return {
            "status": "success",
            "payment_id": payment.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Travel Payment Creation Failed")
        return {
            "status": "error",
            "message": str(e)
        }
    
@frappe.whitelist()
def get_traveler_reviews(traveler_email):
    """Get all reviews by a traveler along with stats"""
    try:
        # Get traveler name from email
        traveler_name = frappe.db.get_value("Traveler", {"email": traveler_email}, "name")
        if not traveler_name:
            return {"status": "error", "message": "Traveler not found"}

        # Get all reviews by this traveler
        reviews = frappe.get_all("Review",
            filters={"traveler": traveler_name},
            fields=["name", "guide", "guide_name", "rating", "review_text",
                   "review_date", "trip_date", "booking", "guide_reply", "reply_date"],
            order_by="review_date desc"
        )

        # Calculate stats
        total_reviews = len(reviews)
        replies_received = sum(1 for r in reviews if r.get("guide_reply"))
        
        if total_reviews > 0:
            average_rating = sum(r["rating"] for r in reviews) / total_reviews
        else:
            average_rating = 0

        return {
            "status": "success",
            "reviews": reviews,
            "stats": {
                "average_rating": round(average_rating, 1),
                "total_reviews": total_reviews,
                "replies_received": replies_received
            }
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to fetch traveler reviews")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_areas_with_images(district):
    """Returns areas with their images for a given district"""
    try:
        if not district:
            frappe.throw(_("District parameter is required"))
        
        areas = frappe.get_all("Area",
            filters={"district": district},
            fields=["name", "area"])
        
        result = []
        for area in areas:
            try:
                doc = frappe.get_doc("Area", area["name"])
                images = []
                if hasattr(doc, 'images'):
                    images = [{"image": img.image} for img in doc.images if img.image]
                
                result.append({
                    "name": area["name"],
                    "area": area["area"],
                    "images": images
                })
            except Exception as e:
                frappe.log_error(f"Error processing area {area['name']}: {str(e)}")
                continue
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in get_areas_with_images: {str(e)}")
        frappe.throw(_("Failed to fetch areas. Please try again later."))