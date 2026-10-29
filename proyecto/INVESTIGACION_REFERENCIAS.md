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
