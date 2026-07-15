import streamlit as st
import pandas as pd
import os
import tempfile
from engine_analyzer import EngineAnalyzer
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Engine Diagnostic", layout="wide")

# ---------- Настройка языка ----------
if 'lang' not in st.session_state:
    st.session_state.lang = 'ru'

# Список поддерживаемых языков
LANGUAGES = {
    'ru': 'Русский',
    'en': 'English',
    'de': 'Deutsch',
    'fr': 'Français',
    'es': 'Español',
    'zh-CN': '中文',
    'ja': '日本語',
    'ko': '한국어'
}

# ---------- Переключатель в боковой панели ----------
with st.sidebar:
    st.markdown("### 🌐 Язык / Language")
    lang = st.selectbox(
        "",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=0 if st.session_state.lang == 'ru' else list(LANGUAGES.keys()).index(st.session_state.lang)
    )
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()

# ---------- Функция перевода (с кешированием) ----------
@st.cache_data(ttl=3600)
def translate_text(text, target_lang):
    if target_lang == 'ru':
        return text
    try:
        return GoogleTranslator(source='ru', target=target_lang).translate(text)
    except Exception:
        return text  # в случае ошибки возвращаем оригинал

# ---------- Русские тексты ----------
RUSSIAN_TEXTS = {
    'title': '🚀 Диагностический анализ двигателя',
    'data': '📂 Данные',
    'upload': 'Загрузите Excel-файл',
    'sheet': 'Имя листа',
    'simplex': '🧮 Симплекс',
    'num': 'Числитель',
    'den': 'Знаменатель',
    'filter': '📊 Фильтрация',
    'poly': 'Степень полинома',
    'k_mode': 'Режим коэффициента IQR',
    'k_common': 'Общий',
    'k_individual': 'Индивидуальный',
    'k_label': 'Общий коэффициент k',
    'k_hint': 'Введите коэффициенты для каждого параметра:',
    'run': '🔍 Запустить анализ',
    'running': '⏳ Выполняется анализ...',
    'success': '✅ Анализ завершён успешно!',
    'error': '❌ Ошибка при выполнении анализа. Проверьте логи выше.',
    'wait_file': '👈 Загрузите Excel-файл и настройте параметры.',
    'wait_run': '👆 Настройте параметры и нажмите кнопку запуска.',
    'tab1': '📊 Симплекс',
    'tab2': '📈 Коэффициенты',
    'tab3': '📉 Корреляции',
    'tab4': '🖼 Графики',
    'corr_pearson': 'Корреляции Пирсона',
    'corr_partial': 'Частные корреляции (контроль по Index)',
    'download': '📥 Скачать результаты (Excel)',
    'no_results': 'Файл результатов не найден.',
    'no_plots': 'Графики не найдены.',
    'file_loaded': 'Файл загружен:'
}

# ---------- Перевод всего интерфейса ----------
def _(text):
    return translate_text(text, st.session_state.lang)

st.title(_(RUSSIAN_TEXTS['title']))

# --- Боковая панель ---
with st.sidebar:
    st.header(_(RUSSIAN_TEXTS['data']))
    uploaded_file = st.file_uploader(_(RUSSIAN_TEXTS['upload']), type=["xlsx", "xls"])
    sheet_name = st.text_input(_(RUSSIAN_TEXTS['sheet']), "DG1")

    st.header(_(RUSSIAN_TEXTS['simplex']))
    numerator = st.text_input(_(RUSSIAN_TEXTS['num']), "Pz")
    denominator = st.text_input(_(RUSSIAN_TEXTS['den']), "Index")

    st.header(_(RUSSIAN_TEXTS['filter']))
    poly_deg = st.selectbox(_(RUSSIAN_TEXTS['poly']), [1, 2], index=1)
    k_mode = st.radio(_(RUSSIAN_TEXTS['k_mode']), [_(RUSSIAN_TEXTS['k_common']), _(RUSSIAN_TEXTS['k_individual'])], index=0)
    
    if k_mode == _(RUSSIAN_TEXTS['k_common']):
        k_iqr = st.number_input(_(RUSSIAN_TEXTS['k_label']), value=0.9, step=0.05, format="%.2f")
        k_params = None
    else:
        st.write(_(RUSSIAN_TEXTS['k_hint']))
        k_params = {}
        param_names = ["Pz", "Pc", "Pi", "Ni", "Index"]
        for p in param_names:
            val = st.number_input(f"k для {p}", value=0.9, step=0.05, format="%.2f", key=f"k_{p}")
            k_params[p.lower()] = val
        k_iqr = None

    run_btn = st.button(_(RUSSIAN_TEXTS['run']), type="primary", use_container_width=True)

# --- Основная область ---
if uploaded_file and run_btn:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    log_container = st.container()
    log_placeholder = log_container.empty()
    log_messages = []

    def log_callback(msg):
        log_messages.append(msg)
        log_placeholder.text("\n".join(log_messages[-20:]))

    with st.spinner(_(RUSSIAN_TEXTS['running'])):
        analyzer = EngineAnalyzer(
            file_path=tmp_path,
            sheet_name=sheet_name,
            numerator=numerator,
            denominator=denominator,
            poly_deg=poly_deg,
            k_iqr=k_iqr,
            k_params=k_params
        )
        success = analyzer.run(log_callback=log_callback)

    if success:
        st.success(_(RUSSIAN_TEXTS['success']))

        tab1, tab2, tab3, tab4 = st.tabs([
            _(RUSSIAN_TEXTS['tab1']),
            _(RUSSIAN_TEXTS['tab2']),
            _(RUSSIAN_TEXTS['tab3']),
            _(RUSSIAN_TEXTS['tab4'])
        ])

        with tab1:
            if os.path.exists("results.xlsx"):
                df = pd.read_excel("results.xlsx", sheet_name="Simplex")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(_(RUSSIAN_TEXTS['no_results']))

        with tab2:
            if os.path.exists("results.xlsx"):
                df = pd.read_excel("results.xlsx", sheet_name="Polynomials")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(_(RUSSIAN_TEXTS['no_results']))

        with tab3:
            if os.path.exists("results.xlsx"):
                df = pd.read_excel("results.xlsx", sheet_name="Correlations")
                st.subheader(_(RUSSIAN_TEXTS['corr_pearson']))
                st.dataframe(df, use_container_width=True)
                df2 = pd.read_excel("results.xlsx", sheet_name="PartialCorr")
                st.subheader(_(RUSSIAN_TEXTS['corr_partial']))
                st.dataframe(df2, use_container_width=True)
            else:
                st.warning(_(RUSSIAN_TEXTS['no_results']))

        with tab4:
            if os.path.exists("plots"):
                images = [f for f in os.listdir("plots") if f.endswith(".png")]
                if images:
                    for img in images:
                        st.image(os.path.join("plots", img), caption=img, use_column_width=True)
                else:
                    st.info(_(RUSSIAN_TEXTS['no_plots']))
            else:
                st.info(_(RUSSIAN_TEXTS['no_plots']))

        with open("results.xlsx", "rb") as f:
            st.download_button(
                label=_(RUSSIAN_TEXTS['download']),
                data=f,
                file_name="results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        os.unlink(tmp_path)

    else:
        st.error(_(RUSSIAN_TEXTS['error']))

elif uploaded_file and not run_btn:
    st.info(_(RUSSIAN_TEXTS['wait_run']))
else:
    st.info(_(RUSSIAN_TEXTS['wait_file']))

if uploaded_file:
    st.sidebar.success(f"{_(RUSSIAN_TEXTS['file_loaded'])} {uploaded_file.name}")
