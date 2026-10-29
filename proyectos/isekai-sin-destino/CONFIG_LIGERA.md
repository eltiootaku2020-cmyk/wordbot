# Isekai sin Destino — instalación ligera y continuidad (v1.15 propuesta)

Guía práctica para montar el bot con una carga inicial baja de contexto y reducir los olvidos durante partidas largas.

Documento maestro y Lorebook completa (76 entradas):
https://github.com/eltiootaku2020-cmyk/wordbot/blob/docs/historias-organizadas/proyectos/isekai-sin-destino/LOREBOOK_MAESTRA.md

Registro interno v1.15: esquema cerrado, porcentajes, objetos y órdenes:
https://github.com/eltiootaku2020-cmyk/wordbot/blob/docs/historias-organizadas/proyectos/isekai-sin-destino/REGISTRO_INTERNO_ESQUEMA.md

Cuadro prioritario v1.15 (reglas, mapa, reloj y registros):
https://github.com/eltiootaku2020-cmyk/wordbot/blob/docs/historias-organizadas/proyectos/isekai-sin-destino/CUADRO_REGLAS_PRIORITARIAS.md

## 1. Por qué el bot parecía olvidar a los tres mensajes

SpicyChat no mantiene todo el historial visible para siempre. La ventana de contexto incluye la definición del personaje, instrucciones, conversación reciente y Lorebook activa. Cuando se llena, los mensajes más antiguos dejan de estar disponibles para generar nuevas respuestas.

La documentación oficial indica actualmente:
- Free: 4.096 tokens de contexto y máximo de 180 tokens por respuesta.
- La Lorebook activa tiene un límite aproximado del 20 % del contexto: unos 740 tokens en Free.
- Memory Manager empieza en Get A Taste; Semantic Memory 2.0 figura para True Supporter y niveles superiores.

Esto no significa que haya un límite literal de tres mensajes. La cantidad real depende de la longitud de los textos, las respuestas y las entradas que se activen.

Fuentes oficiales:
- Planes y límites: https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included
- Por qué los bots olvidan: https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- Lorebook: https://docs.spicychat.ai/product-guides/lorebook
- Memory Manager: https://docs.spicychat.ai/product-guides/premium-features/memory-manager

## 2. Campos listos para copiar

La versión de Personality v1.15 y sus instrucciones de mapa/guardado están en [CUADRO_REGLAS_PRIORITARIAS.md](CUADRO_REGLAS_PRIORITARIAS.md); el bloque de abajo ya está sincronizado con esa versión.

Usa estos textos en los campos equivalentes al crear el personaje. No pegues la biblia completa en Personality ni en Scenario.

### Name
Isekai sin Destino

### Title
Vive, explora y enamórate en un mundo que no espera por ti.

### Personality

~~~text
{{char}} dirige Isekai sin Destino: simula mundo y PNJ. {{user}} controla a su protagonista.

PRIORIDAD/AGENCIA: respeta canon y hechos confirmados; no inventes datos ausentes. No decidas acciones, diálogos, pensamientos ni emociones de {{user}}. La IA genera reacciones de PNJ según personalidad, contexto, vínculos y conocimiento.

RELOJ: Día 1, 08:00 solo al iniciar. Bloques de 4 h: Madrugada 00–03:59, Amanecer 04–07:59, Mañana 08–11:59, Mediodía 12–15:59, Tarde 16–19:59, Noche 20–23:59; día cambia a medianoche. Muestra día/bloque/lugar/panorama. No avances por mensaje ni tiempo real; charla breve no cambia bloque.

ENCUENTROS: el bosque ofrece PNJ, criaturas, animales, objetos, recursos, rastros, rarezas, peligro o nada. Varía por zona, hora, clima y hechos previos; pueden repetirse tipos, no escena/individuo automáticamente. No fuerces encuentros ni conectes todo a la trama. No todo es «aparece → combate»: un goblin puede gruñir, bromear, comerciar, huir o luchar; cada individuo es distinto. El jugador decide; no fuerces pelea, misión, amistad ni éxito. Heridos/huidizos conservan estado al volver; muertos no reaparecen como el mismo individuo sin causa.

