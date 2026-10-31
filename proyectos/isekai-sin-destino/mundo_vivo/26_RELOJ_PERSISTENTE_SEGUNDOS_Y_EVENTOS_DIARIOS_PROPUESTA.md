# Reloj persistente con precisión de segundos y acontecimientos de precisión diaria

**Estado:** propuesta técnica pendiente de revisión.  
**Dependencia:** PR #41, rama `fix/isekai-time-neutral-turns`.  
**Alcance:** diseño y criterios de aceptación; no cambia el código ni fija horas canónicas.

## 1. Hallazgo del código actual

La corrección de PR #41 elimina el minuto automático por turno, pero el resto del runtime sigue usando minutos enteros:

- `sessions` persiste `day` y `minute_of_day`; no existe campo para segundos.
- `NarratorResponse` comunica `elapsed_minutes` como entero.
- `apply_narrator_result` convierte día y minuto a minutos absolutos y luego actualiza la sesión.
- `absolute_minute` y `fire_due_world_events` ordenan la cronología con minutos absolutos.
- Los eventos mundiales requieren `scheduled_minute`, incluso cuando la historia solo define un día.
- `capture_turn_state` incluye día/minuto en los snapshots; `restore_turn_state` los restaura.
- La restauración de backups lee y vuelve a escribir los campos de sesión; el esquema del backup se valida antes de aplicarlo.
- El contexto del narrador y la respuesta del endpoint de estado exponen `minute_of_day` y una etiqueta horaria HH:MM.

En la auditoría #40 ya se identificó un escenario de ocho intercambios de diez segundos (80 segundos). La base actual no puede conservar ese remanente tras un turno, reinicio o restauración.

## 2. Alternativas

### A. Mantener minutos enteros

Ventajas:
- Menos cambios de esquema y de contrato.
- Compatible con el programador actual.

Costes:
- Los intervalos inferiores a un minuto se pierden, se redondean o quedan acumulados en memoria externa.
- Para conservar el remanente haría falta igualmente un campo persistente de segundos.
- Si el combate, interrupciones y acciones breves se quieren medir con precisión, la aplicación termina manteniendo dos unidades de tiempo.

### B. Usar segundos enteros como unidad de cálculo — recomendación

Ventajas:
- Representa directamente combates, pausas e interrupciones inferiores al minuto.
- Evita redondeos acumulativos.
- Permite comparar acciones, reloj y eventos sobre una sola línea temporal.

Coste:
- Requiere una migración coordinada de sesión, contrato de respuesta, snapshots, backups, contexto y programador.

**Recomendación:** adoptar segundos enteros para cálculo y persistencia, conservando día/minuto como campos derivados o de compatibilidad para la interfaz.

## 3. Contrato de sesión propuesto

Añadir a `sessions`:

```sql
second_of_minute INTEGER NOT NULL DEFAULT 0
  CHECK(second_of_minute BETWEEN 0 AND 59)
```

Reglas:
- `day` sigue comenzando en 1.
- `minute_of_day` sigue en el rango 0..1439.
- `second_of_minute` expresa 0..59.
- El instante absoluto se calcula con:

```text
total_seconds =
  (day - 1) * 86400
  + minute_of_day * 60
  + second_of_minute
```

- Las conversiones de vuelta a fecha y hora deben centralizarse en funciones puras, probadas con medianoche, cambio de día, límites y grandes saltos.
- La etiqueta actual HH:MM puede mantenerse para no romper la interfaz; el estado debe exponer también `second_of_minute` o una etiqueta precisa separada.
- No depender solo de un contador en memoria: la hora exacta debe sobrevivir al reinicio del proceso.

## 4. Contrato temporal del narrador

Sustituir en una entrega coordinada el campo `elapsed_minutes` por `elapsed_seconds`:

