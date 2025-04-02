from frappe.model.document import Document
import frappe
from frappe.utils import nowdate, getdate, date_diff, flt
from frappe import _

class Booking(Document):
    def validate(self):
        self.validate_dates()
        self.calculate_trip_details()
    
    def validate_dates(self):
        if getdate(self.start_date) < getdate(nowdate()):
            frappe.throw(_("Start date cannot be in the past"))
        
        if getdate(self.start_date) > getdate(self.end_date):
            frappe.throw(_("End date cannot be before start date"))
    
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
    """Automatically mark past trips as completed"""
    try:
        today = getdate(nowdate())
        past_bookings = frappe.get_all("Booking",
            filters={
                "status": "Confirmed",
                "end_date": ["<", today]
            },
            fields=["name", "end_date"]
        )

        for booking in past_bookings:
            # Mark as completed
            frappe.db.set_value("Booking", booking.name, {
                "status": "Completed",
                "is_reviewable": 1 if (today - getdate(booking.end_date)).days <= 7 else 0
            })

        frappe.db.commit()
        return {
            "status": "success",
            "count": len(past_bookings),
            "message": f"Marked {len(past_bookings)} bookings as completed"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Failed to mark completed trips")
        return {
            "status": "error",
            "message": str(e)
        }

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