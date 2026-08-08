"""Calcula curvas IDF (Intensidade-Duração-Frequência) para todos os municípios
a partir da série de chuva máxima diária anual gerada por
`chuva_maxima_anual_municipios_xavier.ipynb`.

Reaproduz a metodologia validada em `calibracao_cascavel.ipynb` (teste de
aderência de distribuições, desagregação de chuva diária pelos fatores
DAEE/CETESB e calibração da equação IDF), rodando em lote para cada município
e salvando um único JSON estático (uso pretendido: página no GitHub Pages).

Uso:
    python calcular_idf_municipios.py
    python calcular_idf_municipios.py --entrada outro_arquivo.json --limite 20
"""

import argparse
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.stats import kstest

warnings.filterwarnings('ignore')

ANO_INICIAL_PADRAO = 1961
ANO_FINAL_PADRAO = 2025

MIN_ANOS_VALIDOS = 20  # mínimo de anos com dado para tentar ajustar distribuição/IDF

DISTRIBUICOES = {
    'Gumbel': stats.gumbel_r,
    'GEV': stats.genextreme,
    'Normal': stats.norm,
    'Log-Normal': stats.lognorm,
    'Weibull': stats.weibull_min,
    'Gama': stats.gamma,
}

# Fatores de desagregação de chuva diária (DAEE/CETESB, 1980).
#
# LIMITAÇÃO CONHECIDA (aceita, ver MEMORIA_PROJETO.md): esses fatores são
# regionais (originalmente de SP) e aplicados aqui a todos os municípios do
# Brasil. Como resultado, a "forma" da curva intensidade x duração é idêntica
# para qualquer município (só muda a escala, vinda da distribuição ajustada à
# série de cada um) — na prática, os coeficientes b e c da equação IDF saem
# quase constantes nacionalmente (variação < 0,05% testada em municípios do
# AC), só k e a carregam diferença real entre municípios. Corrigir isso
# exigiria fatores de desagregação regionalizados, que não temos hoje.
FATORES_DESAGREGACAO = {
    '5 min': 0.34, '10 min': 0.54, '15 min': 0.70, '20 min': 0.81, '25 min': 0.91, '30 min': 0.74,
    '60 min': 0.42, '360 min': 0.72, '480 min': 0.78, '600 min': 0.82, '720 min': 0.85,
    '1440 min': 1.14,
}

# Duração em horas, para converter lâmina (mm) em intensidade (mm/h)
DURACAO_HORAS = {
    '5 min': 5 / 60, '10 min': 10 / 60, '15 min': 15 / 60, '20 min': 20 / 60,
    '25 min': 25 / 60, '30 min': 30 / 60, '60 min': 1, '360 min': 6, '480 min': 8,
    '600 min': 10, '720 min': 12, '1440 min': 24,
}

DURACOES_ORDENADAS = list(DURACAO_HORAS.keys())
PERIODOS_RETORNO = [5, 10, 25, 50, 100]


def d_critico(n, alpha=0.05):
    return 1.36 / math.sqrt(n)


def carregar_series_por_municipio(caminho_json):
    with open(caminho_json, encoding='utf-8') as arquivo:
        registros = json.load(arquivo)

    municipios = {}
    for registro in registros:
        codigo = registro['codigo_ibge']
        valor = registro['chuva_max_diaria_mm']
        if codigo not in municipios:
            municipios[codigo] = {
                'nome_municipio': registro['nome_municipio'],
                'uf': registro['uf'],
                'anos': [],
                'chuva': [],
            }
        if valor is not None:
            municipios[codigo]['anos'].append(registro['ano'])
            municipios[codigo]['chuva'].append(float(valor))

    return municipios


def escolher_distribuicao(serie):
    """Ajusta as distribuições candidatas e escolhe a de menor Dsup entre as
    aceitas no teste KS (p > 0.05 e D < D_critico); sem nenhuma aceita, usa a
    de menor Dsup mesmo assim (mesmo fallback do calibracao_cascavel.ipynb)."""
    n = len(serie)
    dcrit = d_critico(n)

    candidatas = []
    for nome, dist in DISTRIBUICOES.items():
        try:
            params = dist.fit(serie)
            D, p_val = kstest(serie, dist.cdf, args=params)
            candidatas.append({'nome': nome, 'dist': dist, 'params': params, 'D': D, 'p': p_val})
        except Exception:
            continue

    if not candidatas:
        return None

    candidatas.sort(key=lambda c: c['D'])
    aceitas = [c for c in candidatas if c['p'] > 0.05 and c['D'] < dcrit]
    return aceitas[0] if aceitas else candidatas[0]