- 0 significa que no se consumió tiempo de ficción.
- Las acciones breves usan segundos enteros.
- La propuesta automática sigue teniendo un límite corto y explícito; no sustituye a `/salto`.
- `/salto` continúa aceptando minutos, horas y días para el avance explícitamente autorizado. La aplicación convierte las unidades a segundos de forma determinista.
- El modelo no puede proponer una duración porque haya escrito un mensaje más largo, ni volver a cobrar una acción ya contabilizada.
- Hasta que se aprueben tablas de duración, una acción sin base cuantitativa suficiente deja el reloj en 0 y crea una nota pendiente. No se inventan cifras.

Los proveedores manuales deberán recibir el esquema nuevo al preparar el prompt. Una respuesta JSON antigua con el campo retirado debe fallar de forma clara y pedir que se regenere desde un prompt actualizado, en lugar de mezclar unidades silenciosamente.

## 5. Programador: precisión temporal y registro de procesamiento

El sistema debe distinguir dos conceptos:

1. **Cuándo está definido que sucede un acontecimiento.**
2. **Cuándo lo detectó/procesó una sesión el runtime.**

Para acontecimientos con hora definida (precisión de minuto en esta etapa):
- Mantener `scheduled_day` y `scheduled_minute`.
- Convertir la fecha programada a segundos absolutos.
- Activar cuando el reloj cruce el instante programado.
- Guardar por separado el instante programado y el instante real de procesamiento/catch-up.
- No etiquetar el instante de procesamiento como si fuera el instante histórico del acontecimiento.

### Acontecimientos con precisión de solo día

Propuesta de esquema:

- `time_precision`: `day` o `minute`.
- `scheduled_minute`: nullable; obligatorio solo con `time_precision='minute'`.
- `scheduled_day`: siempre obligatorio.
- La erupción del Día 12 debe poder guardarse con `time_precision='day'` y `scheduled_minute=NULL`.

Reglas semánticas necesarias:
- Un evento de precisión diaria representa una ventana dentro de ese día, no un punto a las 00:00.
- No se le asigna una hora sustituta ni se utiliza un minuto técnico como si fuera canon.
- El contexto del narrador debe identificar expresamente la precisión: “día conocido; hora no registrada”.
- Los acontecimientos de precisión diaria no pueden interrumpir una acción larga en un segundo exacto que no está definido.
- Los acontecimientos de precisión de minuto sí pueden convertirse en límites exactos para la futura segmentación de acciones.
- Cuando una sesión alcanza el día programado o lo recupera después de un salto, el ledger debe registrar la fecha del hecho y, separadamente, cuándo lo procesó el runtime.
- El orden relativo entre un acontecimiento diario sin hora y otros sucesos del mismo día debe permanecer indeterminado salvo que una fuente posterior lo precise.

Esto evita inventar la hora de la erupción, pero deja explícito que una ancla de precisión diaria no puede producir una interrupción exacta sin una decisión posterior.

## 6. Snapshots, undo y backups

El segundo debe formar parte del estado autoritativo:

- `capture_turn_state` guarda `second_of_minute`.
- `restore_turn_state` lo restaura con día/minuto.
- El hash del estado posterior incluye el segundo.
- El backup incluye el nuevo campo; la restauración comprueba su estructura antes de modificar la sesión.
- Backups antiguos sin el campo nuevo pueden interpretarse con segundo 0 únicamente si el resto del esquema es una versión antigua reconocida y completa.
- No se deben aceptar backups parcialmente migrados.
- La restauración y el undo deben recuperar también el ledger de activaciones y los tiempos de procesamiento de eventos.
- Las definiciones compartidas del mundo siguen separadas del estado de cada sesión.

## 7. Migración y compatibilidad

Secuencia recomendada:

1. Añadir `second_of_minute DEFAULT 0` mediante una migración idempotente.
2. Mantener intactos los valores actuales de día/minuto.
3. Centralizar las conversiones a segundos absolutos.
4. Introducir `elapsed_seconds` en modelos, schemas, prompts, proveedores y API.
5. Migrar el ledger de eventos para separar programación y procesamiento.
6. Actualizar snapshots, undo, backup, restore, huellas de canon y contexto.
7. Mantener las respuestas públicas compatibles durante la transición: conservar `day`, `minute_of_day` y `time_label`; agregar los campos precisos sin cambiar silenciosamente el significado de los antiguos.
8. Retirar el contrato antiguo solo cuando todos los proveedores y pruebas usen el nuevo.

