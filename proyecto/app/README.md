# Gestor local de canon — prototipo v0.1

**Estado de validación:** CI aprobó 32 pruebas Python y comprobación sintáctica JavaScript el 29-10-2026: [ver resultados](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40877808136). Sigue pendiente probar manualmente Windows y realizar llamadas reales a los proveedores.

Esta carpeta contiene un primer prototipo ejecutable del flujo local: interfaz de chat en Chromium, base SQLite y narrador simulado por defecto. El proveedor simulado permite probar la persistencia sin clave ni coste. OpenAI y Gemini son opciones externas configurables.

## Requisitos

- Python 3.11 o posterior.
- Chromium o cualquier navegador moderno.
- Una clave API solo si eliges un proveedor remoto.

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

## Proveedor remoto

- OpenAI: configura APP_PROVIDER=openai, OPENAI_API_KEY y OPENAI_MODEL en .env.
- Gemini: configura APP_PROVIDER=gemini, GEMINI_API_KEY y GEMINI_MODEL en .env.

Ambos adaptadores usan APIs oficiales y una respuesta estructurada. La aplicación valida la estructura y después verifica los cambios con su propio estado. El uso de API puede facturarse por separado de la suscripción de chat.

No pegues claves API en una conversación, en GitHub ni en una exportación de Lorebook.

## Alcance y limitaciones

Implementado en esta primera versión: interfaz local, base SQLite, importación de Lorebook JSON, recuperación de contexto por palabras clave, narrador simulado, adaptadores API iniciales, registro de mensajes/eventos, propuesta y aprobación/rechazo de cambios, reloj básico, historial de usos de Eco y copia de seguridad.

Todavía incompleto: validación exhaustiva de movimientos y acciones físicas, editor completo de mundos/entidades, restauración visual de copias, selección semántica avanzada, comprobación automática de todos los cambios de canon y prueba real con claves/modelos del usuario. Las propuestas de inventario y movimiento permanecen pendientes para revisión; no se aplican automáticamente.

Este es un prototipo de desarrollo, no una aplicación final endurecida para producción. Ejecuta solo en tu propio PC y no expongas el servidor a Internet.


## Validación automática

La última ejecución de CI enlazada en esta guía informa 15 pruebas de Python aprobadas y comprobación de sintaxis del JavaScript incrustado: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40867432602. Es una prueba automatizada en el entorno de CI; no demuestra que la interfaz se haya probado visualmente en Windows ni que las claves/modelos reales funcionen.

## Hallazgos importantes antes de una campaña larga

- **Privacidad básica implementada y probada en CI:** el selector de alcance permite escena/grupo o privado con destinatario; mensajes y eventos se filtran por audiencia/testigos. Faltan el inspector y los casos de cambio de presencia.
- Las operaciones de inventario y movimiento se registran como propuestas pendientes en esta versión; falta una política segura para autoaplicar cambios cotidianos de baja ambigüedad.
- Falta probar edición/regeneración con reversión de efectos, llamadas API reales y una partida de 50–100 turnos.

No expongas el servidor a Internet: el prototipo está pensado para ejecutarse solo en el PC.


## Qué valida la CI actual

La ejecución con 32 pruebas cubre el preset real, privacidad por destinatario, inclusión/exclusión de mensajes/eventos, presupuesto Lorebook editable/persistente, consumo y estado de objetos, movimientos de PNJ, compras, ingresos/gastos de recursos, rollback de relación/Eco y undo/regeneración. La CI usa proveedor simulado; no mide tokens/coste real ni valida API/Windows.

Limitaciones conocidas:
- Las compras se cobran dentro de `InventoryOperation acquire`; no debe emitirse además un `ResourceOperation spend` duplicado para ese evento.
- La idempotencia de compra tiene prueba API: un reintento del mismo request_id no vuelve a invocar al proveedor simulado ni duplica la compra. Falta ensayar la pérdida de respuesta a nivel de red y proveedores reales.
- El inspector explica disparadores Lorebook y motivos de inclusión/exclusión de mensajes/eventos. El presupuesto es configurable desde la UI y queda guardado en SQLite; falta conteo exacto de tokens por proveedor.
- El botón «Deshacer último turno» restaura reloj, ubicación, presencia, inventario, recursos, relaciones y usos de poderes desde el snapshot preturno; marca las versiones anuladas para auditoría. CI comprueba compra/monedas/reloj, una relación, un uso de Eco, regeneración y rechazo de undo fuera de orden. Falta ensayo manual de Windows y campaña larga.
