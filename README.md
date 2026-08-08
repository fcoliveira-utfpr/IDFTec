# 🌧️ IDFTec

**Curvas de Intensidade-Duração-Frequência do Brasil, município por município.**

Este repositório reúne os dados, os códigos e a plataforma web desenvolvidos a partir da chuva máxima diária anual (1961–2025) para calcular, para cada um dos 5.569 municípios brasileiros com dado disponível, a sua curva IDF — a ferramenta clássica de engenharia hidrológica usada para dimensionar galerias pluviais, bueiros, canais e qualquer estrutura que precise resistir a um evento de chuva raro sem virar manchete de enchente.

Se você chegou até aqui por curiosidade, é revisor de periódico conferindo reprodutibilidade, ou só quer saber quantos mm/h sua cidade aguenta antes de alagar — as três motivações são bem-vindas.

---

## 🗺️ Veja no mapa antes de ler o código

A plataforma **IDFTec Data** deixa explorar os resultados sem abrir uma linha de Python:

🔗 **[fcoliveira-utfpr.github.io/IDFTec](https://fcoliveira-utfpr.github.io/IDFTec/)**

- Escolha um estado e um município
- Veja os coeficientes da equação IDF, a distribuição estatística usada e o R² do ajuste
- Explore o gráfico intensidade × duração para os períodos de retorno de 5 a 100 anos
- Veja a série histórica de chuva máxima diária anual (1961–2025) em gráfico de barras
- Colora o mapa do Brasil por intensidade projetada, chuva máxima média, ou pelo coeficiente `k`
- Baixe os dados do município em CSV (curva IDF e série histórica)

Toda a aplicação roda no navegador — sem servidor, sem backend, só HTML/JS e uma dose generosa de `fetch()`.

---

## 🎯 Do que se trata

**5.569 municípios brasileiros. Uma equação, calibrada individualmente para cada um, a partir de 65 anos de dados de satélite.**

$$I(T, t) = \frac{k \cdot T^{a}}{(t + b)^{c}}$$

onde `I` é a intensidade de chuva (mm/h), `T` o período de retorno (anos) e `t` a duração (minutos). Por trás de cada curva:

| Etapa | O que acontece |
|---|---|
| **Extração** | Chuva máxima diária anual (1961–2025) extraída via Google Earth Engine da grade Xavier BR-DWGD (0,1°, ~11 km), amostrada no centróide de cada município. |
| **Preenchimento** | Municípios com centróide sobre um pixel sem dado (tipicamente litorâneos) são reamostrados por média da vizinhança, com raio progressivo. |
| **Ajuste estatístico** | Seis distribuições de extremos (Gumbel, GEV, Log-Normal, Weibull, Gama, Normal) são testadas por aderência (Kolmogorov-Smirnov); a de melhor ajuste é escolhida por município. |
| **Desagregação** | A chuva de 1 dia é desagregada em 12 durações (5 min a 24 h) pelos fatores DAEE/CETESB (1980), e os quantis por duração são obtidos escalando analiticamente o quantil de 1 dia — sem reajuste redundante por duração. |
| **Calibração IDF** | Os coeficientes `k, a, b, c` são calibrados por regressão log-linear com varredura de `b` — método fechado, sem otimizador não-linear nem limites artificiais. |

Detalhes completos, incluindo os bugs encontrados e corrigidos ao longo do caminho, estão em [`MEMORIA_PROJETO.md`](MEMORIA_PROJETO.md).

---

## ⚠️ Limitação metodológica — leia antes de citar um número

Os coeficientes **`b` e `c`** da equação IDF saem **praticamente constantes em qualquer município do Brasil** (variação < 0,05% testada em municípios de climas completamente diferentes). Isso não é uma descoberta sobre o regime de chuva do país — é consequência de aplicar os **mesmos fatores de desagregação DAEE/CETESB, originalmente regionais de São Paulo, a todos os municípios**. Só **`k`** e **`a`** carregam diferença real entre municípios, vinda da distribuição estatística ajustada à série de chuva de cada um.

Essa e outras ressalvas (teste KS com parâmetros estimados da própria amostra, amostragem no centróide em vez do polígono municipal, R² do ajuste IDF sendo otimista) estão documentadas na íntegra em [`MEMORIA_PROJETO.md`](MEMORIA_PROJETO.md) e destacadas na própria página web.

---

## 📦 Estrutura do repositório

```
IDFTec/
│
├── 📓 Notebooks
│   ├── verificacao_centroides_municipios_br.ipynb   # valida o asset de centroides contra o IBGE
│   ├── chuva_maxima_anual_municipios_xavier.ipynb    # extração via GEE (versão Colab)
│   └── analise_estatistica_idf_municipios.ipynb      # estatística descritiva, heatmaps, mapas geobr
│
├── 🐍 Scripts de processamento
│   ├── extrair_chuva_maxima.py         # extração via GEE (versão local, sem Colab)
│   ├── calcular_idf_municipios.py      # ajuste estatístico + calibração IDF, todos os municípios
│   └── exportar_dados_site.py          # reempacota os resultados para o formato do site
│
├── 📊 Dados
│   ├── xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json   # chuva máxima anual, bruta
│   ├── idf_municipios.json                                          # curvas IDF completas
│   ├── idf_municipios_ignorados.json                                # municípios sem série válida
│   ├── idf_municipios_resumo.csv                                    # 1 linha/município (mapa + tabela)
│   ├── idf_uf/{UF}.json                                             # curvas completas, por estado
│   └── serie_uf/{UF}.json                                           # série histórica anual, por estado
│
├── 📝 MEMORIA_PROJETO.md               # histórico completo de decisões, bugs e correções
│
└── 🌐 IDFTec Data (aplicação web)
    ├── index.html
    └── idf.html
```

---

## 🧮 Como os dados foram gerados, em três frases

1. A chuva máxima diária anual (1961–2025) foi extraída da grade Xavier BR-DWGD via Google Earth Engine, amostrada no centróide de cada um dos 5.571 municípios do IBGE (verificado contra a base oficial).
2. Para cada município, a distribuição de valores extremos com melhor aderência foi ajustada à série de 65 anos, os quantis de chuva de 1 dia foram desagregados em 12 durações e a equação IDF foi calibrada por regressão log-linear.
3. Os resultados foram consolidados numa tabela municipal e, para a aplicação web, reempacotados num CSV resumo nacional e em JSONs leves por estado — porque ninguém merece esperar o carregamento de um JSON de 16 MB pra ver a curva IDF de um município só.

Este projeto segue o mesmo padrão de arquitetura do repositório irmão [`climas_brasil`](https://github.com/fcoliveira-utfpr/climas_brasil) (ClimaTec Data), reaproveitando a malha municipal do IBGE via [`geodata-br`](https://github.com/tbrugz/geodata-br) e a mesma filosofia de site 100% estático.

---

## 📖 Como citar

Se este repositório ou os dados forem úteis para o seu trabalho, por favor cite:

```
[Oliveira, F. C. Curvas de Intensidade-Duração-Frequência para o Brasil: uma abordagem
por unidades político-administrativas. Periódico, v. X, n. X, ano. DOI: [inserir]]
```

*(referência completa a ser atualizada após publicação)*

---

## 🙏 Agradecimentos

UTFPR — Campus Santa Helena

---

## 📬 Contato

Fabrício Correia de Oliveira — UTFPR, Campus Santa Helena
`fcoliveira@utfpr.edu.br`

---

*Feito com Python, JavaScript, Earth Engine e a convicção teimosa de que todo bug tem uma causa raiz encontrável — mesmo quando ela está escondida atrás de três camadas de reajuste estatístico redundante.*
