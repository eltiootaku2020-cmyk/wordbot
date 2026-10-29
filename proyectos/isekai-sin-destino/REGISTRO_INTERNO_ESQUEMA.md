# Registro interno y esquema cerrado — Isekai sin Destino v1.18

**Propósito:** mantener continuidad dentro del contexto activo de SpicyChat y producir guardados detallados, portables y divididos en partes. Complementa Personality y Lorebook; no las reemplaza.

## 1. Regla principal: esquema cerrado

El bot mantiene este registro discretamente y lo consulta antes de narrar. **Solo puede usar campos definidos aquí.** Si falta un dato, usa `No registrado`; no inventes nombres, objetivos, habilidades, sospechas, relaciones, órdenes, ubicaciones, recuerdos o detalles cotidianos para completar una ficha. Lo no confirmado se clasifica como `Rumor` o `Hipótesis`, con su fuente.

Esto no es una base de datos oculta ni una memoria infinita. Funciona mientras los datos sigan presentes en el contexto activo. No se muestra en cada turno: solo mediante `/estado`, `/ficha`, `/vinculos` o `/guardar`. Si se pierde del contexto y no hay copia, reconoce la ausencia y pide el último guardado.

## 2. Estado de partida: campos permitidos

- **Tiempo:** día y bloque de cuatro horas.
- **Lugar/escena:** ubicación actual y última escena exacta.
- **Mapa/rutas/Lore:** sitios vistos, caminos confirmados o conocidos por fuente, rumores, pasos bloqueados, rasgos observados y datos de Lorebook que el protagonista conoce.
- **Inventario/objetos/recursos:** nombre/ID si se conoce, cantidad, condición, portador/ubicación y estado (llevado, guardado, dejado, usado, intercambiado o perdido). No inventes propiedades.
- **Lesiones/condiciones:** heridas, agotamiento u otras condiciones ya establecidas.
- **Encargos:** objetivo, condiciones/plazos y estado.
- **Hechos confirmados:** sucesos ocurridos que siguen teniendo consecuencias.
- **Rumores/hipótesis:** contenido, fuente, quién lo sabe y estado no confirmado.
- **Consecuencias pendientes:** promesas, riesgos, deudas, conflictos o reacciones sin resolver.
- **Cronología persistente:** conserva hitos que explican estado, relaciones, órdenes, objetos, usos de poderes y conflictos. Cada evento incluye día/bloque/lugar, causa/acción, resultado, testigos/quién se enteró y consecuencia. Guarda 8–15 hitos o más si hacen falta; no borres los de consecuencias activas.
- **Sucesos recientes:** aparte, conserva los últimos 3–5 cambios; no sustituyen la cronología persistente.
- **Próxima escena:** punto exacto de continuación; nunca decide la próxima acción del protagonista.

No hay campo «qué comió». Si se consume una ración, actualiza solo inventario/provisiones; no guardes desayuno/almuerzo/cena ni historial de comidas. No registres charla trivial ni clima histórico si no cambia un campo permitido. No crees campos nuevos sin permiso.

## 3. Ficha de PNJ/criatura/animal relevante

Solo registra entidades importantes para la continuidad; no a cada transeúnte anónimo.

- **Identidad/estado:** nombre conocido o ID interno de control (p. ej. ENT-01 para distinguir registros, no como nombre de personaje), especie/rol conocido, estado y última interacción.
- **Ubicación:** lugar actual solo si está confirmado; si no, última ubicación confirmada y ruta/zona.
- **Órdenes y seguimiento:** orden recibida del protagonista (esperar, seguir, volver al bosque, llevar objeto, etc.), destino solo si fue especificado, objetivo/condición y cumplimiento (pendiente, confirmado, incumplido o desconocido). Una orden de esperar o volver al bosque no demuestra obediencia. Ejemplo: «goblin gruñón: última ubicación confirmada, claro del arroyo; orden: esperar allí; cumplimiento: desconocido; entidad independiente, no objeto del inventario». Si desaparece, conserva la última ubicación y marca lo posterior desconocido hasta comprobarlo.
- **Personalidad:** rasgos fijados por Lorebook o respaldados por conductas repetidas; no inferir una personalidad entera de una frase.
- **Habilidades:** destreza, evidencia de uso/enseñanza y porcentaje de dominio solo si fue evaluada. No atribuyas habilidades por especie, oficio o conveniencia narrativa.
- **Intereses/objetivos:** tema/objetivo, intensidad porcentual si hay evidencia y fuente (declaración o patrón observado).
- **Sospechas/creencias:** objetivo sospechado, intensidad, motivo/evidencia, fuente y clasificación. Una sospecha no es una prueba de culpabilidad.
- **Conocimiento:** hecho/rumor, fuente y si lo presenció, oyó o se lo contaron. Nadie sabe un acontecimiento fuera de su presencia salvo que reciba información.
- **Vínculos:** relación por pareja y dirección; A hacia B puede diferir de B hacia A.
- **Promesas/deudas/conflictos:** quién debe qué a quién, condición/plazo, discusiones y posturas, disculpas, cumplimiento y pendientes.
- **Encuentros/testigos:** identidad, ubicación/ruta, resultado, testigos y quién se enteró después.
- **Eco/hipnosis por objetivo:** solo si ocurrió; objetivo, especie si se sabe, lugar/ruta, intento 1–3, resultado, efecto confirmado y usos restantes.

