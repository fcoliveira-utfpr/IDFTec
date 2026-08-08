# Projeto IDF — Curvas Intensidade-Duração-Frequência por Município (Brasil)

## Objetivo

Gerar curvas IDF (Intensidade-Duração-Frequência) para todos os municípios brasileiros a partir da série de chuva máxima diária anual (1961–2025, grade Xavier BR-DWGD), e publicar os resultados em uma página estática hospedada no GitHub Pages.

## Estrutura do projeto

| Arquivo | Papel |
|---|---|
| `verificacao_centroides_municipios_br.ipynb` | Confere o asset GEE `projects/fcoliveira/assets/centroide_br` (5.571 centróides municipais) contra a lista oficial do IBGE. Cobertura completa confirmada, sem duplicidade. |
| `chuva_maxima_anual_municipios_xavier.ipynb` | Extrai, via Google Earth Engine, a chuva máxima diária anual (mm/dia) de cada município, 1961–2025, a partir da grade Xavier BR-DWGD. Salva `xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json`. |
| `calcular_idf_municipios.py` | Script batch que generaliza a metodologia do `calibracao_cascavel.ipynb` para todos os municípios do JSON de extração, gerando `idf_municipios.json` (curvas IDF por município, pronto para consumo pela página estática). |
| `analise_estatistica_idf_municipios.ipynb` | Estatística descritiva nacional/por UF, heatmaps e mapas coropléticos (`geobr`) sobre os resultados — relatório-base para o artigo. |
| `exportar_dados_site.py` | Reempacota `idf_municipios.json` + a série bruta no formato do site: `idf_municipios_resumo.csv` (1 linha/município) e `idf_uf/{UF}.json` (curvas completas, por estado). |
| `index.html` / `idf.html` | Site estático **IDFTec Data** (mesmo padrão do repositório irmão `fcoliveira-utfpr/climas_brasil`/ClimaTec Data): mapa Leaflet colorido por métrica escolhível, painel de detalhe por município com gráfico da curva IDF (Chart.js) e exportação CSV. |

> Nota: `calibracao_cascavel.ipynb` — o notebook exploratório original que validou a metodologia (ajuste de distribuição, desagregação DAEE/CETESB, calibração IDF) num único município (Cascavel) antes de generalizar para `calcular_idf_municipios.py` — não faz mais parte deste repositório (removido por ser provisório), mas é citado no histórico abaixo porque foi a origem de vários bugs encontrados e corrigidos.

## Pipeline

1. **Extração** (`chuva_maxima_anual_municipios_xavier.ipynb`, GEE) → `xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json`
   (registros por município/ano: `codigo_ibge, nome_municipio, uf, ano, chuva_max_diaria_mm, unidade, fonte, metodo`)
2. **Cálculo IDF** (`calcular_idf_municipios.py`) → `idf_municipios.json`
   (por município: distribuição escolhida, coeficientes `k,a,b,c` da equação IDF, métricas de ajuste, tabela de quantis por duração × período de retorno)
3. **Reempacotamento para o site** (`exportar_dados_site.py`) → `idf_municipios_resumo.csv` + `idf_uf/{UF}.json`
4. **Site estático IDFTec Data** (`index.html`, `idf.html`) — carrega o CSV resumo (leve, nacional) para o mapa e a tabela; ao trocar de UF, busca sob demanda `idf_uf/{UF}.json` com as curvas completas daquele estado. Nenhum cálculo/otimização acontece no navegador — só lookup e renderização (Leaflet + Chart.js).

## Decisões e bugs importantes (histórico)

