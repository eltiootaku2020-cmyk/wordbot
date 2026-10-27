# DanMachi — registro de decisiones y continuidad del proyecto

## Identidad del proyecto

- Proyecto: DanMachi — bot de SpicyChat.
- Repositorio: https://github.com/eltiootaku2020-cmyk/wordbot
- Rama exclusiva: `docs/danmachi-spicychat`
- Proyecto separado de Isekai sin Destino, cuya rama sigue siendo `docs/isekai-spicychat-lorebook`.
- Versión actual: v0.1 — base de configuración.
- Estado: guardado en GitHub; aún no probado en SpicyChat.

## Decisiones ya fijadas

1. El usuario quiere participar como protagonista original dentro del universo de DanMachi.
2. La historia debe tener un mundo vivo, personajes canónicos coherentes y decisiones del jugador con consecuencias.
3. No se deben inventar poderes ni mezclar sistemas de otras obras.
4. El bot no debe controlar los diálogos, acciones, pensamientos ni decisiones del protagonista.
5. Debe existir una Lorebook organizada por entradas; SpicyChat permite adjuntar una Lorebook por bot según su documentación actual.
6. Hay que conservar la continuidad y evitar que la partida vuelva al inicio al retomar el mismo chat.
7. La configuración y el registro de las decisiones se mantienen en esta rama para no mezclar proyectos.

## Valores provisionales usados para poder preparar una configuración jugable

- Protagonista: aventurero original adulto que acaba de llegar a Orario.
- Familia: ninguna al comienzo.
- Falna: ninguna al comienzo.
- Poder original: ninguno confirmado.
- Cronología: cerca del comienzo de la historia principal, sin forzar encuentros canónicos ni revelar spoilers posteriores.
- Primer lugar: avenida cercana al Gremio de Orario.
- Visibilidad recomendada en SpicyChat: privado durante pruebas.

Estos valores son una base conservadora, no decisiones permanentes del usuario. Cambiarlos requiere actualizar la configuración y las entradas relacionadas.

## Decisiones pendientes — NO convertir en canon sin autorización

- ¿El protagonista llega desde nuestro mundo, reencarna en DanMachi o simplemente es un aventurero nuevo que viaja a Orario?
- ¿Comienza sin poderes especiales o se quiere una habilidad original?
- Si hay un poder original: nombre, activación, efectos, alcance, coste, límites, riesgos y progresión.
- ¿En qué momento exacto del anime/manga comienza la aventura?
- ¿El canon se respeta estrictamente o se crea una línea temporal alternativa desde el inicio?
- ¿El protagonista quiere unirse a una Familia existente, crear una nueva o dejar la elección abierta?
- Nombre, aspecto, género y trasfondo del protagonista.
- Tono preferido: aventura, acción, romance, comedia, drama u otra combinación.
- Qué personajes canónicos quiere conocer y qué personajes o spoilers desea evitar.
- Si la versión final será pública o privada.

## Estado de los archivos

- `DANMACHI_SPICYCHAT_CONFIG.md`: completo como base v0.1, con decisiones provisionales marcadas.
- `DANMACHI_LOREBOOK_ENTRIES.md`: 26 entradas compactas preparadas para carga manual.
- `PRUEBAS_DE_COHERENCIA.md`: lista de validación preparada.
- JSON de importación: **no creado**. No se debe adivinar el esquema del exportador de SpicyChat; primero debe conseguirse una exportación JSON real y válida como plantilla.

## Protocolo de trabajo futuro

Cuando el usuario responda una decisión pendiente:
1. Añadirla aquí como decisión confirmada.
2. Actualizar Personality, Scenario, Greeting, Example Dialogue y Lorebook donde corresponda.
3. Mantener la coherencia con el punto temporal del canon.
4. Registrar versión y cambios.
5. No afirmar que se probó en SpicyChat hasta realizar una prueba real.

## Historial

### v0.1
- Se creó una configuración inicial para DanMachi.
- Se prepararon instrucciones de canon, agencia, continuidad y control de poderes.
- Se añadieron 26 entradas compactas de Lorebook en formato Markdown.
- Se dejaron origen del protagonista, poder original y punto temporal exacto como decisiones pendientes.