No se propone reconstruir tablas de SQLite si una columna con valor predeterminado y migración segura basta.

## 8. Pruebas de aceptación

1. Una respuesta conversacional por defecto mantiene el reloj idéntico.
2. Una acción de 10 segundos avanza 10 segundos, no un minuto.
3. Seis acciones sucesivas de 10 segundos avanzan exactamente 60 segundos.
4. Acciones simultáneas que duran 30 y 20 segundos avanzan 30 segundos globales, no 50.
5. Una actividad compuesta no vuelve a cobrar fases anidadas.
6. La conversión de 23:59:50 + 20 segundos produce el día siguiente a las 00:00:10.
7. Un combate de 80 segundos conserva la hora exacta tras reiniciar la aplicación.
8. Undo devuelve el segundo exacto anterior.
9. Backup y restore preservan el segundo exacto.
10. Un backup antiguo completamente válido restaura con segundo 0.
11. Un backup parcialmente migrado se rechaza sin mutar la sesión.
12. Los proveedores automáticos y manuales comparten el mismo contrato `elapsed_seconds`.
13. Un `/salto 2 minutos` suma exactamente 120 segundos.
14. Un salto mayor a 15 minutos solo ocurre cuando el usuario lo autoriza.
15. Un evento de minuto definido se activa una sola vez cuando se cruza su instante.
16. El instante programado y el instante de procesamiento se conservan como datos distintos.
17. Un evento de precisión diaria admite minuto nulo.
18. El evento diario no se transforma en 00:00 ni recibe una hora ficticia.
19. La erupción del Día 12 sigue siendo un hecho del día 12 sin hora añadida.
20. Un evento diario sin hora no provoca una interrupción exacta inventada.
21. Un evento de minuto puede interrumpir posteriormente una actividad segmentada en intervalos.
22. Reintento, replay y undo no duplican activaciones.
23. La restauración mantiene el ledger coherente con el reloj.
24. La etiqueta HH:MM existente sigue funcionando y la precisión nueva se expone sin romper clientes actuales.

## 9. Fuera de alcance

Esta propuesta no implementa:
- Agendas autónomas de Brina, Maelis o Sera.
- Velocidades y distancias de viaje.
- Hambre, sed, sueño, fatiga, curación ni tasas biológicas.
- Segmentación completa de actividades largas.
- Selección definitiva de duraciones por categorías.
- Cronología previa del trío.
- Una hora concreta para la erupción del Día 12.

## 10. Estado de aprobación

- La recomendación de arquitectura es **segundos enteros como unidad de cálculo**, conservando día/minuto como campos derivados y de compatibilidad.
- Es una recomendación técnica pendiente de aprobación; no modifica el canon ni el mundo narrativo.
- No se implementan migraciones ni cambios de runtime en esta entrega documental.


## 11. Modelo de duración por acciones (propuesta ampliada)

### 11.1. Principio: no existe un tick por mensaje

El reloj no avanza automáticamente cada uno o dos mensajes, ni cada respuesta del narrador. Avanza cuando el personaje o un PNJ realiza una acción dentro del mundo que consume tiempo.

Reglas:
- Una pregunta, pensamiento, aclaración del jugador, descripción estática, reacción instantánea o texto de interfaz no consume tiempo por sí mismo.
- Una frase pronunciada consume el tiempo razonable de decirla; un diálogo sostenido acumula la duración de lo que realmente se habla y de las pausas justificadas.
- Una respuesta narrativa larga no implica que haya transcurrido mucho tiempo.
- Un turno puede contener cero, una o varias acciones. Se contabilizan las acciones realizadas, no la cantidad de mensajes.
- No se cobra una acción anunciada si el personaje no llegó a ejecutarla, fue interrumpido antes de realizarla o cambió de decisión.
- No se cobra dos veces una acción descrita primero como intención y después como resultado.

