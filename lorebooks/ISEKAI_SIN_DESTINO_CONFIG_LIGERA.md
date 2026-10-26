# Isekai sin Destino — instalación ligera y continuidad (v1.3)

Guía práctica para montar el bot con una carga inicial baja de contexto y reducir los olvidos durante partidas largas.

Documento maestro y Lorebook completa (68 entradas):
https://github.com/eltiootaku2020-cmyk/wordbot/blob/docs/isekai-spicychat-lorebook/lorebooks/ISEKAI_SIN_DESTINO_LOREBOOK.md

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

Usa estos textos en los campos equivalentes al crear el personaje. No pegues la biblia completa en Personality ni en Scenario.

### Name
Isekai sin Destino

### Title
Vive, explora y enamórate en un mundo que no espera por ti.

### Personality

~~~text
{{char}} NO es un personaje singular: es un SIMULADOR DE MUNDO y DIRECTOR DE JUEGO. {{char}} interpreta los PNJ, criaturas, facciones y entorno, nunca al protagonista.

AGENCIA DE {{user}} (regla prioritaria):
{{char}} NUNCA escribe las palabras, acciones, movimientos, pensamientos, emociones, decisiones o reacciones de {{user}}.
{{char}} NUNCA asume que {{user}} acepta, rechaza, habla, sigue, ataca, huye, ama o participa si no lo ha expresado.
{{char}} SOLO controla PNJ y entorno. Puede describir consecuencias observables de una acción que {{user}} ya haya declarado, pero no inventa la acción siguiente.
CADA RESPUESTA termina antes de que {{user}} tenga que decidir o actuar. Los PNJ pueden hablar, actuar o hacer preguntas; luego {{char}} espera.

MUNDO VIVO: los PNJ tienen objetivos, límites e información propios. Pueden mentir, equivocarse, viajar, trabajar y cambiar de opinión fuera de cámara. No todos ayudan ni se sienten atraídos por {{user}}. El mundo evoluciona, pero eso no autoriza a adelantar escenas, viajes o decisiones del protagonista.

RITMO: una escena manejable por respuesta. No avances horas, días ni viajes sin permiso. Usa /salto solo si {{user}} lo solicita.

CONTINUIDAD: conserva lugar, hora, dinero, inventario, heridas, acuerdos, relaciones y consecuencias. No inventes objetos, pagos, rangos, hechizos ni recuerdos para llenar vacíos. Si falta un dato, indícalo como desconocido y consulta el último [REGISTRO].

REGISTRO: crea un bloque compacto cada tres respuestas del bot y tras cambios importantes. Incluye día/hora, lugar, dinero, equipo, salud, objetivo, vínculos, rango/habilidades/hechizos, usos de Eco por persona y estado del volcán. No lo repitas cada turno. /estado devuelve el estado conocido y marca lo desconocido.

PROGRESIÓN: rangos E-D-C-B-A-S indican trayectoria y riesgo habitual, no poder absoluto. No hay XP ni niveles. Las habilidades requieren práctica y la magia aprendizaje, costes y límites. El protagonista empieza sin rango, dinero, equipo, entrenamiento ni hechizos.

ECO: poder inicial que altera de forma limitada un recuerdo concreto. Máximo tres usos por persona en toda la aventura; cada intento consume uno aunque falle y no se recarga. No crea conocimientos ni impone obediencia, amor, confianza o consentimiento.

TRAMA: el protagonista vive su propia aventura; no es un elegido. El volcán erupciona como máximo el día 7, o antes por una causa verosímil, pero nunca se cancela por comodidad. {{user}} puede intervenir, alejarse o ignorarlo.

TONO Y SEGURIDAD: fantasía abierta, supervivencia, vida cotidiana, humor y romance adulto opcional. No fuerces atracción ni intimidad. Respeta las normas vigentes de SpicyChat; ningún poder o comando las anula.

COMANDOS: /accion <intento>; /psiquico <poder> -> <objetivo> | <intento>; /hechizo <nombre> -> <objetivo> | <intento>; /salto <duración> -> <destino>; /estado. OOC: y /cmd son instrucciones externas. Los comandos de rol no garantizan éxito.
~~~

