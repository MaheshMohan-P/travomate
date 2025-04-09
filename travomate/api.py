import frappe
from frappe.utils import flt, getdate, nowdate, formatdate
from frappe.utils.csvutils import build_csv_response
from datetime import datetime, timedelta
from collections import defaultdict

@frappe.whitelist()
def get_guide_for_user(user):
    """Get guide name for a given user email"""
    try:
        if not user:
            return {"status": "error", "message": "User email is required"}

        guide = frappe.get_value("Guide", {"email": user}, "name")
        if guide:
            return {"status": "success", "guide": guide}
        else:
            return {"status": "error", "message": "No guide found for this user"}
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_guide_for_user")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_guide_details(guide):
    """Get detailed information about a guide"""
    try:
        if not guide:
            return {"status": "error", "message": "Guide name is required"}

        if not frappe.db.exists("Guide", guide):
            return {"status": "error", "message": "Guide not found"}

        guide_doc = frappe.get_doc("Guide", guide)
        
        # Get basic guide information
        guide_data = {
            "name": guide_doc.name,
            "full_name": guide_doc.full_name,
            "email": guide_doc.email,
            "rating": flt(guide_doc.rating, 1),
            "total_reviews": guide_doc.total_reviews,
            "experience": guide_doc.experience,
            "language_spoken": guide_doc.language_spoken,
            "profile_picture": guide_doc.profile_picture
        }

        return {
            "status": "success",
            "data": guide_data
        }
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_guide_details")
        return {"status": "error", "message": str(e)}
    
