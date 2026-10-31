# 24 — Auditoría de coherencia temporal y escenarios de campaña (propuesta)

**Estado:** auditoría documental y de lectura de código; recomendaciones pendientes de aprobación.  
**Rama:** story/isekai-temporal-consistency-audit.  
**Base:** story/isekai-time-and-trio-prehistory (PR #39).  
**Alcance:** contrastar las duraciones de la PR #39 con las agendas de la PR #38, las reglas de viaje y el programador temporal existente; comprobar solapamientos, doble conteo, continuidad diaria y límites de implementación.

Esta entrega no modifica código ni convierte las duraciones propuestas en canon. El código se inspeccionó en la rama `feat/world-timeline-scheduler` correspondiente a la PR #21, que en el momento de la auditoría continúa abierta y sin integrar. Por tanto, los hallazgos de código describen esa rama, no garantizan el estado de `main`.

## 1. Resultado ejecutivo

**Conclusión:** la estructura general es compatible, pero todavía no es suficientemente precisa para implementar una simulación temporal completa.

No se encontró una contradicción matemática en los seis bloques horarios ni en la conversión de día a minutos. Sí se encontraron cinco problemas que deben resolverse antes de considerar fiable el reloj para una campaña larga:

1. El runtime actual puede avanzar un minuto por turno narrativo por defecto, aunque la propuesta dice que debe avanzar por acciones, no por mensajes.
2. Los rangos de acciones se solapan y no tienen una regla de clasificación que impida sumar dos veces una misma actividad.
3. El reloj ejecutable usa minutos enteros; el remanente de segundos de la PR #39 todavía no existe en el código.
4. El evento programado exige día y minuto exactos; no puede representar directamente una fecha cuya precisión aprobada sea solo «Día 12».
5. El programador recupera acontecimientos vencidos al cerrar un intervalo, pero no divide por sí solo una acción prolongada en el instante del acontecimiento ni simula las agendas autónomas durante el intervalo.

También falta una fórmula de duración de viajes. La especificación de viaje establece factores correctos, pero no ofrece distancias, velocidades ni unidades numéricas, por lo que no se pueden validar tiempos de ruta todavía.

## 2. Fuentes revisadas y alcance de la evidencia

### 2.1 Documentación narrativa

- PR #38 — `21_VIDA_INDEPENDIENTE_AGENDAS_Y_AUTONOMIA_DIAS_1_12_PROPUESTA.md`: agendas flexibles, resolución fuera de escena, bloques de cuatro horas, conocimiento separado, actividades posibles y registro de comienzo/fin.
- PR #39 — `22_SISTEMA_TEMPORAL_DURACION_DE_ACCIONES_Y_CONTINUIDAD_PROPUESTA.md`: reloj, rangos de acción, simultaneidad, interrupciones, remanente de segundos y requisitos de persistencia.
- Fundación de mundo vivo — `12_VIAJES_TRANSPORTE_Y_CARAVANAS.md`: viaje como actividad que consume tiempo, cálculo contextual, interrupciones y descanso, sin velocidad ni fórmula numérica aprobada.
- Modelo de variables — `02_MODELO_VARIABLES.json`: campos de día, bloque horario y hora exacta como propuesta de diseño.

### 2.2 Código consultado

Se inspeccionó la rama `feat/world-timeline-scheduler` de la PR #21:

- `proyecto/app/src/canon_manager/models.py`: `NarratorResponse.elapsed_minutes`, `WorldTimelineEventCreate`, `WorldTimelineEventUpdate`, `SessionCreate`.
- `proyecto/app/src/canon_manager/providers.py`: prompt del narrador y respuesta del proveedor de prueba.
- `proyecto/app/src/canon_manager/main.py`: autorización de saltos, avance del reloj, y llamada al programador de acontecimientos.
- `proyecto/app/src/canon_manager/timeline.py`: conversión de día/minuto y activación de acontecimientos vencidos.

Esta lectura no reemplaza una auditoría técnica de implementación ni una ejecución de pruebas. No se modificó ningún archivo de código.

## 3. Consistencia de la representación del día

Los bloques de las PR #38 y #39 coinciden exactamente:

| Bloque | Inicio | Fin |
|---|---:|---:|
| Madrugada | 00:00 | 03:59 |
| Amanecer | 04:00 | 07:59 |
| Mañana | 08:00 | 11:59 |
| Mediodía | 12:00 | 15:59 |
| Tarde | 16:00 | 19:59 |
| Noche | 20:00 | 23:59 |

Los seis bloques no se solapan ni dejan huecos. Cada uno abarca 240 minutos y los seis suman 1.440 minutos.

La conversión propuesta y la función del programador son equivalentes:

`total_minutes = (day - 1) * 1440 + minute_of_day`

La función valida días desde 1 y minutos entre 0 y 1.439. El modelo de sesión permite día y minuto del día, y usa 08:00 como valor inicial por defecto. Ese valor coincide con el punto de llegada provisional de Isekai, pero no convierte el clima ni la hora provisional del prólogo en canon nuevo.

**Resultado:** sin contradicción detectada en bloques y aritmética de días.

## 4. Hallazgo prioritario: el runtime aún puede medir por turno y no por acción

En el código consultado:

- `NarratorResponse.elapsed_minutes` permite de 0 a 10.080 minutos, pero su valor por defecto es 1.
- El prompt de sistema del narrador no proporciona una regla para decidir la duración de una acción ni indica cuándo devolver 0.
- El proveedor de prueba devuelve explícitamente `elapsed_minutes=1`.
- Al aplicar la respuesta, el motor acepta automáticamente un valor entre 0 y 15 minutos. Un valor mayor no avanza el reloj y agrega una nota de pendiente que explica que faltó autorización; esa nota no es por sí misma una operación de aprobación persistida. El salto explícitamente autorizado es la ruta que permite un avance mayor.
- El comando local `/salto` acepta saltos explícitos desde 1 minuto hasta 7 días.

**Riesgo:** el valor por defecto puede consumir un minuto en cada turno narrativo incluso cuando el turno solo continúa una conversación, responde una frase, confirma una decisión o no inicia una acción temporal nueva. El comportamiento exacto de cada proveedor depende de su respuesta, pero la ausencia de una política temporal explícita deja el resultado indeterminado.

**Esto contradice el principio de la PR #39:** el reloj debe avanzar por acciones realizadas y su duración, no por la cantidad de mensajes.

### Recomendación

Antes de implementar la autonomía del trío:

1. Definir en el contrato del narrador una duración explícita por acción o continuación de acción.
2. No utilizar silenciosamente un minuto por defecto para toda respuesta.
3. Representar explícitamente los turnos que no consumen tiempo.
4. Distinguir acción nueva, continuación de actividad en curso, respuesta conversacional y operación de interfaz.
5. Exigir que una duración superior a 15 minutos se justifique como actividad prolongada; no debería depender de una aprobación manual si es una acción normal y segura ya decidida por el usuario.
6. Mantener `/salto` como comando explícito de espera/avance, no como sustituto del cálculo normal de tareas.

No se propone eliminar las autorizaciones para cambios de mundo. Se propone separar la autorización de consecuencias de la estimación temporal de una acción ordinaria.

## 5. Auditoría de rangos: solapamientos y regla de clasificación

Los rangos de la PR #39 son razonables como primera calibración, pero se solapan. Esto no es un error si cada acción se clasifica una sola vez; sí lo sería si se suman todas las categorías que describen el mismo hecho.

| Categorías que se solapan | Riesgo | Regla recomendada |
|---|---|---|
| Mirada rápida 1–2 min / observación cuidadosa 2–5 min / examen 3–10 min | Cobrar tres veces una sola inspección | Seleccionar la categoría que describe la intención principal; sumar solo fases realmente distintas |
| Intercambio breve 1–3 min / conversación 5–20 min / negociación 15–60 min | Sumar conversación y negociación como si fueran actividades separadas | Una negociación contiene diálogo; se registra como una única actividad de negociación |
| Buscar en zona pequeña 5–15 min / registrar área amplia 15–60+ min / rastrear 10–30 min por tramo | Doble cobro por buscar y seguir la misma pista | Distinguir barrido de zona, lectura de pista y desplazamiento real; no repetir el mismo trabajo en dos categorías |
| Preparar comida 15–60 min / comer 10–30 min | Omitir una fase o duplicarla | Preparación y consumo son fases secuenciales diferentes; solo la preparación se cobra si la comida ya estaba lista |
| Pausa 10–30 min / descanso 30–120 min / sueño 6–9 h | Acumular tres etiquetas para el mismo descanso | Elegir el tipo de descanso; sueño prolongado reemplaza el descanso genérico durante ese intervalo |
| Tratar lesión menor / recuperación o descanso | Cobrar dos veces la misma inmovilidad | El tratamiento y la recuperación posterior son fases diferentes; una persona que asiste puede actuar mientras otra reposa |
| Combate / persecución / huida / atención posterior | Sumar cada descripción al mismo movimiento | Separar acercamiento, combate, persecución/retirada y cuidados posteriores solo cuando ocurran como fases reales |

### 5.1 Regla general para evitar el doble conteo

Cada intervalo de tiempo debe pertenecer a una actividad primaria por personaje. Una actividad compuesta puede tener varias fases, pero sus subfases no se agregan de nuevo como actividades independientes si describen el mismo tiempo.

Ejemplos:

- «Negociar durante 25 minutos» ya incluye escuchar, responder y discutir condiciones. No sumar otros 10 minutos por conversación sustantiva.
- «Examinar cuidadosamente un objeto durante 6 minutos» no recibe además 2 minutos de mirada rápida salvo que el personaje haya hecho primero una inspección independiente.
- «Seguir un rastro durante un tramo» incluye observar los rastros y avanzar siguiendo esa pista, según la definición que se apruebe. No sumar automáticamente el mismo desplazamiento como viaje aparte.
- «Preparar una comida y comerla» sí contiene dos fases diferentes; sus tiempos se suman para la persona que las realiza secuencialmente.

### 5.2 Definición pendiente para el rastreo

Antes de asignar valores numéricos definitivos, definir «tramo de rastreo» como una unidad operativa verificable: desde la inspección inicial hasta el siguiente punto donde se obtiene una pista nueva, se pierde el rastro, se decide cambiar de método o se abandona.

El desplazamiento independiente hacia la zona donde comienza el rastreo se contabiliza como viaje. El movimiento necesario para seguir la propia pista pertenece al tramo, para evitar contarlo dos veces.

## 6. Selección de una duración dentro de cada rango

La PR #39 define mínimos, máximos y factores, pero todavía no especifica cómo se elige un valor concreto. Sin esa regla, dos respuestas podrían asignar duraciones muy diferentes a una misma tarea y contexto.

**Regla de selección propuesta, pendiente de aprobación:**

- Parte baja del rango: tarea sencilla, conocida, preparada, segura y sin interrupciones.
- Zona media: condiciones ordinarias, complejidad esperada y herramientas adecuadas.
- Parte alta o por encima del rango: tarea compleja, terreno difícil, fatiga, poca visibilidad, herramientas inadecuadas, oposición o interrupciones.
- Las interrupciones reales se registran como fases propias; no se esconden dentro de un multiplicador arbitrario.
- Si la tarea no puede estimarse con la información disponible, se expresa un rango de incertidumbre en vez de inventar una hora exacta.
- Si se utiliza azar para elegir entre duraciones válidas, la semilla y el resultado deberán persistir para reproducir la partida.

No se proponen coeficientes numéricos porque faltan datos de velocidades, capacidades, terreno y fisiología.

## 7. Simultaneidad: cómo sumar sin duplicar el reloj

El principio de la PR #38 y #39 es compatible: una partida tiene un solo reloj global, pero cada personaje mantiene su propia actividad.

### 7.1 Actividades secuenciales

Para una misma persona, cuando una tarea comienza después de terminar la anterior, las duraciones se suman.

Ejemplo: 5 minutos para examinar una herida y después 20 minutos de tratamiento implican 25 minutos si ambas fases son realizadas secuencialmente por la misma persona.

### 7.2 Actividades completamente simultáneas

Si varias personas empiezan tareas independientes al mismo tiempo y ninguna depende de que termine otra, el intervalo global es el mayor tiempo de las tareas paralelas, no la suma de todos los tiempos.

Ejemplo: protagonista 10 min, Brina 15 min, Maelis 20 min y Sera 12 min; si las cuatro actividades pueden realizarse en paralelo durante el mismo intervalo, el reloj avanza 20 minutos.

### 7.3 Actividades parcialmente solapadas

Si una tarea comienza después de otra o termina antes, se conserva la línea temporal de cada actividad. El tiempo global transcurrido corresponde al intervalo real entre inicio y fin, no a la suma de horas-persona.

### 7.4 Restricción individual

Un personaje no puede hacer dos actividades físicas incompatibles a la vez. Caminar y conversar podrían ser compatibles; estudiar un documento con concentración mientras se combate no lo sería. La compatibilidad debe depender de la atención y las capacidades necesarias, no de una regla universal que permita combinar cualquier cosa.

### 7.5 Actividad compartida

Una conversación o negociación realizada por Brina, Maelis y Sera es una sola actividad con tres participantes. No se registra como tres conversaciones independientes ni se triplica su duración.

**Resultado:** no hay contradicción conceptual; falta un contrato técnico de intervalos concurrentes, compatibilidad por personaje y bloqueo de tareas incompatibles.

## 8. Escenario aritmético de una mañana

El siguiente ejemplo comprueba que las duraciones propuestas pueden convivir dentro de una jornada. No representa hechos del canon, una misión o un itinerario obligatorio.

### 8.1 Actividades secuenciales

| Inicio | Actividad | Duración | Fin |
|---|---|---:|---|
| 08:00 | Observación rápida | 2 min | 08:02 |
| 08:02 | Conversación sustantiva | 10 min | 08:12 |
| 08:12 | Examinar un objeto | 5 min | 08:17 |
| 08:17 | Buscar en una zona pequeña | 10 min | 08:27 |
| 08:27 | Preparar comida | 20 min | 08:47 |
| 08:47 | Comer una ración ya preparada | 15 min | 09:02 |
| 09:02 | Descanso breve | 30 min | 09:32 |

Tiempo secuencial: 92 minutos.

### 8.2 Actividades paralelas de los cuatro participantes

De 09:32 a 10:02:

| Participante | Actividad posible | Duración individual |
|---|---|---:|
| Protagonista | Examinar el entorno ya accesible | 20 min |
| Brina | Practicar una habilidad conocida, si tiene condiciones | 30 min |
| Maelis | Revisar observaciones o estudiar | 15 min |
| Sera | Inspeccionar un tramo de rastros disponible | 10 min |

Las ubicaciones, motivos, recursos y condiciones tendrían que ser compatibles. Si las tareas comienzan a las 09:32, el intervalo global es 30 minutos, no 75.

Reloj al final del bloque: 10:02.

### 8.3 Acción breve en segundos

Supóngase un combate de prueba de ocho intercambios a 10 segundos por intercambio:

- 8 × 10 s = 80 segundos.
- 80 segundos = 1 minuto y 20 segundos.
- El reloj pasa de 10:02:00 a 10:03:20.

Tiempo global desde las 08:00: 2 horas, 3 minutos y 20 segundos.

**Resultado:** los rangos secuenciales y paralelos no producen una contradicción matemática si se aplica una sola línea temporal global y no se duplica la duración de tareas anidadas.

## 9. Descanso, comida y recuperación

Los rangos pueden coexistir si se diferencian sus significados:

- Preparar una comida no incluye automáticamente consumirla.
- Comer una ración ya preparada no incluye cocinar.
- Un descanso breve no equivale a sueño prolongado.
- El sueño es un intervalo de descanso; no se suma además una pausa genérica por las mismas horas.
- La atención de una lesión no garantiza recuperación. El descanso posterior puede ser necesario y tener un intervalo distinto.
- Una persona que vigila mientras otra duerme puede actuar en paralelo, pero la persona de guardia no está descansando de la misma manera.
- La comida, la hidratación y el sueño pueden ocurrir en paralelo con tareas de otros personajes, pero una misma persona no debe recibir crédito por dos actividades que exigen atención completa al mismo tiempo.

**Pendiente:** no hay tasas cuantitativas de hambre, sed, fatiga, sueño, curación ni recuperación mágica en la documentación revisada. El reloj puede registrar cuánto tiempo pasó, pero no debe actualizar esas variables por valores arbitrarios.

## 10. Viajes: coherentes en principio, no calculables numéricamente todavía

El documento de viajes establece que la duración depende de distancia, terreno, clima, hora, visibilidad, estado de camino, carga, estado físico, método y eventos. También separa duración estimada de real.

No establece todavía:

- unidad de distancia del mapa;
- velocidades base a pie, corriendo, montado o en vehículo;
- modificaciones por camino, vegetación, desnivel, carga y cansancio;
- duración de pausas y orientación durante el trayecto;
- frecuencia o probabilidad de interrupciones;
- coste temporal de perder la ruta o buscar un desvío.

Por esta razón, no se puede verificar con rigor que un viaje concreto encaje en una jornada ni que las tres aventureras puedan recorrer una ruta antes de una hora concreta.

### Recomendación

Definir primero una unidad de distancia y velocidades base por medio de transporte, con modificaciones transparentes y límites plausibles. La duración final debe ser estimada por tramos de ruta; desvíos, combate, espera y descanso se suman solo cuando ocurren como intervalos separados.

No se deben rellenar las ausencias con una velocidad terrestre inventada.

## 11. Combate y precisión inferior al minuto

La propuesta de 5–15 segundos por intercambio funciona como rango de prueba, pero aún no está definida la estructura del intercambio: acciones simultáneas de varios combatientes, interrupciones, desplazamientos, pausas y acciones defensivas pueden formar parte del mismo intervalo.

**Regla propuesta:** el tiempo de un intercambio se cuenta una sola vez para el grupo que participa en ese momento. No se multiplica por número de combatientes, ataques, mensajes o párrafos. Acciones sucesivas dentro del mismo intercambio pueden ampliar el intervalo solo si efectivamente ocurren una después de otra.

El documento #39 propone acumular segundos sobrantes; sin embargo, la sesión y el programador consultados almacenan día y minuto, y `NarratorResponse` comunica `elapsed_minutes` como entero.

**Conclusión:** el remanente de segundos es una propuesta todavía no implementada en la rama técnica consultada. Debe añadirse mediante migración persistente antes de exigir que el sistema conserve precisión de segundos tras reinicios, snapshots o restauraciones.

## 12. Día 12: precisión de fecha incompatible con el esquema actual

La historia mantiene la erupción como acontecimiento ancla del Día 12, pero no tiene hora fijada.

En el código consultado:

- `WorldTimelineEventCreate.scheduled_minute` es obligatorio y acepta de 0 a 1.439.
- `WorldTimelineEventUpdate.scheduled_minute` también es un campo de minuto.
- El programador compara día y minuto y transforma ambos a minutos absolutos.

Por lo tanto, el sistema actual exige inventar un minuto para un acontecimiento que solo tiene precisión de día.

**Recomendación:** introducir una precisión declarada, por ejemplo `time_precision = "day" | "minute"`, y permitir minuto nulo solo en la precisión de día. La resolución diaria debe definirse expresamente: el sistema no debe sustituirla automáticamente por 00:00. Si la historia necesita un instante exacto para interrumpir una acción, el autor debe fijar una hora o aprobar una ventana/evento cuya incertidumbre tenga reglas propias.

No se modifica ahora el esquema porque requiere una migración técnica y una decisión de diseño.

## 13. Acontecimientos dentro de una acción prolongada

El programador consultado tiene dos propiedades positivas:

- detecta acontecimientos confirmados vencidos cuando el reloj alcanza o supera el momento programado;
- ordena los acontecimientos por día/minuto y evita la segunda activación dentro de una misma partida mediante una restricción única.

Sin embargo, el flujo inspeccionado actualiza la sesión al minuto final y después llama a `fire_due_world_events`. La función recupera acontecimientos vencidos en orden cronológico, pero no parte por sí sola una acción larga en subintervalos ni interrumpe una actividad en el instante exacto del acontecimiento.

Ejemplo: una tarea ocupa 08:00–08:30 y un suceso está programado para las 08:10. La recuperación al final detecta el suceso, pero no demuestra que la tarea se haya detenido a las 08:10 ni que sus efectos posteriores se hayan resuelto después del acontecimiento.

Además, la tabla de activación guarda `fired_total_minutes` igual al minuto programado, no el momento real en que se procesó una recuperación tardía. El comentario de código indica que se desea conservar la fecha mundial programada. Es una semántica útil, pero falta un campo independiente para la hora real de procesamiento cuando exista una recuperación atrasada.

### Recomendación

La futura resolución temporal debe dividir cada acción en:
1. inicio;
2. siguiente acontecimiento o interrupción relevante;
3. resolución de ese hecho;
4. actualización de condiciones y actividades afectadas;
5. continuación del tiempo restante, si la acción todavía puede continuar.

Guardar por separado:
- `scheduled_total_minutes`: cuándo debía ocurrir el hecho;
- `processed_total_minutes`: cuándo se detectó/aplicó en esa partida;
- `fired/activated`: registro de que ya se procesó.

La fecha programada no se altera por un retraso de procesamiento. La nueva marca no debe reemplazar la activación única ya existente.

## 14. Agendas autónomas: faltan reglas de intervalo y continuidad

La PR #38 define inicio y fin de actividad, ubicación, participantes, prerrequisitos, resultado, evidencia y visibilidad. Eso es una buena base, pero no basta todavía para demostrar que las actividades autónomas caben en el tiempo.

Antes de implementar se necesitan:
- intervalos con inicio y fin absolutos comparables con el reloj de sesión;
- estado de actividad: planificada, activa, pausada, completada, interrumpida o cancelada;
- actor bloqueado en una actividad incompatible;
- participantes compartidos y dependencias;
- duración restante para una actividad interrumpida;
- ubicación y ruta plausibles durante cada segmento de desplazamiento;
- prioridad para resolver dos actividades/eventos al mismo instante;
- clave de idempotencia para evitar que una reanudación repita el mismo intervalo;
- eventos autónomos resueltos durante ausencias largas sin revelar automáticamente escenas privadas al protagonista.

Una agenda de bloques horarios no debe crear seis acciones por día. El bloque agrupa actividades; no es una unidad de duración obligatoria.

La simulación debe permitir una jornada sin sucesos, una actividad que se prolonga, una tarea abandonada y personajes separados que no se reencuentran automáticamente.

## 15. Tabla de resultados de la auditoría

| Área | Resultado | Acción necesaria |
|---|---|---|
| Seis bloques y duración del día | Consistente | Ninguna |
| Día 1, 08:00 provisional | Compatible con valor por defecto del modelo | Mantener provisional |
| Acción frente a mensaje | Inconsistencia de runtime | Corregir política de elapsed_minutes |
| Rangos de acción | Solapamientos controlables | Añadir clasificación y no doble conteo |
| Selección de duración | Incompleta | Definir reglas para mínimo/medio/máximo |
| Simultaneidad | Principio consistente | Diseñar intervalos y compatibilidad |
| Comida y descanso | Consistente con separación de fases | Evitar sumar categorías anidadas |
| Viajes | No verificable numéricamente | Definir distancia y velocidades |
| Combate en segundos | Propuesta compatible, runtime minuto entero | Persistir remanente o migrar a segundos |
| Erupción Día 12 | Día válido, hora no registrada | Añadir precisión de fecha sin inventar minuto |
| Eventos dentro de una acción | Catch-up existente, sin interrupción demostrada | Intercalar intervalos y procesar en el instante |
| Agendas fuera de escena | Propuesta narrativa, no runtime | Motor de actividades y persistencia |
| Necesidades biológicas | Sin tasas numéricas | No aplicar desgaste arbitrario |

## 16. Pruebas de aceptación que deben añadirse antes de implementación completa

### Duración y turnos
1. Un mensaje sin acción temporal nueva no avanza el reloj.
2. Una continuación de la misma conversación no vuelve a cobrar la duración inicial.
3. Una acción corta usa su rango apropiado y no recibe un minuto automático solo por ser un turno nuevo.
4. Una acción prolongada aceptada puede consumir más de 15 minutos sin transformarse artificialmente en una pausa fuera de la ficción.
5. Las operaciones de interfaz no avanzan el reloj.

### Doble conteo y simultaneidad
6. Una negociación no se cobra además como conversación sustantiva.
7. Una inspección única no se cobra como mirada rápida, observación y examen a la vez.
8. Buscar y rastrear la misma pista no duplica el intervalo.
9. Preparar comida y comerla suma ambas fases si se realizan secuencialmente.
10. La misma persona no realiza tareas incompatibles en paralelo.
11. Cuatro actividades que comienzan juntas y duran 10, 15, 20 y 12 minutos avanzan el reloj 20 minutos, no 57.
12. Una actividad compartida por tres personajes solo consume su intervalo real una vez.

### Viaje, descanso y combate
13. Un viaje tiene duración basada en distancia y parámetros aprobados.
14. Una ruta con desvío suma el tiempo real del desvío, no una estimación duplicada.
15. Un descanso de 30 minutos no se suma otra vez como sueño si describe el mismo intervalo.
16. Ocho intercambios de 10 segundos conservan 80 segundos acumulados después de guardar y reabrir la sesión.
17. El tratamiento y el descanso posterior se registran como fases diferentes cuando realmente ocurren.

### Acontecimientos y autonomía
18. Un acontecimiento a mitad de una acción prolongada se procesa antes de resolver el resto de esa acción.
19. La erupción del Día 12 se puede registrar con precisión de día sin inventar hora.
20. La recuperación atrasada conserva la hora programada y la de procesamiento como datos distintos.
21. Una actividad autónoma no se repite si un turno se reintenta.
22. Las actividades de Brina, Maelis y Sera avanzan en paralelo solo si lugar, capacidades, tiempo y conocimiento lo permiten.
23. El protagonista no conoce una escena fuera de campo sin una fuente.
24. La restauración recupera reloj, remanentes de segundos, acciones y activaciones temporales coherentes.

## 17. Orden recomendado de corrección

No conviene construir primero una simulación compleja de las tres aventureras. El orden de dependencias recomendado es:

1. **Definición temporal:** clasificar acciones, evitar doble conteo y establecer cómo seleccionar una duración.
2. **Contrato del reloj:** eliminar el minuto automático por turno y acordar la persistencia de segundos o una precisión solo de minuto.
3. **Agenda de intervalos:** representar actividades individuales, incompatibilidades, solapamientos y pausas.
4. **Acontecimientos:** soportar fechas con precisión de día y procesar sucesos dentro de intervalos largos.
5. **Viajes:** establecer unidades, velocidades y costes por tramo.
6. **Necesidades y recuperación:** definir tasas y reglas antes de actualizar hambre, sed, sueño, fatiga y curación.
7. **Prueba de campaña:** simular una jornada completa, luego varios días y después el tramo hasta el Día 12.
8. **Historia previa del trío:** crear la cronología de sus encuentros y desplazamientos solo cuando las duraciones de ruta puedan validarse.

## 18. Límites y estado

- Esta auditoría no selecciona una historia previa para Brina, Maelis y Sera.
- No fija distancias, velocidades, horarios de viaje ni hora de la erupción.
- No añade tasas de hambre, sed, fatiga o curación.
- No declara implementadas las agendas autónomas ni el cobro de tiempo por acción.
- No modifica `main`, fichas maestras, Greeting ni originales v1.19 de SpicyChat.
- No modifica código ni ejecuta pruebas de software.

**Conclusión final:** la base temporal es consistente como modelo general, pero todavía hay brechas entre la propuesta narrativa y el runtime de la PR #21. Los hallazgos prioritarios son el valor por defecto de un minuto por turno, el minuto obligatorio para eventos de día sin hora, la falta de intercalado de sucesos dentro de acciones largas y la ausencia de parámetros numéricos de viaje. Resolverlos antes de crear la cronología previa de las aventureras evitará que el pasado del trío dependa de horarios inventados.
