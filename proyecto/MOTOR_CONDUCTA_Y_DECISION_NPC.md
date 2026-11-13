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
- La firma de decisión incluye las condiciones percibidas y la procedencia de observaciones ambientales e informes recibidos. Un cambio relevante invalida únicamente las actividades autónomas futuras; las tareas en curso y agendas manuales permanecen intactas. Se conservan las firmas v2, v3 y v4 heredadas; las agendas nuevas usan v5. Una agenda v4 solo se invalida por esta nueva dimensión cuando el PNJ recibe un informe atribuido.
- La percepción directa sigue derivándose de testigos/audiencias. Para comunicar información existe una vía separada y explícita: `session_knowledge_transmissions` conserva evento de origen, evento de comunicación, emisor, destinatario, versión textual, tipo (testimonio/rumor), ubicación, minuto y transmisión anterior si se trata de una retransmisión.
- Un testimonio requiere que el emisor haya sido testigo directo del evento de origen. Un rumor requiere una transmisión aceptada anterior del mismo evento, recibida por el emisor; el sistema no permite inventar una cadena de conocimiento sin procedencia. La percepción reconstruye esa ruta con los IDs, emisores, destinatarios y textos inmutables de cada salto, y distingue al originador de los retransmisores.
- Si el destinatario recibió una rectificación aprobada, puede decidir retransmitir esa versión como una comunicación nueva. `parent_transmission_id` conserva el informe recibido y `parent_correction_id` señala la rectificación exacta usada como base. La aplicación valida que esa rectificación ya estuviera aprobada y vigente al momento de crear la retransmisión; no se permite retransmitir una versión retirada ni presentar una versión anterior como si fuera la corregida.
- Emisor y destinatario deben figurar como testigos y audiencia autorizada del evento de comunicación y compartir ubicación en el momento de transmitir. La propuesta queda pendiente; aprobar el evento registra la comunicación y actualiza la percepción del destinatario. Rechazarlo no concede conocimiento.
- El destinatario recibe una entrada atribuida en `knowledge_reports` con `epistemic_status=reported_not_verified`, además de condiciones `heard_testimony_of_event:<id>` o `heard_rumor_of_event:<id>`. No se añade el evento original a `knows_event_id` salvo que el personaje también lo haya presenciado o tuviera otra vía directa válida.
- El contexto narrativo y el panel de estado muestran cada versión bajo el personaje que la recibió. Compartir ubicación o estar en la misma partida no propaga informes automáticamente.
- `session_knowledge_assessments` guarda juicios personales append-only del destinatario: postura (`believes`, `uncertain`, `doubts`, `contradicts`), confianza de 0–100, justificación, minuto y una evidencia exacta. La evidencia debe ser otro informe que el mismo personaje recibió sobre el mismo evento, o un evento registrado que conoce por una vía directa.
- Las evaluaciones que comparan dos informes fijan `assessed_correction_id` y `evidence_correction_id` para identificar exactamente qué versión de cada informe conocía y comparó el PNJ. Si el informe todavía no tenía rectificaciones, el ID queda vacío y representa su texto original. Las correcciones posteriores no reescriben la valoración histórica. La API rechaza IDs obsoletos si la interfaz intenta guardar una comparación desde versiones que ya dejaron de ser las vigentes al momento de enviarla; los clientes antiguos omiten los campos y el servidor fija la versión actual durante la solicitud. Las valoraciones existentes anteriores a esta migración quedan marcadas con `version_refs_exact=0` y se muestran como históricas sin referencia exacta, en lugar de atribuirles una versión que el registro antiguo no guardó.
- La percepción construye `knowledge_comparisons` por destinatario: pares de informes del mismo acontecimiento, recibidos por el mismo PNJ, de emisores distintos y con versiones vigentes diferentes. Una diferencia de texto solo crea un candidato de comparación; no se etiqueta automáticamente como contradicción ni decide cuál versión es verdadera. Las retractaciones se excluyen de las versiones vigentes.
- Para registrar `stance=contradicts`, la evaluación debe vincular dos informes recibidos por el mismo PNJ, ambos vigentes y de emisores distintos. La valoración sigue siendo personal y append-only; el panel muestra quién comparó qué versiones y con qué motivo, sin propagarla a los demás personajes.
- La confianza es subjetiva y pertenece a un PNJ y a un informe concretos. No es una puntuación global, no se copia a otros personajes y nunca modifica el evento fuente ni el texto original. `epistemic_status` continúa como `reported_not_verified` incluso cuando el receptor confía mucho en la versión.
- La API `POST /api/sessions/{session_id}/knowledge-reports/{transmission_id}/assessments` registra una evaluación explícita e idempotente. Requiere exactamente una referencia de evidencia; no permite que un personaje evalúe un informe recibido por otro ni que cite hechos que desconoce. Las nuevas evaluaciones se conservan en snapshots, deshacer y copias de seguridad.
- Una evaluación nueva replanifica las actividades autónomas futuras en el minuto actual, porque cambia la percepción individual que firma la agenda. No adelanta el reloj; conserva las tareas manuales y las ya iniciadas, y un reintento idempotente no vuelve a planificar.
- `session_knowledge_corrections` registra rectificaciones/retractaciones append-only vinculadas a una transmisión concreta y a un nuevo evento de comunicación aprobado. El tipo del nuevo evento debe coincidir con el tramo corregido: `knowledge` para testimonios y `rumor` para retransmisiones. Solo el emisor de ese tramo puede corregir o retirar lo que comunicó ante el mismo destinatario; una comunicación no puede corregir el informe de otra persona.
- `correction_kind=corrected` conserva el texto original y añade una versión corregida con motivo; `correction_kind=retracted` conserva el texto original y marca que el emisor retiró la afirmación sin sustituirla. Cada entrada posterior apunta mediante `parent_correction_id` a la versión vigente inmediatamente anterior. El historial es append-only y forma una cadena única, sin ramas ni sobrescrituras.
- La corrección/retractación exige un evento nuevo del tipo correspondiente (`knowledge` o `rumor`), testigos/audiencia autorizados y aprobación explícita. Al corregir un rumor solo cambia el tramo retransmitido por ese emisor: el `parent_transmission_id`, la versión del tramo anterior, el evento fuente, sus evaluaciones y los destinatarios anteriores o posteriores no se reescriben ni se notifican automáticamente. La nueva versión tampoco se convierte en verdad objetiva.
- El destinatario ve el historial completo de correcciones del tramo que recibió y la cadena de procedencia (originador, retransmisores, destinatarios y texto inmutable de cada salto), junto al informe atribuido. La última corrección aprobada determina el estado vigente: una nueva rectificación puede sustituir una versión corregida, pero una retractación es terminal. Las condiciones individuales `received_report_corrected:<id>` o `received_report_retracted:<id>` y la replanificación de agendas reflejan solo el estado vigente, sin avanzar el reloj.
- Las propuestas pendientes se guardan en `state_changes.field=knowledge_correction` y se aprueban/rechazan junto con el evento de comunicación. Las referencias duplicadas al mismo informe y los actos que mezclan una nueva transmisión con una rectificación se dejan sin aplicar y el evento queda pendiente de revisión. El ledger se conserva en snapshots, deshacer y backups/restauración; los backups anteriores que no contienen esta tabla siguen siendo restaurables.
- Las observaciones ambientales se guardan por observador, ubicación y minuto de juego en `session_environment_observations`. Cada registro exige un evento fuente `observation` en estado `recorded`, testigo explícito y audiencia compatible.
- Clima y seguridad local son dominios separados: `observes_weather:<value_key>` y `observes_local_safety:<value_key>`. Las claves son datos configurables del mundo; Word Bot no inventa un estado cuando no existe una observación.
- La API `POST /api/sessions/{session_id}/environment/observations` toma la ubicación y el minuto del estado autoritativo de la partida; no acepta fechas futuras ni ubicaciones elegidas libremente. Cada observación caduca entre 1 y 240 minutos de juego después de registrarse.
- Las respuestas del narrador pueden incluir propuestas estructuradas `environment_observations`, vinculadas por `event_ref` a un evento de tipo `observation`. El observador debe aparecer como testigo explícito y dentro de la audiencia autorizada. La aplicación no las activa automáticamente: convierte el evento fuente en pendiente y expone la propuesta dentro de `pending_events`.
- La propuesta captura en el servidor la ubicación y el minuto de juego en que ocurrió el evento observado. Aprobarla más tarde no renueva su duración ni traslada la observación a la ubicación actual del PNJ: si ya caducó, se conserva como registro histórico pero no habilita condiciones para agendas.
- Aprobar `POST /api/sessions/{session_id}/events/{event_id}/approve` valida de nuevo dominio, clave, duración, pertenencia al mundo, testigos, audiencia/procedencia y la ubicación/minuto capturados en el instante observado. Solo entonces crea la observación personal y replanifica en el mismo minuto, sin avanzar el reloj. Rechazar el evento también rechaza su propuesta.
- Las propuestas se guardan en el ledger transaccional existente (`state_changes.field=environment_observation`), por lo que participan en snapshots, deshacer y copias de seguridad sin una tabla paralela. No aparecen como cambios genéricos aprobables: se revisan junto al evento que las justifica.
- Esta aprobación confirma únicamente una observación personal para un personaje y ubicación; no cambia un clima mundial/global ni crea un pronóstico. El narrador puede sugerir, pero no es autoridad de la condición ambiental.
- Una observación solo se usa para el mismo personaje y ubicación mientras siga vigente y su evento fuente continúe registrado. Compartir región o escena no copia automáticamente el clima ni la evaluación de seguridad.
- Registrar una observación replanifica las actividades autónomas futuras en el mismo minuto de juego, sin avanzar el reloj. Si una observación caduca antes de que una actividad empiece, la firma deja de coincidir y la actividad se bloquea sin efectos.
- Las observaciones se incluyen en snapshots, deshacer/restaurar y copias de seguridad de la partida.
- Las condiciones no registradas permanecen desconocidas y no se dan por verdaderas. Las acciones que requieren descanso seguro, comida, agua u otra condición solo son candidatas cuando el contexto aporta esa condición expresamente.
- Las acciones no se repiten en la misma jornada salvo que el catálogo indique `autonomous_repeatable: true`; las repetibles tienen un máximo de tres ejecuciones diarias. El planificador admite hasta seis actividades automáticas por jornada y deja diez minutos entre tareas.
- Cada agenda automática guarda una firma del perfil, catálogo, ubicación y percepción individual. Si alguno cambia de forma material, se cancelan solo las tareas autónomas futuras y se recalcula el resto de la jornada. Las tareas en curso y los compromisos manuales no se interrumpen. Las agendas nuevas usan la firma v5; las firmas v2/v3/v4 heredadas siguen validándose con su formato original hasta que una nueva condición de conocimiento justifique recalcular.
- Antes de ejecutar una tarea automática que aún no había comenzado, el runtime vuelve a comparar la firma de decisión. Si el perfil, el catálogo o la ubicación cambió durante un salto temporal, la tarea obsoleta se bloquea sin aplicar sus efectos.
- El runtime se invoca al avanzar tiempo por turnos del narrador y por tramos/cancelación de viajes. Nunca crea tiempo por sí mismo ni funciona como un proceso en segundo plano.
- El desgaste emocional configurado se aplica a los perfiles cuando avanza el reloj. No se desgastan emociones si no transcurre tiempo de juego.
- En la ejecución se vuelven a comprobar perfil, capacidades, condiciones y catálogo guardado. Los efectos permitidos son deliberadamente limitados: cambios sobre necesidades ya conocidas, emociones nuevas con evento fuente, actualización de objetivos existentes y cambio/limpieza del foco.
- Las actividades completadas generan un registro de evento y una fila de ejecución. Perfiles, agendas y ejecuciones se incluyen en snapshots de turno y copias de seguridad/restauración.

