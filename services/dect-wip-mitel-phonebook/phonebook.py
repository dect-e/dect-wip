import os
from flask import Flask, request, render_template_string
import requests
import click
from tools.confighelper import DectWIPConfig

app = Flask(__name__)

xsi_template = """<?xml version="1.0" encoding="UTF-8"?>
<Personal xmlns="http://schema.broadsoft.com/xsi">
{% for entry in names_and_extensions: %}
<entry>
<name>{{entry["name"]}}</name>
<number>{{entry["extension"]}}</number>
</entry>
{% endfor %}
</Personal>"""

@app.route('/com.broadsoft.xsi-actions/v2.0/user/<caller>/directories/personal')
def return_phonebook(caller):

    search_string = request.args.get('name')
    search_index = request.args.get('start')
    search_index = int(search_index)-1 # let search_index start at 0 not 1
    search_results_count = int(request.args.get('results'))

    if config.mitelphonebook_always_search_with_contains:
        if not search_string.startswith('*'):
            print(f'config.ini phonebook always_search_with_contains is true --> converting {search_string} to *{search_string}')
            search_string = f'*{search_string}'
        if not search_string.endswith('*'):
            print(f'config.ini phonebook always_search_with_contains is true --> converting {search_string} to {search_string}*')
            search_string = f'{search_string}*'

    search_string = search_string.replace('*','%')

    if search_string == '':
        names_and_extensions = requests.get(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/phonebook").json()
    else:
        names_and_extensions = requests.get(f"http://{config.dect_wip_internal_ip}:{config.dect_wip_port}/api/v1/phonebook?search={search_string}").json()

    print(f"{caller} searched for {search_string}, index={search_index}, results_count={search_results_count}")

    # limit amount to requests search_index and search_string
    names_and_extensions = names_and_extensions[
        search_index : search_index+search_results_count
    ]

    return render_template_string(xsi_template, names_and_extensions=names_and_extensions)

def init(config_path):

    # setup global config

    global config

    config = DectWIPConfig(config_path=config_path)

@click.command()
@click.option('--config', 'config_path', envvar='CONFIG_PATH', default='/etc/dect-wip.ini', help='optional config location')
def init_dev(config_path):
    init(config_path)
    app.run(host=config.mitelphonebook_listen_ip, port=config.mitelphonebook_port, debug=False, use_reloader=True)

def init_wsgi():
    init(os.environ.get('CONFIG_PATH', '/etc/dect-wip.ini'))
    return app

if __name__ == '__main__':
    init_dev()