### `chuva_maxima_anual_municipios_xavier.ipynb`
- **Import do `geemap.foliumap` quebrava a inicialização** (`BoxKeyError`) — isolado com `try/except`, só afeta o mapa opcional no fim do notebook.
- **Limite de ~5.000 elementos do Earth Engine por consulta síncrona** — Brasil tem 5.571 municípios, então a extração é paginada (`TAMANHO_PAGINA = 2000`) dentro de cada ano.
- **Retry + checkpoint incremental**: até 3 tentativas por página, e o JSON é regravado a cada ano processado (não perde progresso se um ano posterior falhar).
- **Bug de escala/offset (crítico)**: a banda `pr` do asset Xavier vem como inteiro (int16), não em mm. Fórmula correta: `mm = bruto * BAND_pr_MULT + BAND_pr_ADD` (constantes confirmadas fixas de 1961 a 2025: `MULT=0.00686666`, `ADD=225`). Sem isso, os valores extraídos eram números negativos sem sentido (ex.: -25838).
- **Bug de nome de propriedade (crítico)**: `reduceRegions` com `ee.Reducer.first()` puro nomeia a saída como `'first'`, não com o nome da banda — por isso vinha tudo nulo mesmo com o cálculo certo por trás. Corrigido com `ee.Reducer.first().setOutputs(['chuva_max_diaria_mm'])`.
- **Preenchimento por vizinhança**: municípios cujo centróide cai num pixel sem dado válido (tipicamente litorâneos/de borda) são reamostrados com buffer progressivo (20/50/100 km) e `ee.Reducer.mean()` sobre os pixels vizinhos válidos. Campo `metodo` no registro indica `centroide` ou `media_vizinhanca_XXkm`.
- **Casos sem solução conhecida** (ficam nulos mesmo após vizinhança):
  - **Fernando de Noronha (PE)** — ilha oceânica fora da cobertura da grade Xavier (interpolada a partir de estações no continente). Precisaria de outra fonte de dados.
  - **Vitória (ES)** — centróide do asset `centroide_br` está incorreto, caindo no oceano (~130 km a leste da cidade real). Bug no asset de centroides, não neste notebook — pendente de correção separada (ver Próximos passos).

### `calcular_idf_municipios.py`
- Generaliza a metodologia do `calibracao_cascavel.ipynb`: teste de aderência (KS) entre Gumbel/GEV/Normal/Log-Normal/Weibull/Gama, desagregação DAEE/CETESB, calibração da equação IDF.
- Remove a dependência do `sklearn` (MAE/RMSE calculados com numpy puro).
- `MIN_ANOS_VALIDOS = 20`: municípios com menos anos válidos que isso são ignorados e listados em `idf_municipios_ignorados.json`, com o motivo.
- Testado com dados sintéticos e depois com dados reais (20 primeiros municípios, todos no AC, e depois nos 5.571 completos).

**Bug crítico corrigido: reajustar a distribuição independentemente em cada duração gerava quantis absurdos.**
A primeira versão de `quantis_por_duracao` reajustava (MLE) a distribuição vencedora em cada uma das 12 séries de duração (cada uma só a série de 1 dia multiplicada por uma constante fixa). Isso é redundante matematicamente e, na prática real (não só teórica), instável: rodando nos 5.571 municípios, a duração de 15 min de alguns municípios (ex.: Boqueirão do Leão/RS) teve o refit de GEV convergir pra um parâmetro de forma mal condicionado, produzindo quantis de **até 593.056 mm/h** (contra ~100 mm/h nas durações vizinhas) — detectado porque o R² da calibração IDF desses municípios saiu negativo. **Corrigido**: a distribuição agora é ajustada **uma única vez** na série de 1 dia (reaproveitando os `params` já calculados em `escolher_distribuicao`), e os quantis das outras durações são obtidos **escalando analiticamente** o quantil de 1 dia pelo fator de desagregação acumulado (`FATORES_EFETIVOS_POR_DURACAO`) — matematicamente exato para essas famílias sob reescala positiva (`quantil(a·X) = a·quantil(X)`), sem nenhum refit adicional. Após a correção, rodando os 5.569 municípios válidos: R² entre 0,9978 e 0,9996, nenhum caso negativo ou fora da faixa.