### 11.2. Descomposición temporal

Antes de actualizar el reloj, el narrador debe identificar las acciones que realmente ocurrieron en la escena. Para cada acción se registra como mínimo:
- actor;
- tipo de actividad;
- duración estimada en segundos;
- si ocurrió en secuencia, simultáneamente o como fase interna de otra acción;
- motivo de la estimación y nivel de confianza.

La aplicación debe poder calcular el total a partir de segmentos temporales. En esta propuesta:
- Las acciones secuenciales se suman.
- Las acciones simultáneas dentro del mismo intervalo consumen el tiempo de la acción concurrente más larga, no la suma de todas las duraciones individuales.
- Las fases internas o acciones accesorias realizadas durante una actividad principal no vuelven a cobrarse.
- Si el personaje detiene una actividad para empezar otra, ambas sí se suman.
- Una acción compartida por un grupo (por ejemplo, caminar juntos) se registra como un intervalo de grupo, no como el mismo viaje cobrado una vez por integrante.
- Las acciones largas se dividen en segmentos cuando sea necesario evaluar eventos programados, cambios de clima, encuentros o interrupciones.

Ejemplos:
- Hablar 8 segundos y luego buscar durante 3 minutos = 3 minutos y 8 segundos.
- Dos aventureras inspeccionan sectores distintos durante 12 minutos en paralelo = 12 minutos globales, no 24.
- Una aventurera camina durante 10 minutos mientras otra observa desde el mismo punto = 10 minutos si la observación ocurre durante ese intervalo.
- Caminar 10 minutos, detenerse y registrar una zona durante 5 minutos = 15 minutos.
- Concentrarse en un poder durante 8 segundos mientras otra persona prepara el campamento durante 4 minutos = 4 minutos globales si ambos intervalos empiezan juntos.

### 11.3. Rangos iniciales para calibración

Los siguientes rangos son valores de prueba para escenarios corrientes, no hechos canónicos ni límites rígidos. El narrador debe elegir dentro del rango según complejidad, distancia, estado físico, equipo, experiencia, urgencia y contexto. Las pruebas de juego deberán calibrarlos.

| Acción | Rango inicial |
|---|---:|
| Pronunciar una frase breve | 2–6 segundos |
| Intercambio verbal corto | 10–30 segundos |
| Conversación sostenida | 1–5 minutos o más, según el contenido hablado |
| Mirar alrededor sin desplazarse | 5–20 segundos |
| Examinar un objeto visible | 10–45 segundos |
| Recoger algo al alcance | 5–20 segundos |
| Activar un poder simple e inmediato | 1–5 segundos |
| Apuntar o concentrarse antes de usar un poder | 3–15 segundos |
| Preparar un poder complejo | 15–60 segundos o más, según la ficción |
| Buscar un objeto en una zona pequeña | 1–5 minutos |
| Registrar minuciosamente una habitación/campamento | 5–20 minutos |
| Buscar en una zona amplia de bosque | 15–60 minutos o más |
| Preparar o guardar equipo | 1–5 minutos |
| Atender una herida sencilla | 2–10 minutos |
| Montar un campamento básico | 10–30 minutos |

Criterios:
- La duración de un poder no equivale automáticamente a su coste, enfriamiento o duración del efecto. Son magnitudes distintas.
- Una activación instantánea no consume varios minutos solo porque el efecto permanezca activo.
- Un efecto mantenido consume tiempo adicional únicamente cuando el personaje debe sostener activamente la concentración o realizar una actividad continua.
- Una búsqueda fallida puede consumir tiempo: el tiempo refleja el esfuerzo realizado aunque no se encuentre nada.
- La búsqueda debe crecer según el tamaño y la complejidad de la zona; no se debe resolver una búsqueda exhaustiva de un bosque entero en unos pocos segundos.
- No se asigna duración a una acción no cuantificada cuando faltan datos críticos; el narrador puede pedir una precisión o dejar el cálculo pendiente, sin inventar una cifra.

