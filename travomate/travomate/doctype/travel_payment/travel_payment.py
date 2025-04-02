from frappe.model.document import Document
import frappe
from frappe.utils import now_datetime, nowdate

class TravelPayment(Document):
    def validate(self):
        """Set defaults and auto-generate fields"""
        self.set_defaults()
        self.generate_transaction_id()
    
    def before_submit(self):
        """Optional validation for completed payments"""
        if self.status == "Completed":
            self.validate_completion()
            self.update_booking()
    
    def set_defaults(self):
        """Ensure all fields have sensible defaults"""
        if not self.payment_date:
            self.payment_date = nowdate()
        if not self.status:
            self.status = "Draft"
        if not self.amount:
            self.amount = 0
    
    def generate_transaction_id(self):
        """Auto-generate if empty"""
        if not self.transaction_id:
            self.transaction_id = f"TPAY-{frappe.generate_hash(length=8)}"
    
    def validate_completion(self):
        """Optional validation - only runs when status=Completed"""
        if self.payment_method == "UPI" and not self.upi_id:
            frappe.msgprint("UPI ID is recommended for UPI payments", alert=True)
        elif self.payment_method == "Card" and not self.card_reference:
            frappe.msgprint("Card reference is recommended", alert=True)
    
    def update_booking(self):
        """Optional: Link to booking if provided"""
        if self.booking:
            frappe.db.set_value("Booking", self.booking, {
                "payment_status": "Paid",
                "paid_amount": self.amount,
                "payment_reference": self.name
            })
    
    def on_cancel(self):
        """Optional cleanup"""
        if self.booking:
            frappe.db.set_value("Booking", self.booking, "payment_status", "Unpaid")