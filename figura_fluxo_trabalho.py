"""Draws the processing-workflow diagram used as Fig. 1 of the paper.

Usage:
    python figura_fluxo_trabalho.py [saida.png]
"""

import sys

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

VERDE = '#0b5d3f'
VERDE_CLARO = '#eef6f2'
LARANJA = '#a64b00'
LARANJA_CLARO = '#fdf1e7'

ETAPAS = [
    # (x, title, tool, script, action, output file, output detail)
    (0.0, '1. Extraction', 'Google Earth Engine', 'extrair_chuva_maxima.py',
     'Annual maximum daily\nrainfall at each centroid', 'xavier_..._1961_2025.json', '362,115 records'),
    (1.0, '2. Quality control', 'Python', 'controle_qualidade_\nestacoes.py',
     'Screen the grid against the\nBR-DWGD source gauges', 'qc/anos_excluidos.json', '968 municipality-years\nflagged'),
    (2.0, '3. IDF calculation', 'Python', 'calcular_idf_\nmunicipios.py',
     'Fit distributions and\ncalibrate the IDF equation', 'idf_municipios.json', '5,569 municipalities'),
    (3.0, '4. Repackaging', 'Python', 'exportar_dados_\nsite.py',
     'Split results for\nbrowser delivery', 'idf_municipios_resumo.csv\nidf_uf/{UF}.json', ''),
    (4.0, '5. Presentation', 'HTML / JavaScript', 'index.html\nidf.html',
     'Interactive map and\nmunicipal IDF curves', 'IDFTec Data', 'static web application'),
]
ANALISE = ('6. Statistical analysis', 'Python', 'analise_estatistica_idf_municipios.ipynb\ncontrole_qualidade_grade.ipynb',
           'National, state and quality-control statistics and figures')

W, H, GAP = 0.86, 1.0, 1.0


def caixa(ax, x, y, w, h, cor_borda, cor_fundo, estilo='-'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.0,rounding_size=0.03',
                                linewidth=1.3, edgecolor=cor_borda, facecolor=cor_fundo, linestyle=estilo))


def seta(ax, p0, p1, cor=VERDE, estilo='-'):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>', mutation_scale=12, color=cor, lw=1.4, linestyle=estilo))


def main(saida):
    fig, ax = plt.subplots(figsize=(13, 5.6))
    ax.set_xlim(-0.08, 4.95); ax.set_ylim(-1.55, 1.35); ax.axis('off')

    for i, (x, titulo, ferramenta, script, acao, arquivo, detalhe) in enumerate(ETAPAS):
        cor = LARANJA if i == 1 else VERDE
        fundo = LARANJA_CLARO if i == 1 else VERDE_CLARO
        caixa(ax, x, 0.15, W, H, cor, fundo)
        ax.add_patch(FancyBboxPatch((x, 0.88), W, 0.27, boxstyle='round,pad=0.0,rounding_size=0.03',
                                    facecolor=cor, edgecolor=cor))
        ax.text(x + 0.04, 1.06, titulo, color='white', fontsize=11, fontweight='bold', va='center')
        ax.text(x + 0.04, 0.95, ferramenta, color='white', fontsize=8.5, va='center')
        ax.text(x + W / 2, 0.66, script, family='monospace', fontsize=8.3, ha='center', va='center')
        ax.text(x + W / 2, 0.33, acao, fontsize=8.5, ha='center', va='center')
        caixa(ax, x, -0.62, W, 0.5, cor, 'white', estilo='--')
        ax.text(x + W / 2, -0.30, arquivo, family='monospace', fontsize=7.6, ha='center', va='center')
        if detalhe:
            ax.text(x + W / 2, -0.50, detalhe, fontsize=7.8, ha='center', va='center', color='0.3')
        seta(ax, (x + W / 2, 0.15), (x + W / 2, -0.12), cor)
        if i < len(ETAPAS) - 1:
            seta(ax, (x + W, 0.6), (x + GAP, 0.6))

    # gauge data entering the QC stage
    ax.text(1.0 + W / 2, 1.27, 'BR-DWGD source gauges (pr.npz, 14,170 gauges)', fontsize=8, ha='center', color=LARANJA)
    seta(ax, (1.0 + W / 2, 1.22), (1.0 + W / 2, 1.16), LARANJA)

    # analysis branch
    titulo, ferramenta, nbs, acao = ANALISE
    caixa(ax, 1.0, -1.5, 2.0 + W, 0.62, VERDE, VERDE_CLARO)
    ax.text(1.04, -0.98, f'{titulo}  ·  {ferramenta}', fontsize=10, fontweight='bold', color=VERDE, va='center')
    ax.text(1.04, -1.17, nbs, family='monospace', fontsize=7.8, va='center')
    ax.text(1.04, -1.4, acao, fontsize=8.3, va='center')
    for x in (0.0, 1.0, 2.0):
        seta(ax, (x + W / 2, -0.62), (max(x + W / 2, 1.1), -0.88), '0.45', '--')

    plt.savefig(saida, dpi=300, bbox_inches='tight', facecolor='white')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'fluxo_trabalho.png')
