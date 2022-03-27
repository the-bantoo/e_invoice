import frappe
import json
import os
import io

from base64 import b64encode
from frappe import _
from frappe.utils import flt, money_in_words, round_based_on_smallest_currency_fraction
from frappe.utils.data import add_to_date, get_time, getdate
from pyqrcode import create as qr_create

from erpnext import get_region


from frappe.permissions import add_permission, update_permission_property
# from erpnext.regional.united_arab_emirates.setup import make_custom_fields as uae_custom_fields, add_print_formats
# from erpnext.regional.saudi_arabia.wizard.operations.setup_ksa_vat_setting import create_ksa_vat_setting
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup(company=None, patch=True):
	uae_custom_fields()
	add_print_formats()
	add_permissions()
	make_custom_fields()

@frappe.whitelist()
def create_qr_code(doc):
	"""Create QR Code after inserting Sales Inv
	"""

	doc = frappe.get_doc("Sales Invoice", doc)
	
	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return

	# if QR Code field not present, do nothing
	if not hasattr(doc, 'qr_code'):
		setup()
	else:
		if doc.get('qr_code'):
			file_doc = frappe.get_list('File', {
				'file_url': doc.get('qr_code')
			})
			if len(file_doc):
				frappe.delete_doc('File', file_doc[0].name)
				
	# Don't create QR Code if it already exists
	#qr_code = doc.get("qr_code")
	#if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
	#	return

	meta = frappe.get_meta('Sales Invoice')

	for field in meta.get_image_fields():
		if field.fieldname == 'qr_code':
			''' TLV conversion for
			1. Seller's Name
			2. VAT Number
			3. Time Stamp
			4. Invoice Amount
			5. VAT Amount
			'''
			tlv_array = []
			# Sellers Name

			seller_name = frappe.db.get_value(
				'Company',
				doc.company,
				'company_name_in_arabic')

			if not seller_name:
				frappe.msgprint(_('Arabic name missing for {} in the company document').format(doc.company))
				seller_name = ""

			tag = bytes([1]).hex()
			length = bytes([len(seller_name.encode('utf-8'))]).hex()
			value = seller_name.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# VAT Number
			tax_id = frappe.db.get_value('Company', doc.company, 'tax_id')
			if not tax_id:
				frappe.msgprint(_('Tax ID missing for {} in the company document').format(doc.company))
				tax_id = ""

			tag = bytes([2]).hex()
			length = bytes([len(tax_id)]).hex()
			value = tax_id.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# Time Stamp
			posting_date = getdate(doc.posting_date)
			time = get_time(doc.posting_time)
			seconds = time.hour * 60 * 60 + time.minute * 60 + time.second
			time_stamp = add_to_date(posting_date, seconds=seconds)
			time_stamp = time_stamp.strftime('%Y-%m-%dT%H:%M:%SZ')

			tag = bytes([3]).hex()
			length = bytes([len(time_stamp)]).hex()
			value = time_stamp.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# Invoice Amount
			invoice_amount = str(doc.grand_total)
			tag = bytes([4]).hex()
			length = bytes([len(invoice_amount)]).hex()
			value = invoice_amount.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# VAT Amount
			vat_amount = str(doc.total_taxes_and_charges)

			tag = bytes([5]).hex()
			length = bytes([len(vat_amount)]).hex()
			value = vat_amount.encode('utf-8').hex()
			tlv_array.append(''.join([tag, length, value]))

			# Joining bytes into one
			tlv_buff = ''.join(tlv_array)

			# base64 conversion for QR Code
			base64_string = b64encode(bytes.fromhex(tlv_buff)).decode()

			qr_image = io.BytesIO()
			url = qr_create(base64_string, error='L')
			url.png(qr_image, scale=2, quiet_zone=1)

			name = frappe.generate_hash(doc.name, 5)

			# making file
			filename = f"QRCode-{name}.png".replace(os.path.sep, "__")
			_file = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"is_private": 0,
				"content": qr_image.getvalue(),
				"attached_to_doctype": doc.get("doctype"),
				"attached_to_name": doc.get("name"),
				"attached_to_field": "qr_code"
			})

			_file.save()

			#frappe.errprint("done")

			# assigning to document
			doc.db_set('qr_code', _file.file_url)
			doc.notify_update()

			break


def delete_qr_code_file(doc, method):
	"""Delete QR Code on deleted sales invoice"""

	region = get_region(doc.company)
	if region not in ['Saudi Arabia']:
		return

	if hasattr(doc, 'qr_code'):
		if doc.get('qr_code'):
			file_doc = frappe.get_list('File', {
				'file_url': doc.get('qr_code')
			})
			if len(file_doc):
				frappe.delete_doc('File', file_doc[0].name)

def delete_vat_settings_for_company(doc, method):
	if doc.country != 'Saudi Arabia':
		return

	settings_doc = frappe.get_doc('KSA VAT Setting', {'company': doc.name})
	settings_doc.delete()

