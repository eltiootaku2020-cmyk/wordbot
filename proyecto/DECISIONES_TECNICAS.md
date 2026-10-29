# Decisiones técnicas — gestor local v0.1

Estado: decisiones provisionales informadas por la investigación. No equivalen a código implementado.

## ADR-001 — La base local es la fuente de verdad

**Decisión:** SQLite conserva todo estado confirmado. La IA no puede escribir directamente en la base. Devuelve un contrato estructurado; el validador local decide qué operaciones se aplican.

**Motivo:** una salida de IA puede ser sintácticamente válida pero narrativamente incorrecta. El estado oficial necesita integridad, historial y reversión.

## ADR-002 — Cliente web local, no extracción del chat de consumo

**Decisión:** el primer prototipo tendrá una interfaz ligera abierta en Chromium en una dirección de loopback local, por ejemplo `http://127.0.0.1:8000`. No automatizará la lectura o extracción de respuestas desde la pestaña de ChatGPT de consumo.

**Motivo:** las condiciones de OpenAI para ChatGPT de consumo prohíben extracción programática de datos o respuestas; la API es una vía distinta. Véase [investigación y fuentes](INVESTIGACION_REFERENCIAS.md).

**Alternativa evaluable:** una extensión local para SillyTavern, que ya ofrece chat de rol, lorebooks y proveedores, si la construcción de una interfaz propia se vuelve el mayor obstáculo. Debe evaluarse la licencia AGPL-3.0 y la compatibilidad de la extensión antes de distribuirla.

## ADR-003 — Stack del primer prototipo

- Backend: Python + FastAPI.
- Frontend: HTML/CSS/JavaScript ligero; sin un framework grande en la primera versión.
- Persistencia: SQLite.
- Validación: modelos de datos de Python con tipos estrictos; contrato JSON Schema compartido con el proveedor.
- IA: adaptadores intercambiables para las APIs oficiales de OpenAI y Gemini.
- Distribución inicial: ejecutar localmente y abrir la URL en Chromium; empaquetado de escritorio solo después de validar el flujo.

**Motivo:** mantiene el uso de memoria local bajo, permite usar modelos remotos y deja el navegador como interfaz sin extraer datos de páginas ajenas. No requiere una GPU potente para inferencia local porque no ejecuta el modelo en la PC.

## ADR-004 — Contexto selectivo en lugar de Lorebook completa

Cada turno carga:
1. reglas fundamentales;
2. estado actual;
3. fichas de entidades presentes o aludidas;
4. Lorebook activada por nombre/palabra clave;
5. mensajes/eventos recientes y recuerdos recuperados por relevancia;
6. reglas específicas de la acción (inventario, viaje, magia, Eco).

La selección tiene presupuesto de tokens configurable. Nunca se envía la base de datos completa por defecto.

## ADR-005 — Estado tabular + registro de eventos, sin grafo obligatorio

**Decisión:** empezar con tablas SQLite para mundos, partidas, entidades, Lorebook, mensajes, eventos, cambios de estado, inventario, relaciones, usos de habilidades y snapshots.

Cada cambio conserva causa, fuente, estado de validación y valores anterior/propuesto/aceptado. Los mensajes son el archivo completo; el resumen actual no sustituye al historial.

**No incluir en v0.1:** Graphiti, Mem0, embeddings ni vector DB como dependencia obligatoria. Se pueden evaluar más adelante para recuperar recuerdos narrativos antiguos, pero no deben decidir cantidades o reglas de canon.

## ADR-006 — Salida estructurada más validación semántica

El proveedor debe producir la narración y los cambios en campos separados. Se usará el subconjunto común de JSON Schema compatible con ambos proveedores. Después:
- validar estructura y tipos;
- validar IDs y reglas de mundo;
- asociar cambios a eventos;
- rechazar claves/operaciones desconocidas;
- pedir aprobación para cambios irreversibles o ambiguos;
- aplicar cambios válidos en una transacción;
- almacenar un ID idempotente generado por el programa para no repetir cambios al reintentar.

