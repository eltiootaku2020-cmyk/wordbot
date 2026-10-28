# Investigación aplicada — SpicyChat, personalidad de PNJ, cronología y estado (v1.13)

## Objetivo
Mejorar Isekai sin Destino sin convertir Personality en una enciclopedia ni gastar contexto registrando cada detalle. Se combinan límites reales de SpicyChat con patrones documentados de diseño de personajes y estado en juegos narrativos.

## Qué confirma la documentación de SpicyChat
- La ventana Free publicada es de 4.096 tokens para todo el contexto; la respuesta tiene un máximo de 180 tokens. El contexto se comparte entre definición, instrucciones, Lorebook activada e historial reciente. Los mensajes antiguos salen cuando se llena. Fuentes: [planes y límites](https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included) y [por qué se olvidan los personajes](https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-).
- La Lorebook se activa por palabras clave; no es una base de datos de estado que se actualice automáticamente. Soporte indica hasta 5.000 entradas de 2.000 caracteres, aunque el contexto activo sigue siendo el cuello de botella. Fuente: [Lorebooks](https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks).
- Por tanto: Personality = reglas de alto nivel; Lorebook = canon estable activado por palabras clave; /guardar = instantánea compacta copiable del estado cambiante. No prometer memoria infinita ni afirmar que el estado oculto está guardado si ya no sigue en contexto.

