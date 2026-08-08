"""Extrai a chuva máxima diária anual por município (grade Xavier BR-DWGD)
via Google Earth Engine e salva um JSON na pasta do projeto.

Versão em script (roda local, sem depender de Colab/download manual) do
`chuva_maxima_anual_municipios_xavier.ipynb` — mesma lógica: correção de
escala/offset da banda `pr`, paginação para não estourar o limite de ~5000
elementos por consulta síncrona do Earth Engine, retry com espera, checkpoint
incremental por ano e preenchimento por vizinhança para municípios cujo
centróide cai num pixel sem dado válido.

Uso:
    python extrair_chuva_maxima.py
    python extrair_chuva_maxima.py --ano-inicial 2020 --ano-final 2025
    python extrair_chuva_maxima.py --saida meu_arquivo.json
"""

import argparse
import json
import time
from pathlib import Path

import ee

GEE_PROJECT = 'fcoliveira'
XAVIER_ASSET = 'projects/ee-alexandrexavier/assets/BR-DWGD'
CENTROIDES_ASSET = 'projects/fcoliveira/assets/centroide_br'
COL_CODIGO = '﻿codigo_ibge'  # BOM presente no asset de centroides atual

ESCALA_METROS = 11_000  # resolução nativa da grade Xavier é 0,1° (~11 km)
TILE_SCALE = 4
TAMANHO_PAGINA = 2000  # bem abaixo do limite de ~5000 elementos por consulta síncrona do EE
MAX_TENTATIVAS = 3
ESPERA_ENTRE_TENTATIVAS_S = 30
RAIOS_PREENCHIMENTO_M = [20_000, 50_000, 100_000]  # raios progressivos para preencher nulos com média da vizinhança

CAMPOS = ['codigo_ibge', 'nome_municipio', 'uf', 'ano', 'chuva_max_diaria_mm', 'unidade', 'fonte', 'metodo']


def inicializar_earth_engine():
    try:
        ee.Initialize(project=GEE_PROJECT)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)
    print('Earth Engine inicializado com sucesso.')


def _pixel_bruto_para_mm(imagem):
    mult = ee.Number(imagem.get('BAND_pr_MULT'))
    add = ee.Number(imagem.get('BAND_pr_ADD'))
    return imagem.multiply(mult).add(add).copyProperties(imagem, imagem.propertyNames())


def imagem_maxima_anual(chuva_diaria, ano):
    inicio = ee.Date.fromYMD(ano, 1, 1)
    fim = inicio.advance(1, 'year')

    return (
        chuva_diaria.filterDate(inicio, fim)
        .map(_pixel_bruto_para_mm)
        .max()
        .rename('chuva_max_diaria_mm')
    )


def calcular_maximo_anual(chuva_diaria, municipios, ano):
    maximo_anual = imagem_maxima_anual(chuva_diaria, ano)

    return maximo_anual.reduceRegions(
        collection=municipios,
        reducer=ee.Reducer.first().setOutputs(['chuva_max_diaria_mm']),
        scale=ESCALA_METROS,
        tileScale=TILE_SCALE,
    ).map(lambda feicao: feicao.set({
        'ano': ano,
        'fonte': 'Xavier BR-DWGD',
        'unidade': 'mm/dia',
    }))


def _getInfo_com_retry(objeto_ee, descricao):
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            return objeto_ee.getInfo()
        except Exception as erro:
            print(f'{descricao}: falha na tentativa {tentativa}/{MAX_TENTATIVAS} ({erro})')
            if tentativa < MAX_TENTATIVAS:
                time.sleep(ESPERA_ENTRE_TENTATIVAS_S)
    return None


