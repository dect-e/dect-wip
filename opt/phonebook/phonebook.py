from bottle import route, run, request, template

entries = [
    {"name": "val", "extension" : "123"},
    {"name": "anna", "extension" : "2323"},
    {"name": "leo", "extension" : "4242"},
]

xsi_template = """<?xml version="1.0" encoding="UTF-8"?>
<Personal xmlns="http://schema.broadsoft.com/xsi”>
% for entry in entries:
<entry>
<name>{{entry["name"]}}</name>
<number>{{entry["extension"]}}</number>
</entry>
% end
</Personal>"""

@route('/com.broadsoft.xsi-actions/v2.0/user/<caller>/directories/personal')
def return_phonebook(caller):
    search_string = request.query.name
    search_index = request.query.start
    search_results = request.query.results

    print(f"{caller} hat nach {search_string} gesucht, i={search_index}, n={search_results}")

    return template(xsi_template, entries=entries)

run(host='0.0.0.0', port=8081, debug=True)