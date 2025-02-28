import frappe
from frappe import _

def get_context(context):
    if not frappe.session.user or frappe.session.user == "Guest":
        # frappe.local.response["redirect_to"] = "/index.html"
        frappe.throw(_("You are not permitted to access this page."), frappe.PermissionError)
    return context
