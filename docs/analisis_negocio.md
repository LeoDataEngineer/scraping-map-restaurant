# Análisis de negocio a partir de los datos de Google Maps (Apify)

Restaurantes analizados: **FRANCELINA FOOD** (Porlamar) y **Pizzería Portarossa** (Pampatar).  
Fuente: 2 archivos raw de `data/raw/` con las **2.000 reseñas más recientes** de cada restaurante + agregados históricos del perfil de Google.  
Salida: 6 tablas en `data/processed/` (`restaurants`, `reviews`, `monthly_trend`, `themes`, `occupancy`, `competitors`).

> **Cómo leer las cifras.** "Histórico" es lo que reporta el perfil de Google (`totalScore`, `reviewsCount`, distribución completa por estrellas). "Muestra" es el corte de 2.000 reseñas más recientes que descargó Apify; el dashboard lo rotula como *rating reciente*. La muestra **no** es el historial completo, pero ya cubre varios años: 2023-04 → 2026-11 en Francelina y 2017-09 → 2026-11 en Portarossa.

---

## 1. Resumen ejecutivo

- Ambos restaurantes tienen un desempeño **muy bueno y estable**: 4.5–4.6 histórico y 4.55–4.56 en la muestra. La diferencia entre ambos es de una centésima: **no hay un ganador claro en satisfacción**.
- El **NPS proxy** (4–5★ menos 1–2★) es idéntico: **~85 puntos** en los dos, tanto histórico como en la muestra. La insatisfacción duradera es baja (1–2★ ≈ 5%).
- El **talento comercial de Portarossa está en el producto y no en el perfil**: 4.6 histórico con 2.056 reseñas y una pizza que promedia 4.39★ en 442 menciones, pero su perfil de Google está al **81.8%** (le faltan web y menú).
- **El precio es el punto débil compartido**: es el único tema con rating promedio por debajo de 4.0 en ambos restaurantes (3.94 en Francelina, 3.89 en Portarossa) y el de mayor porcentaje de reseñas negativas (14.4% y 17.6%).
- La **respuesta del dueño es el hallazgo más accionable**: en la muestra agregada solo se responde el **29.4% (Francelina)** y el **16.8% (Portarossa)**, y a las reseñas de 1–2★ apenas el **17.2%** y **13.9%**. Pero el dato tiene una lectura positiva: **ambos empezaron a responder en 2025** y en los últimos meses de 2026 están en 90–100%. El problema no es la capacidad, es la **cobertura histórica sin respuesta** y las caídas puntuales.
- **Francelina tiene un perfil perfecto (100%) y Portarossa no (81.8%)**; a la inversa, Francelina tiene menos texto por reseña (46.3% vs 62.1%) y más "promotores silenciosos" (54.1% de sus 5★ sin texto vs 38.0% en Portarossa).
- La **capacidad ociosa está en las mañanas de ambos**: Francelina opera al 41.2% de ocupación media con valle a las 6–10, 22 y 23 h; Portarossa al 29.2% con valle 6–11 y 23 h.
- El mayor límite analítico sigue siendo el sesgo del texto: quien escribe no es una muestra neutral (los insatisfechos escriben más). Además, el **rating detallado** (comida/servicio/ambiente) solo viene en el 74.3% de las reseñas de Francelina y en el **36.0%** de Portarossa, así que úsalo como referencia, no como verdad absoluta.

---

## 2. Qué datos tienes (activos analíticos)

### A nivel de restaurante — `restaurants.csv` (1 fila × 84 columnas por restaurante)
- Identidad y perfil: nombre, `place_id`, categoría, dirección, ciudad, web, teléfono, rango de precio, `raw_file`, `generated_at`.
- Histórico de Google: `totalScore`, `reviewsCount`, distribución completa por estrellas y NPS proxy histórico.
- Muestra: rating, distribución, velocidad (`reviews_per_day`, `reviews_per_month`), periodo cubierto, idioma, fotos, Local Guides, rating detallado.
- Respuesta del dueño: cobertura global, a 1–2★, a 1–3★, genéricas, repetidas, con nombre y largo medio.
- Salud del perfil: `profile_score`, campos presentes/ausentes, atributos e imágenes.
- Resumen de ocupación: hora pico, día más ocupado, horas valle y ocupación media.