**Calibração da equação IDF — de otimizador não-linear para regressão log-linear com varredura de `b`.**
Primeira versão usava `scipy.optimize.minimize` (nonlinear, com limites tipo `k:500-5000, a:0.05-0.5, b:1e-6-20, c:0.3-0.9` copiados do `calibracao_cascavel.ipynb`, calibrados só para Cascavel). Testando com município reais do Acre, **9 de 20 (45%) tinham pelo menos um coeficiente preso exatamente na borda do limite** (`k=500`, `a=0.5`, `b=20`, `c=0.9`) — sinal de que os limites, tunados só pra Cascavel, eram apertados demais para outras regiões, gerando coeficientes artificiais. Trocado pelo método padrão da prática hidrológica brasileira: fixado `b`, `log(I) = log(k) + a·log(T) − c·log(t+b)` é linear em `[log(k), a, c]`, resolvido por OLS fechado (sempre converge, sem chute inicial nem limite artificial); busca-se o `b` que maximiza o R² dessa regressão (varredura grosseira 0,01–200 min, depois refinada). Testado de novo nos mesmos 20 municípios: zero presos em limite, `k`/`a` variam de fato entre municípios.

**Limitação estrutural encontrada (aceita e documentada, não corrigida por ora): `b` e `c` saem praticamente constantes para qualquer município.**
Ao rodar a regressão corrigida, `b` variou entre 11.822 e 11.827 e `c` entre 0.7579 e 0.7580 nos 20 municípios testados (variação < 0,05%) — mesmo eles sendo municípios com climas bem diferentes. **Isso não é bug da regressão**: é consequência de aplicar os **mesmos 12 fatores fixos de desagregação DAEE/CETESB (1980, originalmente regionais de SP) a todos os municípios do Brasil**. Como a série de cada duração é sempre a série de chuva de 1 dia multiplicada pela mesma razão fixa, a "forma" da curva intensidade×duração é idêntica em qualquer lugar — só a escala (`k`, `a`, vindos da distribuição ajustada à série de cada município) varia de verdade.
**Decisão (2026-08-08): aceitar essa limitação por ora e documentá-la claramente**, tanto aqui quanto na futura página estática (ver Próximos passos) — em vez de buscar fatores de desagregação regionalizados (que exigiria outra fonte de dados ainda não disponível). Ou seja: **hoje, o pipeline produz uma curva IDF com a mesma forma (`b`,`c`) para o Brasil inteiro, variando só a magnitude (`k`,`a`) por município** — isso deve ficar visível para quem for usar os resultados, não só enterrado no código.

### Decisão de arquitetura (site)
- GitHub Pages é hospedagem estática — sem backend. Decisão: **pré-computar tudo offline** (extração + ajuste estatístico + coeficientes IDF) e publicar um JSON estático; a página só faz lookup e renderiza. Alternativa descartada: recalcular ajuste/otimização em JavaScript a cada seleção de município (duplicaria lógica já validada em Python e seria mais lento/frágil no cliente).
- Decisão de linguagem: o script de cálculo em lote ficou em `.py` (não `.ipynb`) por ser um job batch sem necessidade de inspeção célula a célula nem do fluxo de autenticação interativa do Earth Engine.

### Site estático "IDFTec Data" — mesmo padrão do `climas_brasil`/ClimaTec Data
O usuário já tem um projeto irmão publicado (`https://github.com/fcoliveira-utfpr/climas_brasil`, site "ClimaTec Data") com exatamente essa arquitetura, validada em produção: Leaflet (mapa) + Chart.js (gráfico) + PapaParse (CSV) + Tailwind, 100% client-side, malha municipal via `geodata-br` (GeoJSON por UF, hospedado no GitHub), CSV resumo nacional para o mapa e JSON leve por UF (`mensal_uf/{UF}.json` lá, `idf_uf/{UF}.json` aqui) carregado sob demanda para os gráficos. `idf.html` foi adaptado de perto do `koppen.html` daquele repositório — mesma estrutura de paineis, troca de estado/município, e conceito de "preenchido por vizinho" (aqui: campo `pct_anos_vizinhanca`).
Diferença de conteúdo: em vez de climograma (chuva+temperatura mensal), o painel de detalhe mostra a **curva IDF** (intensidade × duração, uma linha por período de retorno 5/10/25/50/100 anos); em vez de colorir o mapa por classe climática categórica, o mapa tem um **dropdown de métrica contínua** (intensidade TR=100/24h, chuva máxima média, ou coeficiente k), com escala de cor por quantil calculada em JS.

