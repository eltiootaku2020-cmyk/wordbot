# 22 — Sistema temporal, duración de acciones y continuidad del reloj (propuesta)

**Estado:** propuesta de diseño pendiente de revisión y aprobación.  
**Rama:** story/isekai-time-and-trio-prehistory.  
**Base:** story/isekai-independent-companion-life (PR #38).  
**Alcance:** completar la especificación del tiempo narrativo para campañas largas: reloj, duración de acciones, viajes, interrupciones, simultaneidad, agendas autónomas y acontecimientos programados.

Este documento no afirma que la simulación temporal completa esté implementada. Se apoya en el modelo de día/minuto, los bloques horarios, las reglas de viaje y el programador de acontecimientos ya documentados. Las duraciones de ejemplo son valores iniciales de diseño para revisar, no datos del canon ni fórmulas definitivas.

## 1. Problema que resuelve

Una historia larga no puede medir el tiempo por cantidad de mensajes, párrafos o turnos del chat. Tampoco puede tratar cada acción como instantánea ni hacer avanzar una jornada completa por una conversación breve.

El mundo necesita un reloj único por partida, y cada acción que realmente sucede debe consumir una duración razonable. Durante ese intervalo:

- el protagonista realiza su acción;
- los personajes autónomos pueden continuar actividades compatibles;
- pueden llegar acontecimientos programados;
- cambian luz, clima, disponibilidad, fatiga, rutas y oportunidades cuando las reglas correspondientes estén definidas;
- el protagonista solo conoce lo que observa, deduce razonablemente o recibe por una fuente.

El reloj controla continuidad. No debe convertirse en un castigo por escribir, pensar o conversar fuera de la ficción.

## 2. Principios temporales

1. **Un solo reloj de ficción por partida.** Todas las entidades de una misma sesión consultan el mismo tiempo del mundo.
2. **La acción, no el mensaje, consume tiempo.** Dos mensajes que describen una sola conversación no deben duplicar su duración.
3. **El tiempo no avanza por inactividad del chat.** Cerrar la página, dejar de escribir o tardar en responder no adelanta la historia.
4. **Las intenciones no son acciones realizadas.** Decir que se piensa viajar no consume el viaje hasta que se ejecuta.
5. **Las acciones tienen duración estimada y duración real.** Un obstáculo, error, lesión, conversación o desvío puede modificar el tiempo.
6. **El mundo sigue durante el intervalo.** Las agendas autónomas y los acontecimientos no esperan a que el protagonista los mire.
7. **La simultaneidad no se suma.** Dos personajes que hacen cosas al mismo tiempo no duplican el tiempo transcurrido en el reloj global.
8. **No fingir exactitud.** Si solo se conoce un rango, el narrador no presenta una duración exacta como dato observado.
9. **Los cambios quedan registrados.** Cada avance relevante conserva causa, intervalo, ubicación y resultado.
10. **La cronología aprobada prevalece.** Ninguna estimación de una acción mueve un acontecimiento ancla confirmado a otra fecha.

## 3. Reloj de mundo y unidad interna

### 3.1 Representación

La forma legible del reloj será:

- Día: entero a partir del Día 1.
- Hora: formato de 24 horas, HH:MM.
- Unidad interna: minuto de mundo.
- Día completo: 24 horas = 1.440 minutos.
- El Día 1 comienza a las 00:00 como referencia aritmética; el punto de llegada heredado en el claro se mantiene provisionalmente en Día 1, 08:00.

La representación absoluta puede calcularse como:

`total_minutes = (day - 1) × 1440 + minute_of_day`

La hora del día debe estar entre 00:00 y 23:59. El siguiente minuto después de Día 1, 23:59 es Día 2, 00:00.

El proyecto ya tiene una función temporal que convierte día y minuto en minutos absolutos para evaluar acontecimientos programados. Esta propuesta amplía el uso narrativo del reloj; no reemplaza ese mecanismo.

### 3.2 Bloques horarios de presentación

Se conservan los seis bloques de cuatro horas ya usados por la agenda de autonomía:

| Bloque | Intervalo |
|---|---|
| Madrugada | 00:00–03:59 |
| Amanecer | 04:00–07:59 |
| Mañana | 08:00–11:59 |
| Mediodía | 12:00–15:59 |
| Tarde | 16:00–19:59 |
| Noche | 20:00–23:59 |

Los bloques sirven para agrupar agendas, rutinas y resúmenes. No sustituyen la hora exacta ni hacen que cada acción dure cuatro horas.

### 3.3 Alcance por partida

- Cada partida o sesión guarda su propio reloj y sus propios resultados.
- Las definiciones de acontecimientos del mundo pueden ser compartidas por las partidas del mismo mundo.
- El registro de que un acontecimiento ya se activó pertenece a cada partida, no a todas las partidas en conjunto.
- No se mezclan las horas, decisiones o consecuencias de dos partidas diferentes.
- Una restauración debe devolver el reloj y el registro de activaciones de esa partida al mismo estado coherente.

## 4. Qué hace avanzar el reloj

### 4.1 Acciones que consumen tiempo

Toda actividad ejecutada puede consumir tiempo, aunque su duración sea pequeña:

- desplazarse, orientarse y buscar una ruta;
- observar, examinar, rastrear e investigar;
- hablar, escuchar, preguntar y negociar;
- preparar equipo, fabricar, reparar y ordenar pertenencias;
- comer, beber, cocinar y conseguir suministros;
- curar heridas, recuperarse y practicar habilidades;
- combatir, perseguir, esconderse y escapar;
- montar o desmontar campamento;
- esperar, vigilar, descansar y dormir;
- realizar tareas autónomas fuera de escena.

### 4.2 Acciones que no avanzan el reloj por sí solas

- Mensajes fuera de la ficción sobre diseño, correcciones o preferencias del usuario.
- Pensar una posibilidad sin ejecutarla.
- Abrir una ficha, consultar un estado o pedir un resumen.
- Repetir una respuesta ya emitida sin que haya ocurrido una nueva acción.
- La duración real que el usuario tarda en escribir o leer.
- Pausas entre sesiones o días reales sin una regla expresa de avance fuera de escena.

La consulta de información puede consumir tiempo si dentro de la ficción implica leer, buscar, preguntar o examinar un objeto. La simple consulta de la interfaz no lo consume.

### 4.3 Conversación y mensajes

Una conversación tiene duración narrativa según su extensión y contexto, no según el número de mensajes del chat. Una respuesta corta puede representar unos segundos o minutos; una negociación extensa puede ocupar bastante más. El narrador debe mantener continuidad entre mensajes que pertenecen a la misma conversación.

Si el usuario solo responde con una frase breve durante una escena ya abierta, no se debe cobrar de nuevo el tiempo completo de la actividad anterior.

## 5. Tabla inicial de duraciones orientativas

Los rangos siguientes son una **propuesta de calibración**, no valores canónicos. Sirven para evitar acciones instantáneas o excesivamente lentas mientras se prueba el diseño. La duración elegida dependerá del alcance real de la tarea.

| Actividad | Rango inicial orientativo | Condiciones que pueden modificarlo |
|---|---:|---|
| Mirada rápida / comprobar algo evidente | 1–2 min | Distancia, visibilidad, distracción |
| Observación cuidadosa de un punto cercano | 2–5 min | Cobertura, ruido, luz, peligro |
| Examinar un objeto o detalle | 3–10 min | Complejidad, herramientas, familiaridad |
| Leer una nota breve | 1–5 min | Idioma, estado del texto, interrupciones |
| Leer o estudiar un documento largo | 10–60+ min | Extensión, dificultad, pausas |
| Buscar en una zona pequeña | 5–15 min | Orden, tamaño, vegetación, urgencia |
| Registrar un área amplia | 15–60+ min | Extensión, método, terreno, rastros |
| Rastrear una pista | 10–30 min por tramo | Calidad del rastro, distancia y terreno; el viaje posterior se calcula aparte |
| Intercambio verbal breve | 1–3 min | Número de participantes y objetivo |
| Conversación sustantiva | 5–20 min | Tema, interrupciones y desacuerdos |
| Negociación o planificación | 15–60 min | Complejidad, condiciones y cantidad de partes |
| Preparar o revisar equipo | 2–10 min | Cantidad, organización, daño |
| Beber o tomar algo rápidamente | 1–3 min | Cantidad y situación |
| Comer una ración ya preparada | 10–30 min | Cantidad, compañía y ritmo |
| Preparar una comida | 15–60 min | Ingredientes, fuego, utensilios y complejidad |
| Tratar una lesión menor | 5–20 min | Materiales, cooperación y conocimiento |
| Atención de una lesión seria | 20 min–varias horas | Gravedad, medios, habilidad y estabilidad; no garantiza recuperación |
| Preparar un campamento sencillo | 10–30 min | Refugio, clima, carga y seguridad |
| Desmontar y recoger un campamento | 5–15 min | Cantidad de equipo y urgencia |
| Pausa o descanso breve | 10–30 min | Estado físico y seguridad |
| Descanso deliberado | 30–120 min | Necesidades, refugio e interrupciones |
| Sueño prolongado | Varias horas; referencia inicial 6–9 h para adultos humanos | Fatiga previa, heridas, especie, seguridad y calidad del descanso |
| Combate breve | Segundos a pocos minutos | Número de intercambios, distancias, tácticas y resistencia |
| Persecución o huida | Segundos a decenas de minutos | Distancia, velocidad, terreno, obstáculos y estado físico |
| Viaje | Según distancia y condiciones reales | Sección de viajes; no inventar una velocidad si no está definida |

### 5.1 Cómo interpretar los rangos

- El mínimo no es el resultado automático de toda acción.
- El máximo no es un límite rígido: una búsqueda compleja puede superar el rango.
- El narrador puede dividir una tarea extensa en segmentos y ofrecer oportunidades de detenerse.
- La cifra definitiva se selecciona según la escena y se registra como duración real.
- Si la información disponible no permite estimar de forma útil, debe indicarse que la duración es incierta y evitar inventar una cifra exacta.

### 5.2 Combate

El combate no debe medirse por la cantidad de mensajes ni por la longitud de los párrafos. Se divide en intercambios de acción que incluyen movimiento, defensa, ataque, reacción, recuperación y cambio de posición.

Como punto inicial de calibración, un intercambio breve puede ocupar aproximadamente 5–15 segundos; maniobras más amplias pueden requerir más tiempo. No es una regla universal ni una duración fija de cada turno. La distancia, la velocidad, el número de participantes, las decisiones y los obstáculos determinan la duración real.

Se deben contabilizar aparte, cuando correspondan:
- acercamiento o persecución antes del contacto;
- tiempo de combate efectivo;
- retirada o separación;
- búsqueda de heridos y atención posterior;
- recuperación y reorganización.

Una escena de combate narrada en varios mensajes no vuelve a sumar el mismo intervalo en cada mensaje.

### 5.3 Sueño y necesidades

El rango de 6–9 horas es únicamente una referencia inicial para planificar el descanso de adultos humanos. No fija la fisiología de todas las especies ni garantiza recuperación completa. El descanso depende de cansancio, dolor, heridas, hambre, sed, seguridad, refugio, temperatura y posibles interrupciones.

No se impondrán horarios rígidos idénticos a todas las criaturas o personajes.

## 6. Estimación y cálculo de tiempo real

Cada acción tiene al menos dos medidas distintas:

- **Duración estimada:** lo que razonablemente se espera antes de comenzar.
- **Duración real:** lo que terminó consumiendo según obstáculos, decisiones y resultado.

Factores de ajuste:
- distancia y extensión física;
- terreno, clima, hora y visibilidad;
- complejidad, precisión y cantidad de pasos;
- experiencia, capacidades y herramientas;
- fatiga, heridas, carga y necesidades;
- cooperación, oposición, ruido y riesgo;
- interrupciones, desvíos y sucesos simultáneos.

La estimación no garantiza el éxito. Una búsqueda puede durar lo previsto y no encontrar nada. Una persona competente puede terminar rápido, pero no superar límites físicos imposibles. Una interrupción puede alargar la acción o impedir que termine.

Si la incertidumbre importa para una decisión, se debe comunicar como rango, no disfrazarla de certeza.

## 7. Acciones compuestas e interrupciones

Una actividad compleja se divide en fases con su propio tiempo:

1. preparación;
2. desplazamiento o posicionamiento;
3. ejecución;
4. comprobación del resultado;
5. recuperación, limpieza o cierre.

Ejemplo: investigar una señal lejos del campamento no es una sola acción instantánea. Puede incluir caminar hasta ella, inspeccionarla, contrastar pistas y regresar. Cada fase tiene duración y riesgos propios.

Las tareas prolongadas deben tener puntos de control. Si ocurre un peligro, llega un mensaje, cambia el clima o se activa un acontecimiento:
- la actividad puede detenerse;
- puede continuar con retraso;
- puede terminar parcialmente;
- puede fracasar;
- puede ser abandonada voluntariamente.

No completar automáticamente una tarea larga si el mundo cambia durante su ejecución y el cambio podría afectar al resultado.

## 8. Simultaneidad y agendas autónomas

Este apartado conecta el reloj con la PR #38.

### 8.1 Tiempo global, actividades individuales

El reloj global avanza una sola vez. Cada personaje puede tener su propia actividad dentro del intervalo.

Ejemplo: el protagonista tarda 30 minutos en examinar una construcción mientras Maelis lee sus notas y Sera vigila una entrada. El tiempo del mundo avanza 30 minutos, no 30 + 30 + 30. Las actividades individuales se registran en paralelo.

### 8.2 Restricciones por personaje

Una misma persona no puede completar dos actividades físicas incompatibles al mismo tiempo. Puede combinar tareas compatibles —por ejemplo, caminar y conversar— siempre que no se cuenten como dos duraciones independientes y no comprometan la atención necesaria.

Las actividades compartidas se registran una sola vez con todos los participantes reales. La conversación entre tres personas no triplica el tiempo consumido.

### 8.3 Resolución fuera de escena

Cuando el protagonista consume tiempo:
- identificar el intervalo desde el reloj anterior hasta el nuevo;
- localizar las actividades autónomas que caben dentro del intervalo;
- verificar ubicación, conocimiento, capacidades, recursos y compromisos de cada personaje;
- resolver interrupciones y acontecimientos en orden cronológico;
- guardar hechos y consecuencias;
- actualizar solo el conocimiento de quienes pudieron percibir o recibir información.

No se deben simular seis actividades obligatorias por día ni inventar escenas privadas para rellenar el tiempo.

### 8.4 Ausencia breve y ausencia prolongada

- Una observación rápida o una charla breve no activa una simulación de jornada.
- Una separación de horas puede permitir que los personajes completen tareas, se desplacen, descansen o cambien planes.
- Una ausencia de varios días puede requerir varios registros de actividad, eventos y actualizaciones, sin revelar automáticamente al protagonista todo lo sucedido.
- El intervalo se procesa una vez. Reintentar o continuar una generación no debe duplicar tiempo ni consecuencias.

## 9. Orden de resolución temporal

Para una acción que ocupa un intervalo, el futuro motor debería resolver:

1. registrar el reloj inicial y la acción aceptada;
2. calcular una duración estimada;
3. identificar acontecimientos programados y actividades autónomas que podrían ocurrir antes del final;
4. avanzar hasta el siguiente punto temporal relevante;
5. resolver el hecho o la actividad cuyas condiciones se cumplieron;
6. recalcular lo que pueda verse afectado;
7. continuar el intervalo restante;
8. guardar reloj final, duración real, resultado, cambios y conocimiento.

Si no hay hechos intermedios relevantes, se puede avanzar directamente hasta el final. No es necesario simular cada minuto vacío.

Los hechos simultáneos deben resolverse con una regla de orden estable y verificable. Si el orden puede cambiar el resultado (por ejemplo, una advertencia llega justo cuando empieza un peligro), registrar la incertidumbre o usar un desempate explícito; no elegir el orden que favorezca la trama.

## 10. Acontecimientos programados y el Día 12

El acontecimiento ancla de la erupción del volcán permanece en el Día 12. Su fecha no depende de la presencia del protagonista ni de que las aventureras lo descubran.

**La hora exacta de la erupción no está establecida.** No se debe convertir silenciosamente «Día 12» en 00:00, 08:00, mediodía o cualquier otra hora. El momento debe permanecer con precisión de día hasta que el autor decida si se fija una hora o si se admite una activación con precisión de fecha.

Hay una consideración técnica: el programador temporal existente compara día y minuto programados. Antes de guardar una fecha sin hora como si fuera una hora exacta, la implementación futura tendrá que admitir una precisión temporal de tipo «día» o recibir una hora aprobada. No asignar minuto cero como sustituto accidental.

Cuando el reloj alcance o sobrepase un acontecimiento programado:
- activarlo en orden cronológico;
- registrar su activación una sola vez por partida;
- conservar la fecha/hora programada por separado del momento en que el sistema lo procesa;
- aplicar consecuencias desde la ubicación y el conocimiento reales de cada personaje;
- no transmitir el acontecimiento automáticamente a todo el mundo.

## 11. Visualización para el jugador

En cambios temporales relevantes, mostrar un encabezado o línea breve:

**Día N — HH:MM**  
**Tiempo transcurrido:** X minutos / X horas desde la última acción temporal.

No hace falta mostrar un contador después de cada frase. Sí conviene mostrarlo cuando:
- comienza o termina una actividad larga;
- cambia de bloque horario;
- hay viaje, combate, descanso o espera;
- ocurre un acontecimiento programado;
- una demora puede alterar una oportunidad o un riesgo.

La interfaz puede mantener un resumen de:
- hora actual;
- actividad en curso;
- cuánto tiempo lleva;
- duración estimada restante, si se puede estimar;
- compromisos o eventos próximos que el protagonista conoce.

No mostrar horarios secretos de personajes ni acontecimientos que el protagonista desconoce.

## 12. Registro persistente propuesto

Cada acción temporal debería guardar:

| Campo | Propósito |
|---|---|
| action_id | Identificador estable |
| session_id | Partida cuyo reloj se modifica |
| actor_id | Entidad que ejecuta la acción |
| participant_ids | Participantes reales adicionales |
| action_type | Tipo de actividad |
| intent | Intención registrada |
| location_start / location_end | Ubicaciones confirmadas |
| start_total_minutes | Instante global de inicio |
| estimated_min_minutes | Límite inferior de estimación |
| estimated_max_minutes | Límite superior de estimación |
| actual_duration_minutes | Duración finalmente consumida |
| end_total_minutes | Instante global de fin |
| status | Pendiente, en curso, completada, parcial, interrumpida, fallida o abandonada |
| interruption_ids | Hechos que interrumpieron o alteraron la acción |
| preconditions | Capacidades, conocimiento, herramientas y recursos necesarios |
| outcome | Resultado validado |
| state_changes | Cambios causados por la actividad |
| evidence | Evidencia o fuente del resultado |
| visibility | Visto, contado, rumor, deducible o desconocido |
| created_by | Jugador, personaje autónomo, sistema temporal o acontecimiento |
| idempotency_key | Evita que un reintento aplique dos veces la misma acción |

Los cambios de reloj, acciones, agenda autónoma y activaciones del cronograma deben formar una operación coherente y persistente. Un error a mitad de la resolución no puede dejar el reloj avanzado con los resultados antiguos, o las actividades completadas con el reloj sin avanzar.

## 13. Deshacer, reintentar y restaurar

- El tiempo no retrocede por una respuesta repetida o una llamada duplicada.
- Un reintento usa la misma identidad de acción y no vuelve a cobrar la duración.
- Una continuación de una acción interrumpida conserva el tiempo ya consumido y no lo suma otra vez.
- Un deshacer narrativo restaura el reloj y los registros de activación de esa partida de forma coherente.
- Las definiciones compartidas de acontecimientos del mundo no se modifican al deshacer una partida.
- Una copia de seguridad debe conservar reloj, acciones y registros temporales relacionados.
- Una restauración incompatible con la definición actual de acontecimientos debe rechazarse antes de alterar los datos activos.

Estas reglas son requisitos de diseño para una fase técnica futura, no una afirmación de que ya estén conectadas a la agenda de compañeros.

## 14. Pruebas de aceptación futuras

1. Una pausa entre mensajes no avanza el reloj.
2. Una conversación breve consume menos tiempo que una negociación larga, sin depender de cuántos mensajes se usaron.
3. Dos mensajes que continúan la misma acción no cobran la actividad dos veces.
4. Una búsqueda puede durar el intervalo estimado y no encontrar nada.
5. Un viaje puede tardar más por desvío u obstáculo.
6. Un combate registra intervalos de ficción, no minutos por mensaje.
7. Dos personajes que actúan en paralelo no duplican el avance global.
8. Un personaje no realiza acciones físicas incompatibles en el mismo intervalo.
9. Las agendas autónomas avanzan cuando el protagonista viaja o descansa durante horas.
10. Un personaje no realiza una actividad en un lugar al que no pudo llegar a tiempo.
11. Un acontecimiento programado que cae dentro de un viaje o descanso se procesa antes de cerrar ese intervalo.
12. Un acontecimiento se activa una sola vez por partida.
13. La erupción del Día 12 no recibe una hora inventada.
14. Una consulta de estado no avanza el tiempo.
15. Una restauración devuelve reloj y cronología de la partida a un estado consistente.
16. El nivel de precisión visible no supera la evidencia disponible.
17. Un descanso no cura automáticamente heridas ni elimina necesidades.
18. El paso de un día completo puede resolverse sin inventar escenas dramáticas para cada personaje.

## 15. Decisiones que siguen abiertas

- Si el autor desea conservar únicamente minutos como unidad interna o introducir segundos para combate y acciones muy breves.
- Valores definitivos de velocidad de viaje según terreno, carga, medio y estado físico.
- Duraciones de necesidades por especie y personaje.
- Frecuencia y precisión de las actualizaciones de hambre, sed, fatiga y sueño.
- Reglas de tiempo para fabricación, aprendizaje, entrenamiento, curación y recuperación mágica.
- Si algunos acontecimientos importantes tienen hora exacta o solo fecha.
- Fórmulas de estimación y condiciones para seleccionar la duración real dentro de cada rango.
- Cuánto detalle temporal debe exponerse en la interfaz.

**Regla de aprobación:** los principios de reloj global, avance por acciones reales, simultaneidad y ausencia de avance por inactividad se proponen como estructura. Los rangos de duración son calibración inicial y deben revisarse antes de convertirse en valores fijos. No modificar el canon ni la configuración original de SpicyChat automáticamente.

## 16. Estado técnico

**Ya existe en la base documental/técnica consultada:**
- campos de día, bloque horario y hora exacta en el modelo de mundo;
- una conversión de día/minuto a minutos absolutos;
- acontecimientos fijos procesados cronológicamente por partida;
- reglas aprobadas de que viajes, conversaciones, combates, descansos y desvíos consumen tiempo;
- separación entre hora programada y conocimiento de los personajes.

**Todavía no está demostrado como sistema completo:**
- estimación y cobro de duración por acción;
- reloj conectado a cada tipo de acción;
- procesamiento simultáneo de las tres agendas;
- interrupción temporal y reanudación sin duplicación;
- actualización temporal de necesidades y ecología;
- interfaz visible del reloj;
- pruebas integrales de campaña larga.

Este archivo es diseño documental. No se ejecutaron cambios de software ni pruebas de software en esta entrega.
