# Gestor local de canon — prototipo v0.1

**Estado de validación:** CI aprobó 38 pruebas Python y comprobación sintáctica JavaScript el 29-10-2026: [ver resultados](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40890138277). El modo manual de ChatGPT/Gemini web está cubierto por pruebas automatizadas; falta probar el intercambio real en Windows.

Esta carpeta contiene un primer prototipo ejecutable del flujo local: interfaz de chat en Chromium, base SQLite y narrador simulado por defecto. El proveedor simulado permite probar la persistencia sin clave ni coste. OpenAI y Gemini son opciones externas configurables.

## Requisitos

- Python 3.11 o posterior.
- Chromium o cualquier navegador moderno.
- No necesitas una clave API si usas ChatGPT/Gemini web en modo manual.
- Las claves API solo son necesarias para seleccionar explícitamente un proveedor API.

## Ejecutar en Windows

Abre PowerShell en esta carpeta y ejecuta cada comando por separado:

1. Crea el entorno: python -m venv .venv
2. Actívalo: .venv\Scripts\activate
3. Instala dependencias: pip install -r requirements.txt
4. Copia .env.example a .env.
5. Deja APP_PROVIDER=mock para la primera prueba.
6. Inicia: uvicorn canon_manager.main:app --app-dir src --host 127.0.0.1 --port 8000
7. Abre http://127.0.0.1:8000 en Chromium.

La base predeterminada se guarda en data/canon_manager.sqlite3 dentro de esta carpeta. Los datos locales y el archivo .env están excluidos de Git. La interfaz puede crear mundos desde cero o cargar «Isekai sin Destino v1.16» con un solo botón: importa el JSON real del repositorio, crea el reparto inicial y los cinco objetos, abre una sesión nueva y registra 0 monedas iniciales.

## Primera prueba

Pulsa «Cargar mundo de prueba» y selecciona Maelis como destinataria. Envía «Hola, linda». La respuesta simulada muestra una reacción posible de Maelis y una reacción del grupo. El programa guarda ambos mensajes y sus eventos. La confianza propuesta queda pendiente si no hay una puntuación inicial conocida; no inventa la base. Esta reacción de ejemplo no es canon obligatorio.

Después de reiniciar el servidor, carga el mismo mundo de prueba: los mensajes y el estado deben seguir presentes. El panel también permite importar un Lorebook JSON de formato SpicyChat, inspeccionar el contexto seleccionado sin llamar al modelo, consultar objetos por portador y ver los recursos locales. En mundos personalizados pueden definirse recursos iniciales. Para Isekai, la moneda comienza en 0: las compras solo se aplican si el evento lo confirma, el coste es positivo y el saldo alcanza.

## Usar ChatGPT o Gemini desde el chat web normal

No necesitas activar una API para utilizar el chat web normal de tu cuenta. En el selector superior elige **ChatGPT web (mi cuenta, manual)** o **Gemini web (mi cuenta, manual)**.

1. Escribe la acción o diálogo en la aplicación y pulsa **Preparar prompt**.
2. Pulsa **Copiar prompt** y abre el enlace del sitio elegido.
3. Pega el prompt en tu conversación normal de ChatGPT o Gemini y envíalo.
4. Copia la respuesta completa que devolvió el chat y pégala en **Respuesta completa del chat (JSON)**.
5. Pulsa **Validar y guardar turno**. El programa valida el contrato y las reglas de la partida antes de aplicar cambios.

Si el chat agrega explicaciones o devuelve un JSON incompleto, pídele que responda solo con el objeto JSON completo. El parser admite un bloque JSON entre triple comilla invertida, pero no acepta texto externo al objeto.

**Privacidad:** el prompt puede incluir estado, mensajes recientes, personajes y entradas Lorebook. Revísalo antes de copiarlo. La aplicación no inicia sesión por ti, no lee tu pestaña ni extrae la respuesta automáticamente. No pegues contraseñas ni claves API en el chat.

Este modo no realiza llamadas de red a OpenAI/Gemini desde el programa, por lo que no necesita claves API ni tiene contador propio de tokens o cupos del chat web. Puedes seguir conversando en esa misma sesión para pedir aclaraciones o corregir el JSON; Wordbot no cuenta esos mensajes ni impone un máximo artificial de intercambios. El proveedor web conserva sus límites propios. Wordbot solo valida y guarda la respuesta que pegues como turno.

