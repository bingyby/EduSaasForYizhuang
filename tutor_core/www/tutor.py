import frappe
from tutor_core.portal import identity
no_cache = 1

def get_context(context):
    if frappe.session.user == 'Guest':
        frappe.local.flags.redirect_location = '/login?redirect-to=/tutor'
        raise frappe.Redirect
    context.kind = identity().kind
    context.csrf_token = frappe.sessions.get_csrf_token()
