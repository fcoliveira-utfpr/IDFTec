# 🌧️ IDFTec

**Intensity-Duration-Frequency curves for Brazil, municipality by municipality.**

This repository gathers the data, code, and web platform built from the annual maximum daily rainfall (1961–2025) to compute, for each of the 5,569 Brazilian municipalities with available data, its IDF curve — the classic hydrological engineering tool used to size storm drains, culverts, channels, and any structure that needs to withstand a rare rainfall event without becoming a flood headline.

If you got here out of curiosity, you're a journal reviewer checking reproducibility, or you just want to know how many mm/h your city can handle before flooding — all three motivations are welcome.

---

## 🗺️ See it on the map before reading the code

The **IDFTec Data** platform lets you explore the results without opening a single line of Python:

🔗 **[fcoliveira-utfpr.github.io/IDFTec](https://fcoliveira-utfpr.github.io/IDFTec/)**

- Choose a state and a municipality
- See the IDF equation coefficients, the statistical distribution used, and the fit's R²
- Explore the intensity × duration chart for return periods from 5 to 100 years
- See the historical annual maximum daily rainfall series (1961–2025) as a bar chart
- Color the map of Brazil by projected intensity, average maximum rainfall, or the `k` coefficient
- Download the municipality's data as CSV (IDF curve and historical series)

The whole application runs in the browser — no server, no backend, just HTML/JS and a generous dose of `fetch()`.

---

## 🎯 What this is about

**5,569 Brazilian municipalities. One equation, individually calibrated for each one, from 65 years of satellite data.**

$$I(T, t) = \frac{k \cdot T^{a}}{(t + b)^{c}}$$

where `I` is the rainfall intensity (mm/h), `T` the return period (years), and `t` the duration (minutes). Behind every curve:

| Step | What happens |
|---|---|
| **Extraction** | Annual maximum daily rainfall (1961–2025) extracted via Google Earth Engine from the Xavier BR-DWGD grid (0.1°, ~11 km), sampled at each municipality's centroid. |
| **Gap filling** | Municipalities whose centroid falls on a pixel without data (typically coastal ones) are resampled using a neighborhood average, with a progressive radius. |
| **Statistical fitting** | Six extreme-value distributions (Gumbel, GEV, Log-Normal, Weibull, Gamma, Normal) are tested for goodness of fit (Kolmogorov-Smirnov); the best-fitting one is chosen per municipality. |
| **Disaggregation** | The 1-day rainfall is disaggregated into 12 durations (5 min to 24 h) using the DAEE/CETESB (1980) factors, and the quantiles per duration are obtained by analytically scaling the 1-day quantile — without redundant refitting per duration. |
| **IDF calibration** | The `k, a, b, c` coefficients are calibrated via log-linear regression with a sweep over `b` — a closed-form method, with no non-linear optimizer or artificial bounds. |

Full details, including the bugs found and fixed along the way, are in [`MEMORIA_PROJETO.md`](MEMORIA_PROJETO.md).

---

## 📦 Repository structure

```
IDFTec/
│
├── 📓 Notebooks
│   ├── verificacao_centroides_municipios_br.ipynb   # validates the centroids asset against IBGE
│   ├── chuva_maxima_anual_municipios_xavier.ipynb    # extraction via GEE (Colab version)
│   └── analise_estatistica_idf_municipios.ipynb      # descriptive statistics, heatmaps, geobr maps
│
├── 🐍 Processing scripts
│   ├── extrair_chuva_maxima.py         # extraction via GEE (local version, no Colab)
│   ├── calcular_idf_municipios.py      # statistical fitting + IDF calibration, all municipalities
│   └── exportar_dados_site.py          # repackages the results into the site's format
│
├── 📊 Data
│   ├── xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json   # raw annual maximum rainfall
│   ├── idf_municipios.json                                          # full IDF curves
│   ├── idf_municipios_ignorados.json                                # municipalities without a valid series
│   ├── idf_municipios_resumo.csv                                    # 1 row/municipality (map + table)
│   ├── idf_uf/{UF}.json                                             # full curves, per state
│   └── serie_uf/{UF}.json                                           # annual historical series, per state
│
├── 📝 MEMORIA_PROJETO.md               # full history of decisions, bugs, and fixes
│
└── 🌐 IDFTec Data (web application)
    ├── index.html
    └── idf.html
```

---

## 🧮 How the data was generated, in three sentences

1. The annual maximum daily rainfall (1961–2025) was extracted from the Xavier BR-DWGD grid via Google Earth Engine, sampled at the centroid of each of the 5,571 IBGE municipalities (verified against the official database).
2. For each municipality, the best-fitting extreme-value distribution was fitted to the 65-year series, the 1-day rainfall quantiles were disaggregated into 12 durations, and the IDF equation was calibrated via log-linear regression.
3. The results were consolidated into a municipal table and, for the web application, repackaged into a national summary CSV and lightweight per-state JSONs — because nobody deserves to wait for a 16 MB JSON to load just to see one municipality's IDF curve.

This project follows the same architecture pattern as its sibling repository [`climas_brasil`](https://github.com/fcoliveira-utfpr/climas_brasil) (ClimaTec Data), reusing the IBGE municipal mesh via [`geodata-br`](https://github.com/tbrugz/geodata-br) and the same 100%-static-site philosophy.

---

## 📖 How to cite

If this repository or the data are useful for your work, please cite:

```
[Oliveira, F. C. Intensity-Duration-Frequency Curves for Brazil: An Approach Based on Political-Administrative Units. Paperco, v. X, n. X, ano. DOI: [inserir]]
```

*(full reference to be updated after publication)*

---

## 🙏 Acknowledgments

UTFPR — Santa Helena Campus

---

## 📬 Contact

Fabrício Correia de Oliveira — UTFPR, Santa Helena Campus
`fcoliveira@utfpr.edu.br`

---

*Made with Python, JavaScript, Earth Engine, and the stubborn conviction that every bug has a findable root cause — even when it's hiding behind three layers of redundant statistical refitting.*
