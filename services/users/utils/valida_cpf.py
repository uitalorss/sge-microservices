import re

from validate_docbr import CPF

validate_cpf = CPF()


def valida_cpf(cpf: str):
    num_cpf = re.sub(r"\D", "", cpf)
    if len(num_cpf) != 11:
        raise ValueError("O CPF deve ter exatamente 11 caracteres.")
    if not validate_cpf.validate(num_cpf):
        raise ValueError("CPF inválido.")
    return num_cpf
