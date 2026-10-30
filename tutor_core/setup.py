import frappe

def ensure_roles():
    for role in ('Tutor Teacher', 'Tutor Student'):
        if not frappe.db.exists('Role', role):
            frappe.get_doc({'doctype':'Role','role_name':role}).insert(ignore_permissions=True)
