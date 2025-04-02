# Copyright (c) 2025, Mahesh  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Review(Document):
    def before_save(self):
        # Auto-fill relationship names
        if not self.traveler_name:
            self.traveler_name = frappe.db.get_value("Traveler", self.traveler, "full_name")
        if not self.guide_name:
            self.guide_name = frappe.db.get_value("Guide", self.guide, "full_name")
        
        # Set trip date from booking
        if not self.trip_date:
            self.trip_date = frappe.db.get_value("Booking", self.booking, "end_date")

    def after_insert(self):
        # Update booking's review status
        frappe.db.set_value("Booking", self.booking, {
            "is_reviewable": 0,
            "review_link": self.name
        })
        
        # Update guide's average rating
        update_guide_rating(self.guide)

def update_guide_rating(guide_name):
    avg_rating = frappe.db.sql("""
        SELECT AVG(rating) 
        FROM `tabReview` 
        WHERE guide=%s AND is_approved=1
    """, guide_name)[0][0] or 0
    
    frappe.db.set_value("Guide", guide_name, "rating", round(avg_rating, 1))
