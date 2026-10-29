# Investigación aplicada — SpicyChat, personalidad de PNJ, cronología y estado (v1.19)

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


## Actualización investigada v1.15: datos verificables, no guion fijo

### Límites de SpicyChat comprobados
La ayuda oficial consultada el 29 de octubre de 2026 indica que Free tiene **4.096 tokens de contexto compartido** y máximo de **180 tokens por respuesta**. El contexto incluye definición, instrucciones y mensajes recientes; al llenarse, salen mensajes antiguos. SpicyChat recomienda una definición compacta de aproximadamente 800–1.100 tokens. La Lorebook se activa por palabras clave y solo inserta entradas pertinentes. Las páginas oficiales difieren en cómo expresan algunos topes; usa el contador del editor y la tabla de planes como referencia práctica.

Fuentes oficiales:
- https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included
- https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks
- https://support.spicychat.ai/support/solutions/articles/153000260635-how-spicychat-generates-messages

### Patrones de diseño de NPC/dialogue
Las investigaciones consultadas separan estado del mundo, conocimiento individual y diálogo generado:
- **Personalized Quest and Dialogue Generation in Role-Playing Games** (CHI 2023) combina un modelo de lenguaje con un grafo de conocimiento de ubicaciones, entidades, objetos y relaciones: https://doi.org/10.1145/3544548.3581441
- **Personalized Non-Player Characters: A Framework for Character-Consistent Dialogue Generation** (2025) estudia memoria de trabajo, memoria semántica y relaciones entre entidades: https://www.mdpi.com/2673-2688/6/5/93
- **Designing Open Dialogue Systems for LLM-Based NPCs** (DiGRA 2026) examina diálogo libre condicionado por personalidad y estado: https://dl.digra.org/index.php/dl/article/view/2837
- El diseño contextual de diálogo de GDC/Naughty Dog separa conocimiento individual, conocimiento compartido, estado global y entorno inmediato: https://www.gdcvault.com/play/1020386/A-Context-Aware-Character-Dialog

**Aplicación:** identidad estable (personalidad, habilidades demostradas) en Lorebook; datos dinámicos (ubicación, orden, inventario, sospechas, vínculos, quién sabe qué) en registro compacto. La IA genera reacciones/emociones; el registro fija hechos y consecuencias, no diálogos ni emociones obligatorias.

### Porcentajes, objetos y estado dinámico
- Porcentajes = intensidad estimada por eje, no probabilidad matemática. Cambian con hechos/evidencia; sin prueba queda «No registrado».
- Un objeto tiene cantidad/condición/portador/ubicación/estado. Una criatura tiene identidad/última ubicación/orden/conocimiento/vínculos. Si un goblin recibe la orden de esperar en un claro, se registra la orden, pero el cumplimiento queda desconocido hasta comprobarlo.
- Inventario inicial: pañuelo gastado, bolsita de tela vacía y cordel de cáñamo (~1,5 m), además de ropa básica. Sin dinero, comida, agua, armas, mochila ni equipo de aventura. Otros objetos son posibilidades, no regalos automáticos.
- No registrar detalles sin consecuencia (por ejemplo, qué comió). Consumir una ración solo cambia el inventario.
- El estado puede mantenerse mientras siga en contexto, pero no es una base de datos invisible permanente. Para recuperar tras perder contexto, conserva /guardar fuera de SpicyChat.

### Cronología de anime/juegos como método, no destino
Usa: (1) anclas con condiciones/señales, (2) sucesos secundarios causados por decisiones, (3) qué sabe cada personaje y cuándo, y (4) consecuencias pendientes. Así se conserva coherencia sin convertir la aventura en escenas preescritas. El volcán es un ancla temporal; encuentros con goblins, viajeros o animales pueden ser independientes. Una fecha no obliga a insertar una escena si faltan condiciones/causas.


## Revisión v1.16: guardado útil, Eco trazable y escenas con movimiento

### Lo que exige el límite de Free
La ayuda oficial de SpicyChat publica para Free 4.096 tokens de contexto y 180 tokens como máximo por respuesta. La definición, instrucciones, Lorebook activada e historial comparten el contexto. La Lorebook es una biblioteca por palabras clave, no un estado dinámico actualizado automáticamente. Fuentes:
- https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included
- https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks

Por tanto, una memoria de campaña de cientos de palabras no puede salir en una respuesta Free. La solución propuesta es un guardado multiparte: cada respuesta contiene una sección numerada y el jugador une las partes en un archivo externo. Esto no amplía el contexto ni recupera información que ya se perdió; hay que guardar antes de llenarlo.

