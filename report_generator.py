# report_generator.py

"""
Модуль формирования PDF-отчета по результатам проверки клиента.
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


REPORTS_DIR = "reports"


def register_fonts():
    possible_fonts = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/times.ttf"
    ]

    for font_path in possible_fonts:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("CustomFont", font_path))
            return "CustomFont"

    return "Helvetica"


def get_risk_color(risk_level):
    if risk_level == "Низкий риск":
        return colors.HexColor("#16a34a")

    if risk_level == "Средний риск":
        return colors.HexColor("#ca8a04")

    return colors.HexColor("#dc2626")


def generate_pdf_report(
    client_name,
    inn,
    client_type,
    country,
    amount,
    operations_count,
    purpose,
    result
):
    """
    Создает PDF-отчет и возвращает путь к файлу.
    """

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_inn = str(inn).replace(" ", "").replace("/", "_").replace("\\", "_")

    filename = f"report_{safe_inn}_{timestamp}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    font_name = register_fonts()
    risk_color = get_risk_color(result["risk_level"])

    purpose_text = purpose.strip() if purpose.strip() else "Не указано"

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="RussianTitle",
            fontName=font_name,
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=12
        )
    )

    styles.add(
        ParagraphStyle(
            name="RussianSubtitle",
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14
        )
    )

    styles.add(
        ParagraphStyle(
            name="RussianSection",
            fontName=font_name,
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=10,
            spaceAfter=8
        )
    )

    styles.add(
        ParagraphStyle(
            name="RussianText",
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#111827")
        )
    )

    styles.add(
        ParagraphStyle(
            name="RussianSmall",
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b")
        )
    )

    story = []

    header_table = Table(
        [
            [
                Paragraph("<b>115-ФЗ Контроль</b>", styles["RussianTitle"]),
                Paragraph(
                    f"Дата формирования:<br/>{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                    styles["RussianSmall"]
                )
            ]
        ],
        colWidths=[120 * mm, 45 * mm]
    )

    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e2e8f0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "Отчет по результатам проверки клиента",
            styles["RussianTitle"]
        )
    )

    story.append(
        Paragraph(
            "Документ сформирован автоматически программным прототипом сервиса проверки клиентов по требованиям 115-ФЗ.",
            styles["RussianSubtitle"]
        )
    )

    risk_table = Table(
        [
            [
                Paragraph("<b>Итоговый уровень риска</b>", styles["RussianText"]),
                Paragraph(f"<b>{result['risk_level']}</b>", styles["RussianText"])
            ],
            [
                Paragraph("Итоговый балл риска", styles["RussianText"]),
                Paragraph(str(result["score"]), styles["RussianText"])
            ],
            [
                Paragraph("Наличие во внутреннем стоп-листе", styles["RussianText"]),
                Paragraph("Да" if result["is_blacklisted"] else "Нет", styles["RussianText"])
            ]
        ],
        colWidths=[85 * mm, 80 * mm]
    )

    risk_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), risk_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, risk_color),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(risk_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Данные клиента", styles["RussianSection"]))

    client_table = Table(
        [
            ["ФИО / наименование клиента", client_name],
            ["ИНН клиента", inn],
            ["Тип клиента", client_type],
            ["Страна клиента", country],
        ],
        colWidths=[65 * mm, 100 * mm]
    )

    client_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(client_table)

    story.append(Paragraph("2. Параметры операции", styles["RussianSection"]))

    operation_table = Table(
        [
            ["Сумма операции", f"{amount:,.0f} руб."],
            ["Количество операций за месяц", str(operations_count)],
            ["Назначение операции", Paragraph(purpose_text, styles["RussianText"])],
        ],
        colWidths=[65 * mm, 100 * mm]
    )

    operation_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(operation_table)

    story.append(Paragraph("3. Выявленные признаки", styles["RussianSection"]))

    reasons_data = [["№", "Описание признака"]]

    for index, reason in enumerate(result["reasons"], start=1):
        reasons_data.append(
            [
                str(index),
                Paragraph(reason, styles["RussianText"])
            ]
        )

    reasons_table = Table(
        reasons_data,
        colWidths=[15 * mm, 150 * mm]
    )

    reasons_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    story.append(reasons_table)

    story.append(Paragraph("4. Рекомендация системы", styles["RussianSection"]))

    recommendation_table = Table(
        [
            [
                Paragraph(result["recommendation"], styles["RussianText"])
            ]
        ],
        colWidths=[165 * mm]
    )

    recommendation_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, risk_color),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    story.append(recommendation_table)
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Примечание: приложение является учебным программным прототипом и использует демонстрационные справочники риск-факторов. "
            "Результат проверки носит информационный характер и предназначен для демонстрации алгоритма оценки риска.",
            styles["RussianSmall"]
        )
    )

    doc.build(story)

    return filepath