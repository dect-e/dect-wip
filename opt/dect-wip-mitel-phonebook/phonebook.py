from bottle import route, run, request, template
import requests

dect_wip_ip = "127.0.0.1:8080"

xsi_template = """<?xml version="1.0" encoding="UTF-8"?>
<Personal xmlns="http://schema.broadsoft.com/xsi”>
% for entry in names_and_extensions:
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

    names_and_extensions = requests.get(f"http://{dect_wip_ip}/api/v1/phonebook").json()
    
    print(f"{caller} hat nach {search_string} gesucht, i={search_index}, n={search_results}")

    return template(xsi_template, names_and_extensions=names_and_extensions)

run(host='0.0.0.0', port=8082, debug=True)