## Proveedor API


- OpenAI API: configura APP_PROVIDER=openai, OPENAI_API_KEY y OPENAI_MODEL en .env.
- Gemini API: configura APP_PROVIDER=gemini, GEMINI_API_KEY y GEMINI_MODEL en .env.

Estas opciones son distintas de ChatGPT/Gemini web. La suscripción de chat no equivale a crédito API; usa estas opciones solo si quieres usar sus endpoints API.

Ambos adaptadores usan APIs oficiales y una respuesta estructurada. La aplicación valida la estructura y después verifica los cambios con su propio estado. El uso de API puede facturarse por separado de la suscripción de chat.

No pegues claves API en una conversación, en GitHub ni en una exportación de Lorebook.

## Alcance y limitaciones

Implementado en esta primera versión: interfaz local, base SQLite, importación de Lorebook JSON, recuperación de contexto por palabras clave, narrador simulado, adaptadores API iniciales, registro de mensajes/eventos, propuesta y aprobación/rechazo de cambios, reloj básico, historial de usos de Eco y copia de seguridad.

Todavía incompleto: validación exhaustiva de movimientos y acciones físicas, editor completo de mundos/entidades, restauración visual de copias, selección semántica avanzada, comprobación automática de todos los cambios de canon y prueba real con claves/modelos del usuario. Las propuestas de inventario y movimiento permanecen pendientes para revisión; no se aplican automáticamente.

Este es un prototipo de desarrollo, no una aplicación final endurecida para producción. Ejecuta solo en tu propio PC y no expongas el servidor a Internet.


## Validación automática

Nota histórica: una ejecución temprana informó 15 pruebas; no es la CI actual. La ejecución vigente con 38 pruebas Python y sintaxis JavaScript es https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40890138277. Ninguna sustituye la prueba manual en Windows.

## Hallazgos importantes antes de una campaña larga

- **Privacidad básica implementada y probada en CI:** el selector de alcance permite escena/grupo o privado con destinatario; mensajes y eventos se filtran por audiencia/testigos. Faltan el inspector y los casos de cambio de presencia.
- Las operaciones de inventario y movimiento se registran como propuestas pendientes en esta versión; falta una política segura para autoaplicar cambios cotidianos de baja ambigüedad.
- Faltan la prueba manual de edición/undo en Windows y una campaña de 50–100 turnos. La llamada real a una API es opcional para la modalidad de chat web manual.

No expongas el servidor a Internet: el prototipo está pensado para ejecutarse solo en el PC.


## Qué valida la CI actual

La ejecución actual con 38 pruebas cubre el preset real, privacidad por destinatario, inclusión/exclusión de mensajes/eventos, presupuesto Lorebook editable/persistente, operaciones de objetos y recursos, undo/regeneración, construcción del prompt para ChatGPT/Gemini web, validación/rechazo del JSON pegado y rechazo del contexto desactualizado. La CI no utiliza ni extrae respuestas reales de los chats web y no demuestra el intercambio manual en Windows. Tampoco mide tokens/coste de la API.

Limitaciones conocidas:
- Las compras se cobran dentro de `InventoryOperation acquire`; no debe emitirse además un `ResourceOperation spend` duplicado para ese evento.
- La idempotencia de compra tiene prueba API: un reintento del mismo request_id no vuelve a invocar al proveedor simulado ni duplica la compra. Falta ensayar la pérdida de respuesta a nivel de red y proveedores reales.
- El inspector explica disparadores Lorebook y motivos de inclusión/exclusión de mensajes/eventos. El presupuesto es configurable desde la UI y queda guardado en SQLite; falta conteo exacto de tokens por proveedor.
- El botón «Deshacer último turno» restaura reloj, ubicación, presencia, inventario, recursos, relaciones y usos de poderes desde el snapshot preturno; marca las versiones anuladas para auditoría. CI comprueba compra/monedas/reloj, una relación, un uso de Eco, regeneración y rechazo de undo fuera de orden. Falta ensayo manual de Windows y campaña larga.
