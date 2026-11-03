# Motor de conducta y decisiones de PNJ

**Estado:** perfiles y catálogos persistidos, previsualización, agendas persistentes, ejecución limitada y primer planificador reactivo conectados a los avances reales del reloj. La autonomía de jornada completa sigue pendiente.  
**Alcance:** motor genérico de Word Bot. Los catálogos de acciones, focos, rasgos y patrones concretos deben ser datos del mundo o de cada personaje; no se deben convertir en reglas globales de todos los universos.

## 1. Diagnóstico del estado anterior

El proyecto ya persistía eventos, cambios de estado, conocimiento y relaciones dirigidas. La relación disponía de ejes como confianza, sospecha, amistad, respeto, rivalidad, resentimiento, miedo, deuda de gratitud, cooperación y atracción.

Eso no equivalía a un sistema de conducta completo. Las fichas de entidad contenían descripciones en texto, y el documento de autonomía de Isekai seguía señalando como pendientes la agenda ejecutable, la selección autónoma de actividades, la simulación fuera de escena, la resolución de conflictos y la persistencia de agendas activas.

Por tanto, no era correcto afirmar que todos los personajes ya tuvieran cientos de reacciones o una vida autónoma.

## 2. Principio de diseño

No conviene escribir miles de frases o reglas aisladas. La variedad debe surgir de combinar piezas independientes:

1. **Rasgos estables:** prudencia, curiosidad, disciplina, empatía, independencia, sociabilidad, asertividad, tolerancia al riesgo, etc.
2. **Necesidades dinámicas:** hambre, sed, cansancio, sueño, seguridad, descanso, contacto social y otras definidas por el mundo. Un dato desconocido permanece desconocido; nunca se convierte automáticamente en cero.
3. **Emociones con procedencia:** tipo, intensidad, objetivo y evento fuente. Cada emoción tiene su propio ritmo de desgaste, configurable; no todas desaparecen con el mismo reloj.
4. **Objetivos:** metas personales, inmediatas, obligaciones e intereses. Una curiosidad no equivale a una promesa ni a una misión aceptada.
5. **Foco de atención:** persona, grupo, lugar, objeto, tarea, amenaza, conocimiento, evento, recurso o el propio personaje.
6. **Capacidades y recursos:** determinan qué acciones son realmente posibles. Una sugerencia no concede habilidades, objetos ni información.
7. **Relaciones dirigidas:** la actitud de A hacia B no se copia automáticamente en B hacia A.
8. **Patrones de conducta:** reglas contextuales que modifican el peso de acciones cuando coinciden rasgos, necesidades, emociones o focos.

La personalidad no debe reducirse a una etiqueta única como «seria», «tímida» o «sarcástica». Esos rasgos pueden influir en decisiones diferentes sin determinar cada respuesta.

## 3. Primera implementación

Módulos: `proyecto/app/src/canon_manager/behavior_engine.py` (reglas y puntuación) y `behavior_controller.py` (persistencia y previsualización).

### Datos por personaje

El contrato de perfil admite:

- `traits`: valores registrados de rasgos entre 0 y 100.
- `needs`: valores entre 0 y 100 o `null` si aún no se conocen.
- `emotions`: colección de emociones con intensidad, desgaste por hora, objetivo y evento fuente.
- `goals`: objetivos con prioridad, etiquetas y estado.
- `focus`: tipo de foco, objetivo, saliencia y etiquetas.
- `capabilities`: capacidades conocidas.
- `resources`: cantidades disponibles.
- `relationships`: valores dirigidos por entidad destinataria y eje.

El perfil es independiente por entidad y partida y se guarda en `session_entity_behavior_profiles`. La relación no se copia en el JSON del perfil: se consulta en la tabla dirigida `relationships` para usar el valor vigente de A→B, sin inferir B→A. El protagonista queda excluido de la previsualización porque sus acciones pertenecen al usuario.

### Acciones y patrones de inicio

El catálogo genérico inicial aporta **29 acciones reutilizables** (observar, preguntar, escuchar, explicar, acercarse, mantener distancia, retirarse, ayudar, rechazar, negociar, proteger, descansar, comer, beber, dormir, practicar, estudiar, investigar, vigilar, rastrear, reparar, recolectar, viajar, esperar, compartir información, ocultarla, planificar, mediar y observar a la espera).

Incluye **22 patrones contextuales** de ejemplo, como evaluación cautelosa, curiosidad investigadora, protección, límites de independencia, cooperación, prioridad de evidencia, recuperación por cansancio, prioridad por hambre/sed, distancia por miedo, foco en amenaza y desescalada.

Son una biblioteca inicial, no miles de reglas escritas a mano. Cada mundo puede guardar un catálogo propio de hasta 500 acciones y 500 patrones adicionales, que se combina con la biblioteca genérica sin contaminar otros mundos. Cada perfil admite hasta 200 emociones activas registradas, 100 objetivos y colecciones separadas de rasgos/necesidades/focos. La variedad sale de combinar condiciones, perfiles, objetivos, recursos, relaciones, focos y estados emocionales; el límite evita que se convierta en una lista ilimitada de reglas duplicadas.