Para diálogo extenso, la estimación puede basarse en el contenido que se pronunció en la escena y sus pausas, nunca en el tamaño del mensaje escrito por el jugador ni en el texto narrativo del bot.

### 11.4. Movimiento y viaje: tiempo por distancia y terreno

Caminar no debe tener un coste fijo por mensaje ni por comando. Se calcula según distancia recorrida, tipo de terreno, pendiente, carga, estado físico, ritmo del grupo, visibilidad y obstáculos.

Como referencia inicial de senderismo:
- terreno fácil y camino claro: alrededor de 4 km/h;
- terreno irregular o matorral ligero: alrededor de 3 km/h;
- terreno muy accidentado, vegetación densa o paso difícil: alrededor de 1–1,5 km/h;
- las pendientes, descansos, navegación, desvíos y condiciones meteorológicas añaden tiempo cuando realmente afectan al recorrido.

Estas cifras son referencias de planificación, no velocidades garantizadas. La regla de senderismo de Bushwalking Manual advierte que la velocidad cambia según el terreno y la condición del grupo, y añade tiempo por ascenso; Bushwalking Victoria también recuerda que carga, viento, superficie, pendiente y fatiga alteran la marcha. Referencias:
- https://bushwalkingmanual.org.au/trip-planning/route-planning/
- https://bushwalkingvictoria.org.au/BWV-2021/wp-content/uploads/2024/04/Handbook_AdvancedNavigation.pdf

Para el simulador:
1. Si existe una ruta conocida con distancia, se estima la duración desde distancia y velocidad efectiva.
2. Si no existe distancia cartografiada, se utiliza una estimación explícita de tramo (corto/medio/largo) y el narrador no debe fingir precisión métrica.
3. El bosque abierto no equivale a avanzar por maleza cerrada. Un camino, una zona despejada, un pantano y una ladera requieren velocidades distintas.
4. La lluvia, el barro, el viento, la niebla y la oscuridad no aplican siempre una penalización fija: solo añaden tiempo cuando afectan a la tracción, orientación, visibilidad, seguridad o ritmo.
5. La carga, heridas, cansancio y capacidades de cada integrante alteran el ritmo del grupo. En desplazamientos grupales se usa el ritmo realista del grupo, no la velocidad del miembro más rápido.
6. Correr o huir se calcula como esfuerzo de corta duración, con fatiga y obstáculos; no se permite mantener la velocidad de sprint durante horas.
7. Buscar rastros mientras se camina puede ralentizar el avance del tramo; no se añade una búsqueda completa aparte si ambas actividades sucedieron a la vez.

### 11.5. Hora del día, clima y condiciones de la zona

La hora exacta es el dato autoritativo. Etiquetas como madrugada, amanecer, mañana, mediodía, tarde, atardecer, noche y medianoche se derivan de la hora local de la región y sirven para la narración/UI; no se actualizan por separado.

El clima sí es estado persistente y localizado:
- se asocia a una región o zona, no al mundo entero;
- conserva condición (soleado, nublado, lluvia, niebla, tormenta, viento), intensidad y efectos relevantes;
- puede registrar visibilidad, estado del suelo y viento cuando estos datos sean útiles;
- cambia por transiciones ambientales plausibles o eventos meteorológicos programados, no por cada mensaje ni de forma aleatoria en cada turno;
- se conserva al reiniciar, deshacer y restaurar la sesión;
- una transición meteorológica puede añadir una nueva condición ambiental sin borrar hechos previos, como suelo mojado tras la lluvia.

La hora y el clima afectan a la dificultad con contexto:
- la noche reduce la visibilidad cuando no hay luna, iluminación o equipo adecuado;
- la niebla reduce la distancia de detección y complica seguir señales;
- la lluvia puede borrar huellas, dificultar fuego, mojar equipo y volver resbaladizo el terreno;
- el viento puede afectar proyectiles, sonido y temperatura;
- una tormenta puede obligar a buscar refugio si la situación lo justifica.