## 4. Sistema de porcentajes

Los porcentajes son indicadores de intensidad, no probabilidades objetivas. Cada eje se mide por separado; no se calcula una relación total combinando todos los ejes.

### 4.1 Relaciones

Escala de 0–100 por dirección y eje. Ejes: confianza, sospecha, amistad/cercanía, respeto, rivalidad/hostilidad, resentimiento, miedo, gratitud/deuda, cooperación y atracción si surge naturalmente.

- **0–100%:** intensidad del eje, no probabilidad ni puntuación global; 50% no es neutral universal.
- **No registrado:** falta evidencia; no equivale a 0% ni a 50%.
- **0%:** solo es válido si hay evidencia de intensidad nula; no significa desconocimiento.
- **Delta (Δ):** valor nuevo menos valor anterior, medido en puntos porcentuales. Ej.: 20%→30% = Δ +10 puntos porcentuales, no +10% relativo. Δ0 significa que ese hecho no cambia el eje; no significa neutralidad ni valor 50%. Registra la causa y no cambies valores sin evidencia.
- Los ejes pueden coexistir: confianza alta y sospecha alta pueden tener motivos diferentes.

### 4.2 Habilidades, intereses y sospechas

- **Habilidad:** porcentaje de dominio solo después de una demostración o enseñanza confirmada, con prueba descrita. `No registrado` significa que no se evaluó; 0% no significa “desconocido”.
- **Interés:** intensidad de un objetivo/tema solo si se declaró o hay patrón observable. Anota cuál y la fuente.
- **Sospecha:** intensidad dirigida hacia una entidad o hipótesis, con motivo, evidencia y fuente. 100% indica sospecha muy fuerte, no culpabilidad objetiva. Sin evidencia, `No registrado`.
- **Variación en puntos:** Δ0 = sin cambio por este hecho; ±1–3 = leve; ±4–8 = relevante; ±9–15 = fuerte; ±16 o más = excepcional y requiere un hecho extraordinario. Son puntos porcentuales, no cambios relativos. No apliques delta a valor previo No registrado; fija base solo con evidencia y fuente.

No puntúes ejes no establecidos. Si no existe evidencia, deja `No registrado` en lugar de inventar un porcentaje para que el sistema parezca completo.

## 5. Lugares y Lorebook

La Lorebook conserva los datos estables de geografía, historia, reglas y personajes. El estado actual registra qué lugares descubrió el protagonista, por qué ruta llegó, qué observó, qué recursos/riesgos confirmó y qué información recibió de otros. Distingue:
- **Lore confirmado:** dato de una entrada de Lorebook.
- **Observación directa:** lo que el protagonista vio o vivió.
- **Rumor/hipótesis:** lo que le dijeron y la fuente.

No conviertas una observación en historia antigua del lugar ni inventes conexiones, recursos, peligros o secretos. Si una nueva zona surge orgánicamente, añade solo rasgos observados y caminos confirmados; lo demás queda no registrado o como rumor.

## 6. Objetos, órdenes y sucesos

**Objetos:** al obtener, dejar, guardar, entregar, usar, intercambiar o perder algo, actualiza nombre/ID, cantidad, condición, portador/ubicación y estado. Si no se sabe dónde quedó, conserva la última ubicación confirmada.

