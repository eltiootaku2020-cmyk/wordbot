# Investigación de referencias: memoria de rol, Lorebooks y persistencia

**Consultada:** 29 de octubre de 2026.  
**Propósito:** comparar proyectos existentes para diseñar el gestor local de canon, sin copiar ni importar código de terceros. Los repositorios y sus licencias pueden cambiar; comprobarlas de nuevo antes de reutilizar código.

## Conclusión ejecutiva

El mejor diseño para este proyecto combina cuatro ideas ya usadas en software existente:

1. **Recuperación selectiva del contexto**, como World Info/Lorebook en clientes de roleplay.
2. **Estado y eventos persistentes**, separado del prompt de la IA.
3. **Respuesta estructurada**, usando JSON Schema cuando el proveedor lo admita.
4. **Validación local, transacciones y copias de seguridad**, para que una salida verosímil de la IA no pueda reescribir el canon por sí sola.

No conviene adoptar como dependencia principal un sistema complejo de memoria semántica o un grafo temporal antes de que el prototipo básico supere las pruebas de continuidad.

## Proyectos de roleplay revisados

### 1. SillyTavern

Repositorio: https://github.com/SillyTavern/SillyTavern  
Documentación de World Info: https://docs.sillytavern.app/usage/worldinfo/  
Documentación de extensiones: https://docs.sillytavern.app/for-contributors/writing-extensions/  
Licencia declarada: AGPL-3.0.

Qué aporta:
- Interfaz local de chat para modelos remotos o locales.
- Character cards, chats grupales y World Info/Lorebook.
- Inserción dinámica de entradas mediante palabras clave.
- Extensiones que pueden interactuar con datos del chat y eventos de la interfaz.
- Implementación existente que evita tener que inventar desde cero cada función de un cliente de roleplay.

Límites para este proyecto:
- La propia documentación indica que insertar World Info no garantiza que el modelo respete o reproduzca esa información.
- Un cambio de versión puede exigir ajustar una extensión.
- La licencia AGPL debe revisarse si se decide construir y distribuir un producto derivado o integrado estrechamente.

Uso recomendado: referencia principal para el flujo de roleplay, recuperación por palabras clave, chats grupales y diseño de extensiones. Mantener como alternativa un complemento para SillyTavern si se desea reutilizar su interfaz; no copiar código sin revisar las obligaciones de la licencia.

### 2. RisuAI

Repositorio: https://github.com/kwaroran/RisuAI  
Guía Lorebook: https://github.com/kwaroran/RisuAI/wiki/Lorebook  
Licencia declarada: GPL-3.0.

Qué aporta:
- Cliente de roleplay multiplataforma.
- Varios proveedores, chats con varios personajes y Lorebook.
- Opciones de memoria de largo plazo y personalización del orden de prompts.

Uso recomendado: referencia de funciones y experiencia de usuario. No es necesario reutilizar su código para el primer prototipo.

### 3. Agnai

Repositorio: https://github.com/agnaistic/agnai  
Licencia declarada: AGPL-3.0.

Qué aporta:
- Conversaciones con múltiples bots y usuarios.
- Abstracción de varios proveedores.
- Lorebooks y funciones adicionales de memoria.

Límites para el primer prototipo:
- Está diseñado también para despliegues multiusuario y una arquitectura más amplia.
- MongoDB y Redis son opcionales en algunos modos, pero esa arquitectura no es necesaria para una aplicación personal en una sola PC.

Uso recomendado: referencia para seleccionar proveedores y manejar escenas con múltiples personajes; no como base inicial.

## Sistemas de memoria y persistencia revisados

### 4. LangGraph y su checkpointer SQLite

Documentación de persistencia: https://docs.langchain.com/oss/python/langgraph/persistence  
Implementación SQLite: https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite

Qué aporta:
- Diferencia entre estado corto de un hilo y datos que deben persistir entre hilos.
- Checkpoints para reanudar una ejecución y recuperar estado después de una interrupción.
- Implementación respaldada por SQLite para desarrollo local y cargas ligeras.

Decisión: adoptar la distinción conceptual entre checkpoint de partida y conocimiento persistente. No introducir LangGraph como dependencia obligatoria hasta que el flujo real demuestre que se necesita un motor de agentes.

### 5. Mem0

Repositorio: https://github.com/mem0ai/mem0  
Documentación: https://docs.mem0.ai/

Qué aporta:
- Capa de recuperación y almacenamiento de recuerdos para aplicaciones de IA.
- Búsqueda de memorias relevantes en lugar de adjuntar todo el historial a cada solicitud.

Límites:
- Puede necesitar modelos de embeddings, un LLM u otros servicios según el modo de uso.
- La recuperación semántica no es la autoridad adecuada para cantidades exactas, gasto de recursos, usos de habilidades o reglas de canon.