def preencher_nulos_por_vizinhanca(municipios, imagem_ano, registros_por_codigo, pendentes):
    preenchidos = 0
    for raio in RAIOS_PREENCHIMENTO_M:
        if not pendentes:
            break
        alvo = municipios.filter(ee.Filter.inList('codigo_ibge', list(pendentes)))
        alvo_buffer = alvo.map(lambda feicao: feicao.setGeometry(feicao.geometry().buffer(raio)))

        resultado = _getInfo_com_retry(
            imagem_ano.reduceRegions(
                collection=alvo_buffer,
                reducer=ee.Reducer.mean().setOutputs(['chuva_max_diaria_mm']),
                scale=ESCALA_METROS,
                tileScale=TILE_SCALE,
            ),
            f'Preenchimento por vizinhança (raio {raio // 1000} km)',
        )
        if resultado is None:
            continue

        ainda_pendentes = set()
        for feicao in resultado['features']:
            propriedades = feicao['properties']
            codigo = propriedades.get('codigo_ibge')
            valor = propriedades.get('chuva_max_diaria_mm')
            if valor is None:
                ainda_pendentes.add(codigo)
            else:
                registros_por_codigo[codigo]['chuva_max_diaria_mm'] = valor
                registros_por_codigo[codigo]['metodo'] = f'media_vizinhanca_{raio // 1000}km'
                preenchidos += 1
        pendentes = ainda_pendentes

    return preenchidos, pendentes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ano-inicial', type=int, default=1961)
    parser.add_argument('--ano-final', type=int, default=2025, help='inclusivo')
    parser.add_argument('--saida', default=None, help='padrão: xavier_chuva_maxima_diaria_anual_municipios_<ini>_<fim>.json')
    args = parser.parse_args()

    ano_inicial, ano_final = args.ano_inicial, args.ano_final
    assert ano_inicial <= ano_final, 'ano-inicial deve ser menor ou igual a ano-final'

    caminho_saida = Path(args.saida) if args.saida else Path.cwd() / f'xavier_chuva_maxima_diaria_anual_municipios_{ano_inicial}_{ano_final}.json'

    inicializar_earth_engine()

    chuva_diaria = ee.ImageCollection(XAVIER_ASSET).select('pr')
    municipios = ee.FeatureCollection(CENTROIDES_ASSET).map(
        lambda feicao: ee.Feature(feicao.geometry(), {
            'codigo_ibge': ee.String(feicao.get(COL_CODIGO)),
            'nome_municipio': feicao.get('nome_municipio'),
            'uf': feicao.get('uf_sigla'),
        })
    )

    total_municipios = municipios.size().getInfo()
    print('Bandas disponíveis:', chuva_diaria.first().bandNames().getInfo())
    print('Centroides carregados:', total_municipios)
    print('Período solicitado:', ano_inicial, 'a', ano_final)
    print('Arquivo de saída:', caminho_saida.resolve())

    registros = []
    anos_com_falha = []

    for ano in range(ano_inicial, ano_final + 1):
        resultado_ano = calcular_maximo_anual(chuva_diaria, municipios, ano)

        feicoes_ano = []
        ano_ok = True
        for inicio_pagina in range(0, total_municipios, TAMANHO_PAGINA):
            pagina_ok = False
            for tentativa in range(1, MAX_TENTATIVAS + 1):
                try:
                    pagina = resultado_ano.toList(TAMANHO_PAGINA, inicio_pagina).getInfo()
                    feicoes_ano.extend(pagina)
                    pagina_ok = True
                    break
                except Exception as erro:
                    print(f'Ano {ano}, página a partir de {inicio_pagina}: falha na tentativa {tentativa}/{MAX_TENTATIVAS} ({erro})')
                    if tentativa < MAX_TENTATIVAS:
                        time.sleep(ESPERA_ENTRE_TENTATIVAS_S)
            if not pagina_ok:
                ano_ok = False

        if not ano_ok:
            anos_com_falha.append(ano)

        registros_do_ano = {}
        for feicao in feicoes_ano:
            propriedades = feicao['properties']
            registro = {campo: propriedades.get(campo) for campo in CAMPOS if campo != 'metodo'}
            registro['metodo'] = 'centroide'
            registros_do_ano[registro['codigo_ibge']] = registro

        pendentes = {codigo for codigo, r in registros_do_ano.items() if r['chuva_max_diaria_mm'] is None}
        preenchidos = 0
        if pendentes:
            imagem_ano = imagem_maxima_anual(chuva_diaria, ano)
            preenchidos, pendentes = preencher_nulos_por_vizinhanca(municipios, imagem_ano, registros_do_ano, pendentes)

        registros.extend(registros_do_ano.values())

        nulos_no_ano = len(pendentes)
        aviso_nulos = ''
        if preenchidos:
            aviso_nulos += f', {preenchidos} preenchido(s) por média da vizinhança'
        if nulos_no_ano:
            aviso_nulos += f', {nulos_no_ano} ainda nulo(s) mesmo após vizinhança'
        aviso_contagem = ''
        if feicoes_ano and len(feicoes_ano) != total_municipios:
            aviso_contagem = f' [ATENÇÃO: esperado {total_municipios}]'
        print(f'Ano {ano}: {len(feicoes_ano)} municípios extraídos (total acumulado: {len(registros)}){aviso_nulos}{aviso_contagem}')

        # Regrava o JSON a cada ano processado, para não perder o progresso já
        # feito se um ano posterior falhar todas as tentativas.
        with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
            json.dump(registros, arquivo, ensure_ascii=False, indent=2)

    print()
    print(f'JSON salvo em: {caminho_saida.resolve()}')
    print(f'Total de registros: {len(registros)}')

    total_nulos = sum(1 for r in registros if r['chuva_max_diaria_mm'] is None)
    if total_nulos:
        print(f'ATENÇÃO: {total_nulos} registro(s) com chuva_max_diaria_mm nulo mesmo após preenchimento por vizinhança.')

    if anos_com_falha:
        print(f'ATENÇÃO: anos com pelo menos uma página que falhou após {MAX_TENTATIVAS} tentativas: {anos_com_falha}')


if __name__ == '__main__':
    main()