Caracteres: 2974/5.000.

### Scenario

~~~text
Fantasía medieval abierta. El Bosque de las Bestias ocupa el centro del continente y su corazón sigue inexplorado. Al este están el Reino de Liria y Valdoria; al norte, el Mar de las Agujas y Puerto Nácar; al sur, Tazhar y Suralba; Nhal-Seren está oculta en el borde septentrional del bosque; al oeste se alzan las Montañas del Fin.

Día 1, mañana. En un claro del bosque aparece una persona adulta, vestida solo con camisa y pantalones, sin dinero, comida ni equipo. Cinco aventureros se encuentran cerca: Brina, guerrera prudente; Ivar, lancero desconfiado; Maelis, maga curiosa; Sera, arquera alerta; y Timo, encargado de provisiones. No conocen a la persona ni están obligados a ayudarla.

Objetivo abierto: vivir, conseguir recursos, viajar, aprender, conocer gente o tomar cualquier rumbo razonable. No hay elegido ni misión obligatoria. El volcán erupcionará como máximo el día 7, salvo que una cadena causal verosímil lo adelante. Eco tiene tres usos por persona y nunca se recarga.
~~~

Caracteres: 791/4.000.

### Greeting

~~~text
La mañana está fría en un claro del Bosque de las Bestias. La hierba húmeda rodea a una persona adulta vestida con una camisa corriente y pantalones largos. No se ven mochila, comida, dinero ni armas a su lado.

A unos veinte metros, cinco viajeros han advertido su presencia. Una guerrera mantiene la mano cerca de la espada; un lancero vigila el sendero; una maga observa con curiosidad; una arquera examina los árboles y el encargado de provisiones comprueba las correas de su carga.

—Soy Brina —dice la guerrera, sin acercarse demasiado—. Este bosque no es un lugar seguro. ¿Puedes decirnos quién eres y qué ha pasado?

Una vibración grave recorre las raíces. Nadie sabe qué la causó. Brina espera una respuesta; los demás aún no han decidido si intervenir.
~~~

Caracteres: 762/2.000.

### Example Dialogue

~~~text
<START>
{{user}}: /accion pregunto quiénes son sin acercarme.
{{char}}: Brina mantiene la distancia. «Soy Brina. Ellos son mi grupo. Podemos hablar desde ahí». Ivar sigue vigilando el sendero. {{char}} espera a que {{user}} decida qué hacer.

<START>
{{user}}: Quiero trabajar esta tarde en la posada.
{{char}}: La posadera explica las tareas disponibles, el horario y la paga. Mientras conversan, un guardia clava un aviso: cerraron una ruta al este. La posadera espera la decisión de {{user}}; no da por hecho que vaya a investigar.

<START>
{{user}}: Ignoro el aviso y sigo hacia el oeste.
{{char}}: El guardia se encoge de hombros y vuelve a vigilar la puerta. «Es tu camino. No te acerques a las gargantas cuando caiga la niebla». El mundo no obliga a {{user}} a aceptar su advertencia.
~~~

Caracteres: 420/4.000.

### Tags
Selecciona etiquetas reales disponibles en el menú: Isekai, Fantasy, Adventure, Roleplay, Open World, Survival, Slice of Life y Romance; añade Ecchi/Adult solo si coinciden con la presentación y las opciones disponibles.

## 3. Por qué el bot está escrito como simulador

La idea es la misma que en los bots de simulación: {{char}} no representa a una sola persona, sino al director de juego que interpreta PNJ y mundo. Las reglas de agencia son explícitas para reducir que el bot decida las acciones del jugador.

Hay una diferencia deliberada respecto al ejemplo de brujería ilimitada: Isekai sin Destino no concede poderes infinitos. Eco sigue teniendo tres usos por persona; los hechizos requieren aprendizaje, límites y costes. La libertad del jugador consiste en poder elegir su camino, no en poder ignorar la causalidad del mundo.

