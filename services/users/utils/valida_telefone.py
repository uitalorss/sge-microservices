import re


def valida_telefone(value):
    regex = r"^\d{10,11}$"
    if not re.match(regex, value):
        raise ValueError("Número de telefone inválido")

    ddd = int(value[:2])
    if ddd < 11 or ddd > 99:
        raise ValueError("DDD inválido")

    num_telefone = value[2:]
    if num_telefone[0] in {"0", "1"}:
        raise ValueError("Número de telefone inválido")

    return value