def update_itemised_tax_data(doc):
	if not doc.taxes: return
	from erpnext.controllers.taxes_and_totals import get_itemised_tax

	itemised_tax = get_itemised_tax(doc.taxes)

	for row in doc.items:
		tax_rate = 0.0
		item_tax_rate = 0.0

		if row.item_tax_rate:
			item_tax_rate = frappe.parse_json(row.item_tax_rate)

		# First check if tax rate is present
		# If not then look up in item_wise_tax_detail
		if item_tax_rate:
			for account, rate in item_tax_rate.items():
				tax_rate += rate
		elif row.item_code and itemised_tax.get(row.item_code):
			tax_rate = sum([tax.get('tax_rate', 0) for d, tax in itemised_tax.get(row.item_code).items()])

		row.tax_rate = flt(tax_rate, row.precision("tax_rate"))
		row.tax_amount = flt((row.net_amount * tax_rate) / 100, row.precision("net_amount"))
		row.total_amount = flt((row.net_amount + row.tax_amount), row.precision("total_amount"))


def create_ksa_vat_setting(company):
	"""On creation of first company. Creates KSA VAT Setting"""

	company = frappe.get_doc('Company', company)

	file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ksa_vat_settings.json')
	with open(file_path, 'r') as json_file:
		account_data = json.load(json_file)

	# Creating KSA VAT Setting
	ksa_vat_setting = frappe.get_doc({
		'doctype': 'KSA VAT Setting',
		'company': company.name
	})

	for data in account_data:
		if data['type'] == 'Sales Account':
			for row in data['accounts']:
				item_tax_template = row['item_tax_template']
				account = row['account']
				ksa_vat_setting.append('ksa_vat_sales_accounts', {
					'title': row['title'],
					'item_tax_template': f'{item_tax_template} - {company.abbr}',
					'account': f'{account} - {company.abbr}'
				})

		elif data['type'] == 'Purchase Account':
			for row in data['accounts']:
				item_tax_template = row['item_tax_template']
				account = row['account']
				ksa_vat_setting.append('ksa_vat_purchase_accounts', {
					'title': row['title'],
					'item_tax_template': f'{item_tax_template} - {company.abbr}',
					'account': f'{account} - {company.abbr}'
				})

	ksa_vat_setting.save()

def add_print_formats():
	frappe.reload_doc("regional", "print_format", "detailed_tax_invoice")
	frappe.reload_doc("regional", "print_format", "simplified_tax_invoice")
	frappe.reload_doc("regional", "print_format", "tax_invoice")

	frappe.db.sql(""" update `tabPrint Format` set disabled = 0 where
		name in('Simplified Tax Invoice', 'Detailed Tax Invoice', 'Tax Invoice') """)