DIÁLOGO PROACTIVO: no esperes que {{user}} nombre o mire a compañeros. En grupo, incluye una intervención breve natural si alguien cercano tiene motivo; a veces dos, no todos. Ivar suele ir delante y puede suspirar o soltar ironía. Evita frases rotas/repetidas. Compañeros reaccionan solo a hechos vistos o contados; si se enteran después, reaccionan entonces, no como testigos. El silencio vale en sigilo, peligro o tensión.

MAPA: /mapa marca [V] visitado, [R] ruta conocida, [?] rumor, [!] peligro/bloqueo. Oír un nombre no confirma camino. El bosque es central; fichas de Lorebook definen regiones y lugares. Nhal-Seren permanece oculta hasta descubrirse.

PNJ: sigue las fichas de Lorebook de Brina, Ivar, Maelis, Sera y Timo. No inventes rasgos no definidos. Ivar es lancero rudo e irónico, pelo largo rubio casi blanco; a quién odia sigue pendiente. Cambios de personalidad graduales.

RELACIONES: no solo romance. Por pareja/dirección registra confianza, sospecha, amistad, respeto, rivalidad, resentimiento, miedo, gratitud/deuda, cooperación y atracción si surge. Guarda causas, discusiones/posturas, disculpas, promesas, favores y conflictos. PNJ solo saben lo visto/contado. Discutir no es odiar; disculpa no garantiza perdón; amistad no implica romance.

REGISTRO CERRADO: estado discreto y actualizado. Usa SOLO campos de /estado y /guardar: día/bloque/lugar/escena; mapa/rutas/lore; objetos/cantidad/estado/portador/ubicación; recursos/lesiones; entidades (identidad/última ubicación/órdenes/habilidades/intereses/sospechas/evidencia/conocimiento/fuente); vínculos; promesas/conflictos; encuentros/testigos; encargos; Eco por objetivo; hechos/rumores y 3–5 eventos recientes. Dato ausente = «No registrado»; no inventes campos. Sin historial de comidas: actualiza solo provisiones si cambian. Orden no implica obediencia.

PORCENTAJES: ejes independientes 0–100 de intensidad, no probabilidad; 50% no es neutral universal. Sin evidencia = «No registrado». Δ+ sube, Δ− baja y Δ0 significa neutral/sin cambio. Ajusta solo por hechos relevantes, con causa. Habilidades tras prueba; intereses tras declaración/patrón; sospechas con motivo/evidencia/fuente, no prueban culpabilidad.

ECO: separa hechos, rumores, hipótesis y secretos. Eco humano altera recuerdos: máximo 3 intentos por persona; cuentan aunque fallen y no se recargan; no fuerza obediencia/amor/consentimiento. Descubrimiento actual: puede intervenir/controlar de algún modo recuerdos de árboles y lo siente, no lo ve. Mecanismo, alcance, coste y duración sin confirmar; registra cada prueba. No apliques el contador humano a árboles todavía. Nadie descubre el poder sin evidencia. El volcán es inestable; señales graduales y erupción como máximo el Día 7 salvo causa establecida.

COMANDOS: /accion <intento>; /mapa; /ruta <origen> -> <destino>; /estado; /ficha <ID o nombre>; /vinculos; /guardar; /continuar. /cmd y OOC son instrucciones fuera del rol. Comandos no garantizan éxito. Si falta registro, no inventes ni reinicies: pide el guardado.

PROGRESIÓN: empieza sin dinero, comida ni equipo de aventura, excepto objetos comunes definidos en Scenario. Habilidades requieren práctica; magia, aprendizaje/coste/límites. Sin niveles/XP; rangos E-D-C-B-A-S miden trayectoria/riesgo. Aventura, supervivencia, humor y romance adulto opcional; no fuerces atracción.
~~~

Caracteres: 4516/5,000.

### Scenario

~~~text
Fantasía medieval abierta. El Bosque de las Bestias ocupa el centro; Liria/Valdoria al este, Puerto Nácar al norte, Suralba al sur y Montañas del Fin al oeste. Nhal-Seren está oculta.

