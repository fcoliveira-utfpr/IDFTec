"""Reempacota os resultados (idf_municipios.json + série bruta) no formato
usado pelo site estático IDFTec Data — mesmo padrão do climas_brasil
(fcoliveira-utfpr/climas_brasil): um CSV resumo (para o mapa/tabela) e um
JSON leve por UF (para os gráficos, carregado sob demanda ao trocar de estado).

Gera:
    idf_municipios_resumo.csv   — 1 linha por município (mapa + cards de índice)
    idf_uf/{UF}.json            — curvas IDF completas por município daquela UF
    serie_uf/{UF}.json          — série histórica anual (chuva máx. diária) por município

Uso:
    python exportar_dados_site.py
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
DURACOES_MIN = [5, 10, 15, 20, 25, 30, 60, 360, 480, 600, 720, 1440]
PERIODOS_RETORNO = ['5', '10', '25', '50', '100']

# O código IBGE já contém o código do estado nos 2 primeiros dígitos — usado
# como fallback para o único registro com UF vazia no asset de centroides
# (Boa Esperança do Norte, MT, ver MEMORIA_PROJETO.md).
CODIGO_UF = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF',
}


def corrigir_uf(codigo_ibge, uf):
    return uf if uf else CODIGO_UF.get(codigo_ibge[:2], uf)


def main():
    with open(BASE / 'xavier_chuva_maxima_diaria_anual_municipios_1961_2025.json', encoding='utf-8') as f:
        registros_brutos = json.load(f)

    anos_vizinhanca = defaultdict(int)
    anos_total = defaultdict(int)
    for r in registros_brutos:
        anos_total[r['codigo_ibge']] += 1
        if r['metodo'] != 'centroide':
            anos_vizinhanca[r['codigo_ibge']] += 1

    anos = sorted({r['ano'] for r in registros_brutos})
    ano_para_indice = {ano: i for i, ano in enumerate(anos)}
    uf_para_serie = defaultdict(dict)
    nome_por_codigo = {}
    for r in registros_brutos:
        codigo = r['codigo_ibge']
        nome_por_codigo[codigo] = r['nome_municipio']
        uf = corrigir_uf(codigo, r['uf'])
        serie = uf_para_serie[uf].setdefault(codigo, {
            'nome': r['nome_municipio'],
            'valores': [None] * len(anos),
            'anos_vizinhanca': [],
        })
        idx = ano_para_indice[r['ano']]
        v = r['chuva_max_diaria_mm']
        serie['valores'][idx] = round(v, 1) if v is not None else None
        if r['metodo'] != 'centroide':
            serie['anos_vizinhanca'].append(r['ano'])
    for uf, municipios in uf_para_serie.items():
        for serie in municipios.values():
            if not serie['anos_vizinhanca']:
                del serie['anos_vizinhanca']

    with open(BASE / 'idf_municipios.json', encoding='utf-8') as f:
        idf_registros = json.load(f)

    linhas_csv = []
    uf_para_municipios = defaultdict(dict)

    for r in idf_registros:
        codigo = r['codigo_ibge']
        uf = corrigir_uf(codigo, r['uf'])
        pct_vizinhanca = round(100 * anos_vizinhanca[codigo] / anos_total[codigo], 1) if anos_total[codigo] else 0.0

        linhas_csv.append({
            'code_muni': codigo,
            'name_muni': r['nome_municipio'],
            'abbrev_state': uf,
            'n_anos': r['n_anos'],
            'distribuicao': r['distribuicao'],
            'idf_k': round(r['idf']['k'], 2),
            'idf_a': round(r['idf']['a'], 4),
            'idf_b': round(r['idf']['b'], 3),
            'idf_c': round(r['idf']['c'], 4),
            'idf_r2': round(r['idf']['r2'], 4),
            'intensidade_tr100_24h_mm_h': round(r['quantis_mm_h']['1440 min']['100'], 2),
            'chuva_max_media_mm': None,  # preenchido abaixo
            'pct_anos_vizinhanca': pct_vizinhanca,
        })

        curvas = {tr: [round(r['quantis_mm_h'][f'{d} min'][tr], 2) for d in DURACOES_MIN] for tr in PERIODOS_RETORNO}
        uf_para_municipios[uf][codigo] = {
            'idf_k': round(r['idf']['k'], 2),
            'idf_a': round(r['idf']['a'], 4),
            'idf_b': round(r['idf']['b'], 3),
            'idf_c': round(r['idf']['c'], 4),
            'idf_r2': round(r['idf']['r2'], 4),
            'distribuicao': r['distribuicao'],
            'duracoes_min': DURACOES_MIN,
            'curvas_mm_h': curvas,
        }

    # Chuva máxima diária anual média — calculada direto da série bruta
    soma = defaultdict(float)
    conta = defaultdict(int)
    for r in registros_brutos:
        if r['chuva_max_diaria_mm'] is not None:
            soma[r['codigo_ibge']] += r['chuva_max_diaria_mm']
            conta[r['codigo_ibge']] += 1
    media_chuva = {c: soma[c] / conta[c] for c in soma if conta[c]}
    for linha in linhas_csv:
        m = media_chuva.get(linha['code_muni'])
        linha['chuva_max_media_mm'] = round(m, 1) if m is not None else None

    campos = ['code_muni', 'name_muni', 'abbrev_state', 'n_anos', 'distribuicao',
              'idf_k', 'idf_a', 'idf_b', 'idf_c', 'idf_r2',
              'intensidade_tr100_24h_mm_h', 'chuva_max_media_mm', 'pct_anos_vizinhanca']
    caminho_csv = BASE / 'idf_municipios_resumo.csv'
    with open(caminho_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas_csv)
    print(f'{caminho_csv.name}: {len(linhas_csv)} municípios')

    pasta_uf = BASE / 'idf_uf'
    pasta_uf.mkdir(exist_ok=True)
    for uf, municipios in uf_para_municipios.items():
        if not uf:
            continue
        caminho = pasta_uf / f'{uf}.json'
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(municipios, f, ensure_ascii=False, separators=(',', ':'))
        print(f'idf_uf/{uf}.json: {len(municipios)} municípios')

    sem_uf = uf_para_municipios.get('', {})
    if sem_uf:
        print(f'ATENÇÃO: {len(sem_uf)} município(s) sem UF preenchida, não entraram em nenhum idf_uf/*.json: {list(sem_uf.keys())}')

    pasta_serie = BASE / 'serie_uf'
    pasta_serie.mkdir(exist_ok=True)
    for uf, municipios in uf_para_serie.items():
        if not uf:
            continue
        caminho = pasta_serie / f'{uf}.json'
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump({'anos': anos, 'municipios': municipios}, f, ensure_ascii=False, separators=(',', ':'))
        print(f'serie_uf/{uf}.json: {len(municipios)} municípios')


if __name__ == '__main__':
    main()