### A nivel de reseña — `reviews.csv` (1 fila por reseña, 24 columnas)
- Estrellas, texto, fecha, `year_month`, idioma, likes, fotos, `is_local_guide`, reseñas previas del autor.
- `sentiment` (proxy determinista por estrellas: 4–5★ positivo, 3★ neutro, 1–2★ negativo).
- `topics` y `products` detectados por regex (separados por `;`).
- Respuesta del dueño (`owner_replied`, `owner_reply_text`).
- `food_rating`, `service_rating`, `ambience_rating`.

### Tablas derivadas
- `monthly_trend.csv`: evolución mensual por restaurante (rating, volumen, % 1–3★, texto, respuesta, fotos).
- `themes.csv`: temas, productos y etiquetas de Google en formato largo con `dimension`, `label`, `mentions`, rating, gap vs. media y verbatim de ejemplo.
- `occupancy.csv`: ocupación estimada (popular times) por día y hora.
- `competitors.csv`: benchmark de reseñas y rating de competidores.

### Lo que **no** tienes todavía
- Fechas de respuesta del dueño → no se puede medir tiempo de respuesta.
- `visitedIn` vacío → no se sabe si la visita fue desayuno/almuerzo/cena.
- Ventas, ticket promedio, margen por plato, reservas, delivery → sin esto no se puede cuantificar el impacto en ingresos.
- Historial completo de reseñas (la muestra son las 2.000 más recientes).

---

## 3. Snapshot comparativo

| Métrica | Francelina Food | Pizzería Portarossa |
|---|---:|---:|
| Rating histórico | 4.5 | **4.6** |
| Rating de la muestra (n=2.000) | 4.55 | 4.56 |
| Volumen histórico | 2,381 reseñas | 2,056 reseñas |
| Periodo de la muestra | abr 2023 → nov 2026 | sep 2017 → nov 2026 |
| Velocidad en la muestra | **1.52/día (~45.7/mes)** | 0.60/día (~18.0/mes) |
| 5★ históricas | 72.6% | 73.8% |
| 4★ históricas | 17.1% | 15.9% |
| 3★ históricas | 5.7% | 5.2% |
| 1–2★ históricas | **4.6%** | 5.1% |
| NPS proxy histórico | 85.1 | 84.6 |
| NPS proxy de la muestra | 84.9 | 84.8 |
| Reseñas con texto | 46.3% | **62.1%** |
| 5★ sin texto | 54.1% | **38.0%** |
| Reseñas con foto | 10.2% | **13.7%** |
| Local Guides | **67.5%** | 62.8% |
| Rating detallado disponible | **74.3%** | 36.0% |
| Comida / Servicio / Ambiente | 4.57 / 4.49 / 4.73 | **4.64 / 4.68 / 4.78** |
| Respuesta del dueño (muestra) | **29.4%** | 16.8% |
| Respuesta a 1–2★ | **17.2%** | 13.9% |
| Respuesta a 1–3★ | **24.3%** | 15.8% |
| Respuestas genéricas | 46.7% | 46.4% |
| Respuestas con texto exacto repetido | 25.0% | **18.2%** |
| Respuesta menciona el nombre | 61.1% | **67.0%** |
| Largo medio de respuesta | 82 caracteres | **99 caracteres** |
| Español / Inglés / Otro | 97.2 / 1.5 / 1.4 | 95.7 / 2.5 / 1.8 |
| Score del perfil de Google | **100.0%** | 81.8% |
| Campos faltantes | — | web, menú |
| Hora pico | 18:00 (85.3%) | 20:00 (75.0%) |
| Día más ocupado | Sábado (49.1%) | Viernes (37.7%) |
| Ocupación media | 41.2% | 29.2% |
| Horas valle (<25%) | 6–10, 22, 23 | 6–11, 23 |

Lectura: **Francelina tiene más tráfico y mejor perfil; Portarossa tiene mejor producto percibido y más texto por reseña**. Son dos negocios distintos con el mismo techo de satisfacción (≈4.6) y el mismo talón de Aquiles (precio).

---

## 4. Hallazgos clave y valor para el negocio

### 4.1 El precio es el riesgo compartido (y el más rentable de atacar)
- **Francelina:** 118 menciones de precio (12.8% de las reseñas con texto), rating **3.94** y **14.4% negativas**. Es el único tema con gap relevante: **−0.61★ vs. la media**.
- **Portarossa:** 165 menciones (13.3%), rating **3.89** y **17.6% negativas**, gap **−0.67★**. Es su peor tema por amplio margen.
- Valor: revisar **menu engineering**, claridad de la carta y relación porción/precio. Recuperar 0.3–0.5★ en el segmento que castiga el valor mueve la aguja más que cualquier campaña, porque afecta a ~13% de las conversaciones y a la decisión de compra de todos.

