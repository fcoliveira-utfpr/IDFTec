// ==========================================
// IDFTec Data — i18n (English default, Portuguese toggle)
// ==========================================
const I18N = {
  en: {
    // shared
    brand: 'IDFTec Data',
    system_active: 'System Active',
    menu_home: 'Home',
    menu_map: 'IDF Map',
    footer_text: 'IDFTec Data — UTFPR Campus Santa Helena',
    lang_toggle_label: 'PT',
    lang_toggle_title: 'Switch to Portuguese',

    // index.html
    index_title: 'IDFTec Data',
    header_subtitle: 'IDF curves for Brazil, by municipality',
    btn_map: 'MAP',
    hero_title: 'Intensity-Duration-Frequency Curves for Brazil',
    hero_desc: 'IDF curves calculated for 5,569 Brazilian municipalities from the annual maximum daily rainfall series (1961–2025, Xavier BR-DWGD grid), with extreme value distribution fitting (Gumbel, GEV, Log-Normal, Weibull, Gamma or Normal, whichever fits best) and rainfall disaggregation using DAEE/CETESB factors. Explore the interactive map to see the curve, coefficients and projected intensity for each municipality.',
    card_title: 'Interactive IDF curve map',
    card_desc: 'Choose a state and a municipality to see the map colored by the variable of your choice, the coefficients of the IDF equation, and the intensity × duration chart for return periods from 5 to 100 years.',
    card_link: 'Open map',
    stat1_value: '5,569',
    stat1_label: 'municipalities with IDF curve',
    stat2_value: '65',
    stat2_label: 'years of data (1961–2025)',
    stat3_value: '6',
    stat3_label: 'statistical distributions tested',
    stat4_value: '0.999',
    stat4_label: 'average R² of the IDF fit',
    data_source: 'Data: annual maximum daily rainfall 1961–2025 (Xavier BR-DWGD, via Google Earth Engine) · Mesh: IBGE via geodata-br',
    warning_text_html: 'The <b>b</b> and <b>c</b> coefficients of the IDF equation come out nearly constant across all of Brazil — an effect of the DAEE/CETESB disaggregation factors (regional, from São Paulo) applied nationwide due to the lack of available regionalized factors, not a real finding about the sub-daily rainfall regime of each region. See the full methodological limitations in the repository.',

    // idf.html
    idf_page_title: 'IDFTec Data — IDF Curves by Municipality',
    header_subtitle2: 'Intensity-Duration-Frequency Curves by Municipality',
    panel_title: 'Parameters',
    label_color_by: 'Color map by:',
    metric_intensity: 'Intensity TR=100 years, 24h (mm/h)',
    metric_rain: 'Average annual max daily rainfall (mm)',
    metric_k: 'IDF equation coefficient k',
    label_state: 'State:',
    label_municipality: 'Municipality:',
    select_state_placeholder: 'Select a state...',
    select_municipality_placeholder: 'Select a municipality...',
    hint_text: 'Choose a municipality from the list or click directly on the map.',
    data_source_title: 'Data Source',
    data_source_body_html: 'Annual maximum daily rainfall, 1961–2025<br>Xavier BR-DWGD grid (Google Earth Engine)<br>Mesh: IBGE via geodata-br<br>IDF curve: I(T,t) = k·T<sup>a</sup>/(t+b)<sup>c</sup>',
    status_waiting: 'Waiting...',
    status_curves_waiting: 'IDF curves: waiting...',
    btn_csv: 'CSV',
    detail_idf_curve_title: 'IDF Curve — Intensity × Duration',
    chart_loading_idf: 'Loading IDF curve...',
    chart_empty_idf: 'No IDF curve calculated for this municipality.',
    detail_series_title: 'Historical Series — Annual Maximum Daily Rainfall',
    chart_loading_series: 'Loading historical series...',
    chart_empty_series: 'No historical series available for this municipality.',
    series_note: 'Light bars: year estimated from neighborhood average (municipality pixel without direct data).',
    warning_text2_html: 'The <b>b</b> and <b>c</b> coefficients of the IDF equation are nearly constant across all of Brazil — an effect of the DAEE/CETESB disaggregation factors (regional, from São Paulo) applied nationwide.',

    // idf.html dynamic strings
    msg_loading_resumo: 'Loading IDF curve summary...',
    msg_loading_grid: 'Loading geographic grid...',
    msg_loading_grid_uf: uf => `Loading grid for ${uf}…`,
    status_processing: 'Processing…',
    status_loading_grid: 'Loading geographic grid…',
    status_ready: uf => `${uf} — IDF ✓`,
    status_error_grid: 'Error loading grid',
    status_error_resumo: 'Error loading IDF summary',
    curvas_loading: uf => `IDF curves for ${uf}: loading...`,
    curvas_ready: uf => `IDF curves for ${uf} ready ✓`,
    curvas_error: uf => `Error loading IDF curves for ${uf}`,

    tooltip_municipio_label: 'Municipality:',
    badge_distribution: d => `Distribution: ${d}`,
    badge_neighborhood_pct: p => `${p}% of years by neighborhood average`,
    idx_rain_avg: 'Avg. annual max daily rainfall',
    idx_intensity: 'Intensity TR=100y, 24h',
    idx_coef_k: 'Coefficient k',
    idx_coef_a: 'Coefficient a',
    idx_coef_b: 'Coefficient b',
    idx_coef_c: 'Coefficient c',
    idx_years_data: 'Years of data',
    no_idf_curve_available: 'No IDF curve available for this municipality.',
    ibge_code_label: (code, uf) => `IBGE code: ${code} · ${uf}`,
    detail_title_placeholder: '—',
    unknown_municipality: 'Unknown',
    no_data: 'no data',

    chart_x_duration: 'Duration (min)',
    chart_y_intensity: 'Intensity (mm/h)',
    chart_tr_label: tr => `TR = ${tr} years`,
    chart_x_year: 'Year',
    chart_y_rain: 'Max daily rainfall (mm)',
    series_dataset_label: 'Max daily rainfall (mm)',
    tooltip_year_title: y => `Year ${y}`,
    tooltip_no_data: 'no data',
    tooltip_estimated_suffix: '(estimated from neighborhood)',

    alert_select_municipality_first: 'Select a municipality first.',
    alert_no_idf_curve: 'No IDF curve for this municipality.',
    alert_no_series: 'Historical series unavailable for this municipality (still loading or not covered).',

    csv_header1: '# IDFTec Data — IDF curves — municipality data',
    csv_source: '# Source: annual maximum daily rainfall 1961-2025, Xavier BR-DWGD grid, via Google Earth Engine',
    csv_block1: '# Block 1: IDF equation coefficients and annual variables',
    csv_block2: '# Block 2: intensity (mm/h) by duration and return period',
    csv_block2_unavailable: '# IDF curve unavailable (still loading or no coverage for this state)',
    csv_series_header1: '# IDFTec Data — Historical series of annual maximum daily rainfall',
    csv_series_municipality: (nome, code, uf) => `# Municipality: ${nome} (IBGE code ${code}, ${uf})`,
    csv_series_source: '# Source: annual maximum daily rainfall, Xavier BR-DWGD grid, via Google Earth Engine, 1961-2025',
  },
  pt: {
    brand: 'IDFTec Data',
    system_active: 'Sistema Ativo',
    menu_home: 'Início',
    menu_map: 'Mapa IDF',
    footer_text: 'IDFTec Data — UTFPR Campus Santa Helena',
    lang_toggle_label: 'EN',
    lang_toggle_title: 'Mudar para inglês',

    index_title: 'IDFTec Data',
    header_subtitle: 'Curvas IDF do Brasil, por município',
    btn_map: 'MAPA',
    hero_title: 'Curvas Intensidade-Duração-Frequência do Brasil',
    hero_desc: 'Curvas IDF calculadas para 5.569 municípios brasileiros a partir da série de chuva máxima diária anual (1961–2025, grade Xavier BR-DWGD), com ajuste de distribuição de valores extremos (Gumbel, GEV, Log-Normal, Weibull, Gama ou Normal, conforme melhor aderência) e desagregação de chuva pelos fatores DAEE/CETESB. Explore o mapa interativo para ver a curva, os coeficientes e a intensidade projetada de cada município.',
    card_title: 'Mapa interativo de curvas IDF',
    card_desc: 'Escolha um estado e um município para ver o mapa colorido pela variável de sua escolha, os coeficientes da equação IDF, e o gráfico intensidade × duração para os períodos de retorno de 5 a 100 anos.',
    card_link: 'Abrir mapa',
    stat1_value: '5.569',
    stat1_label: 'municípios com curva IDF',
    stat2_value: '65',
    stat2_label: 'anos de dados (1961–2025)',
    stat3_value: '6',
    stat3_label: 'distribuições estatísticas testadas',
    stat4_value: '0,999',
    stat4_label: 'R² médio do ajuste IDF',
    data_source: 'Dados: chuva máxima diária anual 1961–2025 (Xavier BR-DWGD, via Google Earth Engine) · Malha: IBGE via geodata-br',
    warning_text_html: 'Os coeficientes <b>b</b> e <b>c</b> da equação IDF saem praticamente constantes em todo o Brasil — efeito dos fatores de desagregação DAEE/CETESB (regionais, de SP) aplicados nacionalmente por falta de fatores regionalizados disponíveis, não uma descoberta real sobre o regime de chuva sub-diária de cada região. Ver limitações metodológicas completas no repositório.',

    idf_page_title: 'IDFTec Data — Curvas IDF por Município',
    header_subtitle2: 'Curvas Intensidade-Duração-Frequência por Município',
    panel_title: 'Parâmetros',
    label_color_by: 'Colorir mapa por:',
    metric_intensity: 'Intensidade TR=100 anos, 24h (mm/h)',
    metric_rain: 'Chuva máxima diária anual média (mm)',
    metric_k: 'Coeficiente k da equação IDF',
    label_state: 'Estado (UF):',
    label_municipality: 'Município:',
    select_state_placeholder: 'Selecione um estado...',
    select_municipality_placeholder: 'Selecione um município...',
    hint_text: 'Escolha um município na lista ou clique diretamente no mapa.',
    data_source_title: 'Fonte de Dados',
    data_source_body_html: 'Chuva máxima diária anual, 1961–2025<br>Grade Xavier BR-DWGD (Google Earth Engine)<br>Malha: IBGE via geodata-br<br>Curva IDF: I(T,t) = k·T<sup>a</sup>/(t+b)<sup>c</sup>',
    status_waiting: 'A aguardar...',
    status_curves_waiting: 'Curvas IDF: a aguardar...',
    btn_csv: 'CSV',
    detail_idf_curve_title: 'Curva IDF — Intensidade × Duração',
    chart_loading_idf: 'Carregando curva IDF...',
    chart_empty_idf: 'Sem curva IDF calculada para este município.',
    detail_series_title: 'Série Histórica — Chuva Máxima Diária Anual',
    chart_loading_series: 'Carregando série histórica...',
    chart_empty_series: 'Sem série histórica disponível para este município.',
    series_note: 'Barras claras: ano estimado por média da vizinhança (pixel do município sem dado direto).',
    warning_text2_html: 'Os coeficientes <b>b</b> e <b>c</b> da equação IDF são praticamente constantes em todo o Brasil — efeito dos fatores de desagregação DAEE/CETESB (regionais, de SP) aplicados nacionalmente.',

    msg_loading_resumo: 'Carregando resumo das curvas IDF...',
    msg_loading_grid: 'Carregando grade geográfica...',
    msg_loading_grid_uf: uf => `Carregando grade de ${uf}…`,
    status_processing: 'Processando…',
    status_loading_grid: 'Carregando grade geográfica…',
    status_ready: uf => `${uf} — IDF ✓`,
    status_error_grid: 'Erro ao carregar malha',
    status_error_resumo: 'Erro ao carregar resumo IDF',
    curvas_loading: uf => `Curvas IDF de ${uf}: carregando...`,
    curvas_ready: uf => `Curvas IDF de ${uf} prontas ✓`,
    curvas_error: uf => `Erro ao carregar curvas IDF de ${uf}`,

    tooltip_municipio_label: 'Município:',
    badge_distribution: d => `Distribuição: ${d}`,
    badge_neighborhood_pct: p => `${p}% dos anos por média de vizinhança`,
    idx_rain_avg: 'Chuva máx. diária anual média',
    idx_intensity: 'Intensidade TR=100a, 24h',
    idx_coef_k: 'Coeficiente k',
    idx_coef_a: 'Coeficiente a',
    idx_coef_b: 'Coeficiente b',
    idx_coef_c: 'Coeficiente c',
    idx_years_data: 'Anos de dado',
    no_idf_curve_available: 'Sem curva IDF disponível para este município.',
    ibge_code_label: (code, uf) => `Código IBGE: ${code} · ${uf}`,
    detail_title_placeholder: '—',
    unknown_municipality: 'Desconhecido',
    no_data: 'sem dado',

    chart_x_duration: 'Duração (min)',
    chart_y_intensity: 'Intensidade (mm/h)',
    chart_tr_label: tr => `TR = ${tr} anos`,
    chart_x_year: 'Ano',
    chart_y_rain: 'Chuva máxima diária (mm)',
    series_dataset_label: 'Chuva máxima diária (mm)',
    tooltip_year_title: y => `Ano ${y}`,
    tooltip_no_data: 'sem dado',
    tooltip_estimated_suffix: '(estimado por vizinhança)',

    alert_select_municipality_first: 'Selecione um município primeiro.',
    alert_no_idf_curve: 'Não há curva IDF para este município.',
    alert_no_series: 'Série histórica indisponível para este município (ainda a carregar ou sem cobertura).',

    csv_header1: '# IDFTec Data — Curvas IDF — dados do município',
    csv_source: '# Fonte: chuva máxima diária anual 1961-2025, grade Xavier BR-DWGD, via Google Earth Engine',
    csv_block1: '# Bloco 1: coeficientes da equação IDF e variáveis anuais',
    csv_block2: '# Bloco 2: intensidade (mm/h) por duração e período de retorno',
    csv_block2_unavailable: '# Curva IDF indisponível (ainda carregando ou sem cobertura para esta UF)',
    csv_series_header1: '# IDFTec Data — Série histórica de chuva máxima diária anual',
    csv_series_municipality: (nome, code, uf) => `# Município: ${nome} (código IBGE ${code}, ${uf})`,
    csv_series_source: '# Fonte: chuva máxima diária anual, grade Xavier BR-DWGD, via Google Earth Engine, 1961-2025',
  },
};

