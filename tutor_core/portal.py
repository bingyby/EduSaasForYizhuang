"""Narrow portal API; Tutor DocTypes remain inaccessible to generic REST roles."""
import frappe
from frappe.utils import get_datetime, now_datetime


def identity(expected=None):
    user = frappe.session.user
    if user == 'Guest':
        frappe.throw('Login required', frappe.PermissionError)
    rows = frappe.get_all('Tutor Identity', filters={'user':user}, fields=['kind','student','teacher'], limit=2)
    if len(rows) != 1 or (expected and rows[0].kind != expected):
        frappe.throw('No matching identity', frappe.PermissionError)
    who = rows[0]
    if 'Tutor ' + who.kind not in frappe.get_roles(user):
        frappe.throw('Role required', frappe.PermissionError)
    return who


@frappe.whitelist()
def lessons():
    who = identity()
    filt = {'teacher':who.teacher} if who.kind == 'Teacher' else {'student':who.student}
    rows = frappe.get_all('Lesson Session', filters=filt, fields=['name','student','teacher','course','starts_at','ends_at','status'], order_by='starts_at asc', limit_page_length=500)
    if who.kind == 'Student':
        # Only summaries of lessons already visible to this student.
        for row in rows:
            row['summaries'] = frappe.get_all('Lesson Summary', filters={'lesson':row.name}, pluck='summary')
    return {'kind':who.kind,'lessons':rows}


@frappe.whitelist(methods=['POST'])
def reschedule(lesson, starts_at, ends_at, reason=''):
    who = identity('Teacher')
    frappe.db.sql('select name from `tabLesson Session` where name=%s for update', lesson)
    doc = frappe.get_doc('Lesson Session', lesson)
    if doc.teacher != who.teacher:
        frappe.throw('Not your lesson', frappe.PermissionError)
    if doc.status != 'Scheduled':
        frappe.throw('Only scheduled lessons can be rescheduled')
    start, end = get_datetime(starts_at), get_datetime(ends_at)
    if end <= start or (end-start).total_seconds() > 24*3600:
        frappe.throw('Invalid lesson time')
    before = {'starts_at':str(doc.starts_at),'ends_at':str(doc.ends_at)}
    doc.starts_at, doc.ends_at = start, end
    doc.save(ignore_permissions=True)
    frappe.get_doc({'doctype':'Lesson Change','lesson':doc.name,'change_type':'reschedule',
        'before_json':frappe.as_json(before),'after_json':frappe.as_json({'starts_at':str(start),'ends_at':str(end)}),
        'reason':reason[:1000]}).insert(ignore_permissions=True)
    return {'lesson':doc.name,'starts_at':str(start),'ends_at':str(end)}
