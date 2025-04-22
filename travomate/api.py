import frappe
from frappe.utils import flt, getdate, nowdate
from frappe.utils.csvutils import build_csv_response
from datetime import datetime, timedelta
from collections import defaultdict
from frappe.utils.pdf import get_pdf
from frappe.utils import today, formatdate
import json

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
        # Get all districts with bookings for this guide
        districts = frappe.db.sql("""
            SELECT 
                b.district as district,
                d.district_name as district_name,  # Get proper name from District doctype
                COUNT(b.name) as total_bookings,
                SUM(CASE WHEN b.status = 'Completed' THEN b.total_amount ELSE 0 END) as earnings,
                AVG(r.rating) as rating
            FROM `tabBooking` b
            LEFT JOIN `tabDistrict` d ON b.district = d.name
            LEFT JOIN `tabReview` r ON r.booking = b.name
            WHERE 
                b.guide = %(guide)s
                AND b.district IS NOT NULL
                {% if from_date %} AND b.start_date >= %(from_date)s {% endif %}
                {% if to_date %} AND b.start_date <= %(to_date)s {% endif %}
            GROUP BY b.district, d.district_name
            HAVING COUNT(b.name) > 0
            ORDER BY total_bookings DESC
        """, {
            "guide": guide,
            "from_date": from_date,
            "to_date": to_date
        }, as_dict=True)
        
        # Get status breakdown
        status_data = frappe.db.sql("""
            SELECT 
                district,
                status,
                COUNT(*) as count
            FROM `tabBooking`
            WHERE 
                guide = %(guide)s
                AND district IS NOT NULL
                {% if from_date %} AND start_date >= %(from_date)s {% endif %}
                {% if to_date %} AND start_date <= %(to_date)s {% endif %}
            GROUP BY district, status
        """, {
            "guide": guide,
            "from_date": from_date,
            "to_date": to_date
        }, as_dict=True)
        
        # Add status counts to each district
        for district in districts:
            district.status_counts = {}
            for status in status_data:
                if status.district == district.district:
                    district.status_counts[status.status] = status.count
        
        return {
            "status": "success",
            "data": districts or []
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "District Performance Error")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }
    
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

@frappe.whitelist()
def generate_guide_report_pdf(guide, period, from_date=None, to_date=None):
    """Generate PDF report for guide's performance"""
    try:
        if not guide:
            frappe.throw("Guide is required")

        # Get all the required data
        booking_stats = get_guide_booking_stats(guide, from_date, to_date)
        if booking_stats.get("status") != "success":
            frappe.throw("Failed to fetch booking stats")
            
        earnings_trend = get_guide_earnings_trend(guide, period, from_date, to_date)
        district_performance = get_guide_district_performance(guide, from_date, to_date)
        recent_transactions = get_guide_recent_transactions(guide, from_date, to_date, limit=10)
        
        # Get guide details
        guide_doc = frappe.get_doc("Guide", guide)
        
        # Format numbers before passing to template
        def format_currency(value):
            return "₹{:,.2f}".format(float(value or 0))
            
        def format_float(value, decimals=1):
            return "{:,.{}f}".format(float(value or 0), decimals)
        
        # Format earnings trend data
        formatted_earnings_trend = {
            "labels": earnings_trend.get("labels", []),
            "data": [format_currency(amount) for amount in earnings_trend.get("data", [])]
        }
        
        # Format district performance data
        formatted_districts = []
        for district in district_performance.get("data", []):
            formatted_districts.append({
                "district": district.get("district", ""),
                "bookings": district.get("bookings", 0),
                "earnings": format_currency(district.get("earnings", 0)),
                "rating": format_float(district.get("rating", 0))
            })
        
        # Format transactions
        formatted_transactions = []
        for tx in recent_transactions.get("transactions", []):
            formatted_transactions.append({
                "date": tx.get("date", ""),
                "booking": tx.get("booking", ""),
                "amount": format_currency(tx.get("amount", 0)),
                "status": tx.get("status", "")
            })
        
        # Prepare report data
        report_data = {
            "guide_name": guide_doc.full_name,
            "report_period": period.capitalize(),
            "from_date": formatdate(from_date) if from_date else "",
            "to_date": formatdate(to_date) if to_date else "",
            "generated_on": formatdate(today()),
            "total_earnings": format_currency(booking_stats.get("total_earnings", 0)),
            "completed_bookings": booking_stats.get("completed_bookings", 0),
            "average_rating": format_float(guide_doc.rating),
            "pending_payout": format_currency(booking_stats.get("pending_payout", 0)),
            "earnings_trend": formatted_earnings_trend,
            "district_performance": formatted_districts,
            "recent_transactions": formatted_transactions,
            "logo": "/assets/img/icon2.png"
        }
        
        # Render HTML template
        html = frappe.render_template("templates/guide_report.html", report_data)
        
        # Generate PDF
        pdf = get_pdf(html)
        
        # Set response headers for PDF download
        frappe.local.response.filename = f"{guide}_report_{period}.pdf"
        frappe.local.response.filecontent = pdf
        frappe.local.response.type = "pdf"
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in generate_guide_report_pdf")
        frappe.throw(f"Failed to generate PDF report: {str(e)}")