### Puntuación y salida

`rank_actions()`:
- descarta acciones sin capacidades, tiempo, condiciones o recursos requeridos;
- puntúa alivio de necesidades conocidas;
- aplica afinidad con rasgos registrados;
- premia acciones que contribuyen a objetivos activos;
- considera el foco actual y las emociones;
- aplica modificadores de relación hacia el destinatario concreto;
- aplica patrones que sí coinciden con el perfil;
- produce un orden determinista y códigos de motivo.

`rank_focuses()` ordena focos candidatos según saliencia, objetivos y emociones dirigidas al objetivo.

`advance_emotions()` aplica el desgaste configurado por emoción y tiempo del mundo. Una emoción con desgaste cero no desaparece por una regla universal.

`append_emotion()` registra una nueva emoción sin sobrescribir otras causas todavía activas.

## 4. Estado real y límites pendientes

La primera fase sigue siendo un **evaluador de propuestas**, pero ahora existe una segunda capa parcial: agenda persistente y ejecución limitada de actividades cuando el reloj ya avanzó por una acción autorizada.

### Runtime implementado

- `session_entity_agendas` conserva actividades por PNJ, con acción, inicio, duración, prioridad, contexto, estado y resultado.
- `behavior_action_executions` registra una ejecución completada por agenda. Los identificadores de solicitud hacen idempotente la creación; el estado y la transacción impiden aplicar dos veces una actividad.
- La API permite crear, consultar y cancelar actividades. La creación no modifica la hora.
- Las actividades empiezan cuando el reloj cruza su hora programada y solo se completan cuando alcanza el final de su duración.
- En cada avance real del reloj, el runtime procesa actividades vencidas y puede construir varias actividades secuenciales para el resto del día de cada PNJ configurado; respeta huecos, tareas en curso y compromisos manuales.
- El planificador selecciona acciones deterministas según el motor, pero solo si el catálogo del mundo las marca expresamente como aptas para autonomía, con duración positiva de hasta cuatro horas, riesgo máximo 20/100, sin coste de recursos ni desplazamiento físico.
- El contexto autónomo deriva condiciones de conocimiento por PNJ: `knows_event_kind:<kind>`, `knows_event_ref:<external_ref>` y `knows_event_id:<event_id>`. Solo entran eventos en estado `recorded` donde el PNJ figure como testigo explícito o en la audiencia autorizada del mensaje fuente.
- Los mensajes privados requieren que el PNJ figure en su audiencia/recipiente. Metadatos dañados, eventos pendientes/rechazados y hechos de cronología mundial sin una vía individual de conocimiento se excluyen. La presencia en la misma partida o ubicación no concede conocimiento.
- La firma de decisión incluye las condiciones percibidas. Un nuevo hecho conocido invalida únicamente las actividades autónomas futuras; las tareas en curso y agendas manuales permanecen intactas. La versión anterior de firma se conserva para no invalidar agendas v2 ya programadas.
- Esta primera capa deriva conocimiento directo de testigos/audiencias existentes; todavía no modela transmisión autónoma de rumores/testimonios ni convierte rumores en hechos.
- Las observaciones ambientales se guardan por observador, ubicación y minuto de juego en `session_environment_observations`. Cada registro exige un evento fuente `observation` en estado `recorded`, testigo explícito y audiencia compatible.
- Clima y seguridad local son dominios separados: `observes_weather:<value_key>` y `observes_local_safety:<value_key>`. Las claves son datos configurables del mundo; Word Bot no inventa un estado cuando no existe una observación.
- La API `POST /api/sessions/{session_id}/environment/observations` toma la ubicación y el minuto del estado autoritativo de la partida; no acepta fechas futuras ni ubicaciones elegidas libremente. Cada observación caduca entre 1 y 240 minutos de juego después de registrarse.
- Una observación solo se usa para el mismo personaje y ubicación mientras siga vigente y su evento fuente continúe registrado. Compartir región o escena no copia automáticamente el clima ni la evaluación de seguridad.
- Registrar una observación replanifica las actividades autónomas futuras en el mismo minuto de juego, sin avanzar el reloj. Si una observación caduca antes de que una actividad empiece, la firma deja de coincidir y la actividad se bloquea sin efectos.
- Las observaciones se incluyen en snapshots, deshacer/restaurar y copias de seguridad de la partida.
- Las condiciones no registradas permanecen desconocidas y no se dan por verdaderas. Las acciones que requieren descanso seguro, comida, agua u otra condición solo son candidatas cuando el contexto aporta esa condición expresamente.
- Las acciones no se repiten en la misma jornada salvo que el catálogo indique `autonomous_repeatable: true`; las repetibles tienen un máximo de tres ejecuciones diarias. El planificador admite hasta seis actividades automáticas por jornada y deja diez minutos entre tareas.
- Cada agenda automática guarda una firma del perfil, catálogo y ubicación. Si alguno cambia de forma material, se cancelan solo las tareas autónomas futuras y se recalcula el resto de la jornada. Las tareas en curso y los compromisos manuales no se interrumpen.
- Antes de ejecutar una tarea automática que aún no había comenzado, el runtime vuelve a comparar la firma de decisión. Si el perfil, el catálogo o la ubicación cambió durante un salto temporal, la tarea obsoleta se bloquea sin aplicar sus efectos.
- El runtime se invoca al avanzar tiempo por turnos del narrador y por tramos/cancelación de viajes. Nunca crea tiempo por sí mismo ni funciona como un proceso en segundo plano.
- El desgaste emocional configurado se aplica a los perfiles cuando avanza el reloj. No se desgastan emociones si no transcurre tiempo de juego.
- En la ejecución se vuelven a comprobar perfil, capacidades, condiciones y catálogo guardado. Los efectos permitidos son deliberadamente limitados: cambios sobre necesidades ya conocidas, emociones nuevas con evento fuente, actualización de objetivos existentes y cambio/limpieza del foco.
- Las actividades completadas generan un registro de evento y una fila de ejecución. Perfiles, agendas y ejecuciones se incluyen en snapshots de turno y copias de seguridad/restauración.

