from frappe.model.document import Document
import frappe
from frappe.utils import now_datetime, nowdate, getdate, date_diff, flt
from frappe import _

class Booking(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_trip_details()
    
    def validate_dates(self):
        # if getdate(self.start_date) < getdate(nowdate()):
        #     frappe.throw(_("Start date cannot be in the past"))
        
        # if getdate(self.start_date) > getdate(self.end_date):
        #     frappe.throw(_("End date cannot be before start date"))
        pass
    
    def calculate_trip_details(self):
        """Calculate duration and total amount based on travel zone"""
        if self.start_date and self.end_date and self.travel_zone:
            # Calculate trip duration (inclusive of both dates)
            self.trip_duration = date_diff(self.end_date, self.start_date) + 1
            
            # Get daily rate from travel zone
            daily_rate = flt(frappe.db.get_value("Travel Zone", self.travel_zone, "daily_rate"))
            if not daily_rate:
                frappe.throw(_("Daily rate not set for selected Travel Zone"))
            
            self.daily_rate = daily_rate
            self.total_amount = flt(daily_rate * self.trip_duration, 2)

@frappe.whitelist()
def mark_completed_trips():
    """Automatically mark past trips as completed and handle notifications"""
    try:
        today = getdate(nowdate())
        # Get confirmed bookings that ended before today
        past_bookings = frappe.get_all("Booking",
            filters={
                "status": "Confirmed",
                "end_date": ["<", today]
            },
            fields=["name", "traveler", "guide", "end_date", "start_date", "travel_zone"]
        )

        results = {
            "updated": 0,
            "notified_travelers": 0,
            "notified_guides": 0
        }

        for booking in past_bookings:
            # Skip if already processed (safety check)
            if frappe.db.get_value("Booking", booking.name, "status") != "Confirmed":
                continue

            # Calculate review eligibility (7-day window)
            days_since_trip = (today - getdate(booking.end_date)).days
            is_reviewable = 1 if days_since_trip <= 7 else 0

            # Update booking status
            frappe.db.set_value("Booking", booking.name, {
                "status": "Completed",
                "is_reviewable": is_reviewable,
                "modified": now_datetime()
            })

            # Create review request notification for traveler
            if is_reviewable:
                create_review_notification(
                    traveler=booking.traveler,
                    guide=booking.guide,
                    booking=booking.name,
                    travel_zone=booking.travel_zone,
                    trip_date=f"{booking.start_date} to {booking.end_date}"
                )
                results["notified_travelers"] += 1

            # Create completion notification for guide
            create_guide_notification(
                guide=booking.guide,
                booking=booking.name,
                traveler=booking.traveler
            )
            results["notified_guides"] += 1

            results["updated"] += 1

        frappe.db.commit()
        
        # Log results for monitoring
        frappe.logger().info(f"Booking completion job: {results}")
        return {
            "status": "success",
            **results,
            "message": f"Processed {results['updated']} bookings"
        }

    except Exception as e:
        frappe.log_error(
            title="Failed to mark completed trips",
            message=frappe.get_traceback()
        )
        return {
            "status": "error",
            "message": str(e)
        }

def create_review_notification(traveler, guide, booking, travel_zone, trip_date):
    """Create notification for traveler to review their trip"""
    try:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": "How was your trip?",
            "email_content": f"""
                <p>We hope you enjoyed your trip to {travel_zone} from {trip_date}!</p>
                <p>Please take a moment to review your guide.</p>
                <p><a href="/booking/{booking}/review">Leave a Review</a></p>
            """,
            "for_user": traveler,
            "type": "Alert",
            "document_type": "Booking",
            "document_name": booking
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("Failed to create review notification")

def create_guide_notification(guide, booking, traveler):
    """Create notification for guide about completed trip"""
    try:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": "Trip completed",
            "email_content": f"""
                <p>Your booking #{booking} with {traveler} has been marked as completed.</p>
                <p>You may receive a review from the traveler soon.</p>
            """,
            "for_user": guide,
            "type": "Alert",
            "document_type": "Booking",
            "document_name": booking
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error("Failed to create guide notification")

@frappe.whitelist()
def get_payment_url(booking_id):
    """Generate payment URL for booking"""
    try:
        booking = frappe.get_doc("Booking", booking_id)
        
        if booking.status != "Confirmed":
            frappe.throw(_("Only confirmed bookings can be paid for"))
        
        if booking.payment_status == "Paid":
            frappe.throw(_("This booking has already been paid"))

        payment_request = frappe.get_doc({
            "doctype": "Payment Request",
            "reference_doctype": "Booking",
            "reference_name": booking.name,
            "subject": _("Payment for Booking {0}").format(booking.name),
            "grand_total": booking.total_amount,
            "payment_gateway": "Razorpay",
            "email_to": frappe.db.get_value("Traveler", booking.traveler, "email"),
            "description": _("{0} day trip from {1} to {2}").format(
                booking.trip_duration,
                booking.start_date.strftime("%d %b %Y"),
                booking.end_date.strftime("%d %b %Y")
            )
        }).insert(ignore_permissions=True)
        
        return {
            "status": "success",
            "payment_url": payment_request.get_payment_url(),
            "amount": booking.total_amount
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment URL Generation Failed")
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist()
def mark_as_paid(booking_id, amount, method=None):
    """Mark booking as paid after successful payment"""
    try:
        booking = frappe.get_doc("Booking", booking_id)
        
        if booking.total_amount != flt(amount):
            frappe.throw(_("Payment amount doesn't match booking amount"))
        
        booking.payment_status = "Paid"
        booking.payment_date = nowdate()
        booking.payment_method = method
        booking.save(ignore_permissions=True)
        
        # Update guide earnings
        if booking.guide:
            guide = frappe.get_doc("Guide", booking.guide)
            guide.append("earnings", {
                "date": nowdate(),
                "amount": amount,
                "booking": booking.name
            })
            guide.save(ignore_permissions=True)
        
        return {
            "status": "success",
            "message": _("Payment recorded successfully")
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Recording Failed")
        return {
            "status": "error",
            "message": str(e)
        }