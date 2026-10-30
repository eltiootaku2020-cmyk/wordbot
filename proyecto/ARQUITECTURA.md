# Arquitectura del gestor local

## 1. Autoridad de datos

El programa local es la fuente de verdad para el estado de la partida. La IA no mantiene ni sustituye esa base de datos: recibe el contexto mínimo, devuelve una narración y propone acontecimientos/cambios. El validador decide qué propuestas se aceptan.

Orden de autoridad:

1. Reglas y canon aprobado del mundo.
2. Acciones explícitas del usuario y hechos de partida previamente aceptados.
3. Último estado persistido y registro de eventos.
4. Lorebook aplicable a la escena.
5. Propuestas nuevas de la IA, pendientes de validación.
6. Improvisación narrativa que no contradiga las capas anteriores.

Un rumor no se promueve a hecho confirmado sin evidencia. Una posibilidad en la Lorebook no significa que haya sucedido. La IA no puede reescribir el canon fijo mediante una respuesta de diálogo.

## 2. Ciclo de turno

### A. Entrada

La interfaz guarda el texto original del usuario y los metadatos que conozca: mundo, partida, protagonista, destinatario opcional y momento actual. El programa no debe cambiar el texto original.

### B. Recuperación de contexto

El constructor de contexto selecciona solo:

- Reglas generales prioritarias.
- Ubicación, hora, clima/panorama y escena actuales.
- Personajes presentes y sus fichas relevantes.
- Relación entre interlocutores y eventos recientes de esa relación.
- Reglas/poderes relevantes para la acción actual.
- Entradas de Lorebook activadas por palabras clave o por las entidades/lugares presentes.
- Inventario o recursos si la acción los afecta.
- Últimos mensajes necesarios para mantener tono y continuidad.
- Acontecimientos ancla cercanos, sin revelar al protagonista información que desconoce.

Debe existir un límite de contexto configurable. Si el contenido excede el presupuesto, se priorizan reglas, estado actual y fichas de participantes; las entradas menos relevantes se omiten. No se concatena toda la Lorebook por defecto.

### C. Generación

El proveedor recibe instrucciones concisas y el mensaje actual. Se pide una respuesta con dos zonas separadas:

- `narracion`: texto natural que se muestra al usuario.
- `cambios_propuestos`: acontecimientos y modificaciones estructuradas para validar.

La IA no debe incluir bloques de guardado extensos en el diálogo narrativo. El contrato está documentado en [CONTRATO_RESPUESTA_IA.md](CONTRATO_RESPUESTA_IA.md).

### D. Validación

Antes de escribir el estado:

- Validar el JSON, campos obligatorios, tipos e identificadores.
- Confirmar que los personajes/lugares/objetos existan o que la creación local esté permitida.
- Verificar que la IA no decida acciones, palabras, pensamientos ni emociones del protagonista.
- Verificar cronología, desplazamientos, distancias, objetos, recursos, poderes y límites de uso.
- Confirmar que cada cambio incluye motivo y referencia al acontecimiento que lo justifica.
- Rechazar o marcar como pendiente cualquier cambio que contradiga canon, no tenga evidencia o exceda los permisos.
- No aceptar cambios numéricos de relación sin motivo narrativo suficiente.
- No aceptar recargas de Eco ni objetos/recursos aparecidos sin causa establecida.
- Las muertes, cambios permanentes de canon, nuevos poderes, giros irreversibles y cambios de alta repercusión pueden requerir aprobación del usuario según configuración.

### E. Aplicación atómica

Los cambios aceptados se escriben en una transacción de SQLite. Si falla la validación de una operación obligatoria, no se deja la mitad del estado aplicado. El registro conserva valores anteriores/nuevos para permitir auditoría y reversión.

El registro distingue:
- `accepted`: cambio aceptado y aplicado.
- `pending`: falta aprobación o evidencia.
- `rejected`: contradice una regla o no está permitido.
- `superseded`: una propuesta posterior sustituyó a otra pendiente.

### F. Presentación

La aplicación muestra la narración normal. Puede mostrar una notificación discreta y un panel de cambios, por ejemplo «Hora +1 min; Maelis: confianza −1; objetos: sin cambios». El mensaje técnico completo queda en el registro local, no en la conversación de rol.

## 3. Qué puede proponer la IA

- Diálogos y reacciones de PNJ según carácter y conocimientos.
- Acontecimientos observables de la escena.
- Duración aproximada de la acción.
- Movimiento de los PNJ y del entorno; no el movimiento elegido por el protagonista si el usuario no lo indicó.
- Cambios de relación con motivo narrativo explícito.
- Adquisición, uso, pérdida o transferencia de objetos cuando ocurra en la escena.
- Activaciones y efectos de poderes, con el coste correspondiente.
- Nuevas observaciones, rumores o hipótesis etiquetados como tales.

