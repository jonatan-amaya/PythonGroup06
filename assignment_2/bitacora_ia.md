# Bitácora de IA – Assignment 2 (Grupo 6, temporada 2023)

**Cómo se elaboró esta bitácora.** Esta bitácora no se hizo con el historial de chat original del grupo. Para registrar los errores con respuestas reales, el 4 de octubre de 2026 se volvió a plantear a Claude las tareas de las Partes 1 y 2, con un enunciado equivalente al del trabajo y sin darle pistas. Su respuesta se copió tal cual, se probó contra los datos reales del repositorio y contra las APIs, y solo se registran los fallos que se comprobaron. El código que estaba bien no se registra como error. Por ejemplo, la identificación de departamentos con `re.search` y límites de palabra devolvió exactamente los mismos departamentos que `detalle_decreto_departamento.csv` en los 21 decretos.

---

## Caso 1 – Parte 1: las reglas de texto dejan fuera un decreto de lluvias (DS 036-2023-PCM)

**¿Qué le pedimos a la IA?**
Crear `es_lluvia`, `tipo` y `motivo` con el título en minúsculas y el operador `in`, y quedarse solo con las normas de lluvias.

**¿Qué respondió?**
```python
t = df["titulo"].str.lower()
df["es_lluvia"] = t.apply(lambda x: "lluvia" in x or "precipitaciones" in x)
...
df = df[df["es_lluvia"]].reset_index(drop=True)
```
Entregó el código como correcto y sin ninguna advertencia sobre revisar las normas excluidas.

**¿Qué estaba mal y cómo nos dimos cuenta?**
El código cumple la regla literal, pero la regla es incompleta. Al aplicarlo sobre `titulo_web` de `auditoria_normas_pcm.csv`, `es_lluvia` da 20 normas y el DS 036-2023-PCM queda como `False`. Su descripción web dice solo "Declaratoria de Estado de Emergencia", sin mencionar precipitaciones. Al abrir su PDF oficial se comprobó que declara emergencia por daños de precipitaciones en distritos de Lima. Además, `"declara" in texto` etiqueta como `declara` a las directivas 004 y 005 de 2015 por la palabra "declarados", aunque no son declaratorias.

**¿Cómo lo corregimos?**
Se revisaron a mano las normas que quedaron fuera. El DS 036 se incorporó con su título tomado del PDF, y la versión web se conservó en la auditoría. Las directivas quedan fuera con `es_lluvia=False`. Se guardó `decretos_solo_regla_web.csv` para comparar: la regla automática da 17 declaratorias y 3 prórrogas, y la versión revisada da 18 y 3.

---

## Caso 2 – Parte 2: la tabla de Wikipedia no trae Callao y deja texto extra en la capital de Lima

**¿Qué le pedimos a la IA?**
Leer con pandas la tabla de departamentos de Wikipedia y quedarse con `departamento` y `capital`.

**¿Qué respondió?**
Un código que descarga la página con `requests`, busca la tabla con columnas "departamento" y "capital" y limpia solo las notas `[1]`. Dejó este comentario en el código:
```python
print(f"\nFilas: {len(df)}")  # Esperado: ~25 (24 departamentos + Callao)
```
También avisó: "no lo ejecuté ni verifiqué la estructura actual de la tabla en Wikipedia".

**¿Qué estaba mal y cómo nos dimos cuenta?**
Se ejecutó su código contra la página real. La tabla devuelve **24 filas** y Callao no está, aunque el comentario del código daba a entender que sí. La capital de Lima viene como `Huacho (de facto)`, y el código solo quita notas entre corchetes, no paréntesis.

**¿Cómo lo corregimos?**
Se agregó Callao desde la tabla de provincias de régimen especial de la misma página de Wikipedia, con capital Callao. Se limpió el texto entre paréntesis con `.str.replace(r"\(.*?\)", "", regex=True)` y se usó Huacho. Se añadieron `assert len(departamentos) == 25` y la comprobación de departamentos únicos.

---

## Caso 3 – Parte 2: la geocodificación pierde a Lima y no verifica el departamento

**¿Qué le pedimos a la IA?**
Obtener latitud y longitud de cada capital con la API de geocodificación de Open-Meteo y calcular la lluvia total y los días con 20 mm o más por departamento.

**¿Qué respondió?**
```python
peru = [x for x in resultados if x.get("country_code") == pais]
pref = [x for x in peru if x.get("feature_code", "").startswith(("PPLA", "PPLC"))]
elegido = (pref or peru)[0]
...
for _, fila in deps.dropna(subset=["lat", "lon"]).iterrows():
    ...
    time.sleep(0.5)  # evitar límites de tasa de la API
```
Dijo que bastaba con revisar `deps[deps["lat"].isna()]`.

**¿Qué estaba mal y cómo nos dimos cuenta?**
Se ejecutó su lógica contra la API real, con las 25 capitales tal como salen de Wikipedia:
- Con `Huacho (de facto)` la API no devuelve ningún resultado. El código lo mandaría a `(None, None)` y el `dropna` quitaría a **Lima** de la tabla de lluvias, sin ningún error. Faltarían filas en silencio.
- Nunca compara `admin1` con el departamento esperado. Por tanto, no cumple la verificación pedida de que cada ciudad esté en su departamento, y un homónimo peruano pasaría sin aviso. Además, `admin1` viene escrito de formas distintas ("Departamento de Cusco", "Ancash" sin tilde).
- Espera 0.5 s entre pedidos, y el enunciado pide al menos 1 s.
- Usa `.sum()` y `>= 20` sin contar los días sin dato, y la verificación pedida es contar cuántos días llegaron en `None`.

**¿Cómo lo corregimos?**
Se limpió la capital antes de geocodificar y se usó 1.1 s de pausa. Se normalizó `admin1` (se quitan prefijos como "Departamento de" y "Provincia Constitucional del", y también las tildes, y se pasa a minúsculas) y se eligió el primer resultado peruano que coincide con el departamento. Una verificación final exige las 25 filas correctas. Se agregó el conteo de días `None` por departamento (resultó 0 en los 151 días de la temporada) y un `assert` de 25 filas antes de guardar.
