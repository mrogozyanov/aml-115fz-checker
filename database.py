# database.py

"""
Модуль работы с базой данных SQLite.

В базе данных хранится журнал проверок клиентов:
- дата и время проверки;
- данные клиента;
- параметры операции;
- итоговый балл риска;
- уровень риска;
- причины;
- рекомендация системы;
- путь к PDF-отчету.
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd


DB_NAME = "aml_checks.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    return connection


def init_database():
    """
    Создает таблицу проверок, если она еще не существует.
    Также добавляет недостающие колонки, если база уже была создана раньше.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_datetime TEXT NOT NULL,
            client_name TEXT NOT NULL,
            inn TEXT NOT NULL,
            client_type TEXT NOT NULL,
            country TEXT NOT NULL,
            amount REAL NOT NULL,
            operations_count INTEGER NOT NULL,
            purpose TEXT NOT NULL,
            is_blacklisted INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            reasons TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            report_path TEXT
        )
        """
    )

    cursor.execute("PRAGMA table_info(checks)")
    columns = [column[1] for column in cursor.fetchall()]

    if "report_path" not in columns:
        cursor.execute("ALTER TABLE checks ADD COLUMN report_path TEXT")

    connection.commit()
    connection.close()


def save_check(
    client_name,
    inn,
    client_type,
    country,
    amount,
    operations_count,
    purpose,
    is_blacklisted,
    result,
    report_path
):
    """
    Сохраняет результат проверки клиента в базу данных.
    """

    connection = get_connection()
    cursor = connection.cursor()

    check_datetime = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    reasons_text = "; ".join(result["reasons"])
    purpose_text = purpose if purpose.strip() else "Не указано"

    cursor.execute(
        """
        INSERT INTO checks (
            check_datetime,
            client_name,
            inn,
            client_type,
            country,
            amount,
            operations_count,
            purpose,
            is_blacklisted,
            risk_score,
            risk_level,
            reasons,
            recommendation,
            report_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            check_datetime,
            client_name,
            inn,
            client_type,
            country,
            amount,
            operations_count,
            purpose_text,
            int(is_blacklisted),
            result["score"],
            result["risk_level"],
            reasons_text,
            result["recommendation"],
            report_path
        )
    )

    connection.commit()
    connection.close()


def get_all_checks():
    """
    Возвращает все проверки из базы данных в виде DataFrame.
    """

    connection = get_connection()

    query = """
        SELECT
            id AS "ID",
            check_datetime AS "Дата и время",
            client_name AS "Клиент",
            inn AS "ИНН",
            client_type AS "Тип клиента",
            country AS "Страна",
            amount AS "Сумма операции",
            operations_count AS "Операций за месяц",
            risk_score AS "Балл риска",
            risk_level AS "Уровень риска",
            is_blacklisted AS "Стоп-лист",
            purpose AS "Назначение операции",
            reasons AS "Причины",
            recommendation AS "Рекомендация",
            report_path AS "Путь PDF"
        FROM checks
        ORDER BY id DESC
    """

    dataframe = pd.read_sql_query(query, connection)
    connection.close()

    if not dataframe.empty:
        dataframe["Стоп-лист"] = dataframe["Стоп-лист"].apply(
            lambda value: "Да" if value == 1 else "Нет"
        )

    return dataframe


def get_check_by_id(check_id):
    """
    Возвращает одну проверку по ID.
    """

    connection = get_connection()

    query = """
        SELECT
            id AS "ID",
            check_datetime AS "Дата и время",
            client_name AS "Клиент",
            inn AS "ИНН",
            client_type AS "Тип клиента",
            country AS "Страна",
            amount AS "Сумма операции",
            operations_count AS "Операций за месяц",
            risk_score AS "Балл риска",
            risk_level AS "Уровень риска",
            is_blacklisted AS "Стоп-лист",
            purpose AS "Назначение операции",
            reasons AS "Причины",
            recommendation AS "Рекомендация",
            report_path AS "Путь PDF"
        FROM checks
        WHERE id = ?
    """

    dataframe = pd.read_sql_query(query, connection, params=(check_id,))
    connection.close()

    if dataframe.empty:
        return None

    row = dataframe.iloc[0].to_dict()
    row["Стоп-лист"] = "Да" if row["Стоп-лист"] == 1 else "Нет"

    return row


def get_statistics():
    """
    Возвращает базовую статистику по проверкам.
    """

    dataframe = get_all_checks()

    if dataframe.empty:
        return {
            "total_checks": 0,
            "low_risk": 0,
            "medium_risk": 0,
            "high_risk": 0,
            "average_score": 0
        }

    return {
        "total_checks": len(dataframe),
        "low_risk": len(dataframe[dataframe["Уровень риска"] == "Низкий риск"]),
        "medium_risk": len(dataframe[dataframe["Уровень риска"] == "Средний риск"]),
        "high_risk": len(dataframe[dataframe["Уровень риска"] == "Высокий риск"]),
        "average_score": round(dataframe["Балл риска"].mean(), 1)
    }


def delete_file_if_exists(filepath):
    """
    Удаляет файл, если он существует.
    """

    if filepath and isinstance(filepath, str) and os.path.exists(filepath):
        os.remove(filepath)


def delete_check_by_id(check_id):
    """
    Удаляет одну проверку из журнала по ID и удаляет связанный PDF-отчет.
    """

    check = get_check_by_id(check_id)

    if check:
        delete_file_if_exists(check.get("Путь PDF"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM checks WHERE id = ?",
        (check_id,)
    )

    connection.commit()
    connection.close()


def delete_all_checks():
    """
    Полностью очищает журнал проверок и удаляет связанные PDF-отчеты.
    """

    checks_df = get_all_checks()

    if not checks_df.empty and "Путь PDF" in checks_df.columns:
        for filepath in checks_df["Путь PDF"].dropna().tolist():
            delete_file_if_exists(filepath)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM checks")

    connection.commit()
    connection.close()