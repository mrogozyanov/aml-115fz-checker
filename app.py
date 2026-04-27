import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    delete_all_checks,
    delete_check_by_id,
    get_all_checks,
    get_statistics,
    init_database,
    save_check,
)
from report_generator import generate_pdf_report
from scoring import calculate_client_risk
from validators import validate_client_input


st.set_page_config(
    page_title="Проверка клиентов 115-ФЗ",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_database()


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 4.5rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }

        .main-title {
            font-size: 38px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 6px;
            line-height: 1.15;
        }

        .subtitle {
            font-size: 18px;
            color: #cbd5e1;
            margin-bottom: 34px;
            line-height: 1.4;
        }

        .risk-low {
            background: linear-gradient(135deg, #064e3b, #065f46);
            padding: 24px;
            border-radius: 18px;
            color: white;
            border: 1px solid #10b981;
            box-shadow: 0 12px 32px rgba(16, 185, 129, 0.12);
        }

        .risk-medium {
            background: linear-gradient(135deg, #78350f, #92400e);
            padding: 24px;
            border-radius: 18px;
            color: white;
            border: 1px solid #f59e0b;
            box-shadow: 0 12px 32px rgba(245, 158, 11, 0.12);
        }

        .risk-high {
            background: linear-gradient(135deg, #7f1d1d, #991b1b);
            padding: 24px;
            border-radius: 18px;
            color: white;
            border: 1px solid #ef4444;
            box-shadow: 0 12px 32px rgba(239, 68, 68, 0.12);
        }

        .scale-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 24px;
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.35);
        }

        .scale-card h3 {
            color: #f8fafc;
            margin-top: 0;
            margin-bottom: 12px;
        }

        .scale-card p {
            color: #cbd5e1;
            margin-bottom: 8px;
        }

        .risk-badge-low {
            background-color: #166534;
            color: white;
            padding: 6px 10px;
            border-radius: 10px;
            font-weight: 700;
        }

        .risk-badge-medium {
            background-color: #a16207;
            color: white;
            padding: 6px 10px;
            border-radius: 10px;
            font-weight: 700;
        }

        .risk-badge-high {
            background-color: #b91c1c;
            color: white;
            padding: 6px 10px;
            border-radius: 10px;
            font-weight: 700;
        }

        div[data-testid="stSidebar"] {
            background-color: #020617;
        }

        div[data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        div[data-testid="stMetric"] {
            background-color: #111827;
            border: 1px solid #334155;
            padding: 18px;
            border-radius: 16px;
        }

        div[data-testid="stMetricLabel"] {
            color: #cbd5e1;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        .stButton > button {
            border-radius: 12px;
            height: 48px;
            font-weight: 700;
            font-size: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


with st.sidebar:
    st.markdown("## 🛡️ 115-ФЗ Контроль")
    st.markdown("### Сервис проверки клиентов")
    st.divider()

    page = st.radio(
        "Разделы системы:",
        [
            "🛡️ Проверка клиента",
            "📋 Журнал проверок",
            "📊 Аналитика",
            "📚 Справочники",
            "⚙️ О проекте"
        ]
    )

    st.divider()
    st.caption("Курсовой проект")
    st.caption("Прототип сервиса проверки клиентов")


if page == "🛡️ Проверка клиента":
    st.markdown(
        '<p class="main-title">Проверка клиента по 115-ФЗ</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Оценка клиента по внутренним стоп-листам, параметрам операции и риск-факторам</p>',
        unsafe_allow_html=True
    )

    with st.expander("📌 Как система рассчитывает уровень риска", expanded=True):
        scale_col1, scale_col2 = st.columns(2, gap="large")

        with scale_col1:
            st.markdown(
                """
                <div class="scale-card">
                    <h3>Шкала итогового риска</h3>
                    <p><span class="risk-badge-low">0–30 баллов</span> — низкий риск</p>
                    <p><span class="risk-badge-medium">31–60 баллов</span> — средний риск</p>
                    <p><span class="risk-badge-high">61+ баллов</span> — высокий риск</p>
                    <p>Итоговый уровень определяется по сумме баллов за выявленные риск-факторы.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with scale_col2:
            st.markdown(
                """
                <div class="scale-card">
                    <h3>Основные риск-факторы</h3>
                    <p>• Наличие клиента во внутреннем стоп-листе: <b>+45</b></p>
                    <p>• Сумма операции от 600 000 ₽: <b>+25</b></p>
                    <p>• Страна повышенного риска: <b>+20–30</b></p>
                    <p>• 10 и более операций за месяц: <b>+20</b></p>
                    <p>• Подозрительное назначение операции: <b>+10–25</b></p>
                    <p>• Пустое назначение операции: <b>+5–15</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### 👤 Карточка клиента")

        client_name = st.text_input(
            "ФИО или наименование клиента",
            placeholder="Например: ООО Вектор Поставка"
        )

        inn = st.text_input(
            "ИНН клиента",
            placeholder="Для юрлица — 10 цифр, для физлица и ИП — 12 цифр"
        )

        client_type = st.selectbox(
            "Тип клиента",
            [
                "Физическое лицо",
                "Индивидуальный предприниматель",
                "Юридическое лицо"
            ]
        )

        country = st.selectbox(
            "Страна клиента",
            [
                "Россия",
                "Беларусь",
                "Казахстан",
                "Армения",
                "Киргизия",
                "Иран",
                "Северная Корея",
                "Сирия",
                "Афганистан",
                "Ирак",
                "Ливия",
                "Йемен",
                "Сомали",
                "Судан",
                "Мьянма",
                "Другая страна"
            ]
        )

    with col2:
        st.markdown("### 💳 Параметры операции")

        amount = st.number_input(
            "Сумма операции, руб.",
            min_value=0,
            step=10000,
            value=100000
        )

        operations_count = st.number_input(
            "Количество операций за месяц",
            min_value=0,
            step=1,
            value=1
        )

        purpose = st.text_area(
            "Назначение операции",
            placeholder="Можно оставить пустым. Например: Оплата по договору оказания услуг",
            height=120
        )

    st.divider()

    check_button = st.button(
        "🚀 Выполнить проверку клиента",
        use_container_width=True
    )

    if check_button:
        errors, warnings, normalized_inn = validate_client_input(
            client_name=client_name,
            inn=inn,
            client_type=client_type,
            amount=amount,
            purpose=purpose
        )

        if errors:
            for error in errors:
                st.error(error)
        else:
            for warning in warnings:
                st.warning(warning)

            result = calculate_client_risk(
                amount=amount,
                country=country,
                operations_count=operations_count,
                purpose=purpose,
                inn=normalized_inn,
                client_type=client_type
            )

            report_path = generate_pdf_report(
                client_name=client_name,
                inn=normalized_inn,
                client_type=client_type,
                country=country,
                amount=amount,
                operations_count=operations_count,
                purpose=purpose,
                result=result
            )

            save_check(
                client_name=client_name,
                inn=normalized_inn,
                client_type=client_type,
                country=country,
                amount=amount,
                operations_count=operations_count,
                purpose=purpose,
                is_blacklisted=result["is_blacklisted"],
                result=result,
                report_path=report_path
            )

            st.markdown("## Результат проверки")

            result_col1, result_col2, result_col3 = st.columns(3)

            with result_col1:
                st.metric("Итоговый балл риска", result["score"])

            with result_col2:
                st.metric("Уровень риска", result["risk_level"])

            with result_col3:
                st.metric("Дата проверки", datetime.now().strftime("%d.%m.%Y"))

            purpose_view = purpose.strip() if purpose.strip() else "Не указано"

            st.markdown(
                f"""
                <div class="{result['risk_class']}">
                    <h2>{result['emoji']} {result['risk_level']}</h2>
                    <p><b>Клиент:</b> {client_name}</p>
                    <p><b>ИНН:</b> {normalized_inn}</p>
                    <p><b>Тип клиента:</b> {client_type}</p>
                    <p><b>Страна:</b> {country}</p>
                    <p><b>Сумма операции:</b> {amount:,.0f} руб.</p>
                    <p><b>Назначение операции:</b> {purpose_view}</p>
                    <p><b>Рекомендация:</b> {result['recommendation']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("### Причины присвоения уровня риска")

            for reason in result["reasons"]:
                st.write(f"• {reason}")

            if result["is_blacklisted"]:
                st.error(
                    f"Совпадение по внутреннему стоп-листу: "
                    f"{result['blacklist_name']} — {result['blacklist_reason']}"
                )
            else:
                st.info("По внутреннему стоп-листу совпадений не найдено.")

            st.success("Проверка выполнена, сохранена в журнал, PDF-отчет сформирован.")

            with open(report_path, "rb") as pdf_file:
                st.download_button(
                    label="📄 Скачать PDF-отчет по проверке",
                    data=pdf_file,
                    file_name=os.path.basename(report_path),
                    mime="application/pdf",
                    use_container_width=True
                )

            st.caption(f"PDF-отчет сохранен в папку проекта: {report_path}")


elif page == "📋 Журнал проверок":
    st.markdown(
        '<p class="main-title">Журнал проверок клиентов</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">История всех выполненных проверок клиентов и операций</p>',
        unsafe_allow_html=True
    )

    checks_df = get_all_checks()

    if checks_df.empty:
        st.info("Журнал пока пуст. Выполните первую проверку клиента, чтобы запись появилась здесь.")
    else:
        st.success(f"В журнале найдено записей: {len(checks_df)}")

        visible_columns = [
            "ID",
            "Дата и время",
            "Клиент",
            "ИНН",
            "Тип клиента",
            "Страна",
            "Сумма операции",
            "Операций за месяц",
            "Балл риска",
            "Уровень риска",
            "Стоп-лист",
            "Назначение операции",
            "Причины",
            "Рекомендация"
        ]

        st.markdown("### Фильтры журнала")

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

        with filter_col1:
            search_query = st.text_input(
                "Поиск по клиенту или ИНН",
                placeholder="Введите имя, компанию или ИНН"
            )

        with filter_col2:
            risk_filter = st.multiselect(
                "Уровень риска",
                ["Низкий риск", "Средний риск", "Высокий риск"],
                default=["Низкий риск", "Средний риск", "Высокий риск"]
            )

        with filter_col3:
            client_type_filter = st.multiselect(
                "Тип клиента",
                ["Физическое лицо", "Индивидуальный предприниматель", "Юридическое лицо"],
                default=["Физическое лицо", "Индивидуальный предприниматель", "Юридическое лицо"]
            )

        with filter_col4:
            stoplist_filter = st.selectbox(
                "Стоп-лист",
                ["Все", "Да", "Нет"]
            )

        filtered_df = checks_df.copy()

        if search_query.strip():
            query = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["Клиент"].astype(str).str.lower().str.contains(query, na=False)
                | filtered_df["ИНН"].astype(str).str.lower().str.contains(query, na=False)
            ]

        if risk_filter:
            filtered_df = filtered_df[filtered_df["Уровень риска"].isin(risk_filter)]

        if client_type_filter:
            filtered_df = filtered_df[filtered_df["Тип клиента"].isin(client_type_filter)]

        if stoplist_filter != "Все":
            filtered_df = filtered_df[filtered_df["Стоп-лист"] == stoplist_filter]

        st.divider()

        st.markdown("### Таблица проверок")

        if filtered_df.empty:
            st.warning("По выбранным фильтрам записи не найдены.")
        else:
            st.info(f"Показано записей: {len(filtered_df)} из {len(checks_df)}")

            st.dataframe(
                filtered_df[visible_columns],
                use_container_width=True,
                hide_index=True
            )

            csv_data = filtered_df[visible_columns].to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                label="⬇️ Скачать отфильтрованный журнал в CSV",
                data=csv_data,
                file_name="filtered_journal_115fz_checks.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.divider()

            st.markdown("### PDF-отчеты")

            check_options = filtered_df.apply(
                lambda row: f"ID {row['ID']} — {row['Клиент']} — {row['Уровень риска']}",
                axis=1
            ).tolist()

            selected_report_check = st.selectbox(
                "Выберите проверку для скачивания PDF-отчета",
                check_options,
                key="report_selectbox"
            )

            selected_report_id = int(selected_report_check.split(" — ")[0].replace("ID ", ""))
            selected_row = filtered_df[filtered_df["ID"] == selected_report_id].iloc[0]
            selected_report_path = selected_row["Путь PDF"]

            if isinstance(selected_report_path, str) and os.path.exists(selected_report_path):
                with open(selected_report_path, "rb") as pdf_file:
                    st.download_button(
                        label="📄 Скачать PDF-отчет выбранной проверки",
                        data=pdf_file,
                        file_name=os.path.basename(selected_report_path),
                        mime="application/pdf",
                        use_container_width=True
                    )
            else:
                st.warning(
                    "PDF-файл для этой проверки не найден. "
                    "Это может быть старая запись, созданная до добавления PDF-отчетов."
                )

            st.divider()

            st.markdown("### Управление журналом")

            col_delete_one, col_delete_all = st.columns(2)

            with col_delete_one:
                st.markdown("#### Удалить одну проверку")

                selected_delete_check = st.selectbox(
                    "Выберите проверку для удаления",
                    check_options,
                    key="delete_selectbox"
                )

                selected_delete_id = int(selected_delete_check.split(" — ")[0].replace("ID ", ""))

                if st.button("🗑️ Удалить выбранную проверку и PDF-отчет", use_container_width=True):
                    delete_check_by_id(selected_delete_id)
                    st.success("Проверка и связанный PDF-отчет удалены.")
                    st.rerun()

            with col_delete_all:
                st.markdown("#### Очистить весь журнал")

                st.warning("Это действие удалит все проверки из базы данных и все связанные PDF-отчеты.")

                confirm_delete_all = st.checkbox(
                    "Я подтверждаю очистку всего журнала"
                )

                if st.button("⚠️ Очистить журнал и PDF-отчеты", use_container_width=True):
                    if confirm_delete_all:
                        delete_all_checks()
                        st.success("Журнал проверок и PDF-отчеты полностью очищены.")
                        st.rerun()
                    else:
                        st.error("Сначала поставьте галочку подтверждения.")


elif page == "📊 Аналитика":
    st.markdown(
        '<p class="main-title">Аналитика клиентских рисков</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Раздел для анализа результатов проверок и структуры выявленных рисков</p>',
        unsafe_allow_html=True
    )

    stats = get_statistics()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Всего проверок", stats["total_checks"])

    with col2:
        st.metric("Низкий риск", stats["low_risk"])

    with col3:
        st.metric("Средний риск", stats["medium_risk"])

    with col4:
        st.metric("Высокий риск", stats["high_risk"])

    st.divider()

    if stats["total_checks"] == 0:
        st.info("Пока нет данных для аналитики. Выполните несколько проверок клиентов.")
    else:
        st.metric("Средний балл риска", stats["average_score"])

        checks_df = get_all_checks()

        risk_order = ["Низкий риск", "Средний риск", "Высокий риск"]

        risk_counts = (
            checks_df["Уровень риска"]
            .value_counts()
            .reindex(risk_order, fill_value=0)
            .reset_index()
        )

        risk_counts.columns = ["Уровень риска", "Количество проверок"]

        color_map = {
            "Низкий риск": "#22c55e",
            "Средний риск": "#facc15",
            "Высокий риск": "#ef4444"
        }

        st.markdown("### Распределение проверок по уровню риска")

        fig = px.bar(
            risk_counts,
            x="Уровень риска",
            y="Количество проверок",
            color="Уровень риска",
            color_discrete_map=color_map,
            text="Количество проверок"
        )

        fig.update_traces(
            textposition="outside",
            marker_line_width=0
        )

        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            xaxis=dict(
                title="Уровень риска",
                gridcolor="rgba(148, 163, 184, 0.2)"
            ),
            yaxis=dict(
                title="Количество проверок",
                gridcolor="rgba(148, 163, 184, 0.2)",
                tickformat="d"
            )
        )

        st.plotly_chart(fig, use_container_width=True)


elif page == "📚 Справочники":
    st.markdown(
        '<p class="main-title">Справочники системы</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Демонстрационные справочники, используемые при проверке клиента</p>',
        unsafe_allow_html=True
    )

    st.info(
        "Эти таблицы используются системой для автоматического расчета риска. "
        "В рамках курсового проекта данные являются демонстрационными."
    )

    blacklist_path = os.path.join("data", "blacklist.csv")
    countries_path = os.path.join("data", "high_risk_countries.csv")
    keywords_path = os.path.join("data", "suspicious_keywords.csv")

    st.markdown("## 🚫 Внутренний стоп-лист клиентов")

    if os.path.exists(blacklist_path):
        blacklist_df = pd.read_csv(blacklist_path, dtype=str)
        st.dataframe(blacklist_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Файл data/blacklist.csv не найден.")

    st.divider()

    st.markdown("## 🌍 Страны повышенного риска")

    if os.path.exists(countries_path):
        countries_df = pd.read_csv(countries_path, dtype=str)
        st.dataframe(countries_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Файл data/high_risk_countries.csv не найден.")

    st.divider()

    st.markdown("## 🔎 Подозрительные признаки в назначении операции")

    if os.path.exists(keywords_path):
        keywords_df = pd.read_csv(keywords_path, dtype=str)
        st.dataframe(keywords_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Файл data/suspicious_keywords.csv не найден.")


elif page == "⚙️ О проекте":
    st.markdown(
        '<p class="main-title">О проекте</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Описание назначения и возможностей программного прототипа</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        ### Назначение системы

        Данное приложение является программным прототипом сервиса проверки клиентов
        на предмет рисков, связанных с требованиями Федерального закона №115-ФЗ.

        Система предназначена для первичной оценки клиента и операции по совокупности признаков.

        ### Основные функции

        - ввод данных клиента;
        - проверка корректности введенного ИНН;
        - проверка обязательных полей формы;
        - автоматическая проверка клиента по внутреннему стоп-листу;
        - анализ страны клиента по справочнику стран повышенного риска;
        - анализ назначения операции по справочнику подозрительных признаков;
        - учет отсутствующего назначения операции как небольшого риск-фактора;
        - расчет итогового балла риска;
        - присвоение уровня риска;
        - формирование рекомендации для специалиста внутреннего контроля;
        - автоматическое сохранение результатов проверки;
        - формирование PDF-отчета по результатам проверки;
        - скачивание PDF-отчета из журнала проверок;
        - поиск и фильтрация журнала проверок;
        - выгрузка журнала проверок в CSV;
        - просмотр используемых справочников;
        - удаление отдельных записей вместе с PDF-отчетом;
        - очистка журнала вместе со всеми PDF-отчетами;
        - отображение аналитики по уровням риска;
        - отображение шкалы риск-скоринга.

        ### Логика проверки

        В приложении используется риск-ориентированный подход.  
        Итоговый уровень риска формируется не только по факту наличия клиента в базе,
        но и по дополнительным признакам:

        - сумма операции;
        - страна клиента;
        - количество операций за месяц;
        - назначение операции;
        - отсутствие назначения операции;
        - наличие клиента во внутреннем стоп-листе.

        ### Используемые технологии

        - Python;
        - Streamlit;
        - SQLite;
        - Pandas;
        - Plotly;
        - ReportLab.

        ### Важно

        Приложение является учебным прототипом и не подключается к реальным государственным базам данных.
        Проверка выполняется на основе демонстрационного риск-скоринга и внутренних справочников.
        """
    )