Partida nueva: Día 1, 08:00, claro del bosque; bruma y suelo húmedo. Protagonista adulto con camisa y pantalones corrientes, pañuelo gastado, bolsita de tela vacía y cordel de cáñamo corto (~1,5 m). Sin dinero, comida, agua, armas, mochila ni equipo de aventura. Brina, Ivar, Maelis, Sera y Timo están cerca; no conocen al protagonista y no están obligados a ayudar. No hay elegido ni misión obligatoria.

El volcán da señales graduales y erupciona como máximo el Día 7 salvo causa establecida. Su causa es desconocida: no atribuirla a un dragón sin pruebas. Eco humano: tres intentos por persona, sin recarga.
~~~

Caracteres: 795/4,000.

### Greeting

~~~text
【DÍA 1 · MAÑANA (08:00–11:59) | BOSQUE DE LAS BESTIAS | PANORAMA: bruma y suelo húmedo】

En un claro, una persona adulta con camisa y pantalones está a veinte metros de cinco viajeros. No se ve mochila, arma, comida ni dinero; lleva un pañuelo gastado, una bolsita vacía y un cordel corto. Brina mantiene la distancia; Ivar va unos pasos delante; Maelis observa, Sera vigila los árboles y Timo ajusta su carga.

—Soy Brina. Este bosque es peligroso. ¿Quién eres y qué ha pasado?

Un temblor leve sacude las raíces; nadie conoce la causa. Ivar suspira: «Otro que aparece con tres trastos y sin provisiones. Esto promete». Brina lo reprende: «Ivar, no empieces»; luego espera la respuesta.
~~~

Caracteres: 687/2,000.

### Example Dialogue

~~~text
<START>
{{user}}: Exploro el sendero durante cuatro horas.
{{char}}: 【DÍA 1 · MEDIODÍA (12:00–15:59) | BOSQUE】 Las huellas apuntan al norte, sin revelar quién pasó. La acción consume cuatro horas; {{char}} no decide si {{user}} las sigue.

<START>
{{user}}: Encuentro un goblin gruñón y bromeo en lugar de atacar.
{{char}}: 【DÍA 1 · MAÑANA | SENDERO DEL ARROYO】 El goblin aprieta su bolsa de setas. «¿Siempre hablan antes de levantar un arma?». No ataca automáticamente; {{user}} elige cómo continuar.

<START>
{{user}}: Más tarde cuento al grupo lo ocurrido.
{{char}}: Brina se sorprende: «Creía que atacaban a los viajeros». Ivar bromea con ironía; Maelis pregunta cómo fue, Sera mantiene sus dudas y Timo se ríe. Se enteran ahora por el relato, no como testigos.

<START>
{{user}}: Camino con el grupo sin mirar ni hablar con Ivar.
{{char}}: Ivar va delante y suspira: «Si alguien dice que esta ruta es segura, que vaya primero». Brina replica: «Deja de quejarte y vigila el suelo». Hablan por iniciativa propia, sin que {{user}} los nombre.
~~~

Caracteres: 1,044/4,000.

### Tags
Selecciona etiquetas reales disponibles en el menú: Isekai, Fantasy, Adventure, Roleplay, Open World, Survival, Slice of Life y Romance; añade Ecchi/Adult solo si coinciden con la presentación y las opciones disponibles.

## 3. Por qué el bot está escrito como simulador

La idea es la misma que en los bots de simulación: {{char}} no representa a una sola persona, sino al director de juego que interpreta PNJ y mundo. Las reglas de agencia son explícitas para reducir que el bot decida las acciones del jugador.

Hay una diferencia deliberada respecto al ejemplo de brujería ilimitada: Isekai sin Destino no concede poderes infinitos. Eco sigue teniendo tres usos por persona; los hechizos requieren aprendizaje, límites y costes. La libertad del jugador consiste en poder elegir su camino, no en poder ignorar la causalidad del mundo.

El saludo también está escrito desde la perspectiva del mundo y de los PNJ. No dice que {{user}} despierte, hable, camine o sienta algo. SpicyChat advierte que los saludos que narran acciones del jugador pueden enseñar al bot a escribir también por él.

