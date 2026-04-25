# Monitor de Riesgo Bancario Chileno 🇨🇱

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.17+-3D4FDB?style=flat&logo=plotly&logoColor=white)
![CMF](https://img.shields.io/badge/Fuente-CMF%20Chile-blue?style=flat)
![BCC](https://img.shields.io/badge/Fuente-Banco%20Central%20Chile-red?style=flat)
![Estado](https://img.shields.io/badge/Estado-Completo-3fb950?style=flat)

> Análisis estadístico del riesgo de crédito del sistema bancario chileno integrando datos oficiales de la **CMF** y el **Banco Central de Chile**, con foco en la transmisión de la Tasa de Política Monetaria (TPM) sobre la morosidad bancaria.

---

## Pregunta Central

**¿Cómo impacta el ciclo monetario chileno en el riesgo de crédito del sistema bancario, y qué instituciones son más vulnerables a shocks macroeconómicos?**

Este es el tipo de análisis que realizan analistas en mesas de riesgo, la CMF y el propio Banco Central — aquí replicado con datos públicos y código reproducible.

---

## Fuentes de Datos

| Fuente | Dataset | Acceso |
|--------|---------|--------|
| **CMF Chile** | Indicador de Morosidad 90+ días por banco y cartera | Descarga mensual gratuita |
| **Banco Central (API BDE)** | TPM, IMACEC, Colocaciones, IPC, USD | API REST con registro gratuito |

- CMF: https://www.cmfchile.cl/portal/estadisticas/617/w3-propertyvalue-28914.html  
- BCC API: https://si3.bcentral.cl/Siete/ES/Siete/API

---

## Hallazgos Principales

### 🔴 Transmisión monetaria con rezago
La TPM correlaciona con la morosidad bancaria con un rezago de **12–18 meses**, cuantificado mediante análisis de correlaciones cruzadas. Esto confirma el mecanismo de transmisión documentado por el Banco Central en sus Informes de Política Financiera.

### 📊 Diferencial por tipo de cartera
La cartera de consumo presenta morosidad **2.5× mayor** que la hipotecaria, con mayor sensibilidad a ciclos económicos adversos (estallido social, COVID-19).

### 🏦 Concentración del riesgo
El HHI aplicado a morosidad revela que el riesgo del sistema está más concentrado en períodos de estrés — con las instituciones de banca de consumo absorbiendo un rol desproporcionado.

### ⚡ Períodos de estrés identificados
| Período | Evento | Impacto en mora |
|---------|--------|----------------|
| Oct 2019 | Estallido Social | +25% vs período previo |
| Mar–Jun 2020 | COVID-19 | +60% vs período previo |
| Ene 2022–Jul 2023 | Ciclo inflacionario / Alza TPM | +35% en consumo |

---

## Estructura del Proyecto

```
chilean-banking-risk-monitor/
├── notebooks/
│   ├── 01_pipeline_datos.ipynb         # Descarga API BCC + parseo CMF
│   ├── 02_analisis_estadistico.ipynb   # Análisis completo + visualizaciones
│   └── 03_dashboard_riesgo.ipynb       # Dashboard interactivo Plotly
├── src/
│   ├── bcc_api.py                      # Cliente reutilizable API Banco Central
│   └── descargar_cmf.py               # Web scraper CMF (~126 informes Excel)
├── data/
│   ├── raw/
│   │   └── cmf_morosidad/             # Excel descargados automáticamente
│   └── processed/                      # Dataset maestro integrado
├── reports/                            # Gráficos y dashboard HTML
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
   Parseo y limpieza                           │
   por banco y cartera                         │
         │                                     │
         └──────────────┬────────────────────--┘
                        ▼
             Dataset Maestro Integrado
             (panel mensual banco × período)
                        │
              ┌─────────┼──────────────────┐
              ▼         ▼                  ▼
        Evolución  Correlación TPM    Stress Period
        histórica  con rezagos        Analysis
              │         │                  │
              └─────────┴──────────────────┘
                        ▼
             Dashboard Interactivo
             Semáforo por Institución
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
| **pandas / numpy** | Manipulación de datos |
| **scipy.stats** | Análisis estadístico (correlaciones, tests) |
| **matplotlib / seaborn** | Visualizaciones estáticas |
| **plotly** | Dashboard interactivo |
| **requests + BeautifulSoup4** | Web scraping de informes CMF |
| **python-dotenv** | Manejo seguro de credenciales API |

---

## Contexto Regulatorio

El análisis utiliza definiciones y métricas alineadas con el marco regulatorio chileno:

- **Morosidad 90+ días:** Definición CMF para cartera en incumplimiento (equivalente a la definición Basel II de default)
- **TPM:** Instrumento de política monetaria del BCCh, con efecto indirecto sobre el costo del crédito
- **Carteras CMF:** Segmentación regulatoria en Comercial, Consumo y Vivienda

---

## Autor

**Krishna Bustos Santibáñez**  
Analista de Datos | Finanzas & Control de Gestión 
[LinkedIn](https://linkedin.com/in/krishnabustoss) · [GitHub](https://github.com/Iakrshn)
