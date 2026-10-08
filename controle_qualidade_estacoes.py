"""Quality control of the BR-DWGD annual maxima against the rain-gauge data
used to build the grid (Xavier et al., 2022; observed data distributed by the
authors as `pr.npz`, 14,170 gauges, 1961-2025, not stored in this repository
because of its size: ~1.35 GB).

Steps:
  1. Annual maximum and number of valid days per gauge and year.
  2. Gauge-years with the "monthly totals recorded as daily rainfall" signature
     (<= 24 wet days in a year with annual maximum > 200 mm). Only gauge
     1166000 shows it persistently (37 years, 1961-1998); the others are
     isolated years (e.g. 11 gauges in Rondonia/Amazonas/Mato Grosso in 2006).
  3. Contaminated municipality-years, written to qc/anos_excluidos.json and
     dropped by calcular_idf_municipios.py:
     a) persistent gauges: municipalities within RAIO_INFLUENCIA_KM AND with
        mean grid maximum in the flagged years / mean in the other years above
        the national 95th percentile of the same ratio (all flagged years);
     b) isolated gauge-years: municipalities within RAIO_OUTLIER_KM whose grid
        value in that year is an extreme outlier of their own series
        (> Q3 + 3 IQR of the remaining years, after step a).
  4. Grid vs. nearest gauge (<= 10 km, >= 30 common years): bias, correlation
     and agreement of Mann-Kendall trends.
  5. Grid Mann-Kendall trend and Pettitt change point per municipality, and
     their relation to the change in gauge density within 50 km.

Usage:
    python controle_qualidade_estacoes.py --pr caminho/para/pr.npz
"""

import argparse
import json
import pickle
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import cKDTree

BASE = Path(__file__).parent
PASTA_QC = BASE / 'qc'
ARQ_SERIE = BASE / 'xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json'
ARQ_CENTROIDES = PASTA_QC / 'centroides_municipios.csv'

R_TERRA_KM = 6371.0
MIN_DIAS_VALIDOS = 330           # gauge-year considered complete
MAX_DIAS_CHUVA_MENSAL = 24       # ~2 wet days per month
MIN_MAXIMA_MENSAL_MM = 200.0
MIN_ANOS_ESTACAO_SUSPEITA = 5    # persistent signature, not a one-off year
RAIO_INFLUENCIA_KM = 500.0
QUANTIL_RAZAO = 0.95
RAIO_OUTLIER_KM = 300.0
FATOR_IQR_OUTLIER = 3.0
RAIO_PAR_KM, MIN_ANOS_PAR = 10.0, 30
RAIO_DENSIDADE_KM = 50.0


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def corda(km):
    return 2 * np.sin(km / R_TERRA_KM / 2)


def km_da_corda(c):
    return 2 * R_TERRA_KM * np.arcsin(np.asarray(c) / 2)


class _UnpicklerSoNumpy(pickle.Unpickler):
    """ID.npy is an object array (pickled). Only numpy array reconstruction is
    allowed, so a tampered file cannot execute code."""
    PERMITIDOS = {('numpy.core.multiarray', '_reconstruct'), ('numpy', 'ndarray'), ('numpy', 'dtype')}

    def find_class(self, modulo, nome):
        modulo = modulo.replace('numpy._core', 'numpy.core')
        if (modulo, nome) not in self.PERMITIDOS:
            raise pickle.UnpicklingError(f'classe bloqueada: {modulo}.{nome}')
        return super().find_class(modulo, nome)


def carregar_estacoes(caminho_npz):
    with zipfile.ZipFile(caminho_npz) as z, z.open('ID.npy') as fh:
        versao = np.lib.format.read_magic(fh)
        np.lib.format._read_array_header(fh, versao)
        ids = np.asarray(_UnpicklerSoNumpy(fh).load()).astype(str)
    npz = np.load(caminho_npz, allow_pickle=False)
    lla = npz['lat_lon_alt']
    meta = pd.DataFrame({'id': ids, 'lat': lla[:, 0], 'lon': lla[:, 1], 'alt': lla[:, 2]})
    return npz['data'], meta