## Patrones útiles para PNJ
SillyTavern separa personalidad, escenario, primera respuesta y ejemplos de diálogo; World Info inserta datos solo cuando se activan por contexto. Fuentes: [Character Design](https://docs.sillytavern.app/usage/core-concepts/characterdesign/) y [World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/).

Los sistemas de personajes de juegos narrativos suelen separar:
1. **Identidad estable:** apariencia, oficio, temperamento, valores y forma de hablar.
2. **Estado cambiante:** ubicación, lesiones, objetivo actual, objeto portado y relaciones.
3. **Conocimiento con procedencia:** lo visto, oído, contado o supuesto; los PNJ no son omniscientes.
4. **Objetivos y motivaciones:** explican por qué alguien inicia una conversación o decide callarse.
5. **Situación inmediata:** quién está presente, posición física, qué acaba de pasar y qué puede percibir.

Referencias técnicas: [StoryEngine — Actor: facts, memories and goals](https://storyengine.gg/docs/Concepts/Actor.html), [Epic Games — diseño de conversaciones con personajes de IA](https://dev.epicgames.com/documentation/fortnite/designing-a-conversation-in-unreal-editor-for-fortnite?lang=en-US) y [Microsoft — diálogo ramificado de NPC](https://learn.microsoft.com/minecraft/creator/documents/NPCDialogue).

## Aplicación al grupo
- No esperar siempre una pregunta del jugador: si PNJ clave/cercanos están presentes y tienen motivo, dar 1–2 intervenciones breves por respuesta. Ivar puede ir delante, suspirar o soltar ironía; el suspiro debe tener contexto, no ser una palabra suelta.
- No hacer que todos hablen cada turno. Alternar quién habla según posición, personalidad, objetivo, cansancio, peligro y tema. El silencio también puede tener causa.
- Un personaje cercano puede iniciar diálogo, pero solo conoce lo que presenció u oyó. Si el protagonista cuenta después el encuentro con un goblin, las reacciones empiezan entonces, no retroactivamente.
- Reacciones y emociones son generación narrativa: no se fijan como canon de antemano ni cambian porcentajes sin un hecho que lo justifique. Los porcentajes describen intensidad acumulada, no probabilidad matemática real.
- Si una respuesta Free queda corta, priorizar una acción clara, una intervención de PNJ y el turno del protagonista. No pedir otro mensaje para que el personaje diga la frase que cabía en la respuesta.

## Cronología sin convertir la historia en guion
Usar una cronología de **anclas verificadas** (día/bloque, señales previas, evento esperado, condiciones y consecuencias conocidas) junto a una **línea de sucesos de la partida** (máximo 3–5 eventos recientes). Las anclas del mundo no deben borrar la agencia del protagonista; sus acciones pueden cambiar consecuencias si existe causalidad suficiente. No insertar una escena solo porque toca una fecha si no se cumplen sus condiciones. Una cronología de anime sirve como técnica de planificación, no como canon que deba copiarse en este mundo original.

## Eco vegetal: estado y límites provisionales
**Confirmado por la experiencia del jugador:** descubrió que puede interactuar con recuerdos de árboles y lo percibe como una sensación interna, no como una imagen.

**Todavía no confirmado:** alcance, duración, coste, especies compatibles, si el uso lee o altera recuerdos, si varios árboles pueden afectarse y si cuentan igual que los objetivos humanos.

**Reglas de prueba para no volverlo omnipotente:**
- Un árbol por intento; no obtener recuerdos de lo que ese árbol no pudo percibir.
- La sensación puede ser parcial/ambigua; no se transforma automáticamente en nombres, diálogos exactos, escenas visuales o una verdad objetiva.
- No concede control de animales, raíces, plantas o voluntades por extensión.
- Cada intento se registra con objetivo/lugar, intención, sensación reportada y resultado confirmado. No se inventa el coste ni se descuenta del contador humano hasta confirmar el funcionamiento.
- Mantenerlo secreto si no hubo testigos o evidencia. La cautela del protagonista pertenece a sus decisiones; el bot no debe decidirlas por él.
- Estas son reglas provisionales de prueba, no una explicación definitiva del origen de Eco.

## Objetos comunes como posibilidades, no regalos automáticos
Catálogo de cosas plausibles: cuerda, saco de tela, cuenco, cantimplora, aguja/hilo, paño, vendas, yesca/pedernal, vela/antorcha, tiza/carbón, manta, cuchillo utilitario, olla, frasco, estacas y comida conservada. Son opciones que pueden aparecer en lugares coherentes, comprarse, intercambiarse o recibirse; no entran al inventario hasta que ocurra una adquisición confirmada. El inicio sin equipo/comida sigue vigente, salvo la ropa básica de viaje ya establecida.

## Pruebas antes de declarar terminado
1. **Voz espontánea:** sin nombrar a Ivar, una escena de grupo produce una intervención completa y natural de él u otro PNJ cercano; no fuerza a todos a hablar.
2. **Conocimiento:** un PNJ ausente no conoce el encuentro hasta que alguien se lo cuenta.
3. **Porcentajes:** sin evidencia nueva, el valor no cambia; falta de dato queda como No registrado.
4. **Objetos:** una cuerda aparece solo tras hallazgo/compra/regalo confirmado; si se deja atrás, no permanece en el inventario llevado.
5. **Eco vegetal:** se registra la sensación descrita sin inventar visión ni verdad; alcance/coste permanecen desconocidos hasta probarlos.
6. **Contexto:** /guardar resume solo campos permitidos, sin historial de comidas ni listas verbosas.
7. **Longitud:** Personality no supera 5.000 caracteres y el JSON de Lorebook es sintácticamente válido.

## Fuentes
- SpicyChat, [Plans and what's included](https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included)
- SpicyChat, [Why characters forget things](https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-)
- SpicyChat, [Lorebooks](https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks)
- SillyTavern, [Character Design](https://docs.sillytavern.app/usage/core-concepts/characterdesign/)
- SillyTavern, [World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/)
- StoryEngine, [Actor facts, memories and goals](https://storyengine.gg/docs/Concepts/Actor.html)
- Epic Games, [Designing a Conversation](https://dev.epicgames.com/documentation/fortnite/designing-a-conversation-in-unreal-editor-for-fortnite?lang=en-US)
- Microsoft, [NPC Dialogue](https://learn.microsoft.com/minecraft/creator/documents/NPCDialogue)