API: `POST /api/sessions/{session_id}/entities/{entity_id}/agendas`, `GET /api/sessions/{session_id}/agendas` y `DELETE /api/sessions/{session_id}/agendas/{agenda_id}`. API ambiental: `POST /api/sessions/{session_id}/environment/observations`.

### Límites pendientes

- La planificación cubre el resto del día actual, hasta seis tareas, sin programar automáticamente días futuros. Un PNJ sin perfil válido o sin acciones autorizadas permanece inactivo.
- La replanificación responde a cambios materiales del perfil, catálogo, ubicación y percepción individual derivada de eventos registrados.
- Ninguna acción se habilita por defecto para ejecución autónoma: el catálogo de cada mundo debe marcarla explícitamente.
- No hay panel visual para administrar, reordenar o inspeccionar agendas; la primera interfaz disponible es la API.
- Las actividades todavía no calculan rutas ni distancias. El clima/seguridad disponibles son observaciones explícitas y caducables, no una simulación meteorológica automática ni una evaluación global por región. Las acciones que impliquen desplazamiento físico siguen excluidas.
- Las acciones con coste de recursos se rechazan para agenda hasta contar con reservas atómicas y resolución de concurrencia.
- Los efectos no modifican inventario, ubicación, relaciones ni poderes. No hay aún movimiento autónomo por el mapa.
- Las emociones se desgastan al avanzar el reloj, pero los acontecimientos aceptados todavía no generan emociones de forma automática.
- No hay agenda con interrupciones, reanudación parcial, cambios de prioridad mientras está en curso ni resolución de conflictos entre PNJ.
- La transmisión persistente de testimonios/rumores y las condiciones ambientales estructuradas (clima y seguridad local) siguen pendientes. Los sucesos mundiales de cronología no se comparten automáticamente con los PNJ.
- Continúan pendientes el editor visual de perfiles, el registro de razones para todas las propuestas descartadas y la prueba E2E real del navegador.

La previsualización `rank_actions()` sigue sin producir efectos. Es una lista de propuestas. La ejecución solo ocurre para una actividad que ha sido guardada como agenda y cuyo intervalo ya ha transcurrido en el reloj real de la partida.

## 5. Criterios para considerar completa la autonomía

1. Dos personajes con perfiles distintos pueden elegir acciones diferentes ante el mismo contexto.
2. La misma persona puede elegir otra acción al cambiar su necesidad, emoción, objetivo o foco.
3. No se elige una acción sin la capacidad, el recurso, el tiempo o la condición requerida.
4. Una necesidad desconocida no fuerza una reacción ni se trata como satisfecha.
5. Una emoción conserva su causa y solo cambia según eventos o desgaste configurado.
6. Las relaciones son asimétricas y cada cambio necesita causa y evidencia.
7. Los PNJ no adquieren conocimiento por estar fuera de escena.
8. Un salto temporal simula solo las actividades justificadas por tiempo, ubicación, recursos y compromisos.
9. No se genera una escena dramática si no hay una causa para ella; la inactividad también es un resultado válido.
10. Los efectos se aplican una sola vez, dentro de transacciones recuperables.

## 6. Aplicación a Isekai sin Destino

Isekai puede aportar perfiles, capacidades y patrones propios de Brina, Maelis y Sera, pero sus reglas de personalidad y sus arcos no pertenecen al motor genérico.

Las tres fichas aún requieren que el autor confirme motivaciones personales concretas y estados iniciales desconocidos. No deben inventarse traumas, relaciones entre ellas, hambre, miedo, cansancio ni objetivos secretos para llenar el sistema.

El diseño narrativo de autonomía sigue siendo la fuente de requisitos, no una afirmación de que ya existe simulación fuera de escena.