## ADR-007 — Historial recuperable y backups

- Guardar mensajes originales y narración final.
- Guardar cada acontecimiento y cambio aceptado/rechazado/pendiente.
- Crear snapshots automáticos y copias de seguridad exportables.
- Usar transacciones SQLite y mecanismo de backup consistente con WAL.
- Permitir restaurar una partida sin cambiar el canon del mundo.

## ADR-008 — Claves API y control de gasto

- Las claves no se guardan en Git ni en el JSON de exportación del mundo.
- Mostrar qué proveedor/modelo se usa.
- Añadir límites configurables de respuesta y contexto; registro de consumo informado por el proveedor cuando esté disponible.
- Avisar antes de usar un proveedor cuya API requiere facturación.
- No asumir que ChatGPT Plus incluye consumo de la API de OpenAI.
- Revisar las políticas y tarifas oficiales antes de habilitar cada proveedor.

## Criterio para reconsiderar decisiones

Reevaluar tras el primer slice funcional: un mensaje, contexto recuperado, respuesta JSON, validación, guardado y reinicio. Si la interfaz propia retrasa excesivamente la validación de canon, hacer una prueba comparativa con una extensión de SillyTavern sin cambiar el modelo de datos.


## ADR-009 — Una llamada principal por turno; mantenimiento de fondo solo como ayuda

**Decisión:** el turno interactivo devuelve narración, eventos y cambios propuestos en un único contrato estructurado. Tareas secundarias (resumen histórico, indexación de conversación o sugerencias de organización) pueden ejecutarse después y nunca escribir el estado oficial sin validación.

**Motivo:** los proyectos como Openovel muestran el valor de separar narración y mantenimiento, pero varios agentes autónomos en cada turno aumentan latencia, coste y riesgo de conflicto. Primero necesitamos determinismo y recuperación fiables.

## ADR-010 — Alcance de conocimiento por mensaje y acontecimiento

**Decisión:** cada evento conserva testigos/fuente y cada mensaje debe poder indicar destinatario, audiencia o alcance (público, grupo, privado). El constructor de contexto filtra los recuerdos por lo que el PNJ seleccionado vio, escuchó o recibió de una fuente conocida.

**Motivo:** una conversación privada con Maelis no puede aparecer en el contexto de Ivar solo porque ambos estén en la misma partida. La ficha global de un personaje no es equivalente a lo que ese personaje sabe. Esta corrección tiene prioridad crítica antes de ampliar el uso con grupos.

## ADR-011 — Política de riesgo para aplicar cambios

**Decisión provisional:**

- **Automático si la evidencia es clara:** registrar mensajes/eventos confirmados; tiempo corto propuesto dentro del límite configurado; cambios pequeños de relación cuando existe valor inicial; acciones de inventario ordinario cuando la narración contiene un evento fuente válido, cantidad y objeto existente/registrable; movimiento de PNJ si destino, entidad y causa están confirmados.
- **Pendiente de aprobación:** cambio permanente de canon; muerte/revelación importante; poder nuevo; objeto único/mágico; gasto irreversible ambiguo; cambio de relación grande o sin valor inicial; cualquier operación en conflicto con el estado; movimiento o decisión del protagonista no indicado por el usuario.
- El programa nunca acepta un cambio solo porque el JSON sea válido; comprueba la causa, IDs, límites, conocimientos y estado anterior.

Los umbrales concretos son configurables por mundo y se ajustan tras las pruebas. No eliminar la opción de aprobación manual.

## ADR-012 — Revertir regeneraciones sin duplicar efectos

Antes de permitir editar, borrar o regenerar una respuesta, conservar un snapshot o registro de todas las operaciones aplicadas por el turno. Si el turno se reemplaza, revertir solo sus efectos y volver a calcular el estado desde la última secuencia confirmada. Cada operación debe tener clave idempotente; un reintento de red no puede descontar recursos dos veces.

## ADR-013 — Inspección del contexto y recuperación de Lorebook

