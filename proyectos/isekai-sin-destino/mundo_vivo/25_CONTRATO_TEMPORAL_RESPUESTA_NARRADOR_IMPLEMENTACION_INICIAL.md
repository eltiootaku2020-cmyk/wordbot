# Contrato temporal del narrador — implementación inicial

**Estado:** corrección técnica inicial en PR #41; no constituye una aprobación del canon narrativo ni de las tablas de duración propuestas.

## Regla del reloj

`elapsed_minutes` representa únicamente tiempo de ficción consumido por acciones nuevas y efectivamente realizadas durante la respuesta actual. No representa el número de mensajes, la duración de la generación, la extensión del texto ni el mero hecho de abrir un turno.

- El valor neutral y predeterminado es **0 minutos**.
- Un saludo, una pregunta, una respuesta, una reacción, una observación estática o una continuación conversacional no adelantan el reloj por sí solos.
- No se vuelve a contabilizar una acción cuya duración ya se registró.
- En acciones secuenciales se suman solo intervalos realmente sucesivos. Las tareas simultáneas y las fases incluidas dentro de una actividad principal cuentan una sola vez en el reloj global.
- El narrador solo puede proponer entre 1 y 15 minutos cuando la duración esté respaldada por una regla temporal aprobada o por datos explícitos del contexto.
- Si una acción parece consumir tiempo pero no existe una base suficiente para cuantificarla, el narrador deja 0 y registra en `pending` qué regla necesita calibración. No inventa una cifra.
- Los avances superiores a 15 minutos siguen requiriendo el comando explícito `/salto`; el código aplica ese intervalo de manera determinista.

## Qué cambia en esta entrega

- `NarratorResponse.elapsed_minutes` pasa de valor predeterminado 1 a 0.
- El proveedor de prueba deja de sumar un minuto a cada respuesta conversacional.
- El prompt compartido de los proveedores define el tiempo como duración de acciones y prohíbe cobrarlo por mensaje/turno.
- Las pruebas cubren el valor neutral del modelo, el esquema expuesto a los proveedores, el proveedor de prueba y el reloj API después de mensajes breves repetidos.

## Límites que permanecen abiertos

Esta entrega **no** completa el simulador temporal ni resuelve todavía:

1. La elección definitiva entre almacenar segundos con remanente persistente o mantener precisión exclusiva de minutos. La rama actual sigue guardando día y minuto.
2. La precisión de eventos que solo tienen día conocido, como la erupción del Día 12. No se le asigna ninguna hora.
3. La interrupción y reanudación de acciones largas exactamente cuando vence un acontecimiento. El programador sigue usando recuperación de eventos vencidos (*catch-up*).
4. La calibración final de rangos para diálogo, observación, búsqueda, comida, descanso, combate o viaje. Los rangos de PR #39 continúan siendo propuestas, no constantes aprobadas.
5. Las agendas autónomas, las tasas de hambre/sed/sueño/fatiga y la simulación de campaña.

Por tanto, esta corrección evita el avance fantasma por defecto, pero no debe presentarse como una solución completa de cronología o de simulación de actividades. La siguiente decisión técnica pendiente es fijar la unidad temporal persistente y, después, ampliar el programador sin inventar el momento de los acontecimientos de precisión diaria.
