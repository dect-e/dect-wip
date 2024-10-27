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

def format_token(token):
    """
    Take a token(string) and create groups of four digits sperated by space
    """
    block_size = 4
    token_list = ["".join(token[i:i+block_size]) for i in range(0, len(token), block_size)]
    return " ".join(token_list)
