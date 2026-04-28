# Monitor de Riesgo Bancario Chileno 🇨🇱

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.17+-3D4FDB?style=flat&logo=plotly&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup4-Web%20Scraping-orange?style=flat)
![CMF](https://img.shields.io/badge/Fuente-CMF%20Chile-blue?style=flat)
![BCC](https://img.shields.io/badge/Fuente-Banco%20Central%20Chile-red?style=flat)
![Estado](https://img.shields.io/badge/Estado-Completo-3fb950?style=flat)

> Análisis estadístico del riesgo de crédito del sistema bancario chileno integrando datos reales de la **CMF** y la **API BDE del Banco Central de Chile**. El proyecto cubre 25 instituciones bancarias entre enero 2016 y febrero 2026, con foco en la transmisión de política monetaria sobre la morosidad del sistema.

---

## Pregunta Central

**¿Cómo impacta el ciclo monetario chileno en el riesgo de crédito del sistema bancario, y qué instituciones son más vulnerables a shocks macroeconómicos?**

Este es el tipo de análisis que realizan analistas en mesas de riesgo, la CMF y el propio Banco Central — aquí replicado con datos públicos y código reproducible.

---

## Fuentes de Datos

| Fuente | Dataset | Método de ingesta |
|--------|---------|-------------------|
| **CMF Chile** | Indicador de Morosidad 90+ días por banco y cartera | Web scraping automatizado (BeautifulSoup) |
| **Banco Central (API BDE)** | TPM, IMACEC, Colocaciones, IPC, USD | API REST con registro gratuito |

- CMF: https://www.cmfchile.cl/portal/estadisticas/617/w3-propertyvalue-28914.html
- BCC API: https://si3.bcentral.cl/Siete/ES/Siete/API

---

## Resultados Clave

| Métrica | Resultado |
|---------|-----------|
| Período analizado | Ene 2016 – Feb 2026 (122 meses) |
| Instituciones cubiertas | 25 bancos |
| Rezago TPM → morosidad | **17 meses** (r = 0.67) |
| Morosidad sistema actual | 1.81% |
| TPM vigente | 4.50% |
| Banco más riesgoso (Feb 2026) | Banco Ripley (5.31%) |
| Banco más sólido (Feb 2026) | Banco BICE (1.31%) |
| Mora máxima histórica | 2.17% (COVID-19, 2020) |

### 🔴 Transmisión monetaria con rezago de 17 meses
La TPM correlaciona con la morosidad bancaria con un rezago óptimo de **17 meses** (r = 0.67), cuantificado mediante análisis de correlaciones cruzadas para rezagos de 0 a 24 meses. Esto es consistente con el mecanismo de transmisión documentado por el Banco Central en sus Informes de Política Financiera.

### 📊 Diferencial por tipo de cartera
Las carteras de consumo y vivienda son calculadas exclusivamente sobre bancos retail (aquellos con datos consistentes en esas carteras), evitando la contaminación de bancos corporativos o de inversión que no operan esos segmentos.

### 🏦 Concentración del riesgo (HHI)
El índice HHI aplicado a morosidad se mantiene bajo 1.500 en condiciones normales, pero se concentra durante períodos de estrés — con las instituciones de banca de consumo absorbiendo un rol desproporcionado.

### ⚡ Períodos de estrés identificados
| Período | Evento | Comportamiento observado |
|---------|--------|--------------------------|
| Oct–Dic 2019 | Estallido Social | Alza transitoria en consumo |
| Mar 2020–May 2021 | COVID-19 | Mora máxima histórica del sistema |
| Jun 2021–Jul 2023 | Ciclo inflacionario / Alza TPM | Presión sostenida en cartera comercial |
| Ago 2023–hoy | Normalización monetaria | Descenso gradual de mora total |

---

## Decisiones Metodológicas

**Clasificación por tipo de banco:** el dataset distingue entre bancos retail (con cartera consumo y/o vivienda) y bancos corporativos/inversión (solo comercial). Los promedios del sistema para consumo y vivienda se calculan exclusivamente sobre los bancos con datos consistentes en esa cartera, evitando sesgos por NaN estructurales.

**Limpieza de variación anual:** los valores `inf` generados cuando la mora base es cero son reemplazados por `NaN` antes del análisis, siguiendo criterios estadísticos estándar.

**Parser CMF robusto:** el scraper detecta automáticamente el formato del archivo (SBIF pre-2019, CMF pre-IFRS9, CMF post-IFRS9) ajustando el mapeo de columnas según el período.

---

## Estructura del Proyecto

```
chilean-banking-risk-monitor/
├── notebooks/
│   ├── 01_pipeline_datos.ipynb         # Web scraping CMF + API BCC + dataset maestro
│   ├── 02_analisis_estadistico.ipynb   # Análisis completo + visualizaciones estáticas
│   └── 03_dashboard_riesgo.ipynb       # Dashboard interactivo Plotly + semáforo
├── src/
│   ├── bcc_api.py                      # Cliente reutilizable API Banco Central
│   └── descargar_cmf.py               # Web scraper CMF (~126 informes Excel)
├── data/
│   ├── raw/
│   │   └── cmf_morosidad/             # Excel descargados automáticamente
│   └── processed/                      # Dataset maestro integrado (parquet)
├── reports/                            # Gráficos PNG + dashboards HTML interactivos
├── .env.example                        # Plantilla de credenciales
├── .gitignore
└── requirements.txt
```

---

## Metodología

```
CMF Chile (Web Scraping)             Banco Central (API BDE)
BeautifulSoup extrae ~126 links      TPM, IMACEC, Colocaciones, IPC
requests descarga Excel por mes                │
         │                                     │
         ▼                                     │
   Parser robusto CMF                          │
   (SBIF / pre / post IFRS-9)                  │
   Clasificacion retail vs corporativo         │
         │                                     │
         └──────────────┬────────────────────--┘
                        ▼
             Dataset Maestro Integrado
             2,172 obs | 25 bancos | 122 meses
             18 variables | Ene 2016 – Feb 2026
                        │
         ┌──────────────┼──────────────────────┐
         ▼              ▼                       ▼
   Evolución       Correlación TPM         Stress Period
   histórica       con rezagos 0–24m       Analysis
   por cartera     r=0.67 @ lag=17m        Heatmap retail
         │              │                       │
         └──────────────┴───────────────────────┘
                        ▼
             Dashboard Interactivo (Plotly)
             Semáforo de Riesgo por Institución
```

---

## Cómo Ejecutar

```bash
# 1. Clonar el repositorio
git clone https://github.com/Iakrshn/chilean-banking-risk-monitor.git
cd chilean-banking-risk-monitor

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar credenciales del Banco Central
cp .env.example .env
# Editar .env con tu usuario y contraseña (registro gratuito en si3.bcentral.cl)

# 4. Descargar automáticamente todos los informes CMF (~126 archivos Excel)
python src/descargar_cmf.py

# 5. Ejecutar notebooks en orden
jupyter notebook notebooks/
```

---

## Herramientas

| Herramienta | Uso |
|-------------|-----|
| **Python 3.10** | Lenguaje principal |
| **pandas / numpy** | Manipulación y limpieza de datos |
| **scipy.stats** | Correlaciones de Pearson/Spearman con análisis de rezagos |
| **matplotlib / seaborn** | Visualizaciones estáticas con bandas de ciclo macroeconómico |
| **plotly** | Dashboard interactivo y semáforo de riesgo |
| **requests + BeautifulSoup4** | Web scraping automatizado de informes CMF |
| **python-dotenv** | Manejo seguro de credenciales API |

---

## Contexto Regulatorio

El análisis utiliza definiciones y métricas alineadas con el marco regulatorio chileno:

- **Morosidad 90+ días:** definición CMF para cartera en incumplimiento, equivalente a la definición Basel II de default
- **TPM:** instrumento de política monetaria del BCCh, con efecto indirecto sobre el costo del crédito y la capacidad de pago de los deudores
- **Carteras CMF:** segmentación regulatoria en Comercial, Consumo y Vivienda — analizadas por separado dado su distinto perfil de riesgo

---

## Autor

**Krishna Bustos Santibáñez**  
Analista de Datos | Finanzas & Control de Gestión  
[LinkedIn](https://linkedin.com/in/krishnabustoss) · [GitHub](https://github.com/Iakrshn)