def resumo_anual(dados):
    """Per gauge and year: annual maximum, valid days, wet days, annual total."""
    dias = pd.date_range('1961-01-01', periods=dados.shape[0], freq='D')
    anos = dias.year.values
    saida = {}
    for ano in np.unique(anos):
        bloco = dados[anos == ano].astype('float32')
        bloco[bloco < 0] = np.nan
        validos = np.isfinite(bloco)
        saida[ano] = dict(
            maxima=np.nanmax(np.where(validos, bloco, -1), axis=0),
            n_validos=validos.sum(0),
            n_chuva=(bloco > 0).sum(0),
            total=np.nansum(bloco, axis=0),
        )
    return saida


def serie_grade():
    registros = pd.DataFrame(json.load(open(ARQ_SERIE, encoding='utf-8')))
    registros['codigo_ibge'] = registros.codigo_ibge.astype(str)
    return registros.pivot(index='ano', columns='codigo_ibge', values='chuva_max_diaria_mm')


def centroides():
    if not ARQ_CENTROIDES.exists():
        import geobr  # only needed once, the result is cached in qc/
        m = geobr.read_municipality(year=2020, simplified=True)
        c = m.to_crs(5880).centroid.to_crs(4326)
        pd.DataFrame({'codigo_ibge': m.code_muni.astype('int64').astype(str), 'nome': m.name_muni,
                      'uf': m.abbrev_state, 'lat': c.y, 'lon': c.x}).to_csv(ARQ_CENTROIDES, index=False)
    return pd.read_csv(ARQ_CENTROIDES, dtype={'codigo_ibge': str})


def pettitt(x):
    n = len(x)
    r = stats.rankdata(x)
    u = np.array([2 * r[:t].sum() - t * (n + 1) for t in range(1, n)])
    k = np.abs(u).max()
    return int(np.abs(u).argmax()), float(min(1.0, 2 * np.exp(-6 * k ** 2 / (n ** 3 + n ** 2))))