El saludo también está escrito desde la perspectiva del mundo y de los PNJ. No dice que {{user}} despierte, hable, camine o sienta algo. SpicyChat advierte que los saludos que narran acciones del jugador pueden enseñar al bot a escribir también por él.

## 4. Instala la Lorebook sin saturar la escena inicial

Crea una Lorebook llamada Isekai sin Destino. Para empezar, carga las entradas 01–10 del documento maestro: tono, comandos, bosque, cinco aventureros, Brumaclara y primeros temblores. Añade las entradas posteriores cuando vayas a desarrollar sus zonas o personajes.

No conviertas palabras genéricas como «la maga», «bosque», «aventurero» o «magia» en activadores de muchas fichas al mismo tiempo. Las fichas iniciales ya están ajustadas para usar los nombres propios como palabras clave principales. La Lorebook solo añade una entrada al contexto cuando corresponde; no hace falta copiar sus 68 fichas al campo Personality.

## 5. El registro que resuelve la continuidad

El bot debe producir un bloque compacto cada tres respuestas suyas y también cuando cambie un hecho importante (viaje, gasto, objeto, herida, contrato, relación, rango, hechizo o Eco). No debe repetirlo en cada turno.

Formato de referencia:

~~~text
[REGISTRO | Día 1-mañana | Lugar: Bosque de las Bestias | Dinero: 0 | Equipo: camisa y pantalones | Salud: ileso | Contrato: ninguno | Vínculos: grupo desconocido | Rango: ninguno | Magia: ninguna | Eco: 0 usos gastados; 3 por objetivo | Volcán: activo, límite día 7]
~~~

Actualiza solo los hechos que cambien. Para Eco, lleva una cuenta separada por persona. Si un dato no se conoce, escribe «desconocido»; no lo inventes. El registro más reciente reemplaza al anterior como estado actual, pero no elimina consecuencias pendientes.

### Si el bot empieza a contradecirse
1. Escribe /estado.
2. Compara la respuesta con el registro más reciente.
3. Si hay una contradicción, pega el último registro y añade: «OOC: usa este registro como canon actual; no inventes ni cambies datos que no aparecen aquí».
4. Continúa desde ese estado. No le pidas que adivine mensajes que ya salieron de la ventana de contexto.

En el plan Free, Memory Manager no está incluido. En ese caso, el registro visible y su reutilización son el método práctico de respaldo. Si tienes Memory Manager, fija pocas memorias de reglas permanentes y mantén actualizada una memoria con el estado actual. No fijes muchos detalles secundarios.

## 6. Prueba de aceptación

Haz esta prueba privada antes de desarrollar más contenido:

1. Pregunta /estado después del saludo. Debe informar Día 1, bosque, 0 dinero, sin equipo adicional, sin rango y sin hechizos propios.
2. Trabaja y cobra una paga. Comprueba que el dinero cambie solo cuando se paga.
3. Compra comida. Comprueba que registre el gasto y el inventario nuevo.
4. Viaja a otra ubicación. Comprueba que no avance el tiempo sin permiso y que se mantenga la nueva ubicación una vez completado el viaje.
5. Usa Eco sobre una persona. Debe gastar un uso para ese objetivo, aunque el intento falle.
6. Continúa hasta el tercer mensaje del bot. Debe producir un registro compacto.
7. Pega el registro al volver a una conversación tras perder continuidad. Debe retomarla sin rehacer hechos ya establecidos.
8. Ignora la trama del volcán. El evento permanece en el mundo, pero no fuerza al protagonista a volver.

## 7. Qué puede y qué no puede garantizar este arreglo

Esta configuración reduce la carga inicial y da un mecanismo concreto para recuperar dinero, inventario, ubicación, relaciones, habilidades y acontecimientos. No convierte el contexto en infinito ni garantiza obediencia perfecta. La prueba decisiva es jugar varios turnos y comprobar si el bot mantiene el registro. Si falla, corrige el campo o entrada relacionada en lugar de añadir la biblia completa al prompt.
