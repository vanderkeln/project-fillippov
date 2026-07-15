import streamlit as st
import pandas as pd
import os
import tempfile
from engine_analyzer import EngineAnalyzer
from i18n import get_text

# Настройка страницы
st.set_page_config(page_title="Engine Diagnostic", layout="wide")

# Инициализация языка
if 'lang' not in st.session_state:
    st.session_state.lang = 'ru'

# Боковая панель с выбором языка
with st.sidebar:
    lang = st.selectbox('🌐 Language / Язык', options=['ru', 'en'],
                        index=0 if st.session_state.lang == 'ru' else 1)
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()  # перезагрузка для применения переводов

# Функция для быстрого доступа к текстам
_ = lambda key: get_text(key, st.session_state.lang)

st.title(_('app_title'))

# --- Основной интерфейс ---
with st.sidebar:
    st.header(_('data_header'))
    uploaded_file = st.file_uploader(_('upload_file'), type=["xlsx", "xls"])
    sheet_name = st.text_input(_('sheet_name'), "DG1")

    st.header(_('simplex_header'))
    numerator = st.text_input(_('numerator'), "Pz")
    denominator = st.text_input(_('denominator'), "Index")

    st.header(_('filter_header'))
    poly_deg = st.selectbox(_('poly_deg'), [1, 2], index=1)
    k_mode = st.radio(_('k_mode'), [_('k_common'), _('k_individual')], index=0)
    if k_mode == _('k_common'):
        k_iqr = st.number_input(_('k_common_label'), value=0.9, step=0.05, format="%.2f")
        k_params = None
    else:
        st.write(_('k_individual_hint'))
        k_params = {}
        param_names = ["Pz", "Pc", "Pi", "Ni", "Index"]
        for p in param_names:
            val = st.number_input(f"k для {p}", value=0.9, step=0.05, format="%.2f", key=f"k_{p}")
            k_params[p.lower()] = val
        k_iqr = None

    run_btn = st.button(_('run_button'), type="primary", use_container_width=True)

# Основная область
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

    with st.spinner(_('running')):
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
        st.success(_('analysis_success'))

        tab1, tab2, tab3, tab4 = st.tabs([
            _('tab_simplex'), _('tab_polynomials'),
            _('tab_correlations'), _('tab_plots')
        ])

        with tab1:
            if os.path.exists("results.xlsx"):
                df = pd.read_excel("results.xlsx", sheet_name="Simplex")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(_('no_results'))

        with tab2:
            if os.path.exists("results.xlsx"):
                df = pd.read_excel("results.xlsx", sheet_name="Polynomials")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(_('no_results'))

        with tab3:
            if os.path.exists("results.xlsx"):
                df = pd.read_excel("results.xlsx", sheet_name="Correlations")
                st.subheader(_('corr_pearson'))
                st.dataframe(df, use_container_width=True)
                df2 = pd.read_excel("results.xlsx", sheet_name="PartialCorr")
                st.subheader(_('corr_partial'))
                st.dataframe(df2, use_container_width=True)
            else:
                st.warning(_('no_results'))

        with tab4:
            if os.path.exists("plots"):
                images = [f for f in os.listdir("plots") if f.endswith(".png")]
                if images:
                    for img in images:
                        st.image(os.path.join("plots", img), caption=img, use_column_width=True)
                else:
                    st.info(_('no_plots'))
            else:
                st.info(_('no_plots'))

        with open("results.xlsx", "rb") as f:
            st.download_button(
                label=_('download_results'),
                data=f,
                file_name="results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        os.unlink(tmp_path)

    else:
        st.error(_('analysis_error'))

elif uploaded_file and not run_btn:
    st.info(_('waiting_run'))
else:
    st.info(_('waiting_file'))

if uploaded_file:
    st.sidebar.success(f"{_('file_loaded')} {uploaded_file.name}")