### Memoria de sucesos, no solo un mini resumen
El estado actual no explica por sí solo por qué un personaje sospecha, qué sabe, por qué una criatura espera en un lugar o qué recuerdo fue alterado. El guardado conserva estado vigente, fichas por entidad, relaciones por pareja/dirección, libro de poderes por uso, cronología causal de hitos que siguen importando, últimos sucesos por separado y escena exacta. Los últimos 3–5 sucesos no reemplazan toda la cronología.

### Eco: separar objetivo, resultado y efecto
Cada intento tiene ficha propia. La intención del jugador no demuestra que el objetivo haya sido afectado; registra reacción observable y efecto confirmado. Miedo, confianza, obediencia, familiaridad/memoria y cooperación son ejes distintos. «Miedo 20→30% (Δ +10 puntos)» solo se escribe con un valor anterior y evidencia; sin ellos se usa No registrado. En humanos se conserva el límite de tres intentos por objetivo. En árboles/animales, alcance, coste, duración y contador no heredan automáticamente las reglas humanas.

Ejemplo hipotético, no canon: «Intención: infundir miedo en un lobo gris; lugar: Bosque Oscuro si está confirmado; reacción: retrocede y gruñe; miedo/obediencia/coste/duración: No registrado sin evidencia». No dar por hecho que miedo equivale a control.

### Movimiento físico y voz proactiva
Cada 1–2 respuestas del bot, uno o más PNJ cercanos o elementos del entorno se mueven o realizan una acción concreta, salvo que la escena justifique quietud. Eso no autoriza a mover al protagonista ni a saltar de lugar. PNJ cercanos pueden hablar con frases completas sin ser nombrados, según posición, personalidad, conocimiento y objetivo inmediato.


## Auditoría de coherencia v1.18 (29-10-2026)

### Límite de entrada y activadores
La documentación de soporte vigente publica hasta 2.000 caracteres por Content; una guía detallada anterior conserva 1.000. Para reducir riesgo de importación y activaciones pesadas, esta versión impone menos de 1.000 caracteres como regla conservadora del proyecto, no como máximo oficial vigente. Las keywords se buscan en los últimos cuatro mensajes; si varias entradas comparten keyword, se activan juntas; el contenido de una entrada no activa otras entradas.