### 4.2 La respuesta del dueño: buena en el presente, invisible en el pasado
- En la muestra completa solo se responde el **29.4% / 16.8%**, y a 1–2★ el **17.2% / 13.9%**. Ese número asusta, pero se explica por la historia: **antes de 2025 no hay respuestas registradas** en ninguno de los dos.
- Desde 2025 la operación cambió: Francelina respondió el **90.9%** en 2025 y el **53.4%** en 2026; Portarossa el **83.6%** y el **59.7%**. En los últimos meses de 2026 (jul–nov) los meses buenos están en **86–100%**.
- El problema real, entonces, no es "no responder" sino **consistencia**: hay meses que caen a 0–50%. Y entre lo que sí se responde, **~47% son plantillas genéricas** y **25.0% / 18.2% repiten texto exacto**.
- Valor: convertir la respuesta en un **SLA semanal** (100% de 1–2★ en <48 h) y sustituir plantillas por respuestas con nombre y detalle. Barato, rápido y con impacto directo en la percepción.

### 4.3 Francelina: perfil perfecto, conversación incompleta
- Perfil de Google al **100%** (precio, web, menú, horarios, atributos, reservas, pagos): un activo que Portarossa no tiene.
- Pero solo el **46.3%** de sus reseñas traen texto y el **54.1%** de sus 5★ son "silenciosas". El **67.5%** de sus reseñas vienen de **Local Guides**, una audiencia de alto alcance que está dejando poca señal escrita.
- Valor: no necesita más perfil, necesita **más contenido de cliente**. Pedir reseña con texto/foto en el momento de la experiencia (QR, follow-up) genera señal para el algoritmo y materia prima para el análisis.

### 4.4 Portarossa: el producto es mejor que su escaparate
- 4.6 histórico y las mejores notas de subrating (comida 4.64, servicio 4.68, ambiente 4.78), con pizza como producto bandera: **442 menciones, rating 4.39**.
- Margarita funciona como imán (**81 menciones, 4.74★, solo 2.5% negativas**) y las etiquetas de Google ya destacan "margarita", "pistacho", "carpaccio", "certificado" y "salón".
- Pero el perfil está al **81.8%**: **faltan web y menú**. La certificación Vera Pizza Napoletana aparece en la descripción, no en los campos que convierten.
- Valor: completar web + menú y usar la certificación como propuesta de valor visible. Es la acción de menor esfuerzo con mayor impacto en conversión desde Maps.

### 4.5 Francelina: heladería y café son volumen; pasta y pizza son riesgo
- Productos más mencionados: **helados** (139, 4.46★), **postres** (102, 4.34★) y **café** (69, 4.42★).
- Los puntos flojos dentro del menú: **pasta** (37 menciones, 4.19★, 8.1% negativas) y **pizza** (32 menciones, 4.00★, 9.4% negativas). Son los dos productos con rating más bajo entre los relevantes.
- Valor: la heladería/café sostiene el tráfico y el ticket; la pasta/pizza necesitan una revisión de receta, porción o expectativa. Es una decisión de menú, no de marketing.

### 4.6 Portarossa: reserva y logística son los roces operativos
- **Reserva**: 28 menciones con rating **4.04** y **14.3% negativas**. **Logística y ubicación**: gap **−0.39★** con 16.7% negativas.
- El resto de productos está sano (pizza 4.39, margarita 4.74, postres 4.51, cócteles 4.45).
- Valor: revisar el proceso de reservas (confirmación, puntualidad, mesa asignada) y la información de acceso/estacionamiento. Son dolores concretos, de bajo costo y alta Visibilidad en la reseña.

### 4.7 Capacidad ociosa: las mañanas son la oportunidad común
- **Francelina:** ocupación media 41.2%, pico 18:00 al **85.3%**, sábado el día más cargado (49.1%). Valle: **6–10, 22 y 23 h**.
- **Portarossa:** ocupación media 29.2%, pico 20:00 al **75.0%**, viernes el más cargado (37.7%). Valle: **6–11 y 23 h**.
- Valor: una campaña de **desayuno/café/brunch (7–11 h)** llena capacidad sin canibalizar la cena, sobre todo en Portarossa, que tiene 12 puntos menos de ocupación media. Medir con ocupación y reseñas por franja.