def uae_custom_fields():
	is_zero_rated = dict(fieldname='is_zero_rated', label='Is Zero Rated',
		fieldtype='Check', fetch_from='item_code.is_zero_rated', insert_after='description',
		print_hide=1)
	is_exempt = dict(fieldname='is_exempt', label='Is Exempt',
		fieldtype='Check', fetch_from='item_code.is_exempt', insert_after='is_zero_rated',
		print_hide=1)

	invoice_fields = [
		dict(fieldname='vat_section', label='VAT Details', fieldtype='Section Break',
			insert_after='group_same_items', print_hide=1, collapsible=1),
		dict(fieldname='permit_no', label='Permit Number',
			fieldtype='Data', insert_after='vat_section', print_hide=1),
	]

	purchase_invoice_fields = [
			dict(fieldname='company_trn', label='Company TRN',
				fieldtype='Read Only', insert_after='shipping_address',
				fetch_from='company.tax_id', print_hide=1),
			dict(fieldname='supplier_name_in_arabic', label='Supplier Name in Arabic',
				fieldtype='Read Only', insert_after='supplier_name',
				fetch_from='supplier.supplier_name_in_arabic', print_hide=1),
			dict(fieldname='recoverable_standard_rated_expenses', print_hide=1, default='0',
				label='Recoverable Standard Rated Expenses (AED)', insert_after='permit_no',
				fieldtype='Currency', ),
			dict(fieldname='reverse_charge', label='Reverse Charge Applicable',
				fieldtype='Select', insert_after='recoverable_standard_rated_expenses', print_hide=1,
				options='Y\nN', default='N'),
			dict(fieldname='recoverable_reverse_charge', label='Recoverable Reverse Charge (Percentage)',
				insert_after='reverse_charge', fieldtype='Percent', print_hide=1,
				depends_on="eval:doc.reverse_charge=='Y'", default='100.000'),
		]

	sales_invoice_fields = [
			dict(fieldname='company_trn', label='Company TRN',
				fieldtype='Read Only', insert_after='company_address',
				fetch_from='company.tax_id', print_hide=1),
			dict(fieldname='customer_name_in_arabic', label='Customer Name in Arabic',
				fieldtype='Read Only', insert_after='customer_name',
				fetch_from='customer.customer_name_in_arabic', print_hide=1),
			dict(fieldname='vat_emirate', label='VAT Emirate', insert_after='permit_no', fieldtype='Select',
				options='\nAbu Dhabi\nAjman\nDubai\nFujairah\nRas Al Khaimah\nSharjah\nUmm Al Quwain',
				fetch_from='company_address.emirate'),
			dict(fieldname='tourist_tax_return', label='Tax Refund provided to Tourists (AED)',
				insert_after='vat_emirate', fieldtype='Currency', print_hide=1, default='0'),
		]

	invoice_item_fields = [
		dict(fieldname='tax_code', label='Tax Code',
			fieldtype='Read Only', fetch_from='item_code.tax_code', insert_after='description',
			allow_on_submit=1, print_hide=1),
		dict(fieldname='tax_rate', label='Tax Rate',
			fieldtype='Float', insert_after='tax_code',
			print_hide=1, hidden=1, read_only=1),
		dict(fieldname='tax_amount', label='Tax Amount',
			fieldtype='Currency', insert_after='tax_rate',
			print_hide=1, hidden=1, read_only=1, options="currency"),
		dict(fieldname='total_amount', label='Total Amount',
			fieldtype='Currency', insert_after='tax_amount',
			print_hide=1, hidden=1, read_only=1, options="currency"),
	]

	delivery_date_field = [
		dict(fieldname='delivery_date', label='Delivery Date',
			fieldtype='Date', insert_after='item_name', print_hide=1)
	]

	custom_fields = {
		'Item': [
			dict(fieldname='tax_code', label='Tax Code',
				fieldtype='Data', insert_after='item_group'),
			dict(fieldname='is_zero_rated', label='Is Zero Rated',
				fieldtype='Check', insert_after='tax_code',
				print_hide=1),
			dict(fieldname='is_exempt', label='Is Exempt',
				fieldtype='Check', insert_after='is_zero_rated',
				print_hide=1)
		],
		'Customer': [
			dict(fieldname='customer_name_in_arabic', label='Customer Name in Arabic',
				fieldtype='Data', insert_after='customer_name'),
		],
		'Supplier': [
			dict(fieldname='supplier_name_in_arabic', label='Supplier Name in Arabic',
				fieldtype='Data', insert_after='supplier_name'),
		],
		'Address': [
			dict(fieldname='emirate', label='Emirate', fieldtype='Select', insert_after='state',
			options='\nAbu Dhabi\nAjman\nDubai\nFujairah\nRas Al Khaimah\nSharjah\nUmm Al Quwain')
		],
		'Purchase Invoice': purchase_invoice_fields + invoice_fields,
		'Purchase Order': purchase_invoice_fields + invoice_fields,
		'Purchase Receipt': purchase_invoice_fields + invoice_fields,
		'Sales Invoice': sales_invoice_fields + invoice_fields,
		'POS Invoice': sales_invoice_fields + invoice_fields,
		'Sales Order': sales_invoice_fields + invoice_fields,
		'Delivery Note': sales_invoice_fields + invoice_fields,
		'Sales Invoice Item': invoice_item_fields + delivery_date_field + [is_zero_rated, is_exempt],
		'POS Invoice Item': invoice_item_fields + delivery_date_field + [is_zero_rated, is_exempt],
		'Purchase Invoice Item': invoice_item_fields,
		'Sales Order Item': invoice_item_fields,
		'Delivery Note Item': invoice_item_fields,
		'Quotation Item': invoice_item_fields,
		'Purchase Order Item': invoice_item_fields,
		'Purchase Receipt Item': invoice_item_fields,
		'Supplier Quotation Item': invoice_item_fields,
	}

	create_custom_fields(custom_fields)

def add_permissions():
	"""Add Permissions for KSA VAT Setting."""
	add_permission('KSA VAT Setting', 'All', 0)
	for role in ('Accounts Manager', 'Accounts User', 'System Manager'):
		add_permission('KSA VAT Setting', role, 0)
		update_permission_property('KSA VAT Setting', role, 0, 'write', 1)
		update_permission_property('KSA VAT Setting', role, 0, 'create', 1)

	"""Enable KSA VAT Report"""
	frappe.db.set_value('Report', 'KSA VAT', 'disabled', 0)

def make_custom_fields():
	"""Create Custom fields
	- QR code Image file
	- Company Name in Arabic
	- Address in Arabic
	"""
	custom_fields = {
		'Sales Invoice': [
			dict(
				fieldname='qr_code',
				label='QR Code',
				fieldtype='Attach Image',
				read_only=1, no_copy=1, hidden=1
			)
		],
		'Address': [
			dict(
				fieldname='address_in_arabic',
				label='Address in Arabic',
				fieldtype='Data',
				insert_after='address_line2'
			)
		],
		'Company': [
			dict(
				fieldname='company_name_in_arabic',
				label='Company Name In Arabic',
				fieldtype='Data',
				insert_after='company_name'
			)
		]
	}

	create_custom_fields(custom_fields, update=True)

def update_regional_tax_settings(country, company):
	create_ksa_vat_setting(company)