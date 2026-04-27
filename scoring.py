# scoring.py

"""
Модуль расчета уровня риска клиента по 115-ФЗ.
"""

import os

import pandas as pd


BLACKLIST_PATH = os.path.join("data", "blacklist.csv")
HIGH_RISK_COUNTRIES_PATH = os.path.join("data", "high_risk_countries.csv")
SUSPICIOUS_KEYWORDS_PATH = os.path.join("data", "suspicious_keywords.csv")


def load_csv_safely(path):
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path, dtype=str)
    except Exception:
        return pd.DataFrame()


def check_blacklist_by_inn(inn):
    blacklist_df = load_csv_safely(BLACKLIST_PATH)

    if blacklist_df.empty:
        return {
            "found": False,
            "name": "",
            "client_type": "",
            "reason": "Файл стоп-листа не найден или пуст."
        }

    inn = str(inn).strip()

    matched = blacklist_df[
        blacklist_df["inn"].astype(str).str.strip() == inn
    ]

    if matched.empty:
        return {
            "found": False,
            "name": "",
            "client_type": "",
            "reason": ""
        }

    row = matched.iloc[0]

    return {
        "found": True,
        "name": row.get("name", ""),
        "client_type": row.get("client_type", ""),
        "reason": row.get("reason", "Причина не указана")
    }


def check_country_risk(country):
    countries_df = load_csv_safely(HIGH_RISK_COUNTRIES_PATH)

    if countries_df.empty:
        return {
            "found": False,
            "points": 0,
            "reason": ""
        }

    country = str(country).strip().lower()
    countries_df["country_normalized"] = countries_df["country"].astype(str).str.strip().str.lower()

    matched = countries_df[countries_df["country_normalized"] == country]

    if matched.empty:
        return {
            "found": False,
            "points": 0,
            "reason": ""
        }

    row = matched.iloc[0]

    return {
        "found": True,
        "points": int(row.get("risk_points", 0)),
        "reason": row.get("reason", "Страна относится к зоне повышенного риска")
    }


def check_suspicious_keywords(purpose):
    keywords_df = load_csv_safely(SUSPICIOUS_KEYWORDS_PATH)

    if keywords_df.empty:
        return {
            "found": False,
            "keyword": "",
            "points": 0,
            "reason": ""
        }

    purpose_lower = str(purpose).lower()

    for _, row in keywords_df.iterrows():
        keyword = str(row.get("keyword", "")).strip().lower()

        if keyword and keyword in purpose_lower:
            return {
                "found": True,
                "keyword": keyword,
                "points": int(row.get("risk_points", 0)),
                "reason": row.get("reason", "В назначении операции найден подозрительный признак")
            }

    return {
        "found": False,
        "keyword": "",
        "points": 0,
        "reason": ""
    }


def get_empty_purpose_risk(client_type):
    """
    Возвращает риск за незаполненное назначение операции.
    Для физлица риск небольшой, для ИП и юрлица выше.
    """

    if client_type == "Физическое лицо":
        return 5

    if client_type == "Индивидуальный предприниматель":
        return 10

    if client_type == "Юридическое лицо":
        return 15

    return 5


def calculate_client_risk(amount, country, operations_count, purpose, inn, client_type):
    """
    Рассчитывает итоговый уровень риска клиента.
    """

    score = 0
    reasons = []

    purpose = purpose.strip()

    blacklist_result = check_blacklist_by_inn(inn)
    country_result = check_country_risk(country)
    keyword_result = check_suspicious_keywords(purpose)

    if blacklist_result["found"]:
        score += 45
        reasons.append(
            f"Клиент найден во внутреннем стоп-листе. Причина: {blacklist_result['reason']}."
        )

    if amount >= 600_000:
        score += 25
        reasons.append(
            "Сумма операции превышает 600 000 рублей, что требует повышенного внимания."
        )

    if country_result["found"]:
        score += country_result["points"]
        reasons.append(
            f"{country_result['reason']}. Начислено баллов риска: {country_result['points']}."
        )

    if operations_count >= 10:
        score += 20
        reasons.append(
            "Зафиксировано большое количество операций за месяц."
        )

    if not purpose:
        empty_purpose_points = get_empty_purpose_risk(client_type)
        score += empty_purpose_points
        reasons.append(
            f"Назначение операции не указано. Начислено баллов риска: {empty_purpose_points}."
        )
    elif keyword_result["found"]:
        score += keyword_result["points"]
        reasons.append(
            f"{keyword_result['reason']}: «{keyword_result['keyword']}». "
            f"Начислено баллов риска: {keyword_result['points']}."
        )

    if score <= 30:
        risk_level = "Низкий риск"
        recommendation = (
            "Существенных признаков повышенного риска не выявлено. "
            "Клиент может быть принят на обслуживание в стандартном порядке."
        )
        risk_class = "risk-low"
        emoji = "🟢"

    elif score <= 60:
        risk_level = "Средний риск"
        recommendation = (
            "Рекомендуется провести дополнительную проверку клиента, "
            "уточнить экономический смысл операции и запросить подтверждающие документы."
        )
        risk_class = "risk-medium"
        emoji = "🟡"

    else:
        risk_level = "Высокий риск"
        recommendation = (
            "Рекомендуется передать материалы проверки специалисту внутреннего контроля "
            "для проведения углубленного анализа клиента и операции."
        )
        risk_class = "risk-high"
        emoji = "🔴"

    if not reasons:
        reasons.append("Существенных риск-факторов не выявлено.")

    return {
        "score": score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "reasons": reasons,
        "risk_class": risk_class,
        "emoji": emoji,

        "is_blacklisted": blacklist_result["found"],
        "blacklist_reason": blacklist_result["reason"],
        "blacklist_name": blacklist_result["name"],

        "country_risk_found": country_result["found"],
        "country_risk_points": country_result["points"],

        "keyword_found": keyword_result["found"],
        "keyword": keyword_result["keyword"],
        "keyword_points": keyword_result["points"]
    }