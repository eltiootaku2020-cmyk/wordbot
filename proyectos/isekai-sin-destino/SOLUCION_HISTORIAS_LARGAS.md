# Solución para historias largas — Isekai sin Destino

**Estado:** diagnóstico y opciones, v1.0.  
**Proyecto:** Isekai sin Destino.  
**Rama:** `docs/historias-organizadas`.  
**Importante:** este documento no cambia la configuración v1.7 por sí mismo; registra la solución propuesta para decidir y probar con control.

## Diagnóstico

SpicyChat puede sostener roleplay largo, pero no funciona por sí solo como un RPG con estado persistente garantizado. La definición, instrucciones de generación, mensajes recientes y respuestas comparten la ventana de contexto. Cuando el presupuesto se llena, los mensajes antiguos salen del contexto disponible.

La documentación oficial consultada indica estos límites por plan:
- Free y Get A Taste: 4.096 tokens de contexto.
- True Supporter: 8.192 tokens.
- I'm All In: 16.384 tokens.
- Memory Manager: disponible desde Get A Taste.
- Semantic Memory 2.0: disponible desde True Supporter.

Las cantidades pueden cambiar; comprobar el panel actual de la cuenta antes de pagar. La memoria semántica ayuda a recuperar hechos resumidos, pero no es una base de datos de juego transaccional.

Una Lorebook almacena conocimiento relativamente estable del mundo (reglas, lugares, personajes y cronología) y carga entradas cuando se activan por palabras clave. No sustituye la memoria dinámica del estado de una partida: inventario, dinero, hora, heridas, qué monstruo concreto murió, qué personaje huyó o cuántos usos de Eco quedan.

**El tiempo real que pasa entre mensajes, por sí solo, no debería avanzar el reloj ficticio ni equivale al llenado del contexto.** Si el bot vuelve al Día 1 después de varias horas, hay que comprobar si abrió una conversación nueva, si el historial ya superó la ventana, si el mensaje inicial o una instrucción antigua siguen en el bot de SpicyChat, o si el modelo está obedeciendo una regla contradictoria.

## Tres caminos posibles

### Opción A — Seguir con SpicyChat con un procedimiento de continuidad

Adecuada si el bot debe seguir publicado en SpicyChat y se acepta un punto de guardado manual.

1. Actualizar en el editor real de SpicyChat los campos de la configuración v1.7. Los cambios de GitHub no actualizan el bot publicado automáticamente.
2. Mantener Personality relativamente corta. Dejar la historia fija y las fichas en Lorebook; el estado de la partida no debe ocupar muchas entradas permanentes.
3. Si el plan lo permite, activar Memory Manager y fijar solo recuerdos de alto valor. Semantic Memory 2.0 puede ayudar en los planes compatibles, pero revisar sus memorias y corregir errores.
4. Usar `/guardar` al final de cada jornada ficticia y después de cambios de estado importantes. Copiar el punto de guardado a un archivo local del usuario; no confiar en que el prompt lo almacene fuera del chat.
5. Al reanudar, pegar el último punto de guardado si el bot no puede verificar el estado. No aceptar un reinicio silencioso ni una reconstrucción inventada.

Ventaja: se conserva el bot de SpicyChat.  
Limitación: el usuario debe guardar el estado, y la memoria automática puede resumir mal o recuperar datos incompletos.

### Opción B — Usar SillyTavern para la partida personal larga

Recomendación si el objetivo principal es que una sola persona juegue una campaña muy larga con más control sobre el historial y la memoria.

SillyTavern es una interfaz local de código abierto para conectarse a un modelo de IA local o remoto. No es un modelo por sí misma: hace falta configurar un proveedor de IA; un proveedor remoto evita ejecutar un modelo pesado en la PC, aunque puede tener coste por uso. Incluye:
- World Info, equivalente aproximado a una Lorebook que se activa según la conversación.
- Extensión Summarize incorporada para crear, almacenar y editar resúmenes de la historia.
- Chat Vectorization opcional para buscar mensajes antiguos relevantes e incorporarlos al contexto.

El resumen puede perder hechos o alucinar, así que sigue siendo editable y necesita revisión. La búsqueda vectorial tampoco garantiza memoria perfecta; es una ayuda adicional, no una solución mágica.

Enlaces oficiales:
- SillyTavern: https://docs.sillytavern.app/
- Instalación en Windows: https://docs.sillytavern.app/installation/windows/
- Resúmenes automáticos: https://docs.sillytavern.app/extensions/summarize/
- Recuperación de mensajes antiguos: https://docs.sillytavern.app/extensions/chat-vectorization/

Ventaja: más control del chat, resúmenes y recuperación de mensajes antiguos; la conversación se gestiona desde la propia instalación.  
Limitación: hay que instalarlo y configurar un proveedor de IA. No resuelve por sí solo un bot público multiusuario.

### Opción C — Crear una aplicación de rol con guardados reales por usuario

Recomendación si el objetivo es publicar una aventura donde cada jugador conserva automáticamente su propio progreso, como en un juego.

La aplicación necesitaría:
- Inicio de sesión o identificador individual de jugador.
- Base de datos separada por partida.
- Estado estructurado: hora, ubicación, inventario, salud, dinero, relaciones, misiones, monstruos y efectos de Eco.
- Historial narrativo y resumen.
- Lorebook consultada según la escena.
- Motor de reglas que valide cambios antes de actualizar el estado.
- Modelo de IA para redactar escenas, sin permitir que el texto del modelo cambie arbitrariamente el estado.
- Guardado automático tras cada acción confirmada y opción de exportar/importar una partida.

Ventaja: el estado no depende de que el modelo recuerde todo el historial; cada usuario tiene un registro separado.  
Limitación: es un proyecto de software, requiere conexión a un modelo de IA y posiblemente costes de alojamiento/API. No se consigue añadiendo instrucciones a una Lorebook de SpicyChat.

## Recomendación para el proyecto actual

No seguir agregando más reglas al prompt para compensar toda la falta de memoria. Eso consume contexto y no crea persistencia. Mantener la configuración v1.7 compacta y ejecutar primero una prueba controlada en SpicyChat:

1. Empezar una partida nueva solo después de guardar la actual.
2. Confirmar que el editor real de SpicyChat tiene la versión v1.7, especialmente la regla de cabecera dinámica.
3. Jugar unas 10–15 respuestas, registrar hora, inventario y dos PNJ, y crear un punto de guardado.
4. Salir y volver al mismo chat sin iniciar uno nuevo; probar `/estado`.
5. Si se reinicia, pegar el punto de guardado. Anotar si el fallo ocurrió con el registro visible o sin él.

Si el objetivo es jugar tú mismo durante muchas sesiones sin copiar guardados a mano, probar SillyTavern será el siguiente paso más útil. Si el objetivo es ofrecer un mundo persistente a muchos usuarios públicos, conviene diseñar la aplicación de rol con base de datos.

## Referencias oficiales

- SpicyChat, contexto y olvidos: https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- SpicyChat, planes y funciones de memoria: https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included
- SpicyChat, Lorebooks: https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks
- SpicyChat, Memory Manager: https://docs.spicychat.ai/product-guides/premium-features/memory-manager
- SpicyChat, Semantic Memory 2.0: https://docs.spicychat.ai/product-guides/premium-features/semantic-memory-2.0
- SillyTavern, resúmenes: https://docs.sillytavern.app/extensions/summarize/
- SillyTavern, Chat Vectorization: https://docs.sillytavern.app/extensions/chat-vectorization/