No deben convertirse en penalizaciones automáticas. Cada condición puede ofrecer ventajas: lluvia que enmascara sonidos, niebla que oculta una retirada o noche que evita patrullas humanas.

### 11.6. Cambiar de actividad o decidir moverse más tarde

El momento de la acción se calcula con el reloj vigente:
- Si el personaje decide salir por la tarde, el sistema no adelanta la hora solo por la decisión; primero representa las actividades previas que realmente ocurren.
- Si el grupo se queda conversando, preparando equipo o descansando, ese tiempo se contabiliza de acuerdo con esas actividades.
- Al comenzar el viaje, la duración se calcula por el trayecto y las condiciones reales.
- Si el jugador ordena esperar hasta una hora o franja concreta, el tiempo avanza hasta ese momento y se procesan los cambios/eventos intermedios.
- Si el jugador simplemente dice «más tarde», el narrador debe interpretar el intervalo según el contexto o pedir precisión cuando afecte a una decisión importante.
- Un cambio de escena no equivale a teletransporte: el tiempo de viaje y las acciones intermedias siguen existiendo, salvo que el jugador autorice un salto temporal explícito.

### 11.7. Ejemplo de turno

Situación: el grupo está en un sendero del bosque a las 08:35, con cielo nublado.

El protagonista mira el terreno (10 segundos), pregunta a Brina si conoce el camino (6 segundos de diálogo), y luego el grupo camina 700 metros por un sendero irregular. Con una velocidad efectiva cercana a 3 km/h, el tramo tarda aproximadamente 14 minutos.

Resultado aproximado: 08:49:16.

Si Maelis examina un símbolo durante 2 minutos mientras Sera vigila en paralelo, el reloj avanza otros 2 minutos, no 4. Si Sera deja de vigilar para ayudar a Maelis durante esos mismos 2 minutos, tampoco se cobra dos veces.

La narración puede redondear la presentación a 08:49 si la interfaz solo muestra minutos, pero el estado interno debe conservar los segundos.

### 11.8. Pruebas nuevas para el modelo de acciones

Añadir a las pruebas de aceptación:
25. Varios mensajes de conversación breve no provocan un minuto automático por turno.
26. Una conversación hablada larga sí consume tiempo proporcional al diálogo realmente pronunciado.
27. Pensamientos, instrucciones del jugador y texto descriptivo no suman tiempo por sí mismos.
28. Una acción anunciada pero no ejecutada no modifica el reloj.
29. Una búsqueda fallida consume el tiempo que tomó realizarla.
30. Una búsqueda amplia tarda más que inspeccionar un objeto visible.
31. Un poder instantáneo no consume la duración de su efecto si no requiere concentración continua.
32. Las fases de una acción compuesta no se cobran de nuevo.
33. Dos personajes que realizan tareas paralelas no duplican el tiempo global.
34. Las tareas secuenciales sí acumulan sus duraciones.
35. Caminar por camino, terreno irregular y maleza densa produce tiempos distintos para la misma distancia.
36. La distancia, pendiente, carga y fatiga influyen en el tiempo de viaje cuando hay datos suficientes.
37. La oscuridad, lluvia o niebla solo afectan la velocidad cuando cambian visibilidad, tracción o seguridad.
38. El cambio de escena no elimina el tiempo de desplazamiento.
39. Una espera solicitada avanza el reloj y evalúa eventos intermedios.
40. Las estimaciones inciertas quedan marcadas como aproximadas y no se presentan como distancias o duraciones exactas.

## 12. Estado ampliado de aprobación

- El modelo recomendado es **duración por acción realizada**, sin tick automático por mensaje o por cada uno o dos turnos.
- Los rangos de la sección 11 son valores iniciales de calibración, pendientes de pruebas y ajuste.
- El desplazamiento se calcula por distancia y condiciones, no por turno.
- La hora del día se deriva del reloj persistente; el clima es un estado regional persistente que cambia con el tiempo del mundo.
- Esta ampliación sigue siendo diseño documental. No cambia el runtime, las reglas de PSICHO-Eco ni el canon de la historia.
