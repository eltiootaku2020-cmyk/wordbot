# Motor de conducta y decisiones de PNJ

**Estado:** primera base de puntuación determinista implementada; integración con persistencia y simulación autónoma todavía pendiente.  
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

Módulo: `proyecto/app/src/canon_manager/behavior_engine.py`.

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

El perfil es independiente para cada entidad. El motor no copia rasgos, emociones o relaciones entre personajes.

### Acciones y patrones de inicio

El catálogo genérico inicial aporta **29 acciones reutilizables** (observar, preguntar, escuchar, explicar, acercarse, mantener distancia, retirarse, ayudar, rechazar, negociar, proteger, descansar, comer, beber, dormir, practicar, estudiar, investigar, vigilar, rastrear, reparar, recolectar, viajar, esperar, compartir información, ocultarla, planificar, mediar y observar a la espera).

Incluye **22 patrones contextuales** de ejemplo, como evaluación cautelosa, curiosidad investigadora, protección, límites de independencia, cooperación, prioridad de evidencia, recuperación por cansancio, prioridad por hambre/sed, distancia por miedo, foco en amenaza y desescalada.

Son una biblioteca inicial, no miles de reglas escritas a mano. El catálogo está diseñado para crecer mediante combinaciones de acciones, requisitos, prioridades, rasgos, necesidades, emociones, objetivos y focos. Cada mundo puede aportar acciones y patrones especializados sin contaminar el motor común.

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

- guardar perfiles, emociones, focos y metas en SQLite por partida y entidad;
- editor de personalidad y catálogo de conducta en la interfaz;
- catálogo de acciones por mundo, con precondiciones y efectos verificables;
- ejecutor transaccional que aplique un resultado válido a posición, inventario, tiempo, relaciones y eventos;
- agenda y cola de actividades con duración, interrupciones y cancelaciones;
- simulación fuera de escena cuando realmente transcurre tiempo, sin avanzar el mundo por cada mensaje;
- encuentros entre PNJ, negociación, cooperación, conflicto y resolución con resultados persistentes;
- memoria y conocimiento usados como límites de decisión para impedir que un PNJ actúe con información que no posee;
- historial, snapshots, deshacer y recuperación de decisiones autónomas;
- panel para inspeccionar por qué un PNJ priorizó una acción y qué condiciones la hicieron posible.

La salida actual no modifica la partida. Esta separación es deliberada: primero se prueba la selección; después se conecta a un ejecutor con transacciones, evidencia e idempotencia.

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