La IA no puede por sí sola:
- Cambiar una regla aprobada del mundo.
- inventar que el protagonista aceptó, compró, dijo o hizo algo.
- convertir una sospecha en culpabilidad confirmada.
- cambiar la cantidad de un objeto sin un acontecimiento que lo explique.
- restablecer usos de un poder limitado.
- revelar al protagonista un hecho que ningún personaje conoce sin una fuente narrativa.

## 4. Ejemplo de interacción

Entrada del usuario: «Hola, linda», dirigida a Maelis.

Contexto mínimo enviado: Maelis está presente; ficha de personalidad; relación actual; conversación anterior relevante; reloj y lugar; reglas de diálogo y relaciones. No se envían fichas de todos los personajes del mundo ni el Lorebook completo.

La IA podría narrar que Maelis se sorprende y responde que apenas conoce al protagonista. Puede proponer incomodidad o una impresión temporal. No debería decidir que existe atracción o rechazo permanente sin fundamento.

Si la escena justifica confianza −1, la propuesta debe incluir:
- ID de Maelis.
- campo exacto y valor anterior.
- delta propuesto.
- motivo.
- ID del evento narrativo que lo justifica.
- evidencia textual o descripción breve.

El validador comprueba si esa consecuencia encaja con la regla del mundo. Si la causa es ambigua, registra la reacción como hecho narrativo, pero deja el cambio numérico pendiente o sin modificar.

## 5. Modelo de relación

No existe una sola puntuación que defina toda relación. Las dimensiones son independientes: confianza, sospecha, amistad, respeto, rivalidad, resentimiento, miedo, gratitud/deuda, cooperación y atracción, si corresponde.

Los valores representan intensidad y deben tener causa e historial. La etiqueta «me considera atrevido» no es equivalente a una baja permanente de confianza. Una emoción o impresión puntual puede quedar como evento separado.

El valor `50` no se interpreta automáticamente como neutral universal. Cuando no hay evidencia suficiente, se usa `No registrado` y no un número inventado.

## 6. Tiempo y movimiento

La IA propone una duración estimada y los acontecimientos ocurridos. El programa aplica el reloj según reglas deterministas configuradas por el mundo. La duración explícita indicada por el usuario prevalece. Conversaciones breves no provocan saltos arbitrarios de horas.

El movimiento de un PNJ puede aceptarse si la acción es coherente con la escena. El protagonista solo se mueve conforme a la acción explícita del usuario o a un salto que este haya autorizado.

## 7. Errores y recuperación

Si la IA responde con JSON inválido, falta un ID o el resultado contradice el canon:
1. No aplicar cambios.
2. Guardar la respuesta fallida para diagnóstico.
3. Reintentar una sola vez con una corrección breve si es seguro.
4. Si sigue fallando, mostrar la narración solo si se puede separar sin ambigüedad; en caso contrario, mostrar un error y conservar el estado anterior.
5. Permitir al usuario editar o aprobar las propuestas pendientes.

El estado no se reconstruye a partir de la memoria del modelo si la base de datos contiene un registro válido.


## 8. Decisión técnica provisional basada en referencias

La comparación está documentada en [INVESTIGACION_REFERENCIAS.md](INVESTIGACION_REFERENCIAS.md) y las decisiones detalladas en [DECISIONES_TECNICAS.md](DECISIONES_TECNICAS.md).

### Base propuesta

- Interfaz web mínima abierta desde Chromium en una dirección local (loopback).
- Backend Python/FastAPI para endpoints de mensajes, mundos, sesiones y estado.
- SQLite como base local, con transacciones, historial de eventos y copias de seguridad.
- Adaptadores independientes para APIs oficiales de OpenAI y Gemini.
- Contrato JSON Schema compartido por proveedores, reducido al subconjunto compatible; validación semántica adicional dentro de la aplicación.
- Sin inferencia local obligatoria, sin grafo de conocimiento ni sistema de embeddings en la primera versión.

### Qué se toma de proyectos existentes

- **SillyTavern:** recuperación selectiva de Lorebook, fichas de personajes, chat grupal y extensibilidad.
- **RisuAI:** selección de proveedores, presentación del Lorebook y memoria de contexto.
- **Agnai:** ejemplos de proveedor intercambiable y escenas multi-PNJ.
- **LangGraph:** separación entre checkpoint del hilo y datos duraderos.
- **Mem0/Graphiti:** ideas futuras para recuperar hechos narrativos y mantener procedencia temporal, no fuente de verdad en v0.1.