API: `POST /api/sessions/{session_id}/entities/{entity_id}/agendas`, `GET /api/sessions/{session_id}/agendas` y `DELETE /api/sessions/{session_id}/agendas/{agenda_id}`. API ambiental: `POST /api/sessions/{session_id}/environment/observations`.

### Razonamiento semántico individual y procedencia de evidencias

- `knowledge_reasoning.py` añade un analizador local y determinista, sin servicios externos ni modelos generativos. Por ahora reconoce una gramática acotada de afirmaciones de estado en español/inglés: sujeto, propiedad de estado, valor, negación, periodo temporal y ubicación opcional. Los valores se normalizan mediante un vocabulario explícito; una frase fuera de esa gramática queda como `unstructured`, no se fuerza una interpretación.
- Las comparaciones diferencian `possible_conflict`, `compatible`, `different_time`, `different_location`, `different_claim`, `insufficient_context` y `unstructured`. Una diferencia de redacción no basta para concluir incompatibilidad; una ausencia de dato no se convierte en negación. Los intervalos de tiempo aproximados son filtros conservadores, no una cronología objetiva.
- El análisis usa el mismo evento fuente y las versiones textuales recibidas. Un conflicto semántico es solo un candidato. No selecciona al emisor verdadero ni modifica el evento registrado, el canon o el estado del mundo.
- La independencia se calcula desde la raíz de la cadena, el testigo/originador y el mismo evento fuente, no contando retransmisiones ni envíos paralelos del mismo testigo. Dos rutas desde la misma transmisión o dos envíos raíz del mismo testigo sobre ese evento se muestran como `same_lineage` y cuentan como una sola procedencia; solo originadores distintos con cadenas completas se clasifican como independientes. Si falta un eslabón o la identidad de origen, el resultado es `unknown`, nunca corroboración independiente.
- La clasificación actualmente distingue observación/evento registrado, testimonio directo y rumor retransmitido a partir de los tipos y vínculos ya almacenados. Todavía no existe un registro de primera clase para documentos ni para inspecciones de evidencia física; el motor no inventa esas categorías ni las suma como pruebas separadas.
- `session_knowledge_reasoning_assessments` guarda conclusiones personales append-only: PNJ evaluador, ambos IDs de transmisión, los IDs exactos de corrección usados, raíces de procedencia, independencia, postura, confianza, motivo y minuto. Las conclusiones se consultan únicamente dentro de la percepción de ese PNJ. Dos personajes pueden interpretar de manera distinta los mismos tipos de evidencia.
- La API `POST /api/sessions/{session_id}/knowledge-comparisons/{left_transmission_id}/{right_transmission_id}/reasoning` rechaza informes que el evaluador no recibió, informes retirados, acontecimientos distintos y versiones obsoletas. La postura `contradiction` exige un conflicto semántico candidato y dos cadenas completas e independientes; las dudas y conclusiones compatibles siguen siendo decisiones personales.
- La ruta también protege la API de valoración previa: `stance=contradicts` ya no acepta dos retransmisiones como fuentes independientes cuando comparten origen o la procedencia está incompleta.
- Una corrección posterior conserva la conclusión anterior y la marca como histórica al cambiar uno de los IDs de versión. Repetir una solicitud con el mismo `request_id` devuelve el registro previo sin duplicarlo ni volver a planificar.
- Las conclusiones se incluyen en snapshots de turno y restauración. Una nueva valoración cambia la percepción individual y llama al planificador existente para revisar actividades autónomas futuras autorizadas; no avanza el reloj, no mueve PNJ, no modifica al protagonista ni interrumpe tareas manuales o en curso.
- El panel de conocimiento muestra el resultado semántico como candidato, la procedencia compartida/independiente, las versiones comparadas, la opinión individual y su historial. No convierte el resultado del analizador en una verdad objetiva.