Cada turno debe poder mostrar una vista de diagnóstico: reglas base, entidades incluidas, fichas activadas y motivo, mensajes/eventos considerados visibles, presupuesto estimado y entradas descartadas por límite. Usar activación por nombres/frases con fronteras de palabra cuando convenga y prioridades/presupuesto explícitos; los activadores tipo fragmento deben ser declarados deliberadamente.

**Motivo:** clientes como SillyTavern usan claves, profundidad de búsqueda y presupuesto, y su documentación recuerda que una Lorebook solo orienta la respuesta. La inspección es necesaria para detectar por qué un dato no se incluyó o se filtró.

## ADR-014 — Clasificar memoria en lugar de confundir inferencia con canon

Todo elemento de memoria tendrá una clase y procedencia: canon aprobado, hecho confirmado de la partida, observación, rumor, hipótesis/propuesta, o inferencia revisable. Las inferencias no se promueven automáticamente a canon. Se registra quién conoce cada hecho o la fuente de transmisión.

**Motivo:** adapta la separación de memoria efímera, revisable y canónica que muestran proyectos como Chronicler sin importar su motor de memoria adicional.

### Implementación inicial ADR-010 — alcance de conocimiento

Implementación inicial en la rama organizada y prueba aislada en commit `456ac5a1bc2694fb74725bcd13df4573677fe697`.

- Campo de turno `visibility`: `scene` o `private`.
- `audience_ids` se guarda en metadatos; un turno privado exige destinatario.
- Recuperación limita participantes privados y filtra mensajes/eventos por audiencia, destinatario y testigos; eventos pendientes no se proporcionan como hechos.
- Testigos fuera de audiencia no se guardan como testigos confirmados; el narrador simulado respeta el alcance privado.
- CI: 26 pruebas aprobadas y JavaScript validado: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40867432602

**Pendiente para completar ADR-010:** inspector de por qué un recuerdo es visible, pruebas con personajes que entran/salen de escena y pruebas manuales con OpenAI/Gemini. Los registros previos sin metadatos requieren tratamiento conservador.


## ADR-015 — Libro de recursos y transacciones de compra

**Decisión:** cada partida puede guardar recursos numéricos en SQLite (por ejemplo monedas, fichas o cargas), separados del inventario de objetos. La IA solo propone una adquisición con coste total y clave de moneda; el programa consulta saldo, verifica que existe el evento fuente, valida que el coste esté explícito y que el saldo alcance. Solo entonces descuenta recurso y añade el objeto dentro de la misma transacción SQLite.

**Reglas implementadas y límites:**
- Isekai sin Destino crea un saldo de monedas igual a cero, coherente con su inicio sin dinero.
- Un mundo/partida creada desde la interfaz puede definir recursos iniciales.
- Las compras necesitan coste positivo, moneda registrada y saldo suficiente. No se infieren precios ni se crea dinero para cubrir un faltante.
- El cobro de un artículo se registra como cambio de recurso asociado al evento de compra; el narrador no debe devolver además una segunda operación `spend` para la misma compra.
- Los ingresos/gastos genéricos requieren evento fuente de tipo `resource` y una señal explícita de ingreso o gasto; el saldo nunca puede ser negativo.
- El recurso y objeto se actualizan en el mismo turno/transacción; si la validación de compra falla, no se cambia ninguno.
- La operación y su valor anterior/propuesto/aceptado quedan en `state_changes`.

**Verificación:** CI con 32 pruebas Python y sintaxis de JavaScript aprobadas el 29-10-2026: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40877808136. Incluye compra con saldo suficiente, saldo insuficiente sin mutación, ingreso y gasto explícitos, y reintento de API sin cobro duplicado.

**Verificado con narrador simulado:** compra suficiente/insuficiente, ingresos/gastos explícitos y reintento del mismo request_id sin doble cargo. Pendiente: prueba manual en Windows y contrato con proveedor real.


## ADR-016 — Snapshot por turno y anulación segura

