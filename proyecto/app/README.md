# Gestor local de canon — prototipo v0.1

**Estado de validación:** 13 pruebas automáticas aprobadas en CI; ver [resultados](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40861306798). La instalación manual en Windows y las llamadas reales a proveedores aún están pendientes.

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

La base predeterminada se guarda en data/canon_manager.sqlite3 dentro de esta carpeta. Los datos locales y el archivo .env están excluidos de Git. La interfaz puede crear mundos desde cero o cargar «Isekai sin Destino v1.16» con un solo botón: importa el JSON real del repositorio, crea el reparto inicial y los cinco objetos, y abre una sesión nueva cada vez.

## Primera prueba

Pulsa «Cargar mundo de prueba» y selecciona Maelis como destinataria. Envía «Hola, linda». La respuesta simulada muestra una reacción posible de Maelis y una reacción del grupo. El programa guarda ambos mensajes y sus eventos. La confianza propuesta queda pendiente si no hay una puntuación inicial conocida; no inventa la base. Esta reacción de ejemplo no es canon obligatorio.

Después de reiniciar el servidor, carga el mismo mundo de prueba: los mensajes y el estado deben seguir presentes. El panel también permite importar un Lorebook JSON de formato SpicyChat y crear una copia de seguridad de la base.

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

La última ejecución de CI aprobó las 12 pruebas de Python y comprobó la sintaxis del JavaScript incrustado en la interfaz con `node --check`: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40863082953. Esto no es una prueba visual del navegador ni sustituye el ensayo manual en Windows.


La última ejecución CI pasó 13 pruebas de Python y comprobó la sintaxis del JavaScript incrustado: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40863341616. Sigue pendiente ejecutar en Windows y probar llamadas API reales.