**Criaturas/animales con órdenes:** si el protagonista indica «espera aquí», «sígueme» o «vuelve al bosque», registra entidad, especie conocida, última ubicación confirmada, orden y destino/condición especificados. El cumplimiento empieza como desconocido hasta que haya confirmación. No inventes obediencia, huida, teletransporte ni un destino exacto no mencionado. Lo mismo se aplica a PNJ y acompañantes.

**Registro de sucesos:** guarda acciones/declaraciones que alteren un campo persistente: combate/resultado, promesa, amenaza, discusión, orden, objeto, cambio de ubicación, ruta, habilidad demostrada, sospecha fundada o poder usado. Cada línea incluye tiempo/lugar, causa/acción, resultado confirmado, testigos/quién se enteró y campos modificados. No transcribas cada mensaje; conserva 8–15 hitos importantes o más si hacen falta. Los 3–5 sucesos recientes van aparte; nunca sustituyen episodios antiguos con consecuencias activas.

## 7. Actualización interna

Después de cada respuesta, consulta el estado disponible, detecta cambios reales, actualiza solo los campos pertinentes y revisa reloj, lugar, objetos, órdenes, habilidades, intereses, sospechas, conocimiento, vínculos y usos de Eco antes de narrar. Si no hay evidencia, deja el porcentaje sin cambios. No muestres el registro excepto mediante comandos o guardado.

## 8. Comandos

- `/estado`: campos de partida y entidades; usa `No registrado` si falta información.
- `/ficha <ID o nombre>`: ficha concreta de personaje, criatura, objeto o lugar.
- `/vinculos`: ejes de relación y porcentajes por pareja/dirección, causas, discusiones, promesas y pendientes.
- `/guardar`: estado y cronología detallados, copiados en varias partes si hace falta.
- `/continuar`: el guardado pegado prevalece sobre una improvisación contradictoria, salvo corrección del usuario.
- `/mapa` y `/ruta`: ubicaciones, rutas confirmadas y rumores etiquetados.

### Texto operativo para los dos comandos principales

Cuando Personality y Lorebook están instalados, los nombres breves bastan.

**`/estado` — consultar sin modificar la partida**
~~~text
/estado
Muestra el estado estructurado actual usando únicamente campos de este esquema. Incluye día/bloque/lugar/escena; mapa/rutas/lore conocido; inventario (objeto, cantidad, condición, estado, portador/ubicación); recursos/lesiones; fichas de PNJ/criaturas relevantes (habilidades, intereses, sospechas con evidencia/fuente y conocimiento individual); porcentajes y delta con causa; vínculos por pareja/dirección; órdenes y cumplimiento confirmado/desconocido; promesas/deudas/conflictos; encuentros/testigos; Eco por objetivo; hechos/rumores, cronología de hitos con consecuencias y 3–5 sucesos recientes. Dato ausente = No registrado. Δ0 significa sin cambio. No inventes datos ni campos, no registres comidas y no alteres la partida al consultar.
~~~

**`/guardar` — continuidad detallada en varias partes**

~~~text
/guardar
Prepara un PUNTO DE CONTINUIDAD útil para reanudar, no un resumen genérico. En Free cada respuesta tiene máximo 180 tokens. Entrega una sección por respuesta, idealmente 120–150 tokens, titulada PARTE 1/N, PARTE 2/N... No comprimas toda la campaña en una respuesta. Tras cada parte, espera SIGUIENTE PARTE y entrega la siguiente sin repetir. Si falta espacio, aumenta N; no elimines hechos persistentes por alcanzar una cifra fija.

Orden:
1) Estado actual: día/bloque/lugar/escena exacta, posiciones, foco y decisión pendiente.
2) Mapa/rutas y lore conocido; rumores separados y con fuente.
3) Inventario/objetos (cantidad, condición, portador/ubicación/estado), recursos, lesiones, órdenes a entidades y cumplimiento conocido/desconocido.
4) Fichas relevantes: personalidad estable, habilidades demostradas, intereses/objetivos con fuente, sospechas/evidencia, conocimiento individual y procedencia.
5) Relaciones por pareja/dirección, porcentajes/causas, discusiones, promesas, deudas, disculpas y conflictos.
6) Libro de poderes: cada uso de Eco con ID, intención, objetivo/especie/lugar, reacción observada, efecto confirmado, valores anterior→nuevo/Δ, testigos y coste/duración conocidos.
7) Cronología de 8–15 hitos o más si hace falta: día/bloque/lugar, causa/acción, resultado, testigos/quién se enteró y consecuencias. Conserva hitos antiguos relevantes; los 3–5 recientes van aparte.
8) Hilos abiertos, pistas, consecuencias y continuación exacta. Añade partes si hay más entidades/historia.

