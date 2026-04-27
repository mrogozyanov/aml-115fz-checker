# validators.py

"""
Модуль проверки корректности пользовательского ввода.

Используется для:
- проверки заполнения обязательных полей;
- проверки формата ИНН;
- проверки суммы операции;
- формирования предупреждений для пользователя.
"""


def normalize_inn(inn):
    """
    Очищает ИНН от пробелов.
    """

    return str(inn).strip().replace(" ", "")


def validate_inn(inn, client_type):
    """
    Проверяет корректность ИНН в зависимости от типа клиента.
    """

    normalized_inn = normalize_inn(inn)

    if not normalized_inn:
        return False, "ИНН клиента не заполнен."

    if not normalized_inn.isdigit():
        return False, "ИНН должен содержать только цифры."

    if client_type == "Юридическое лицо" and len(normalized_inn) != 10:
        return False, "Для юридического лица ИНН должен состоять из 10 цифр."

    if client_type in ["Физическое лицо", "Индивидуальный предприниматель"] and len(normalized_inn) != 12:
        return False, "Для физического лица и ИП ИНН должен состоять из 12 цифр."

    return True, ""


def validate_client_input(client_name, inn, client_type, amount, purpose):
    """
    Выполняет общую проверку данных формы.

    Возвращает:
        errors: список критических ошибок;
        warnings: список предупреждений;
        normalized_inn: очищенный ИНН.
    """

    errors = []
    warnings = []

    normalized_inn = normalize_inn(inn)

    if not str(client_name).strip():
        errors.append("Заполните ФИО или наименование клиента.")

    inn_is_valid, inn_error = validate_inn(normalized_inn, client_type)

    if not inn_is_valid:
        errors.append(inn_error)

    if amount <= 0:
        errors.append("Сумма операции должна быть больше 0.")

    if not str(purpose).strip():
        warnings.append(
            "Назначение операции не указано. Система учтет это как небольшой риск-фактор."
        )

    return errors, warnings, normalized_inn