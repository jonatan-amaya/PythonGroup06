# Assignment 3 – Grupo 6

## Parte 3 · Dashboard: ¿el Estado declara emergencia donde más llueve?

**App pública: https://pythongroup06-assignment3.streamlit.app**

Dashboard interactivo en Streamlit que compara, para los 25 departamentos del Perú (24 + Callao), las **declaratorias de emergencia por lluvias** con la **lluvia registrada en su capital** durante la temporada de lluvias del **1 de enero al 31 de mayo de 2023**.

La app permite:

- **Filtrar** en la barra lateral por departamento, por rango de lluvia total y mostrar solo los departamentos con al menos una declaratoria; además, elegir la variable de lluvia (lluvia total en mm o días de lluvia fuerte ≥ 20 mm).
- Ver **métricas** que cambian con el filtro: número de departamentos, declaratorias y prórrogas, y la lluvia promedio comparada con el promedio nacional.
- Explorar **gráficos interactivos de Plotly**: declaratorias por departamento (coloreadas según la lluvia), dispersión lluvia vs. declaratorias con su correlación de Spearman, y un **mapa** de las capitales departamentales.
- Consultar y **descargar la tabla** de datos filtrada.

Con todos los departamentos, la correlación entre lluvia total y declaratorias es ligeramente negativa (−0,19): Lima encabeza las declaratorias (7) con apenas 27,9 mm, mientras que Loreto, el más lluvioso (1604,6 mm), tiene una sola.

## Datos

`datos/dataset.csv` es la tabla final construida en el Assignment 2 (`assignment_2/datos/tabla_final.csv`), con una fila por departamento:

| Columna | Descripción | Fuente |
|---|---|---|
| `ubigeo` | Código INEI del departamento (texto de 2 dígitos) | INEI |
| `departamento`, `capital`, `latitud`, `longitud` | Departamento y coordenadas de su capital | Wikipedia + API de geocodificación de Open-Meteo |
| `lluvia_total_mm`, `dias_lluvia_fuerte` | Lluvia acumulada y días con ≥ 20 mm en la capital, ene–may 2023 | [Open-Meteo](https://open-meteo.com/) (API histórica) |
| `declaratorias`, `prorrogas` | Decretos supremos de emergencia por lluvias (y sus prórrogas) que mencionan al departamento | Decretos de la PCM publicados en [gob.pe](https://www.gob.pe/pcm) |

Un mismo decreto puede abarcar varios departamentos, así que la suma de declaratorias cuenta un decreto una vez por cada departamento que menciona. La lluvia se mide en un solo punto (la capital), no en todo el departamento.

## Archivos

- `app.py` – la aplicación Streamlit (adaptada de la plantilla de la sesión 8).
- `requirements.txt` – dependencias para Streamlit Community Cloud.
- `datos/dataset.csv` – datos de la app.
- `visualizacion.ipynb`, `grafico.html` – Parte 1 (gráficos con Plotly).

## Correr en local

Desde la carpeta `assignment_3/`:

```bash
uv run streamlit run app.py
```

Si el entorno no tiene Streamlit instalado:

```bash
uv run --with-requirements requirements.txt streamlit run app.py
```

## Despliegue

En [share.streamlit.io](https://share.streamlit.io) → *Create app* → repositorio `jonatan-amaya/PythonGroup06`, rama `main`, archivo principal `assignment_3/app.py`.