def _fatores_efetivos_por_duracao():
    """Fator acumulado (cascata de FATORES_DESAGREGACAO) que converte a lâmina
    de 1 dia (mm) na lâmina de cada duração — mesma cascata de
    calibracao_cascavel.ipynb, mas como fator escalar em vez de aplicado a
    uma série inteira."""
    fatores = {'1440 min': FATORES_DESAGREGACAO['1440 min']}
    for duracao in ('720 min', '600 min', '480 min', '360 min', '60 min'):
        fatores[duracao] = fatores['1440 min'] * FATORES_DESAGREGACAO[duracao]
    fatores['30 min'] = fatores['60 min'] * FATORES_DESAGREGACAO['30 min']
    for duracao in ('25 min', '20 min', '15 min', '10 min', '5 min'):
        fatores[duracao] = fatores['30 min'] * FATORES_DESAGREGACAO[duracao]
    return fatores


FATORES_EFETIVOS_POR_DURACAO = _fatores_efetivos_por_duracao()


def quantis_por_duracao(dist, params):
    """Calcula os quantis de intensidade (mm/h) por duração e período de
    retorno a partir da distribuição já ajustada à série de 1 dia (`params`
    vem de `escolher_distribuicao`, não é reajustado aqui).

    Os quantis das outras durações são obtidos escalando analiticamente o
    quantil de 1 dia pelo fator de desagregação (matematicamente exato para
    essas famílias sob reescala positiva: quantil(a*X) = a*quantil(X)), em
    vez de reajustar a distribuição em cada série derivada. A versão anterior
    reajustava por duração e produziu, na prática, casos de instabilidade
    numérica (ex.: GEV com forma mal condicionada) gerando quantis absurdos
    (centenas de milhares de mm/h) nalguns municípios — esta versão evita
    esse risco por construção, além de garantir consistência entre durações."""
    quantis_1dia = {tr: float(dist.ppf(1 - 1 / tr, *params)) for tr in PERIODOS_RETORNO}

    quantis = {}
    for duracao in DURACOES_ORDENADAS:
        fator = FATORES_EFETIVOS_POR_DURACAO[duracao] / DURACAO_HORAS[duracao]
        quantis[duracao] = {tr: valor * fator for tr, valor in quantis_1dia.items()}
    return quantis


# Faixa de varredura de b (minutos) — o parâmetro de deslocamento temporal da
# equação IDF costuma ficar bem abaixo disso na prática hidrológica; a faixa
# é generosa para não artificialmente truncar municípios fora do perfil de
# Cascavel. Se o b escolhido cair perto da borda, fica registrado em
# 'b_no_limite_da_busca' para auditoria.
B_MINIMO_BUSCA = 0.01
B_MAXIMO_BUSCA = 200.0
B_TOLERANCIA_LIMITE = 0.5


def _ajustar_log_linear(t_vec, log_T, y, b):
    """Para um b fixo, log(I) = log(k) + a*log(T) - c*log(t+b) é linear em
    [log(k), a, c] — resolve por mínimos quadrados (OLS) e retorna também o
    R² dessa regressão em log, usado só para escolher o melhor b na varredura."""
    X = np.column_stack([np.ones_like(t_vec), log_T, np.log(t_vec + b)])
    coeficientes, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ coeficientes
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2_log = 1 - ss_res / ss_tot if ss_tot > 0 else -np.inf
    return coeficientes, r2_log


def _melhor_b_na_grade(t_vec, log_T, y, candidatos):
    melhor = max(
        ((b, *_ajustar_log_linear(t_vec, log_T, y, b)) for b in candidatos),
        key=lambda item: item[2],
    )
    return melhor  # (b, coeficientes, r2_log)


def calibrar_equacao_idf(quantis):
    """Calibra I(T, t) = k * T^a / (t + b)^c por regressão log-linear com
    varredura de b — método padrão na prática hidrológica brasileira para
    esta equação. Fixado b, log(I) = log(k) + a*log(T) - c*log(t+b) é linear
    em [log(k), a, c] e resolvido por OLS (fechado, sempre converge); busca-se
    o b que maximiza o R² dessa regressão em duas passadas (grade grosseira e
    depois refinada em torno do melhor ponto). Substitui o otimizador
    não-linear com limites artificiais (L-BFGS-B), que prendia os
    coeficientes na borda do intervalo de busca para municípios fora do
    perfil de Cascavel."""
    t_vec, T_vec, I_obs = [], [], []
    for duracao, valores_por_tr in quantis.items():
        tmin = float(duracao.replace(' min', ''))
        for tr, intensidade in valores_por_tr.items():
            if intensidade <= 0:
                continue
            t_vec.append(tmin)
            T_vec.append(tr)
            I_obs.append(intensidade)

    if len(I_obs) < 6:
        return None

    t_vec = np.array(t_vec)
    T_vec = np.array(T_vec, dtype=float)
    I_obs = np.array(I_obs)
    log_T = np.log(T_vec)
    y = np.log(I_obs)

    grade_grosseira = np.linspace(B_MINIMO_BUSCA, B_MAXIMO_BUSCA, 400)
    b_grosseiro, _, _ = _melhor_b_na_grade(t_vec, log_T, y, grade_grosseira)

    passo = grade_grosseira[1] - grade_grosseira[0]
    grade_fina = np.linspace(max(B_MINIMO_BUSCA, b_grosseiro - passo), b_grosseiro + passo, 400)
    b, coeficientes, r2_log = _melhor_b_na_grade(t_vec, log_T, y, grade_fina)

    log_k, a, menos_c = coeficientes
    k = float(np.exp(log_k))
    a = float(a)
    c = float(-menos_c)
    b = float(b)

    I_pred = (k * (T_vec ** a)) / ((t_vec + b) ** c)
    erro = I_obs - I_pred
    mae = float(np.mean(np.abs(erro)))
    rmse = float(np.sqrt(np.mean(erro ** 2)))
    ss_tot = np.sum((I_obs - I_obs.mean()) ** 2)
    r2 = float(1 - np.sum(erro ** 2) / ss_tot) if ss_tot > 0 else None

    return {
        'k': k, 'a': a, 'b': b, 'c': c,
        'mae': mae, 'rmse': rmse, 'r2': r2,
        'r2_regressao_log': float(r2_log),
        'metodo_ajuste': 'log_linear_varredura_b',
        'b_no_limite_da_busca': bool(b - B_MINIMO_BUSCA < B_TOLERANCIA_LIMITE or B_MAXIMO_BUSCA - b < B_TOLERANCIA_LIMITE),
    }