Fuentes: [planes y límites](https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included), [por qué olvidan los bots](https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-), [Lorebooks](https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks), [guía detallada](https://docs.spicychat.ai/product-guides/lorebook).

### Errores detectados y corregidos
- UID 77 excedía 1.000 caracteres y repetía la keyword `uso de Eco` de UID 67. Se acortó y cambiaron las claves.
- El JSON contiene 77 entradas pero el test del preset esperaba 76. Se actualiza a 77 y se añade prueba de longitud/unicidad.
- Inventario inicial unificado: ropa corriente, pañuelo gastado, bolsita vacía y cordel corto; sin dinero, comida, agua, armas ni mochila.
- Δ = nuevo−anterior en puntos porcentuales: 20%→30% = +10 puntos, no +10% relativo. Δ0 significa sin cambio por ese hecho; No registrado no equivale a 0 ni a 50.
- Guardado activo: cada 5–7 intercambios y tras cambios importantes; Free requiere varias partes por el máximo de 180 tokens por respuesta.
- El registro «interno» no es una base de datos oculta; la copia externa de /guardar permite recuperación después de perder contexto.

### Aceptación v1.18
1. JSON parseable con 77 entradas y UID únicos.
2. Cada Content <1.000 caracteres; sin keywords duplicadas.
3. Cada cambio porcentual documenta valor previo, nuevo, Δ en puntos y causa; sin base, No registrado.
4. Sin campos nuevos ni historial de comidas; solo provisiones cambian tras consumo confirmado.
5. Órdenes quedan con cumplimiento desconocido hasta confirmación.
6. Objetos dejados salen del inventario llevado y conservan última ubicación confirmada.
7. PNJ ausentes reaccionan solo al presenciar o recibir el relato.
8. Test local espera 77 y audita longitudes/keywords.
9. Importación y roleplay real en SpicyChat siguen pendientes de prueba manual.

 
## Revisión aplicada v1.19 (29-10-2026)

### Fuentes vigentes de SpicyChat
La documentación oficial indica que Free dispone de 4.096 tokens de contexto compartido por definición, instrucciones y mensajes; cuando el contexto se llena, los mensajes antiguos dejan de estar disponibles. La respuesta gratuita tiene un máximo de 180 tokens. Esto no puede resolverse mediante una frase de prompt: el registro interno solo funciona mientras sus datos sigan en el contexto activo y por eso la copia externa sigue siendo necesaria.

Fuentes oficiales:
- Contexto y memoria: https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- Lorebooks: https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks
- Escenarios y ejemplos de diálogo: https://docs.spicychat.ai/product-guides/creating-chatbots/advanced-settings
- Director Mode y compatibilidad variable según modelo: https://docs.spicychat.ai/product-guides/director-mode

La página actual de Lorebooks publica capacidad de hasta 5.000 entradas y 2.000 caracteres por Content. El proyecto conserva menos de 1.000 caracteres por entrada como umbral interno conservador para reducir carga y el riesgo de incompatibilidad con documentación detallada anterior.

### Patrones de diseño de NPC y memoria
- StoryEngine separa el estado del mundo (actores, ubicaciones, objetos, hechos, recuerdos y objetivos) de la capa narrativa que expresa ese estado. Aplicación a Isekai: el registro fija hechos, propiedad, ubicación y conocimiento; la IA redacta diálogo y reacciones sin alterar el estado sin causa. Fuentes: https://storyengine.gg/docs/Overview.html y https://storyengine.gg/docs/Concepts/Actor.html
- El trabajo de 2025 sobre NPC personalizados propone conocimiento estático más conocimiento dinámico y relaciones recuperables para sostener consistencia de personaje: https://www.mdpi.com/2673-2688/6/5/93
- El artículo de DiGRA de 2026 estudia diálogo abierto generado por LLM con personalidad definida y actualización del estado durante la interacción: https://dl.digra.org/index.php/dl/article/view/2837
- Estas publicaciones orientan el diseño; no garantizan que SpicyChat mantenga una base de datos ni que el modelo siga todas las reglas a la perfección.

### Reglas consolidadas en v1.19
1. **Porcentajes:** cada cambio persistente contiene valor previo, valor nuevo, delta en puntos porcentuales, tendencia SUBE/BAJA/SIN CAMBIO y causa. No registrado no equivale a cero, 50% o neutralidad. Las emociones del momento quedan al modelo; solo se guardan cambios duraderos con evidencia.
2. **Iniciativa de diálogo:** en escenas de grupo, PNJ cercanos intervienen cada 1–2 respuestas si existe un motivo; alternan voces, no todos hablan siempre. Ivar puede suspirar o comentar el terreno por ir delante, pero cada intervención debe tener contexto y frases completas, no palabras sueltas.
3. **Conocimiento individual:** un PNJ solo conoce lo que presenció, escuchó o le contaron. Si se entera después, reacciona entonces y según sus creencias previas, nunca como testigo retroactivo.
4. **Objetos y criaturas:** los objetos tienen cantidad, condición, estado, portador y ubicación. Una criatura con una orden guarda identidad, última ubicación, destino/condición y cumplimiento pendiente/desconocido hasta confirmación; no se trata como objeto de inventario ni se presupone obediencia.
5. **Eco vegetal:** se conserva como descubrimiento de la partida: una interacción con recuerdos de árboles percibida como sensación interna, no imágenes. La mecánica exacta, alcance, coste, duración y contador siguen sin confirmar.
6. **Catálogo común:** ropa corriente, pañuelo gastado, bolsita vacía y cordel corto son el inventario inicial. Cuerda, cuenco, cantimplora, aguja/hilo, vendas, yesca/pedernal, manta, cuchillo utilitario y otros enseres son posibilidades, no regalos. No se registra historial de comidas: solo se actualizan provisiones si cambia su cantidad.
7. **Uso de contexto:** los hechos estables viven en Lorebook con activadores; el estado cambiante se actualiza solo cuando un campo cambia. No volcar todo el registro cada turno. Guardar cada 5–7 intercambios y tras cambios importantes; dividir el punto de continuidad en partes si la respuesta no alcanza.

### Comprobaciones agregadas
- La Personality permanece bajo 5.000 caracteres.
- Los bloques de Scenario, Greeting y Example Dialogue deben respetar sus límites y mostrar contadores correctos.
- El JSON conserva 77 entradas, UID únicos, Content por debajo de 1.000 caracteres y keywords sin duplicados exactos.
- No deben quedar ejemplos con horas por minuto (08:03, 08:15) ni el horario antiguo de franjas de tres horas.
- Importación y roleplay real siguen pendientes de validación manual dentro de la cuenta de SpicyChat.