### 4.8 Promotores silenciosos y sesgo del texto
- Francelina: **54.1%** de las 5★ sin texto; Portarossa: **38.0%**.
- Consecuencia: el texto disponible sobrerrepresenta a detractores y a clientes muy involucrados. Los temas negativos pesan más de lo que pesan en la experiencia real.
- Valor: leer `themes.csv` como **dirección**, no como porcentaje exacto de la clientela; y usar `mentions` para priorizar, no para extrapolar.

### 4.9 Competencia
- **Francelina** compite con **Trattoria La Romana (4.4, 409 reseñas)**, **Gaia Ristorante (4.5, 792)** y tiene una marca hermana premium, **ATTIMO by Francelina (4.8, 84)**. Su rating histórico (4.5) está en línea con el mercado, no por encima.
- **Portarossa** compite con **Pida Pizza Playa El Angel (4.3, 1.076 reseñas)**, **Restaurant Pola (4.5, 604)** y **Papaya By Pola (4.4, 145)**. Su 4.6 es el mejor rating del grupo, con menos volumen que el líder.
- Valor: benchmark mensual de rating y temas; usar ATTIMO como laboratorio/premium y evitar canibalización. `competitors.csv` trae algunos registros con 0 reseñas: filtrarlos antes de graficar.

### 4.10 Idioma: mercado local con margen turístico
- La conversación es casi toda en español (**97.2% / 95.7%**). El inglés es marginal (**1.5% / 2.5%**) y otros idiomas ~1.4–1.8%.
- Portarossa ya tiene etiquetas de Google como "isla" y "gastronomía" y 15.1% de sus textos mencionan turismo; Francelina 10.3%.
- Valor: contenido bilingüe selectivo (menú, reseñas destacadas, respuestas a turistas) en lugar de traducir todo.

---

## 5. Cómo está armado el análisis (6 tablas, 100% determinista)

| Tabla | Grano | Para qué sirve |
|---|---|---|
| `restaurants.csv` | 1 fila por restaurante | Todos los KPIs de negocio (84 columnas) |
| `reviews.csv` | 1 fila por reseña | Filtros, verbatims y agregados ad hoc |
| `monthly_trend.csv` | restaurante × mes | Evolución y estacionalidad |
| `themes.csv` | restaurante × dimensión × etiqueta | Temas, productos y etiquetas Google |
| `occupancy.csv` | restaurante × día × hora | Operación y franjas |
| `competitors.csv` | restaurante × competidor | Benchmark |

Todo se calcula con **pandas, reglas y expresiones regulares**. El sentimiento es un proxy por estrellas; los temas y productos son coincidencia de palabras clave. No hay IA ni modelos de lenguaje en ninguna etapa.

---

## 6. Ideas de análisis priorizadas

### Quick wins (con los datos actuales, 1–2 semanas)
1. **SLA de respuesta**: meta 100% de 1–2★ en <48 h y >90% global, medida mes a mes con `monthly_trend.pct_with_reply`.
2. **Auditoría de plantillas**: usar `themes.csv` + `reviews.csv` para listar las respuestas repetidas y reescribir las 10 más frecuentes con nombre + detalle.
3. **Matriz menú vs. rating**: priorizar con `themes.csv (dimension = Producto)`. En Francelina: pasta y pizza. En Portarossa: reserva.
4. **Completar perfil de Portarossa**: web y menú; después revisar fotos y atributos de servicio.
5. **Activar mañanas**: promoción 7–11 h y medición con `occupancy.csv` antes/después.
6. **Pedir reseñas con texto**: QR/follow-up post-visita, foco en Francelina (54.1% de 5★ sin texto).

### Medio plazo (requiere integrar más datos)
7. **Integración con POS/reservas**: ticket promedio, margen y ventas por franja/plato. Es donde está el ROI real.
8. **Alertas automáticas**: caída de rating mensual, pico de 1–2★, subida de un tema negativo, caída de `pct_with_reply`.
9. **Segmentación**: Local Guides, turistas, familias y parejas; rating y ticket por segmento.
10. **Benchmark competitivo continuo**: scraping mensual y comparación de rating/temas.
11. **Atribución de campañas**: efecto de promociones en volumen de reseñas, rating y ocupación.
12. **Análisis de respuesta por autor**: ¿responder a un detractor recupera su siguiente reseña?