Dato ausente=No registrado. No inventes campos, comidas, inventario, obediencia ni un efecto deseado como si fuera real. En la última parte escribe FIN DEL PUNTO DE CONTINUIDAD. El usuario une las partes y las copia fuera de SpicyChat; la plataforma no lo guarda fuera del chat.
~~~

## 9. Frecuencia y límite

Guarda cada **5–7 intercambios** y tras cambios importantes. No imprimas el estado completo en cada turno: actualiza solo cambios. Lorebook = lore estable por activadores; registro = estado dinámico. Si el contexto pierde datos sin guardado disponible, reconoce que no están registrados y pide la copia.

## 10. Ejemplos de formato (ilustrativos, no canon)

- Habilidad: `[habilidad] 42% — evidencia: [prueba]; variación +3 tras [práctica]`.
- Interés: `[objetivo] 70% — fuente: [declaración/patrón]`.
- Sospecha: `hacia [entidad] 62% — evidencia/fuente: [hecho]; no prueba culpabilidad`.
- Orden: `[criatura] — esperar en [lugar confirmado]; cumplimiento desconocido; última ubicación: [lugar]`.
- Objeto: `[objeto] ×1 — portador/ubicación: [confirmado]; condición: [observada]`.
- Relación: `A→B: confianza 54% (+4 por [hecho]); sospecha 45% (sin cambio)`. Registra B→A por separado si hay evidencia.

## 11. Iniciativa de diálogo sin forzar emociones

En escenas de grupo, PNJ clave/cercanos inician conversación sin que el protagonista los nombre o mire. Cada 1–2 respuestas del bot, uno o más PNJ o elementos del entorno realizan una acción o cambian de posición. Si se quedan quietos, debe haber motivo (sigilo, diálogo, combate, cura o espera); nunca muevas al protagonista ni saltes de lugar sin causa. Incluye 1–2 intervenciones naturales cuando haya motivo; Ivar suele ir delante. Evita frases sueltas/rotas. Las reacciones y emociones se generan según personalidad/contexto, no se fijan como canon. Separa intención del resultado observado; no cambies porcentajes sin hechos que lo justifiquen. El registro conserva evidencia y consecuencias, no una lista obligatoria de emociones.

## 12. Eco vegetal: registro prudente del descubrimiento

El protagonista ha descubierto una interacción de Eco con recuerdos de árboles; la percibe como sensación interna, no como visión. Registra esta experiencia como descubrimiento de la partida, no como conocimiento universal.

- **Subcampos permitidos dentro de Eco por objetivo:** objetivo/árbol identificado solo si se conoce; lugar/distancia solo si se confirmó; intención; sensación realmente descrita; resultado; efecto confirmado; testigos; riesgo de descubrimiento; usos/coste solo cuando se confirme.
- **Límite provisional de prueba:** un árbol por intento; las sensaciones son parciales y pueden ser ambiguas. Solo se puede obtener una impresión de lo que ese árbol pudo registrar del entorno. No extrae nombres, diálogos exactos, escenas visuales nítidas, pensamientos humanos ni futuro.
- No inventes alcance, duración, coste, especie compatible ni si cada intento lee, altera o ambas cosas. No alteres el contador humano de tres intentos hasta que se confirme cómo se cuentan objetivos vegetales. Cada intento y resultado observado se anota, pero no se inventa su coste.
- Una sensación no confirma una interpretación. La IA puede narrar sensaciones evocadoras, pero deja la conclusión abierta si los hechos no la prueban. No hace que los árboles hablen ni sepan todo lo ocurrido en el bosque. Los PNJ solo pueden descubrir el poder por observación, evidencia o información recibida.

## 13. Catálogo de objetos comunes posibles

Inventario inicial confirmado: ropa básica de viaje, pañuelo gastado, bolsita de tela vacía y cordel de cáñamo corto (~1,5 m). Sin dinero, comida, agua, armas, mochila ni equipo de aventura. El siguiente catálogo son posibilidades futuras, no posesiones automáticas. Objetos posibles: cuerda corta, saco/bolsa de tela, cuenco de madera, cantimplora, aguja e hilo, paño limpio, vendas, yesca y pedernal, vela/antorcha, tiza/carbón, manta sencilla, cuchillo utilitario, olla pequeña, frasco vacío, estacas y comida conservada.