**Decisión:** antes de invocar al proveedor, guardar un snapshot local asociado a `session_id` y `turn_id`. La aplicación puede anular únicamente el último turno completado, restaurando reloj, ubicación, presencia, inventario, recursos, relaciones y usos de poderes. Los mensajes quedan marcados como anulados; eventos y cambios de estado se conservan con estado de rechazo e identificador de auditoría, sin entrar en el contexto activo.

**Regeneración:** el texto original vuelve al cuadro de entrada para poder editarse y enviarse como un nuevo turno. También está cubierto el reintento del mismo `request_id` tras el undo. El sistema rechaza anular un turno antiguo mientras haya turnos posteriores activos.

**Verificación:** CI con 32 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40877808136. Incluye restauración de compra/inventario/monedas/reloj, regeneración sin duplicados y rechazo de undo fuera de orden. La CI usa narrador simulado.

**Verificado por CI simulada:** incluye rollback de una relación y del contador de usos de Eco. Pendiente: pruebas manuales en Windows, campaña larga y restauración visual de copia SQLite.


## ADR-017 — Presupuesto Lorebook editable en la interfaz

**Decisión:** guardar la preferencia global `lore_budget_chars` en la tabla SQLite `app_settings`. El valor por defecto es 4.500; el usuario puede escoger entre 500 y 12.000 caracteres desde la interfaz. El máximo de ocho entradas sigue siendo una protección adicional.

**Aplicación:** el mismo ajuste se consulta al crear el contexto real para la IA y al previsualizarlo. El diagnóstico informa el presupuesto configurado, caracteres usados y fichas omitidas. Los caracteres no equivalen a un conteo exacto de tokens.

**Validación:** la API rechaza valores fuera de rango; la preferencia se conserva en SQLite. CI: 32 pruebas Python más sintaxis JavaScript, https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40877808136.

**Pendiente:** medir tokens reales por proveedor y probar la interfaz manualmente en Windows.


## ADR-018 — Chat web normal mediante puente manual

**Necesidad corregida:** «usar ChatGPT o Gemini» puede significar el chat web de una cuenta normal y no una API de desarrollador. Las dos modalidades deben mostrarse con nombres claros y no confundirse en la interfaz.

**Decisión:** mantener la API oficial como opción avanzada, pero incorporar «ChatGPT web (mi cuenta, manual)» y «Gemini web (mi cuenta, manual)» como alternativas sin clave API. El flujo prepara un prompt local con el contexto seleccionado y contrato JSON; la persona lo pega en la web del proveedor y pega la respuesta completa de vuelta. El servidor local valida el JSON, después ejecuta las mismas validaciones de entidades, eventos, alcance, inventario y recursos, y solo entonces guarda el estado.

**Por qué no se automatiza la pestaña web:** hay repositorios comunitarios que lo hacen con Playwright/CDP, pero dependen de selectores/interfaz cambiantes. Además, las condiciones de OpenAI prohíben extraer respuestas automáticamente o de forma programática desde sus servicios de consumo. Google también limita el acceso automatizado que infrinja sus instrucciones legibles por máquina. No se dependerá de esos puentes experimentales para la entrega inicial.

**Privacidad y límites:** el prompt puede contener fichas y mensajes de la partida; la interfaz advierte al usuario que lo revise antes de copiarlo. El programa no lee la sesión web, no solicita credenciales y no realiza llamadas de red a ChatGPT/Gemini en este modo. La respuesta se vuelve a validar localmente. No se obtiene telemetría exacta del uso/cupo web, por lo que no se promete un contador de tokens o coste.

**Estado de implementación:** selector, endpoint `/api/sessions/{session_id}/manual-prompt`, generación del prompt con esquema, parseo de la respuesta pegada y panel de copiar/pegar están implementados. CI en https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40880074124: 35 pruebas y sintaxis JS aprobadas.

**Pendiente:** uso manual real en Windows con ambos sitios; verificar que el proveedor web devuelva el objeto JSON completo; prueba de 50–100 turnos con reinicio/restauración. No automatizar el scraping del chat de consumo como atajo.