La aplicación no reutilizará fragmentos de esos proyectos sin revisar licencias. SillyTavern declara AGPL-3.0, RisuAI GPL-3.0 y Agnai AGPL-3.0; el objetivo es implementar un diseño propio, usando la documentación como referencia.

### Integración permitida y coste

Se distinguen dos vías. **Modo manual (previsto para el uso normal):** Wordbot prepara el prompt y el usuario lo copia a ChatGPT/Gemini web; después pega la respuesta para validarla. No se automatizan el inicio de sesión, el envío a una pestaña autenticada ni la extracción del DOM. **Modo API (opcional):** el adaptador oficial hace la solicitud con su clave propia. La suscripción del chat web y la facturación/cuota de API son sistemas distintos. El modo manual no tiene contador de mensajes ni límite artificial impuesto por Wordbot: los límites del chat web siguen perteneciendo al proveedor. Solo se registra un turno cuando la respuesta pegada pasa el contrato y las validaciones locales.

### Decisiones de fiabilidad

- JSON válido no equivale a cambio correcto.
- El programa da los IDs definitivos a los turnos y operaciones; no confía en identificadores inventados por el modelo.
- Cada propuesta debe referenciar un evento de su mismo turno.
- Los cambios se aplican una vez y en una transacción.
- Ambigüedad, contradicción o cambio irreversible puede dejarse como pendiente.
- La base local se considera autoridad, nunca un resumen generado por IA.


## Actualización de implementación — 29-10-2026

El código actual incluye:
- Turnos con alcance `scene/private` y audiencia almacenada en metadatos.
- Contexto limitado por destinatario, ubicación, audiencia y testigos; la privacidad se aplica en recuperación, no solo por prompt.
- Inspector de contexto que presenta fichas Lorebook, activadores, límites y uso aproximado en caracteres sin llamar al modelo; explica motivos de inclusión/exclusión para mensajes y eventos.
- Presupuesto Lorebook editable (500–12.000 caracteres) en la interfaz y persistido en SQLite; se aplica al turno y la previsualización.
- Reglas automáticas para operaciones ordinarias de inventario y movimientos no protagonizados con evento fuente validado.
- Tabla `resources` por partida y adquisición de objeto con coste: saldo y artículo se actualizan en la transacción del turno.
- En el preset Isekai, monedas iniciales = 0.

CI aprobada: 38 pruebas Python y sintaxis JavaScript, https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40890138277. La prueba usa el narrador simulado. El undo del último turno restaura estado y deja auditoría; falta ampliar pruebas de rollback para relaciones/poderes, verificar el navegador en Windows, probar APIs reales y realizar campaña larga.


## 10. Registro persistente de conocimiento por entidad

El prototipo añade una capa persistente separada de la tabla de hechos:

- Cada evento registrado crea un registro `direct_observation` para cada testigo autorizado.
- Los registros guardan quién sabe algo, qué acontecimiento conoce, el evento de transmisión, el contenido y la procedencia.
- Un evento `testimony` o `rumor` necesita identificar al hablante (`source_entity_id)) y el acontecimiento al que se refiere (`about_event_id`).
- El hablante debe existir en el mundo, participar como testigo autorizado en la transmisión y tener un registro activo sobre el acontecimiento citado.
- El conocimiento recibido por los oyentes queda ligado tanto al evento de transmisión como al evento original. Un rumor transmitido otra vez sigue siendo rumor aunque el nuevo evento se etiquete como testimonio.
- Los registros se consideran activos solo mientras el evento de transmisión y el evento al que se refieren sigan registrados. Los eventos anulados/rechazados no se recuperan como conocimiento activo.
- El contexto narrativo incluye conocimiento del protagonista y, si corresponde, del PNJ destinatario. No incluye automáticamente el conocimiento privado de todos los presentes.
- El modelo no recibe la descripción del evento original cuando solo conoce un rumor; recibe la versión transmitida claramente etiquetada como rumor o testimonio.

La inicialización de SQLite crea la tabla e índices sin destruir partidas. Una migración idempotente reconstruye los registros de observación directa a partir de los testigos de eventos históricos registrados; ignora testigos inválidos y no transforma eventos antiguos de rumor/testimonio en observaciones directas.

### Límites de esta etapa

Esto resuelve almacenamiento y procedencia básica del conocimiento individual, pero no implementa aún fama por región/facción, una red autónoma de difusión, un sistema de evidencias físicas, identificación forense o atribución validada de delitos. Los testimonios y rumores deben proponerse mediante eventos; no se simula todavía que todo PNJ difunda información automáticamente.
