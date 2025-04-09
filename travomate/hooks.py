app_name = "travomate"
app_title = "Travomate"
app_publisher = "Mahesh "
app_description = "Travel Companion"
app_email = "maheshmohanp16@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "travomate",
# 		"logo": "/assets/travomate/logo.png",
# 		"title": "Travomate",
# 		"route": "/travomate",
# 		"has_permission": "travomate.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/travomate/css/travomate.css"
# app_include_js = "/assets/travomate/js/travomate.js"

# include js, css files in header of web template
# web_include_css = "/assets/travomate/css/travomate.css"
# web_include_js = "/assets/travomate/js/travomate.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "travomate/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "travomate/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "index"
signup_form_template = "travomate/templates/register.html"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "travomate.utils.jinja_methods",
# 	"filters": "travomate.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "travomate.install.before_install"
# after_install = "travomate.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "travomate.uninstall.before_uninstall"
# after_uninstall = "travomate.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "travomate.utils.before_app_install"
# after_app_install = "travomate.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "travomate.utils.before_app_uninstall"
# after_app_uninstall = "travomate.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "travomate.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"travomate.tasks.all"
# 	],
# 	"daily": [
# 		"travomate.tasks.daily"
# 	],
# 	"hourly": [
# 		"travomate.tasks.hourly"
# 	],
# 	"weekly": [
# 		"travomate.tasks.weekly"
# 	],
# 	"monthly": [
# 		"travomate.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "travomate.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "travomate.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "travomate.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["travomate.utils.before_request"]
# after_request = ["travomate.utils.after_request"]

# Job Events
# ----------
# before_job = ["travomate.utils.before_job"]
# after_job = ["travomate.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"travomate.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# app_include_css = "/assets/css/theme.css"
# web_include_css = "/assets/css/theme.css"

# csrf_exempt = ["*"]  # Disable CSRF for all methods

app_include_js = ["/assets/frappe/js/frappe-web.min.js"]


whitelisted = [
    "travomate.custom_app.update_guide_profile",
    "travomate.custom_app.update_traveler_profile"
]

api_methods = ["custom_app.api.update_traveler_profile",
               "custom_app.api.update_guide_profile"
               ]

scheduler_events = {
    "cron": {
        "0 * * * *": [  # Runs at the start of every hour
            "travomate.travomate.doctype.booking.booking.mark_completed_trips"
        ]
    }
}