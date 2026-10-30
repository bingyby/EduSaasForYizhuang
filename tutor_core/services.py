"""Administrator-only initial services. Each request runs in one Frappe transaction."""
from datetime import datetime, timedelta
import frappe
from frappe.utils import getdate, get_datetime
from tutor_core.domain import amount_for_minutes, occurrence_dates


def _admin():
    if 'System Manager' not in frappe.get_roles():
        frappe.throw('Only System Manager may use this prototype', frappe.PermissionError)


@frappe.whitelist(methods=['POST'])
def generate_lessons(recurring_lesson):
    _admin()
    frappe.has_permission('Lesson Session', 'create', throw=True)
    # Serialize generators on this rule; the unique key is a second safeguard.
    frappe.db.sql('select name from `tabRecurring Lesson` where name=%s for update', recurring_lesson)
    rule = frappe.get_doc('Recurring Lesson', recurring_lesson)
    rule.check_permission('read')
    contract = frappe.get_doc('Tutor Contract', rule.contract)
    start, end = getdate(rule.start_date), getdate(rule.end_date)
    if rule.duration_minutes <= 0 or end < start or (end - start).days > 366:
        frappe.throw('Invalid rule: positive duration and at most 366 days required')
    if start < getdate(contract.valid_from) or (contract.valid_to and end > getdate(contract.valid_to)):
        frappe.throw('Recurrence must fall within the contract dates')
    try:
        days = list(occurrence_dates(start, end, int(rule.weekday)))
    except ValueError as exc:
        frappe.throw(str(exc))
    time_value = rule.start_time
    if isinstance(time_value, timedelta):
        offset = time_value
    else:
        parts = str(time_value).split(':')
        offset = timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(float(parts[2])) if len(parts) > 2 else 0)
    created = []
    for day in days:
        key = f'{rule.name}:{day.isoformat()}'
        if frappe.db.exists('Lesson Session', {'occurrence_key': key}):
            continue
        begins = datetime.combine(day, datetime.min.time()) + offset
        doc = frappe.get_doc({'doctype':'Lesson Session', 'occurrence_key':key, 'recurring_lesson':rule.name,
            'occurrence_date':day, 'contract':contract.name, 'student':contract.student, 'teacher':contract.teacher,
            'course':contract.course, 'starts_at':begins, 'ends_at':begins + timedelta(minutes=rule.duration_minutes), 'status':'Scheduled'})
        doc.insert()
        created.append(doc.name)
    return {'created': created, 'count': len(created)}


@frappe.whitelist(methods=['POST'])
def complete_lesson(lesson):
    _admin()
    frappe.has_permission('Billing Record', 'create', throw=True)
    frappe.db.sql('select name from `tabLesson Session` where name=%s for update', lesson)
    doc = frappe.get_doc('Lesson Session', lesson)
    doc.check_permission('write')
    if doc.status == 'Completed':
        bill = frappe.db.get_value('Billing Record', {'lesson': doc.name}, 'name')
        if not bill:
            frappe.throw('Completed lesson has no bill; manual investigation required')
        return {'billing_record': bill, 'already_completed': True}
    if doc.status != 'Scheduled':
        frappe.throw('Only a scheduled lesson can be completed')
    duration = (get_datetime(doc.ends_at) - get_datetime(doc.starts_at)).total_seconds()
    if duration <= 0 or duration % 60:
        frappe.throw('Duration must be a positive whole number of minutes')
    day = getdate(doc.starts_at)
    rates = frappe.get_all('Tutor Rate', filters={'teacher':doc.teacher, 'student':doc.student, 'contract':doc.contract,
        'course':doc.course, 'unit':'hour', 'valid_from':['<=', day]}, fields=['name','price','valid_to'])
    rates = [r for r in rates if not r.valid_to or getdate(r.valid_to) >= day]
    if len(rates) != 1:
        frappe.throw('Exactly one matching rate is required for the lesson date')
    doc.flags.tutor_completion = True
    doc.status = 'Completed'
    doc.save()
    bill = frappe.get_doc({'doctype':'Billing Record', 'lesson':doc.name, 'rate_snapshot':rates[0].price,
        'duration_minutes':int(duration / 60), 'amount':amount_for_minutes(rates[0].price, int(duration / 60))})
    bill.flags.tutor_create_bill = True
    bill.insert()
    return {'billing_record': bill.name, 'already_completed': False}
