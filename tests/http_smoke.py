"""HTTP role and portal smoke test for a disposable seeded CI site."""
import re
import requests

BASE = 'http://localhost:8080'

def login(email):
    s = requests.Session()
    r=s.post(BASE+'/api/method/login', data={'usr':email,'pwd':'ci-only-password-123'}, timeout=30)
    r.raise_for_status()
    page=s.get(BASE+'/tutor',timeout=30)
    page.raise_for_status()
    return s,page.text

def fetch(s):
    r=s.get(BASE+'/api/method/tutor_core.portal.lessons',timeout=30)
    r.raise_for_status()
    return r.json()['message']

teacher,page=login('http-teacher-1@example.invalid')
assert '教师工作台' in page
one=fetch(teacher); assert one['kind']=='Teacher' and len(one['lessons'])==1
other,_=login('http-teacher-2@example.invalid')
two=fetch(other); assert len(two['lessons'])==1 and one['lessons'][0]['name'] != two['lessons'][0]['name']
student,student_page=login('http-student-1@example.invalid')
assert '学生课程' in student_page
mine=fetch(student); assert mine['kind']=='Student' and len(mine['lessons'])==1 and mine['lessons'][0]['name']==one['lessons'][0]['name']
# Check standard REST does not bypass the scoped API.
r=student.get(BASE+'/api/resource/Lesson%20Session/'+two['lessons'][0]['name'],timeout=30)
assert r.status_code in (403,404),r.status_code

# Exercise the same authenticated POST and CSRF mechanism used by the form.
token = re.search(r'csrf="([^"]+)"',page)
assert token, 'Portal did not provide a CSRF token'
response=teacher.post(BASE+'/api/method/tutor_core.portal.reschedule', data={'lesson':one['lessons'][0]['name'],'starts_at':'2026-11-19 18:00:00','ends_at':'2026-11-19 20:00:00'},headers={'X-Frappe-CSRF-Token':token.group(1)},timeout=30)
response.raise_for_status()
assert fetch(teacher)['lessons'][0]['starts_at'].startswith('2026-11-19')
print('PASS HTTP teacher/student portal, scoped data and direct REST denial')