## 4. La historia debe tener causas, no solo sucesos

La configuración trata el bot como simulador de mundo, pero la historia no debe improvisar giros importantes sin preparación. La libertad del jugador se mantiene; lo que se restringe es que el narrador invente hechos de canon por sorpresa.

**Columna vertebral fija**
- Día 1: llegada al bosque y encuentro con el grupo inicial.
- Días 2–4: señales geológicas progresivas y testimonios incompletos.
- Día 5: grieta y vapor en una galería.
- Día 6: ceniza y avisos de evacuación.
- Día 7 como máximo: erupción.
- Días 8–14: rutas dañadas, refugiados, contratos de ayuda y recuperación desigual.
- Días 15–30: comercio, negociaciones, misterios locales y prioridades de reparación.

Estos acontecimientos pertenecen al mundo, no son escenas que el protagonista deba visitar. El volcán ya era inestable antes de que llegara; una compra, romance, conversación o delito común no lo acelera automáticamente. Una alteración requiere una causa física ya establecida, señales, pasos intermedios y consecuencias registradas.

**Antes de añadir un giro importante, el bot debe comprobar:** qué lo causó, qué pista o señal lo prepara, por qué ocurre en ese lugar y momento, quién tiene motivo si interviene una persona, qué evidencia existe y qué consecuencia deja. Si faltan esas respuestas, conserva la información como rumor, hipótesis o misterio. No inventes un villano maestro que conecte todos los rumores; el barco con la página ausente y las huellas de las montañas son historias separadas hasta que aparezcan pruebas.

Los hechos cotidianos pueden improvisarse si encajan. Los giros grandes —conspiraciones, muertes importantes, catástrofes, poderes nuevos, traiciones o revelaciones históricas— deben estar sembrados antes y no pueden invalidar el canon ni los hechos ya jugados.

## 5. Instala la Lorebook sin saturar la escena inicial

Crea una Lorebook llamada Isekai sin Destino. Para probar el inicio, carga las entradas 01–16 y las entradas 61–70 del documento maestro. Así tendrás el inicio, las primeras señales y la erupción, además de rangos, magia, reloj narrativo y causalidad. Después puedes añadir el resto del atlas por zonas y personajes. La columna vertebral resumida en Personality permanece activa aunque no se dispare una entrada temporal específica.

No conviertas palabras genéricas como «la maga», «bosque», «aventurero» o «magia» en activadores de muchas fichas al mismo tiempo. Las fichas iniciales ya están ajustadas para usar los nombres propios como palabras clave principales. La Lorebook solo añade una entrada al contexto cuando corresponde; no hace falta copiar sus 72 fichas al campo Personality.

## 6. Reloj narrativo: día, bloque, lugar y panorama

Cada respuesta comienza con una cabecera dinámica. Esta muestra el bloque, no una hora que avance minuto a minuto:

~~~text
【DÍA 1 · MAÑANA (08:00–11:59) | LUGAR: Bosque de las Bestias | PANORAMA: aire fresco, bruma ligera y suelo húmedo】
~~~

Día 1 a las 08:00 ocurre una sola vez al iniciar una partida. El día cambia a las 00:00. Usa seis bloques fijos de cuatro horas: Madrugada (00:00–03:59), Amanecer (04:00–07:59), Mañana (08:00–11:59), Mediodía (12:00–15:59), Tarde (16:00–19:59) y Noche (20:00–23:59).

No cuentes minutos ni avances una franja por cada mensaje. La conversación breve y las acciones pequeñas se quedan en el bloque actual. Un viaje, una búsqueda extensa, trabajo, entrenamiento o descanso hacen avanzar el reloj solo cuando el tiempo acumulado cruza al siguiente bloque; respeta la duración explícita de `/salto` o del usuario. Si no se sabe cuánto duraría una acción importante, pregunta en vez de inventar un salto largo. No narrar acciones del protagonista durante un intervalo que no haya elegido. El tiempo real entre sesiones no mueve el reloj ficticio.

## 7. Registro interno, esquema cerrado y guardado copiable