### Límites pendientes

- La planificación cubre el resto del día actual, hasta seis tareas, sin programar automáticamente días futuros. Un PNJ sin perfil válido o sin acciones autorizadas permanece inactivo.
- La replanificación responde a cambios materiales del perfil, catálogo, ubicación, conocimiento individual y observaciones ambientales vigentes.
- Ninguna acción se habilita por defecto para ejecución autónoma: el catálogo de cada mundo debe marcarla explícitamente.
- No hay panel visual para administrar, reordenar o inspeccionar agendas; la primera interfaz disponible es la API.
- Las actividades todavía no calculan rutas ni distancias. El clima/seguridad disponibles son observaciones explícitas y caducables, incluidas propuestas del narrador que requieren aprobación del evento fuente; no hay simulación meteorológica automática ni evaluación global por región. Las acciones que impliquen desplazamiento físico siguen excluidas.
- Las acciones con coste de recursos se rechazan para agenda hasta contar con reservas atómicas y resolución de concurrencia.
- Los efectos no modifican inventario, ubicación, relaciones ni poderes. No hay aún movimiento autónomo por el mapa.
- Las emociones se desgastan al avanzar el reloj, pero los acontecimientos aceptados todavía no generan emociones de forma automática.
- No hay agenda con interrupciones, reanudación parcial, cambios de prioridad mientras está en curso ni resolución de conflictos entre PNJ.
- No hay propagación autónoma o automática de rumores: cada comunicación y cada retransmisión requieren un evento explícito y aprobación. Toda rectificación/retractación formal requiere al emisor original y al mismo destinatario. Una propuesta debe apuntar a la última versión conocida; los padres obsoletos se rechazan para impedir bifurcaciones. Los backups de la tabla anterior se migran conservando su única corrección como raíz de la cadena. El olvido y las redes autónomas de rumor siguen pendientes.
- Los sucesos mundiales de cronología no se comparten automáticamente con los PNJ. Las observaciones ambientales son explícitas y caducables; todavía no existe simulación automática del tiempo atmosférico.
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