### Avanzado
13. **Análisis causal de la respuesta del dueño**: comparar la evolución de quienes recibieron respuesta personalizada vs. plantilla.
14. **Predicción de riesgo de reseña negativa** por franja/producto/servicio.
15. **Modelo de expansión**: puntuar ubicaciones por demanda, competencia, turismo y rating esperado.
16. **Precio y elasticidad percibida**: cruzar menciones de precio, ticket y ventas para optimizar precios y porciones.

---

## 7. KPIs recomendados

**Satisfacción**
- Rating histórico y rating de la muestra (evitar llamarlo "últimos 90 días": la muestra son las 2.000 más recientes).
- NPS proxy: % 4–5★ − % 1–2★.
- % reseñas 1–3★ y evolución mensual.
- Subratings: Comida, Servicio, Ambiente (ojo con la cobertura: 74% vs 36%).

**Marca y demanda**
- Velocidad de reseñas (día/mes).
- % reseñas con texto y con foto.
- % Local Guides y "promotores silenciosos" (% 5★ sin texto).

**Operación y servicio**
- % de reseñas respondidas (global y últimos 12 meses).
- Cobertura de respuesta a 1–2★.
- % de respuestas personalizadas (con nombre y detalle).
- Tiempo de respuesta (cuando se capture la fecha).

**Producto y valor**
- Menciones y rating por producto/tema.
- % de menciones de precio y rating asociado.
- Temas negativos emergentes.

**Perfil y conversión**
- Completitud del perfil de Google.
- Rating y volumen vs. competidores.

---

## 8. Modelo de datos

Las 6 tablas de `data/processed/` son la capa de consumo. El modelo subyacente sigue siendo:

- `restaurants` (dimensión enriquecida): identidad + perfil + KPIs agregados.
- `reviews` (hecho): una fila por reseña, con temas/productos y respuesta.
- `monthly_trend` (agregado): restaurante × mes.
- `themes` (puente en formato largo): restaurante × dimensión × etiqueta.
- `occupancy` (hecho): restaurante × día × hora.
- `competitors` (dimensión): restaurante × competidor.
- `fact_sales` (futuro): fecha, franja, plato, unidades, ingresos, margen.

---

## 9. Plan de acción 30/60/90 días

**Primeros 30 días**
1. Completar el perfil de Google de Portarossa: **web y menú** (los dos campos faltantes).
2. Implantar el SLA de respuesta: 100% de 1–3★ en <48 h, con plantillas reescritas (nombre + detalle).
3. Revisar **precio/porciones** en ambos: es el tema con peor rating (3.94 / 3.89).
4. Ajustar dotación en hora pico: Francelina 16–20 h, Portarossa 18–22 h.
5. Lanzar campaña de desayuno/café 7–11 h, empezando por Portarossa (29.2% de ocupación media).

**60 días**
6. Revisar los productos flojos: **pasta y pizza en Francelina**; **reserva y logística en Portarossa**.
7. Pedir reseñas con texto/foto (QR + follow-up), priorizando Francelina.
8. Benchmark mensual de competidores y de ATTIMO.
9. Contenido bilingüe selectivo para turistas (menú, respuestas, reseñas destacadas).

**90 días**
10. Integrar POS/reservas para medir impacto en ventas y ticket.
11. Activar alertas automáticas sobre `monthly_trend` y `themes`.
12. Evaluar resultados: rating, NPS proxy, % quejas de precio, cobertura de respuesta, ocupación por franja y ventas.

---

## 10. Cómo mejorar la base de datos

- Mantener la extracción de **2.000 reseñas** por restaurante: ya permite series de 3+ años y reduce el sesgo frente a las 100 iniciales.
- Guardar **snapshots** (el pipeline ya acumula un raw por día y sobrescribe el mismo día): así se mide evolución real de rating, temas y competencia.
- Capturar **fecha de respuesta** del dueño (si Apify la expone en otro campo o vía otra fuente).
- Ampliar `competitors` para evitar registros con 0 reseñas.
- Integrar **POS/reservas/delivery** para cuantificar el impacto económico.
- Estandarizar el nombre del restaurante (slug) y el `review_id` como claves.

---

## 11. Conclusión

Los datos ya permiten decidir con evidencia: **precio/valor en ambos, consistencia en la respuesta del dueño, perfil incompleto en Portarossa, productos flojos en Francelina y mañanas ociosas en los dos**. El mayor salto de valor no viene de más gráficos, sino de **cruzar reseñas con ventas/reservas** y de **medir la evolución mes a mes** en lugar de mirar una foto fija.