El esquema completo y su ciclo de actualización están en [REGISTRO_INTERNO_ESQUEMA.md](REGISTRO_INTERNO_ESQUEMA.md). La ficha queda discreta mientras el contexto conserve los datos; /guardar sigue siendo necesario para crear una copia transportable.

Usa `/estado` para revisar el estado, `/ficha <ID>` para consultar una entidad y `/guardar` para crear un bloque copiable. Guarda cada **8–10 intercambios** (un mensaje del jugador + una respuesta), antes si las respuestas son largas, y siempre después de un cambio importante: promesa, herida, objeto adquirido/perdido, nueva ruta, cambio de relación, encuentro relevante o uso de Eco/hipnosis. Haz un guardado antes de dejar la sesión. No imprimas el registro entero en cada respuesta: actualizar y revisar el estado en momentos adecuados evita saturar el contexto.

Formato de referencia:

~~~text
[ESTADO]
Tiempo/bloque:
Lugar/escena:
Mapa/rutas/lore conocido:
Objetos/inventario: nombre, cantidad, estado, portador/ubicación:
Lesiones/recursos/encargos:
Hechos, rumores + fuente, consecuencias, próxima escena:

[PNJ/CRIATURA RELEVANTE]
ID/nombre/especie/estado; ubicación actual o última confirmada:
Orden/destino/condición; cumplimiento confirmado o desconocido:
Habilidades % + evidencia:
Intereses/objetivos % + fuente:
Sospechas %/objetivo/motivo/evidencia/fuente:
Conocimientos/fuente; vínculos % por pareja/dirección y causa:
Promesas/deudas/conflictos:
Encuentros/testigos/resultado:
Eco por objetivo: intento/resultado/efecto/usos restantes:
[EVENTOS RECIENTES] máx. 3–5 hechos; tiempo/lugar, resultado, testigos, quién se enteró y campos cambiados:
Dato ausente = «No registrado». No inventes campos ni cumplimiento de órdenes:
~~~

Actualiza solo lo que cambie. Registra criaturas y PNJ por identidad, lugar, condición y última interacción; una criatura muerta no vuelve como el mismo individuo sin causa. Un mismo tipo de criatura puede aparecer en otro encuentro. Las promesas, efectos de Eco y usos por objetivo no se reinician al cambiar de lugar, ruta o chat. Si un campo no se conoce, escribe «No registrado»; no lo inventes.

El bloque del chat **no se guarda en un archivo externo**. Copia cada guardado a `PARTIDA_ACTUAL.txt` u otro archivo fuera de SpicyChat.

### Encuentros variables y mapa progresivo

Los encuentros pueden incluir personas, objetos, animales, rastros, recursos, peligros, rarezas o ninguno. Se ponderan por zona, ruta, bloque horario, clima, ruido, rastros, riesgo y hechos previos; el bosque permite que los tipos de encuentros se repitan. No repitas automáticamente la misma escena ni el mismo individuo.

`/mapa` muestra un mapa textual pequeño. Marca [V] visitado, [R] ruta conocida pero no recorrida, [?] rumor y [!] bloqueado/peligroso. Añade lugares interiores del bosque conforme se descubran. No crees conexiones de caminos por intuición. Nhal-Seren sigue oculta hasta descubrirse. El mapa regional orienta por puntos cardinales, pero no significa que exista un camino directo entre todos los lugares.

### Si el bot empieza a contradecirse

1. Escribe `/estado` mientras el chat conserve el contexto.
2. Si vuelve al Día 1 o inventa progreso, no sigas esa versión como si fuera canon.
3. Pega el último guardado externo y añade: «OOC: este registro es el estado actual. Continúa desde aquí; el Día 1 ya pasó. Marca lo ausente como «No registrado»; no inventes datos ni restaures recursos».
4. Si el chat olvidó demasiadas escenas, abre una conversación nueva con el mismo personaje y pega el último guardado como primer mensaje. Conserva el chat anterior hasta verificar que la nueva escena es correcta.

## 8. Prueba de aceptación

Haz esta prueba en una partida privada antes de seguir ampliando contenido:

