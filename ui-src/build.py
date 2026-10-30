from pathlib import Path
import json
root = Path(__file__).resolve().parent.parent
css=(root/'ui-src/style.css').read_text()
body=(root/'ui-src/markup.html').read_text()
js=(root/'ui-src/app.js').read_text()
(root/'docs').mkdir(exist_ok=True)
static='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>课间 · 家教工作台预览</title><style>'+css+'</style></head><body>'+body+'<script>window.TUTOR_BOOT='+json.dumps({'role':'Teacher','preview':True},ensure_ascii=False)+';</script><script>'+js+'</script></body></html>'
(root/'docs/index.html').write_text(static)
frappe='{% extends "templates/web.html" %}\n{% block page_content %}\n<style>'+css+'</style><span style="position:absolute;left:-9999px">{{ "教师工作台" if kind == "Teacher" else "学生课程" }}</span>'+body+'<script>window.TUTOR_BOOT={role:{{ kind | tojson }},csrf:{{ csrf_token | tojson }},preview:false};</script><script>'+js+'</script>\n{% endblock %}\n'
(root/'tutor_core/www/tutor.html').write_text(frappe)
