# Motor de conducta y decisiones de PNJ

**Estado:** perfiles y catálogos persistidos, previsualización de decisiones y panel local integrados; ejecución autónoma y agendas todavía pendientes.  
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

## 4. Límites que siguen pendientes

Esta fase es un **evaluador de propuestas**, no un simulador completo. No debe marcarse como autonomía terminada.

Todavía falta:

- editor visual de campos de perfil en vez de editar JSON manualmente;
- generación de decisiones a partir de percepción y conocimiento individual comprobable; ahora los límites de conocimiento aún no se construyen automáticamente desde los recuerdos/testigos;
- convertir cada acción candidata en un plan validado con precondiciones, pasos, costes, duración e interrupciones;
- ejecutor transaccional e idempotente que aplique resultados a ubicación, inventario, tiempo, relaciones, eventos y recursos;
- registro de por qué se descartaron acciones, y no solo los motivos de puntuación de las acciones elegidas;
- agendas y colas persistentes por personaje, con compromisos, prioridad, descanso y cancelación;
- simulación fuera de escena al avanzar el reloj por viajes, descanso o saltos autorizados;
- encuentros entre PNJ, diálogo autónomo, negociación, cooperación, conflicto y resolución persistente;
- que emociones se creen o modifiquen a partir de eventos aceptados y se desgasten cuando el tiempo del mundo avance; ahora se pueden guardar y avanzar mediante función, pero no se actualizan solas;
- snapshots, deshacer y recuperación de decisiones ejecutadas, y panel que explique acciones, evidencias y efectos.

La API local expone `GET/PUT /api/sessions/{session_id}/entities/{entity_id}/behavior`, `POST .../behavior/preview` y `GET/PUT /api/worlds/{world_id}/behavior/catalog`. La interfaz permite seleccionar una entidad, cargar/guardar su perfil, mantener el catálogo JSON del mundo y consultar la puntuación de hasta 15 acciones. El contexto de previsualización incluye el reloj y lugar de la sesión; quien invoca puede aportar condiciones, tiempo disponible y destinatario.

La salida de la previsualización **no modifica la partida**: no consume recursos, no mueve PNJ, no avanza el reloj ni crea eventos. Esta separación es deliberada; primero se valida la selección; después se conectará a un ejecutor transaccional con evidencia e idempotencia. Tampoco se han precargado rasgos, necesidades, traumas, emociones ni metas de Brina, Maelis o Sera. Sus perfiles empiezan sin datos y requieren configuración o evidencia real.

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