const LANG_STORAGE_KEY = 'idftec_lang';

function getLang() {
  try {
    return localStorage.getItem(LANG_STORAGE_KEY) || 'en';
  } catch (e) {
    return 'en';
  }
}

function setLang(lang) {
  try { localStorage.setItem(LANG_STORAGE_KEY, lang); } catch (e) {}
  window.location.reload();
}

const IDFTEC_LANG = getLang();

function t(key, ...args) {
  const dict = I18N[IDFTEC_LANG] || I18N.en;
  let val = dict[key];
  if (val === undefined) val = I18N.en[key];
  if (typeof val === 'function') return val(...args);
  return val;
}

function numLocale() {
  return IDFTEC_LANG === 'pt' ? 'pt-BR' : 'en-US';
}

function toggleLang() {
  setLang(IDFTEC_LANG === 'en' ? 'pt' : 'en');
}

function applyI18nStatic() {
  document.documentElement.lang = IDFTEC_LANG === 'pt' ? 'pt-BR' : 'en';
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    el.innerHTML = t(el.getAttribute('data-i18n-html'));
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    document.title = t(el.getAttribute('data-i18n-title'));
  });
  const label = document.getElementById('lang-toggle-label');
  if (label) label.textContent = t('lang_toggle_label');
  const btn = document.getElementById('lang-toggle-btn');
  if (btn) btn.title = t('lang_toggle_title');
}