Decisión: considerar más adelante para buscar hechos narrativos antiguos. Nunca utilizar Mem0 como sustituto de la base estructurada de la partida.

### 6. Graphiti

Repositorio: https://github.com/getzep/graphiti  
Documentación: https://help.getzep.com/graphiti

Qué aporta:
- Grafo temporal de entidades y relaciones.
- Hechos con procedencia y ventanas temporales que permiten distinguir estado actual y anterior.
- Recuperación basada en entidades y relaciones.

Límites:
- Añade complejidad y dependencias de grafo innecesarias para una primera versión local.
- La lógica de qué se convierte en canon seguiría necesitando validación.

Decisión: tomar como referencia la procedencia, temporalidad e historial de relaciones. Mantener tablas SQLite y un registro de eventos hasta que el volumen demuestre que un grafo es necesario.

## APIs de IA y formato estructurado

### 7. OpenAI Structured Outputs

Documentación: https://developers.openai.com/api/docs/guides/structured-outputs

Permite solicitar respuestas conformes a un esquema JSON en modelos y endpoints compatibles. La documentación recomienda Structured Outputs sobre el modo JSON simple cuando esté disponible. El esquema tiene un subconjunto admitido, por lo que debe verificarse con el modelo elegido.

### 8. Gemini Structured Output

Documentación: https://ai.google.dev/gemini-api/docs/structured-output

Gemini también puede generar respuestas según JSON Schema. La documentación advierte que un resultado estructuralmente válido aún requiere validación semántica en la aplicación.

Decisión común:
- Definir un contrato pequeño compartido por ambos adaptadores.
- Mantener el JSON Schema en una sola fuente y adaptar sus restricciones a cada proveedor.
- Validar localmente tanto la estructura como las reglas del mundo.
- Rechazar claves desconocidas y operaciones no permitidas.
- Registrar fallos del modelo sin mutar el estado.

## Persistencia SQLite

Transacciones: https://www.sqlite.org/lang_transaction.html  
Write-Ahead Logging: https://www.sqlite.org/wal.html  
Copia de seguridad en línea: https://www.sqlite.org/backup.html

Qué aporta:
- Transacciones con COMMIT/ROLLBACK para aplicar un turno como unidad coherente.
- WAL permite que lectores y escritor convivan en un mismo equipo; SQLite sigue teniendo un único escritor activo a la vez.
- La API de copia de seguridad en línea puede generar una instantánea consistente de una base activa.

Decisión:
- Cada turno validado se aplica en una transacción.
- Los reintentos no duplican costes ni cambios; cada turno recibe una clave de idempotencia generada por la aplicación.
- Para respaldar la base mientras está abierta, usar el mecanismo de backup de SQLite, no copiar solo el archivo principal a ciegas si se usa WAL.
- Realizar restauraciones en una copia o después de comprobar el archivo de respaldo.

## Integración, privacidad y coste

### No extraer automáticamente la respuesta desde la página de ChatGPT

Condiciones de uso de OpenAI vigentes desde el 1 de enero de 2026: https://openai.com/policies/row-terms-of-use/

Las condiciones para el servicio de ChatGPT de consumo prohíben la extracción automática o programática de datos o respuestas. Por tanto, el diseño no debe leer el DOM, extraer respuestas ni automatizar la pestaña de ChatGPT de consumo para obtenerlas. El camino compatible es una API oficial o un cliente que tenga una integración admitida.

### La API se factura por separado

Ayuda oficial: https://help.openai.com/en/articles/9039756-managing-billing-settings-on-the-chatgpt-web-and-api-platform

La suscripción normal de ChatGPT y el uso de la plataforma API tienen sistemas de facturación separados. Antes de usar un proveedor hay que verificar sus modelos, políticas y precios vigentes. El programa no debe asumir que una suscripción de chat incluye llamadas API.

### Medidas de privacidad previstas

- Los mundos, chats, inventario, relaciones y guardados se almacenan localmente.
- Al proveedor se envía solo el contexto requerido para el turno; nunca la base de datos completa.
- Las claves API se guardan fuera del repositorio, preferentemente en un almacén seguro del sistema.
- La interfaz muestra proveedor/modelo activo, consumo cuando sea posible y errores de conexión.
- No se habilita un endpoint público por defecto; la aplicación escucha solo en loopback local.
- Exportar/importar datos permite hacer copias propias sin depender del servicio de IA.

## Decisión provisional derivada de la investigación

Para v0.1 se recomienda una **aplicación web local pequeña**: interfaz abierta en Chromium, backend Python/FastAPI, SQLite y una capa de proveedor intercambiable para API oficial de OpenAI y Gemini. FastAPI puede exponer la interfaz local y endpoints JSON con esquemas OpenAPI: https://fastapi.tiangolo.com/tutorial/first-steps/

