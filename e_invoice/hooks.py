from . import __version__ as app_version

app_name = "e_invoice"
app_title = "E Invoice"
app_publisher = "Bantoo"
app_description = "Adds QR Code to Invoices"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "devs@thebantoo.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/e_invoice/css/e_invoice.css"
# app_include_js = "/assets/e_invoice/js/e_invoice.js"

# include js, css files in header of web template
# web_include_css = "/assets/e_invoice/css/e_invoice.css"
# web_include_js = "/assets/e_invoice/js/e_invoice.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "e_invoice/public/scss/website"

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

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "e_invoice.install.before_install"
# after_install = "e_invoice.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "e_invoice.notifications.get_notification_config"

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
#	}
# }
regional_overrides = {
	'Saudi Arabia': {
		'erpnext.controllers.taxes_and_totals.update_itemised_tax_data': 'e_invoice.app.update_itemised_tax_data',
	}
}

doc_events = {
	"Sales Invoice": {
		"after_insert": [
			#"e_invoice.app.create_qr_code"
		],
		"on_cancel": [
			"e_invoice.app.delete_qr_code_file"
		]
	},
	"Company": {
		"on_trash":	"e_invoice.app.delete_vat_settings_for_company"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"e_invoice.tasks.all"
# 	],
# 	"daily": [
# 		"e_invoice.tasks.daily"
# 	],
# 	"hourly": [
# 		"e_invoice.tasks.hourly"
# 	],
# 	"weekly": [
# 		"e_invoice.tasks.weekly"
# 	]
# 	"monthly": [
# 		"e_invoice.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "e_invoice.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "e_invoice.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "e_invoice.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"e_invoice.auth.validate"
# ]
"""{"dt": "Custom Field", "filters": [
		[
			"name", "in", [
				"Company-company_name_in_arabic",
				"POS Invoice-qr_code",
				"POS Invoice-einvoice_status",
				"POS Invoice-signed_qr_code",
				"POS Invoice-column_break_133",
				"POS Invoice-qr_code_file",
				"POS Invoice-qr_code_details",
				"Sales Invoice-qr_code",
				"Sales Invoice-e_invoice_status",
				"Sales Invoice-qr_code_file",
				"Sales Invoice-column_break_138",
				"Sales Invoice-signed_qr_code"
			]
		]
	]},
"""
fixtures = [
	
	{"dt": "Print Format", "filters": [
		[
			"name", "in", [
				"E-Invoice Saudi",
				"Saudi VAT Invoice",
				'Simplified Tax Invoice', 
				'Detailed Tax Invoice', 
				'Tax Invoice'
			]
		]
	]},
	{"dt": "Client Script", "filters": [
		[
			"name", "in", [
				"Sales Invoice-Form"
			]
		]
	]},

]
