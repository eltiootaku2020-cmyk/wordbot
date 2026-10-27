# DanMachi — bot de SpicyChat

**Estado del proyecto:** configuración inicial v0.1, en desarrollo.  
**Rama de trabajo:** `docs/danmachi-spicychat`  
**Proyecto separado:** este directorio pertenece a la aventura de DanMachi. No modificar ni mezclar con Isekai sin Destino, que continúa en la rama `docs/isekai-spicychat-lorebook`.

## Archivos

- `DANMACHI_SPICYCHAT_CONFIG.md`: campos preparados para el editor de SpicyChat: nombre, título, descripción, Personality, Scenario, Greeting, Example Dialogue y etiquetas sugeridas.
- `DANMACHI_LOREBOOK_ENTRIES.md`: entradas compactas de Lorebook para añadir manualmente, una por una.
- `DECISIONES_Y_CONTINUIDAD.md`: decisiones confirmadas, valores provisionales y cuestiones pendientes.
- `PRUEBAS_DE_COHERENCIA.md`: lista de pruebas para detectar reinicios, poderes inventados, spoilers y pérdida de continuidad.

## Alcance de v0.1

La base representa una aventura de mundo abierto en Orario. Para no imponer al usuario una idea que aún no confirmó, el punto de partida provisional es un aventurero original recién llegado a la ciudad, sin Familia, sin Falna y sin poderes añadidos. No se define aún si llegó desde nuestro mundo, reencarnó, ni si tendrá una habilidad original.

La cronología exacta del canon queda pendiente de decisión. Los personajes canónicos tienen vida propia y sus conocimientos, capacidades y acontecimientos se ajustan al momento elegido.

## Procedimiento de trabajo

1. No editar la rama de Isekai para introducir contenido de DanMachi.
2. Registrar las decisiones nuevas en `DECISIONES_Y_CONTINUIDAD.md`.
3. Cambiar el número de versión cuando haya cambios importantes en la configuración.
4. Probar cada corrección en SpicyChat antes de considerarla validada.
5. No generar un JSON de importación de Lorebook basándose en un esquema supuesto. Para producirlo, primero hace falta una exportación JSON real y válida de SpicyChat que sirva de plantilla.

## Fuentes de referencia

- Sitio oficial del anime DanMachi: https://danmachi.com/anime/eng_index.php
- Documentación de Lorebook de SpicyChat: https://docs.spicychat.ai/product-guides/lorebook
- Límites y formato de las entradas Lorebook: https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks
- Cómo SpicyChat genera cada respuesta y por qué una conversación no se comparte entre chats: https://support.spicychat.ai/support/solutions/articles/153000260635-how-spicychat-generates-messages