Esta elección evita atar el canon a la ventana de un chat de consumo y permite validar cada cambio antes de guardarlo. SillyTavern queda como alternativa si resulta preferible reutilizar una interfaz de roleplay existente. La decisión se revisará tras una prueba técnica mínima y no implica que la aplicación ya esté construida.

## Referencias consultadas

- SillyTavern: https://github.com/SillyTavern/SillyTavern
- SillyTavern World Info: https://docs.sillytavern.app/usage/worldinfo/
- SillyTavern UI Extensions: https://docs.sillytavern.app/for-contributors/writing-extensions/
- RisuAI: https://github.com/kwaroran/RisuAI
- Agnai: https://github.com/agnaistic/agnai
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph SQLite checkpoint: https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite
- Mem0: https://github.com/mem0ai/mem0
- Graphiti: https://github.com/getzep/graphiti
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Gemini Structured Output: https://ai.google.dev/gemini-api/docs/structured-output
- FastAPI: https://fastapi.tiangolo.com/tutorial/first-steps/
- SQLite transactions: https://www.sqlite.org/lang_transaction.html
- SQLite WAL: https://www.sqlite.org/wal.html
- SQLite backup API: https://www.sqlite.org/backup.html
- OpenAI Terms of Use: https://openai.com/policies/row-terms-of-use/
- OpenAI API billing: https://help.openai.com/en/articles/9039756-managing-billing-settings-on-the-chatgpt-web-and-api-platform


---

## Segunda ronda de investigación — proyectos muy cercanos al objetivo

**Actualizado:** 29 de octubre de 2026. Esta ronda compara implementaciones públicas y además inspecciona el código actual del prototipo. Las referencias son diseños para estudiar, no dependencias que debamos instalar automáticamente.

### 9. Openovel — narración en primer plano y mantenimiento de historia en segundo plano

Repositorio: https://github.com/Feed-Scription/openovel  
Licencia que declara el repositorio: Apache-2.0. Confirmar el archivo LICENSE de la versión exacta antes de reutilizar código.

Openovel separa el ciclo de narración visible de un proceso de mantenimiento que actualiza archivos de historia. El estado narrativo se guarda en archivos simples en vez de depender obligatoriamente de una base vectorial. Es la semejanza conceptual más directa con la idea del usuario: la IA narra; otro componente conserva la continuidad.

**Qué adoptar:** separación entre respuesta visible y mantenimiento del estado, contexto selectivo y datos de historia legibles por humanos.

**Qué no copiar en v0.1:** un conjunto de agentes de fondo que puedan cambiar canon de forma autónoma. Primero validar el turno en una sola llamada estructurada y aplicar sus propuestas localmente. La documentación actual etiqueta el proyecto como beta/demo y señala que el nivel de prueba varía entre sistemas operativos; no asumir que está listo para nuestro Windows.

### 10. Chronicler — niveles de memoria y visibilidad de secretos

Repositorio: https://github.com/yantrikos/chronicler  
El repositorio describe tres niveles: memoria efímera, inferencias revisables y canon duradero, más controles de visibilidad por memoria para evitar que un personaje conozca secretos que no le contaron. Licencia declarada: MIT; verificar la licencia del commit elegido antes de reutilizar código.

**Qué adoptar:** etiquetar cada elemento como canon, hecho de partida, observación, rumor, hipótesis o propuesta; registrar quién lo sabe y de dónde salió; permitir revisar/corregir memorias inferidas.

**Qué no adoptar todavía:** su sistema de memoria cognitiva y la infraestructura adicional. Nuestro registro local estructurado tiene que seguir siendo la autoridad para inventario, cantidades, reloj, estados y usos de poderes.

### 11. RPG Tracker para SillyTavern — estado RPG y reversión

Repositorio: https://github.com/Soyo5800/rpg-tracker-for-sillytavern

El README lo califica como experimental. Rastrea estadísticas, fichas, inventarios, misiones, relaciones y estado del mundo, y documenta snapshots para volver atrás cuando se cambia o elimina una respuesta. Es una referencia funcional para el panel de estado y las consecuencias de regenerar mensajes.

**Qué adoptar:** snapshot antes/después del turno, reversión de operaciones y pruebas de edición/regeneración. No reutilizar código sin comprobar primero licencia y avisos del repositorio.

### 12. Open Dungeon — juego narrativo local y corrección de escenas

Repositorio: https://github.com/newideas99/open-dungeon  
El proyecto describe una aplicación de roleplay local con SQLite, archivos locales, controles Do/Say/Story, reintentar, borrar y editar pasajes, y resumen progresivo del historial. Declara licencia MIT; confirmar los componentes/recursos concretos antes de incorporarlos.

