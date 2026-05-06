from bottle import route, run, request, template
import requests
import os

dect_wip_ip = os.getenv('DECT_WIP_URL', '127.0.0.1:8080')

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

    search_string = search_string.replace('*','')

    print(search_string)

    if search_string == '':
        names_and_extensions = requests.get(f"http://{dect_wip_ip}/api/v1/phonebook").json()
    else:
        names_and_extensions = requests.get(f"http://{dect_wip_ip}/api/v1/phonebook?search={search_string}").json() 

    print(f"{caller} hat nach {search_string} gesucht, i={search_index}, n={search_results}")

    return template(xsi_template, names_and_extensions=names_and_extensions)

port = os.getenv('DECT_WIP_PHONEBOOK_PORT', '8082')
run(host='0.0.0.0', port=port, debug=False)
