# Reparación de Isekai sin Destino — 2026-10-29

## Alcance

Cambios aplicados en la rama `fix/isekai-three-member-continuity`, basada en `docs/isekai-spicychat-lorebook`. Se modificaron únicamente los documentos de configuración y la importación de SpicyChat; no se alteró `main`.

## Correcciones

- Grupo inicial reducido a tres aventureras: Brina Solcor (espadachina), Maelis Orven (maga) y Sera Linde (arquera).
- Ivar y Timo se mantienen como personajes independientes del mundo, pero ya no aparecen como miembros del grupo inicial.
- Se corrigieron el saludo y los ejemplos que trasladaban al protagonista desde el bosque hasta una posada sin describir ni autorizar el viaje.
- Se unificó el reloj en seis franjas: Mañana I, Mañana II, Tarde I, Tarde II, Noche I y Noche II.
- Se eliminó la contradicción entre la regla de no saltar varias horas sin permiso y los comandos `/salto` explícitos: los saltos largos son válidos si el usuario los solicita, sin inventar decisiones del protagonista.
- Se definió qué hacer si falta el registro de Eco: pausar la acción y pedir el punto de guardado/confirmación; una vez confirmado el intento, consumir un uso incluso si falla.
- Se alineó la regla del volcán: la erupción es un acontecimiento ancla, ocurre como máximo el Día 7, no se cancela y solo puede adelantarse por una cadena causal física establecida.
- Se corrigió la numeración de las subsecciones de la sección 39.
- Se añadió `/estado` a la lista de palabras clave de comandos en la importación JSON.
- Se actualizaron los contadores de caracteres de los campos listos para copiar.

## Validaciones realizadas

- JSON parseado correctamente.
- 72 entradas, 72 UID únicos.
- Todas las entradas contienen los campos esperados.
- El contenido más largo de una entrada tiene 1.454 caracteres; ninguna supera 2.000.
- No quedan referencias al grupo inicial de cinco aventureros en los tres archivos revisados.
- Se comprobaron las reglas de seis franjas, Eco, volcán, numeración, comando `/estado` y ejemplo de viaje.

## Limitaciones

Este branch contiene lorebook y configuración, no el motor ejecutable de SpicyChat ni una base de datos RPG propia. Estas comprobaciones validan la consistencia documental y la estructura de importación; no prueban el comportamiento real del modelo dentro de SpicyChat. La persistencia del estado de partida sigue dependiendo del contexto disponible y del uso de puntos de guardado copiados por el usuario.