**Qué adoptar:** controles explícitos para editar/reintentar escenas y almacenamiento local. Su resumen histórico puede ayudar a recuperar mensajes antiguos, pero no reemplaza tablas y eventos para datos exactos como los usos de Eco.

### 13. Gamentic — pruebas en el límite del proveedor

Repositorio: https://github.com/hec-ovi/gamentic

El proyecto publica una arquitectura FastAPI + SQLite + interfaz web ligera y pruebas que simulan el modelo en el límite del servicio para que la base y la lógica puedan evaluarse sin llamadas de IA. Su objetivo de hardware/modelo local es diferente al nuestro; no hace falta traer su requisito de GPU, generación de imágenes o agentes por personaje.

**Qué adoptar:** probar validadores, persistencia, conflictos y recuperación con respuestas simuladas; reservar las llamadas reales para pruebas de integración separadas.

### 14. SillyTavern, RisuAI y la activación de Lorebook

- SillyTavern: https://github.com/SillyTavern/SillyTavern
- World Info / Lorebook: https://docs.sillytavern.app/usage/worldinfo/
- RisuAI: https://github.com/risuai/RisuAI

La documentación de World Info describe activación por claves, presupuesto de contexto, profundidad de búsqueda y contenido conciso. Advierte que insertar una ficha ayuda a orientar el modelo, pero no garantiza que obedezca el lore. Esto respalda la separación entre recuperar lore y validar hechos.

**Qué adoptar:** presupuesto explícito, prioridad de fichas, historial de activación y una pantalla que muestre qué datos se enviaron al modelo. Una coincidencia parcial de texto no debe ser la única forma de decidir qué información recibe un personaje.

### 15. OpenAI y Gemini — salida estructurada no es verdad semántica

- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Gemini Structured Output: https://ai.google.dev/gemini-api/docs/structured-output

Ambos proveedores permiten restringir la salida a un esquema JSON compatible. Esto reduce errores de formato, pero no prueba que el efecto narrativo propuesto sea verdadero ni que respete el canon. El validador local sigue siendo obligatorio; el subconjunto exacto de JSON Schema se debe probar con el modelo/API elegido.

### 16. Qué reveló la inspección del prototipo actual

El código actual de `proyecto/app/src/canon_manager/main.py` ya recupera un contexto reducido, registra los turnos y conserva participantes, relaciones, inventario, Lorebook y usos de Eco. La inspección identifica cuatro tareas concretas antes de llamarlo fiable:

1. **Conocimiento privado de PNJ — prioridad crítica.** El constructor de contexto recupera los últimos mensajes de toda la partida sin filtrar por destinatario, y recupera eventos recientes sin aplicar un filtro de testigos. En una escena privada, Maelis podría recibir contexto de una conversación ajena, o Ivar podría recibir información que nunca presenció. Se debe añadir alcance de conocimiento por evento/mensaje y filtrar por destinatario, testigos o información que alguien le haya contado.
2. **Cambios cotidianos que hoy siempre quedan pendientes.** Los movimientos y operaciones de inventario se marcan para revisión en esta versión. Es prudente para evitar errores, pero no cumple el objetivo final de actualizar automáticamente cambios claros. Se necesita una política de riesgo: operaciones sencillas con evento fuente, IDs válidos, cantidad y causa verificables pueden autoaplicarse; cambios ambiguos o de alto impacto quedan pendientes.
3. **Activación de lore.** El prototipo busca claves por subcadena dentro de mensaje, lugar y nombres, y detiene la selección a 12 entradas. Conviene usar coincidencia de frase/palabra configurable, calcular prioridad/coste, mostrar el motivo de activación y aplicar un presupuesto de contexto; mantener una opción para claves expresamente diseñadas como fragmentos.
4. **Editar/regenerar una respuesta.** Hay idempotencia del mismo request ID, pero el plan de fiabilidad debe probar snapshots y reversión de los cambios derivados si se edita/borrra/regenera un mensaje. No se deben acumular efectos duplicados.

Son hallazgos de revisión del código, no defectos confirmados en una partida real. Requieren pruebas reproducibles y correcciones antes de dar la versión por validada.

## Decisión resultante de la segunda ronda

Mantener el prototipo ligero actual: FastAPI + interfaz en Chromium + SQLite + un turno estructurado por llamada. Añadir primero seguridad de conocimiento, política de aplicación de cambios y reversión. Dejar Mem0, Graphiti, memoria de embeddings, bucles multiagente y generación de imágenes como opciones futuras, solo si las pruebas muestran que el registro estructurado y la recuperación selectiva no bastan.

El programa seguirá sin extraer respuestas de la pestaña de ChatGPT de consumo. Los proveedores remotos se conectarán por APIs oficiales; la UI y los datos persistentes seguirán locales.