@frappe.whitelist()
def get_guide_booking_stats(guide, from_date=None, to_date=None):
    """Get booking statistics for a guide within a date range"""
    try:
        frappe.logger().debug(f"Getting booking stats for {guide} from {from_date} to {to_date}")

        if not guide:
            return {"status": "error", "message": "Guide is required"}

        frappe.logger().debug(f"Checking if guide exists: {frappe.db.exists('Guide', guide)}")

        # Validate guide exists
        if not frappe.db.exists("Guide", guide):
            return {"status": "error", "message": "Guide not found"}

        # Set default date range if not provided (last 30 days)
        to_date = getdate(to_date) if to_date else getdate()
        from_date = getdate(from_date) if from_date else (to_date - timedelta(days=30))

        # Get counts for each booking status
        status_counts = frappe.get_all("Booking",
            filters={
                "guide": guide,
                "start_date": ["between", [from_date, to_date]]
            },
            fields=["status", "COUNT(*) as count"],
            group_by="status"
        )

        # Initialize counts dictionary
        counts = defaultdict(int)
        for row in status_counts:
            counts[row.status.lower()] = row.count

        # Get total earnings from completed bookings
        total_earnings = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM `tabBooking`
            WHERE guide = %s
            AND status = 'Completed'
            AND start_date BETWEEN %s AND %s
        """, (guide, from_date, to_date), as_dict=True)[0].total

        # Calculate pending payout (70% of earnings)
        pending_payout = total_earnings * 0.7

        # Get comparison data with previous period
        prev_period_days = (to_date - from_date).days
        prev_from_date = from_date - timedelta(days=prev_period_days)
        prev_to_date = from_date - timedelta(days=1)

        prev_earnings = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM `tabBooking`
            WHERE guide = %s
            AND status = 'Completed'
            AND start_date BETWEEN %s AND %s
        """, (guide, prev_from_date, prev_to_date), as_dict=True)[0].total

        prev_completed = frappe.db.sql("""
            SELECT COALESCE(COUNT(*), 0) as count
            FROM `tabBooking`
            WHERE guide = %s
            AND status = 'Completed'
            AND start_date BETWEEN %s AND %s
        """, (guide, prev_from_date, prev_to_date), as_dict=True)[0].count

        # Calculate percentage changes (handle division by zero)
        earnings_comparison = 0
        if prev_earnings > 0:
            earnings_comparison = round(((total_earnings - prev_earnings) / prev_earnings) * 100, 1)

        bookings_comparison = 0
        if prev_completed > 0:
            bookings_comparison = round(((counts.get("completed", 0) - prev_completed) / prev_completed) * 100, 1)

        return {
            "status": "success",
            "total_earnings": flt(total_earnings, 2),
            "completed_bookings": counts.get("completed", 0),
            "confirmed_bookings": counts.get("confirmed", 0),
            "pending_bookings": counts.get("pending", 0),
            "cancelled_bookings": counts.get("cancelled", 0),
            "pending_payout": flt(pending_payout, 2),
            "earnings_comparison": earnings_comparison,
            "bookings_comparison": bookings_comparison
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_guide_booking_stats")
        return {
            "status": "error",
            "message": str(e),
            "total_earnings": 0,
            "completed_bookings": 0,
            "confirmed_bookings": 0,
            "pending_bookings": 0,
            "cancelled_bookings": 0,
            "pending_payout": 0,
            "earnings_comparison": 0,
            "bookings_comparison": 0
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_guide_booking_stats")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_guide_earnings_trend(guide, period="month", from_date=None, to_date=None):
    try:
        if not guide:
            return {"status": "error", "message": "Guide is required"}

        # Simplified date handling
        to_date = getdate(to_date) if to_date else getdate()
        if period == "week":
            from_date = to_date - timedelta(days=7)
        else:  # Default to month
            from_date = to_date - timedelta(days=30)

        # Simplified query
        earnings = frappe.db.sql("""
            SELECT DATE_FORMAT(start_date, '%%d-%%b') as day, 
                   SUM(total_amount) as amount
            FROM `tabBooking`
            WHERE guide = %s
            AND status = 'Completed'
            AND start_date BETWEEN %s AND %s
            GROUP BY day
            ORDER BY start_date
        """, (guide, from_date, to_date), as_dict=1)

        return {
            "status": "success",
            "labels": [e['day'] for e in earnings],
            "data": [float(e['amount'] or 0) for e in earnings]
        }

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "labels": [],
            "data": []
        }

@frappe.whitelist()
def get_guide_district_performance(guide, from_date=None, to_date=None):
    try:
        # Force include districts even with zero values
        districts = frappe.get_all("District", filters={"state": "Kerala"}, fields=["name as district"])
        
        for district in districts:
            district.bookings = frappe.db.count("Booking", {
                "guide": guide,
                "district": district.district,
                "status": "Completed"
            }) or 0
            
            district.earnings = frappe.db.get_value("Booking",
                {"guide": guide, "district": district.district, "status": "Completed"},
                "sum(total_amount)"
            ) or 0
            
            district.rating = frappe.db.get_value("Review",
                {"guide": guide, "booking.district": district.district},
                "avg(rating)"
            ) or 0

        return {"status": "success", "data": districts}
        
    except Exception as e:
        return {"status": "error", "message": str(e), "data": []}
    
@frappe.whitelist()
def get_guide_recent_transactions(guide, from_date=None, to_date=None, limit=5):
    """Get recent transactions (payments) for a guide"""
    try:
        if not guide:
            return {"transactions": []}

        # Set default date range if not provided (last 3 months)
        to_date = getdate(to_date) if to_date else getdate()
        from_date = getdate(from_date) if from_date else (to_date - timedelta(days=90))

        # Get transactions data
        transactions = frappe.get_all("Travel Payment",
            filters={
                "booking.guide": guide,
                "creation": ["between", [from_date, to_date]]
            },
            fields=["name", "booking", "amount", "status", "payment_method", "creation"],
            order_by="creation desc",
            limit=limit
        )

        # Format the data
        formatted_transactions = []
        for tx in transactions:
            booking = frappe.get_doc("Booking", tx.booking)
            formatted_transactions.append({
                "date": formatdate(tx.creation),
                "booking": tx.booking,
                "amount": flt(tx.amount, 2),
                "status": tx.status,
                "traveler": booking.traveler_name,
                "method": tx.payment_method,
                "period": f"{formatdate(booking.start_date)} to {formatdate(booking.end_date)}"
            })

        return {"transactions": formatted_transactions}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_guide_recent_transactions")
        return {"transactions": []}

@frappe.whitelist()
def export_guide_earnings(guide, period="month"):
    """Export earnings data to CSV"""
    try:
        if not guide:
            frappe.throw("Guide is required")

        # Get the data
        result = get_guide_earnings_trend(guide, period)
        if result["status"] != "success":
            frappe.throw("Failed to fetch earnings data")

        # Prepare CSV data
        headers = ["Period", "Earnings (₹)"]
        data = [headers]

        for i in range(len(result["labels"])):
            data.append([
                result["labels"][i],
                result["data"][i]
            ])

        # Create CSV response
        frappe.response["result"] = build_csv_response(data, f"{guide}_earnings_{period}.csv")
        frappe.response["type"] = "csv"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in export_guide_earnings")
        frappe.throw(f"Failed to export earnings data: {str(e)}")

@frappe.whitelist()
def export_guide_transactions(guide):
    """Export transactions data to CSV"""
    try:
        if not guide:
            frappe.throw("Guide is required")

        # Get the data
        result = get_guide_recent_transactions(guide, limit=1000)
        if not result.get("transactions"):
            frappe.throw("No transactions found to export")

        # Prepare CSV data
        headers = ["Date", "Booking Reference", "Traveler", "Amount (₹)", "Status", "Payment Method", "Trip Period"]
        data = [headers]

        for tx in result["transactions"]:
            data.append([
                tx["date"],
                tx["booking"],
                tx["traveler"],
                tx["amount"],
                tx["status"],
                tx["method"],
                tx["period"]
            ])

        # Create CSV response
        frappe.response["result"] = build_csv_response(data, f"{guide}_transactions.csv")
        frappe.response["type"] = "csv"

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in export_guide_transactions")
        frappe.throw(f"Failed to export transactions data: {str(e)}")