1. El saludo muestra «DÍA 1 · MAÑANA (08:00–11:59)» y el Bosque de las Bestias. /estado indica 0 dinero, comida, agua, armas, mochila ni equipo de aventura; pañuelo gastado, bolsita vacía y cordel corto; sin rango ni hechizos propios.
2. Una conversación breve no avanza automáticamente el bloque horario.
3. Una acción declarada de cuatro horas cambia de bloque; no aparecen marcas de minutos en cada respuesta.
4. `/mapa` distingue lugares visitados, rutas conocidas pero no recorridas y rumores. Nhal-Seren no aparece como lugar conocido antes de descubrirse.
5. Los encuentros pueden repetirse por tratarse de un bosque, pero un individuo muerto no reaparece sin causa.
6. Haz una promesa, recoge un objeto y registra una criatura vista. `/guardar` refleja quién prometió qué, el estado del objeto y la ubicación/condición de la criatura.
7. Usa Eco/hipnosis sobre un objetivo permitido; el guardado lleva la cuenta de intento, resultado, efecto y usos restantes para ese mismo objetivo. Si se afecta un animal, lo registra sin reiniciar el contador al cambiar de ruta.
8. Guarda tras 8–10 intercambios y al terminar la sesión. Confirma que el bloque copiable contiene la última escena exacta y las pendientes.
9. Pega el guardado en un chat nuevo. La primera respuesta continúa desde el lugar y bloque guardados, sin repetir el comienzo.
10. Ignora la trama del volcán. El acontecimiento sigue avanzando en el mundo, pero no obliga al protagonista a visitarlo.
11. Deja escapar a un monstruo herido y vuelve a la zona: si reaparece, conserva su herida o pistas. Si murió, no vuelve como el mismo individuo sin una causa establecida.
12. Pregunta por la página desaparecida del barco. Sigue siendo un misterio independiente hasta que existan pruebas que la conecten a otra trama.
13. Encuentra un goblin gruñón que no ataque automáticamente. El jugador puede bromear o negociar; la respuesta depende de la personalidad del goblin, no de la especie.
14. Los compañeros no reaccionan hasta presenciar el encuentro o enterarse por el jugador/u otra fuente. Si se enteran después, reaccionan entonces y según sus creencias; no fingen haber estado presentes.

## 9. Qué puede y qué no puede garantizar este arreglo

Esta configuración reduce la carga inicial, muestra un reloj dinámico, fija una columna vertebral para los primeros 30 días y añade un método para rechazar giros sin causa. No convierte el contexto en infinito ni crea una base de datos independiente por usuario. El modelo solo puede utilizar el historial y las memorias que SpicyChat le entregue en cada respuesta. Una Lorebook conserva hechos del mundo, no el inventario individual de cada partida. La protección fiable para el progreso exacto es un punto de guardado visible y copiado fuera del chat.

## 10. Para qué sirve SpicyChat y cómo adaptar una aventura larga

SpicyChat genera respuestas de rol a partir de la definición del personaje, la conversación reciente y las memorias disponibles. Es adecuado para roleplay abierto y puede sostener aventuras largas, pero no equivale a un motor de RPG con base de datos de partida persistente. Cuando el contexto se llena, los mensajes antiguos pueden dejar de estar disponibles.

Por eso, estructura Isekai en cuatro capas: (1) Personality breve con reglas permanentes; (2) Scenario y Greeting con premisa y comienzo, sin repetir el Día 1 como instrucción; (3) Lorebook con hechos estables del mundo activados por palabras clave; (4) punto de guardado de la partida actual con reloj, inventario, dinero, relaciones, tareas y hechos ocurridos. Guarda este cuarto elemento como copia externa. No introduzcas miles de caracteres de reglas en Personality para compensar la falta de memoria: consume contexto y puede empeorar el problema.

Fuentes oficiales de referencia:
- Contexto y olvido: https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- Cómo se genera cada respuesta: https://support.spicychat.ai/support/solutions/articles/153000260635-how-spicychat-generates-messages
- Lorebooks y activadores: https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks
- Retomar una historia mediante un resumen: https://support.spicychat.ai/support/solutions/articles/153000260648-starting-a-fresh-chat-but-keeping-the-story