def fdr_bh(p, q=0.10):
    """Benjamini-Hochberg: boolean mask of discoveries (Wilks, 2016, field significance)."""
    p = np.asarray(p)
    ordem = np.argsort(p)
    m = len(p)
    aceitos = p[ordem] <= q * np.arange(1, m + 1) / m
    mascara = np.zeros(m, bool)
    if aceitos.any():
        mascara[ordem[:aceitos.nonzero()[0].max() + 1]] = True
    return mascara


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--pr', required=True, help='pr.npz com os dados observados usados pelo BR-DWGD')
    args = parser.parse_args()
    PASTA_QC.mkdir(exist_ok=True)

    print('Lendo estações ...')
    dados, meta = carregar_estacoes(args.pr)
    resumo = resumo_anual(dados)
    del dados
    anos = sorted(resumo)
    tabela = lambda campo: pd.DataFrame({a: resumo[a][campo] for a in anos}, index=meta.id).T
    maxima, n_validos, n_chuva = tabela('maxima'), tabela('n_validos'), tabela('n_chuva')
    completo = n_validos >= MIN_DIAS_VALIDOS
    maxima = maxima.where(completo & (maxima >= 0))
    maxima.round(1).to_csv(PASTA_QC / 'estacoes_maxima_anual.csv.gz')
    meta.to_csv(PASTA_QC / 'estacoes_meta.csv', index=False)

    # 2) monthly-totals signature
    suspeito = completo & (n_chuva <= MAX_DIAS_CHUVA_MENSAL) & (maxima > MIN_MAXIMA_MENSAL_MM)
    n_susp = suspeito.sum()
    estacoes_susp = n_susp[n_susp >= MIN_ANOS_ESTACAO_SUSPEITA].index.tolist()
    sinalizadas = []
    for est in estacoes_susp:
        anos_ruins = [int(a) for a in suspeito.index[suspeito[est]]]
        linha = meta.set_index('id').loc[est]
        sinalizadas.append({'id': est, 'lat': float(linha.lat), 'lon': float(linha.lon), 'anos': anos_ruins,
                            'dias_chuva_mediana': float(n_chuva.loc[anos_ruins, est].median()),
                            'maxima_mediana_mm': float(maxima.loc[anos_ruins, est].median())})
    print(f'Estações com assinatura de totais mensais persistente: {[s["id"] for s in sinalizadas]}')
    isolados = []
    for est in n_susp[(n_susp > 0) & (n_susp < MIN_ANOS_ESTACAO_SUSPEITA)].index:
        linha = meta.set_index('id').loc[est]
        for ano in suspeito.index[suspeito[est]]:
            isolados.append({'id': est, 'lat': float(linha.lat), 'lon': float(linha.lon), 'ano': int(ano),
                             'dias_chuva': int(n_chuva.loc[ano, est]), 'maxima_mm': float(maxima.loc[ano, est])})
    print(f'Estação-anos isolados com a mesma assinatura: {len(isolados)}')

    # 3) contaminated municipalities
    grade = serie_grade()
    mun = centroides()
    excluidos, influencia = {}, []
    for s in sinalizadas:
        ruim = grade.index.isin(s['anos'])
        razao = grade[ruim].mean() / grade[~ruim].mean()
        limiar = float(razao.quantile(QUANTIL_RAZAO))
        dist = km_da_corda(np.linalg.norm(xyz(mun.lat.values, mun.lon.values) - xyz([s['lat']], [s['lon']]), axis=1))
        for (_, m), d in zip(mun.iterrows(), dist):
            if d > RAIO_INFLUENCIA_KM or m.codigo_ibge not in razao:
                continue
            afetado = bool(razao[m.codigo_ibge] > limiar)
            influencia.append({'estacao': s['id'], 'codigo_ibge': m.codigo_ibge, 'nome': m.nome, 'uf': m.uf,
                               'dist_km': round(float(d), 1), 'razao': round(float(razao[m.codigo_ibge]), 3),
                               'limiar_p95': round(limiar, 3), 'afetado': afetado})
            if afetado:
                e = excluidos.setdefault(m.codigo_ibge, {'nome': m.nome, 'uf': m.uf, 'anos': [], 'motivo': []})
                e['anos'] = sorted(set(e['anos']) | set(s['anos']))
                e['motivo'].append(f'estação {s["id"]}: totais mensais registrados como chuva diária')
    pd.DataFrame(influencia).to_csv(PASTA_QC / 'influencia_estacoes_sinalizadas.csv', index=False)

    xyz_mun = xyz(mun.lat.values, mun.lon.values)
    for s in isolados:
        dist = km_da_corda(np.linalg.norm(xyz_mun - xyz([s['lat']], [s['lon']]), axis=1))
        for (_, m), d in zip(mun.iterrows(), dist):
            if d > RAIO_OUTLIER_KM or m.codigo_ibge not in grade:
                continue
            x = grade[m.codigo_ibge].dropna()
            ja = excluidos.get(m.codigo_ibge, {}).get('anos', [])
            if s['ano'] not in x.index or s['ano'] in ja:
                continue
            outros = x.drop([s['ano'], *[a for a in ja if a in x.index]])
            q1, q3 = outros.quantile([0.25, 0.75])
            if x[s['ano']] > q3 + FATOR_IQR_OUTLIER * (q3 - q1):
                e = excluidos.setdefault(m.codigo_ibge, {'nome': m.nome, 'uf': m.uf, 'anos': [], 'motivo': []})
                e['anos'] = sorted(set(e['anos']) | {s['ano']})
                e['motivo'].append(f'{s["ano"]}: estação {s["id"]} ({d:.0f} km), totais mensais como chuva diária; '
                                   f'valor da grade {x[s["ano"]]:.0f} mm > Q3 + {FATOR_IQR_OUTLIER:g} IQR')
    with open(PASTA_QC / 'anos_excluidos.json', 'w', encoding='utf-8') as f:
        json.dump({'estacoes_sinalizadas': sinalizadas, 'estacao_anos_isolados': isolados, 'municipios': excluidos},
                  f, ensure_ascii=False, indent=1)
    print(f'Município-anos excluídos: {sum(len(e["anos"]) for e in excluidos.values())}')
    print(f'Municípios com anos excluídos: {len(excluidos)}')

    # 4) grid vs nearest gauge
    arv = cKDTree(xyz(meta.lat.values, meta.lon.values))
    dist, idx = arv.query(xyz(mun.lat.values, mun.lon.values))
    pares = []
    for (_, m), d, j in zip(mun.iterrows(), km_da_corda(dist), idx):
        if d > RAIO_PAR_KM or m.codigo_ibge not in grade:
            continue
        est = meta.id.iat[j]
        ambos = pd.concat([grade[m.codigo_ibge], maxima[est]], axis=1, keys=['g', 's']).dropna()
        if m.codigo_ibge in excluidos:
            ambos = ambos.drop(excluidos[m.codigo_ibge]['anos'], errors='ignore')
        if len(ambos) < MIN_ANOS_PAR:
            continue
        tg, pg = stats.kendalltau(ambos.index, ambos.g)
        ts, ps = stats.kendalltau(ambos.index, ambos.s)
        pares.append({'codigo_ibge': m.codigo_ibge, 'nome': m.nome, 'uf': m.uf, 'estacao': est, 'dist_km': round(float(d), 2),
                      'n_anos': len(ambos), 'media_grade': ambos.g.mean(), 'media_estacao': ambos.s.mean(),
                      'razao': ambos.g.mean() / ambos.s.mean(), 'r': ambos.g.corr(ambos.s),
                      'tau_grade': tg, 'p_grade': pg, 'tau_estacao': ts, 'p_estacao': ps})
    pd.DataFrame(pares).to_csv(PASTA_QC / 'pares_grade_estacao.csv', index=False)
    print(f'Pares grade x estação: {len(pares)}')

    # 5) trends and network density
    vizinhas = arv.query_ball_point(xyz(mun.lat.values, mun.lon.values), corda(RAIO_DENSIDADE_KM))
    ok = completo[meta.id.values].values
    periodo = lambda a0, a1: (np.array(anos) >= a0) & (np.array(anos) <= a1)
    p1, p2 = periodo(1961, 1980), periodo(1981, 2025)
    linhas = []
    for (_, m), viz in zip(mun.iterrows(), vizinhas):
        if m.codigo_ibge not in grade:
            continue
        x = grade[m.codigo_ibge]
        if m.codigo_ibge in excluidos:
            x = x.drop(excluidos[m.codigo_ibge]['anos'])
        x = x.dropna()
        if len(x) < 20:
            continue
        tau, p_mk = stats.kendalltau(x.index, x.values)
        i_cp, p_pet = pettitt(x.values)
        linhas.append({'codigo_ibge': m.codigo_ibge, 'nome': m.nome, 'uf': m.uf, 'lat': m.lat, 'lon': m.lon,
                       'n_anos': len(x), 'mk_tau': tau, 'mk_p': p_mk, 'pettitt_ano': int(x.index[i_cp]),
                       'pettitt_p': p_pet,
                       'n50_1961_1980': ok[p1][:, viz].sum(1).mean() if viz else 0.0,
                       'n50_1981_2025': ok[p2][:, viz].sum(1).mean() if viz else 0.0})
    tend = pd.DataFrame(linhas)
    tend['mk_fdr'] = fdr_bh(tend.mk_p.values)
    tend['pettitt_fdr'] = fdr_bh(tend.pettitt_p.values)
    tend.to_csv(PASTA_QC / 'tendencias_municipios.csv', index=False)
    contagem = pd.DataFrame(completo.values, index=anos, columns=meta.id).T.groupby(
        mun.uf.values[cKDTree(xyz(mun.lat.values, mun.lon.values)).query(xyz(meta.lat.values, meta.lon.values))[1]]).sum().T
    contagem.to_csv(PASTA_QC / 'estacoes_validas_por_uf_ano.csv')
    print(f'Tendência MK significativa (FDR q=0,10): {tend.mk_fdr.sum()} de {len(tend)}')
    print(f'Saídas em {PASTA_QC.resolve()}')


if __name__ == '__main__':
    main()