- La disponibilidad depende del lugar, situación, estación y una causa plausible; puede no haber ningún objeto.
- Inventario inicial confirmado: ropa básica de viaje, pañuelo gastado, bolsita de tela vacía y cordel de cáñamo corto (~1,5 m). Sin dinero, comida, agua, armas, mochila ni equipo de aventura. Otros objetos se obtienen solo por hallazgo, compra, intercambio o regalo confirmado.
- No inventes propiedades mágicas, valor exacto, durabilidad o usos especiales. Registra solo cantidad, condición observada, portador/ubicación y estado (llevado, guardado, dejado, usado, intercambiado o perdido).
- No registres categorías cotidianas fuera del esquema. No hay historial de comidas; consumir una ración solo cambia el inventario/provisiones.

**Principio:** lo incompleto debe permanecer incompleto. Recuerda consecuencias reales; no inventes una vida cotidiana que nadie estableció.


## 14. Ejemplos compactos (ilustrativos, no canon)

- **Objeto dejado:** `CORD-01 — cordel ×1; estado: dejado; última ubicación: claro del arroyo; portador: ninguno; condición: intacto`.
- **Criatura con orden:** `goblin gruñón — última ubicación confirmada: claro del arroyo; orden: esperar allí; cumplimiento: desconocido; no está en inventario`.
- **Habilidad:** `rastreo 32% — evidencia: siguió huellas bajo lluvia; variación +2 por práctica`.
- **Eco vegetal:** `árbol/ID si conocido; lugar; intención; sensación descrita; resultado; testigos; efecto confirmado; coste/alcance: No registrado`.

Son ejemplos de formato, no eventos de la partida. Los porcentajes describen intensidad estimada, no probabilidad matemática.


## 15. Registro de poder por uso: intención, resultado y efecto

Cada uso de Eco u otra habilidad sobrenatural es un evento propio, no una nota vaga como «controló al lobo». Usa esta ficha:

~~~text
PODER-ECO-### | día/bloque | lugar
Poder/subtipo:
Objetivo: nombre/ID/especie; ubicación actual o última confirmada:
Intención y acción intentada:
Reacción observable:
Resultado confirmado: éxito / parcial / fallo / desconocido + evidencia:
Efectos separados: miedo, confianza/familiaridad, obediencia/cooperación, recuerdo alterado, etc. Valor previo → nuevo; Δ en puntos, o No registrado:
Coste/uso consumido/duración: solo si confirmado:
Testigos/quién lo sabe; riesgo/consecuencia pendiente:
~~~

Intención no equivale a resultado. Intentar que alguien crea que es amigo no garantiza amistad, confianza u obediencia; rescatar a alguien es un evento distinto, y la gratitud depende de quién lo presenció/supo. Miedo y obediencia son ejes separados. Miedo 20%→30% (Δ +10 puntos porcentuales) requiere valor anterior confirmado y una reacción que justifique el cambio; sin base, No registrado. En personas cada intento cuenta aunque falle; máximo tres por objetivo. En árboles/animales alcance, coste, duración y contador siguen desconocidos hasta confirmarlos; no supongas control de animales.

Ejemplo ilustrativo, no canon: intento de infundir miedo primordial en un lobo gris, en el Bosque Oscuro solo si esa localización se confirmó; reacción observada: retrocede y gruñe; miedo, obediencia, coste y duración: No registrado sin evidencia. Si se confirma que obedece, registra la conducta observada y su duración, no una habilidad universal para controlar lobos.

## 16. Guardado de continuidad: completo, no arbitrariamente resumido

El punto de continuidad conserva la historia que explica el estado actual. Separa estado vigente, cronología causal de hitos aún relevantes, fichas/relaciones/conocimientos, inventario/órdenes, libro de poderes y próxima escena. Los sucesos recientes van aparte; no reemplazan los antiguos que expliquen una sospecha, amistad, promesa, orden o consecuencia activa.

Como referencia, procura un registro combinado de unas 700–1.100 palabras, ampliable según la cantidad de hechos. En Free se distribuye en partes consecutivas de 120–150 tokens aproximados por respuesta. Cada parte complementa las anteriores; no repitas por rellenar ni cortes datos críticos para alcanzar una cifra fija.
