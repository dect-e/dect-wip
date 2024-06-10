import string
import random

def getRandomStr(lenght: int):
    return ''.join(random.choice(string.digits + string.ascii_uppercase + string.ascii_lowercase) for _ in range(lenght))


def getRandomNumber(lenght: int):
    return ''.join(random.choice(string.digits) for _ in range(lenght))


def pjsipConfig(configfile: str, Extensions, context: str):
    with open(configfile, 'w') as file:
        for ext in Extensions:
            file.write(f'[{ext.extension}]({context})\n')
            file.write(f'inbound_auth/username = {ext.extension}\n')
            file.write(f'inbound_auth/password = {ext.password}\n\n')