def processar_municipio(codigo, dados):
    serie = dados['chuva']
    if len(serie) < MIN_ANOS_VALIDOS:
        return None, f'dados insuficientes ({len(serie)} ano(s) válido(s), mínimo {MIN_ANOS_VALIDOS})'

    escolhida = escolher_distribuicao(np.array(serie))
    if escolhida is None:
        return None, 'nenhuma distribuição pôde ser ajustada'

    quantis = quantis_por_duracao(escolhida['dist'], escolhida['params'])

    idf = calibrar_equacao_idf(quantis)
    if idf is None:
        return None, 'dados insuficientes para calibrar a equação IDF'

    resultado = {
        'codigo_ibge': codigo,
        'nome_municipio': dados['nome_municipio'],
        'uf': dados['uf'],
        'n_anos': len(serie),
        'distribuicao': escolhida['nome'],
        'ks_d': float(escolhida['D']),
        'ks_p_valor': float(escolhida['p']),
        'idf': idf,
        'quantis_mm_h': quantis,
    }
    return resultado, None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '--entrada', default=f'xavier_chuva_maxima_diaria_anual_municipios_{ANO_INICIAL_PADRAO}_{ANO_FINAL_PADRAO}.json',
        help='JSON gerado pelo notebook de extração (padrão: %(default)s)',
    )
    parser.add_argument('--saida', default='idf_municipios.json', help='JSON de saída (padrão: %(default)s)')
    parser.add_argument('--limite', type=int, default=None, help='processar só os N primeiros municípios (teste rápido)')
    parser.add_argument('--checkpoint-a-cada', type=int, default=200, help='regravar o JSON a cada N municípios processados')
    args = parser.parse_args()

    caminho_entrada = Path(args.entrada)
    if not caminho_entrada.exists():
        print(f'Arquivo de entrada não encontrado: {caminho_entrada.resolve()}', file=sys.stderr)
        sys.exit(1)

    print(f'Carregando {caminho_entrada} ...')
    municipios = carregar_series_por_municipio(caminho_entrada)
    print(f'{len(municipios)} municípios encontrados no arquivo de entrada.')

    codigos = list(municipios.keys())
    if args.limite:
        codigos = codigos[:args.limite]
        print(f'Limitando a {len(codigos)} municípios (--limite).')

    caminho_saida = Path(args.saida)
    resultados = []
    ignorados = []

    for indice, codigo in enumerate(codigos, start=1):
        resultado, motivo = processar_municipio(codigo, municipios[codigo])
        if resultado is not None:
            resultados.append(resultado)
        else:
            ignorados.append({'codigo_ibge': codigo, 'nome_municipio': municipios[codigo]['nome_municipio'], 'motivo': motivo})

        if indice % 100 == 0 or indice == len(codigos):
            print(f'{indice}/{len(codigos)} municípios processados ({len(resultados)} ok, {len(ignorados)} ignorados)')

        if indice % args.checkpoint_a_cada == 0:
            with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
                json.dump(resultados, arquivo, ensure_ascii=False, indent=2)

    with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=2)

    print()
    print(f'JSON salvo em: {caminho_saida.resolve()}')
    print(f'Municípios com curva IDF calculada: {len(resultados)}')
    print(f'Municípios ignorados: {len(ignorados)}')

    if ignorados:
        caminho_ignorados = caminho_saida.with_name(caminho_saida.stem + '_ignorados.json')
        with open(caminho_ignorados, 'w', encoding='utf-8') as arquivo:
            json.dump(ignorados, arquivo, ensure_ascii=False, indent=2)
        print(f'Lista de ignorados salva em: {caminho_ignorados.resolve()}')


if __name__ == '__main__':
    main()