**Bugs encontrados e corrigidos na revisão manual do JS** (não havia `node`/navegador disponível de imediato para testar, então a validação inicial foi só revisão de código linha a linha):
- Regex de remoção de acentos em `slugify()` (`replace(/[̀-ͯ]/g,'')`) tinha sido escrita com os caracteres Unicode literais em vez do escape `̀-ͯ` — corrigido para a forma explícita.
- Datasets do gráfico Chart.js usavam `labels` (array de durações) + `data` como array simples, dependendo do mapeamento implícito rótulo→posição num eixo X `logarithmic` — trocado por pares explícitos `{x, y}` por ponto, que o Chart.js sempre interpreta corretamente independente do tipo de escala.

**Validação real com navegador**: `playwright` + Chromium instalados neste ambiente (macOS Ventura/mac13 não é oficialmente suportado pelas versões recentes do Playwright — funcionou baixando os binários do Chromium mesmo assim). Teste automatizado cobriu: carregar `index.html` e `idf.html` sem erros de console, mapa do Paraná carregando e colorindo corretamente, clique/seleção de município (Curitiba) abrindo o painel de detalhe com os cards de coeficientes, gráfico da curva IDF renderizando, troca de métrica do mapa (k) e troca de UF (SC) funcionando. Zero erros em todos os testes.

## Estado atual

- **Extração concluída** (2026-08-08): `xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json` na pasta do projeto, 362.115 registros (5.571 municípios × 65 anos), 130 nulos esperados (Noronha + Vitória × 65 anos). Rodada localmente via `extrair_chuva_maxima.py` (versão `.py` do notebook, sem depender de Colab/download manual).
- **`idf_municipios.json` gerado** (2026-08-08): 5.569 municípios com curva IDF (2 ignorados: Noronha e Vitória, sem série válida), R² entre 0,9978 e 0,9996 em todos.
- **`analise_estatistica_idf_municipios.ipynb` gerado e executado** (2026-08-08): estatística descritiva nacional/UF, heatmaps, mapas `geobr` — relatório-base pronto para o artigo.
- **Site "IDFTec Data" construído e testado** (2026-08-08): `index.html` + `idf.html`, dados reempacotados via `exportar_dados_site.py` (`idf_municipios_resumo.csv` + `idf_uf/*.json`). Testado com Playwright/Chromium real — mapa, seleção de município, gráfico da curva IDF, troca de métrica/UF, tudo sem erro de console. **Falta publicar no GitHub Pages** (repositório ainda não criado/enviado).

## Próximos passos

1. ~~Aguardar a extração terminar (1961–2025) e conferir o JSON final.~~ **Concluído** (2026-08-08).
2. ~~Rodar `calcular_idf_municipios.py` completo (5.571 municípios) → gerar `idf_municipios.json`.~~ **Concluído** (2026-08-08): 5.569 municípios ok, R² 0,9978–0,9996.
3. ~~Gerar o relatório de análise estatística descritiva (notebook com heatmaps e mapas `geobr`).~~ **Concluído** (2026-08-08).
4. ~~Construir o site estático (`index.html` + `idf.html`) seguindo o padrão do `climas_brasil`/ClimaTec Data.~~ **Concluído e testado** (2026-08-08).
5. **Criar o repositório no GitHub e publicar via GitHub Pages** — falta decidir nome do repo, subir os arquivos (`index.html`, `idf.html`, `idf_municipios_resumo.csv`, `idf_uf/*.json`) e ativar o Pages.
6. (Opcional/separado) Investigar e corrigir centróides deslocados no asset `centroide_br` (confirmado pelo menos Vitória-ES; pode haver outros não detectados porque só caem fora da malha Xavier nos casos mais extremos).
7. (Opcional/futuro) Se algum dia houver fonte de fatores de desagregação regionalizados, revisitar a limitação do `b`/`c` constante.
8. (Opcional) Seção "Atlas" na `index.html` reaproveitando as figuras já geradas em `analise_estatistica_idf_municipios.ipynb` (heatmaps, mapas nacionais), no mesmo espírito da aba Atlas do `climas_brasil` — precisaria exportar essas figuras como PNG separados.
