# 27 — Próximos pasos y prioridades de desarrollo de Isekai sin Destino

**Estado:** análisis técnico y hoja de ruta propuesta; no canoniza contenido narrativo ni autoriza cambios de runtime por sí sola.  
**Fecha de revisión:** 31-10-2026.  
**Base técnica inspeccionada:** rama `fix/isekai-time-neutral-turns` (PR #41).  
**Alcance:** ordenar las próximas mejoras del mundo vivo y del motor sin convertir Word Bot en un conjunto de agentes o subsistemas innecesarios.

## 1. Resumen ejecutivo

La recomendación principal es **no añadir más contenido y sistemas en paralelo todavía**. La siguiente etapa debería cerrar las dependencias que hacen que el resto de las funciones sean fiables:

1. Convertir el reloj en un sistema persistente de segundos y acciones verificables.
2. Hacer que los viajes se calculen a partir de rutas, distancias aproximadas y terreno.
3. Añadir hora ambiental y clima persistente por región.
4. Construir autonomía básica de personajes sobre esos intervalos, empezando por una entidad/personaje a la vez.
5. Integrar PSICHO-Eco y su entidad demoníaca con una ficha y una progresión registradas, sin desbloqueos inventados.
6. Después ampliar exploración, mapa, acontecimientos del Día 12 y rutas/finales.

El mayor riesgo actual sería construir agendas, clima, fatiga, combate y eventos del volcán sobre un reloj que todavía depende de un número global propuesto por el narrador. El orden anterior reduce retrabajo.

## 2. Estado verificado del repositorio

### 2.1 PRs relevantes revisadas

| PR | Contenido | Estado comprobado |
|---:|---|---|
| #21 | Programador de acontecimientos mundiales | Abierta, no integrada |
| #38 | Agendas independientes de Brina, Maelis y Sera | Borrador, no integrado; documentación |
| #39 | Reloj, duraciones y prehistoria del trío | Borrador, no integrado; documentación |
| #40 | Auditoría de coherencia temporal | Borrador, no integrado; documentación |
| #41 | Evitar avance temporal automático por turno | Borrador, no integrado; código |
| #42 | Reloj persistente por segundos, precisión diaria y modelo ambiental | Borrador, no integrado; documentación |
| #43 | Entidad demoníaca como origen de PSICHO-Eco | Borrador, no integrado; documentación |

Dependencias relevantes:
- La cadena de mundo vivo llega de PR #21 a #40 mediante PRs apiladas.
- PR #41 parte de PR #40; PR #42 parte de PR #41.
- PR #43 parte de PR #40, no de PR #42. Es una rama documental paralela a la propuesta del reloj.
- No integrar, cerrar ni rebasar estas ramas automáticamente. Revisar el orden de integración cuando se decida cerrar cada dependencia.

### 2.2 Validación técnica de PR #41

La última ejecución consultada de GitHub Actions para el commit `4a8d2fc73ddcc76006d01ef8e19a7f90b8eb01a9` fue el run #274:
- **112 pruebas Python aprobadas.**
- Un aviso de deprecación Starlette/httpx en el test client.
- El paso de sintaxis JavaScript de la interfaz terminó correctamente.
- No equivale todavía a una campaña manual de 50–100 turnos con ChatGPT/Gemini web ni a una prueba manual completa en Windows.

Run: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/41209200614

## 3. Hallazgos del código actual

Los siguientes puntos se comprobaron en `proyecto/app/src/canon_manager` de la rama de PR #41; no son suposiciones del diseño narrativo.

| Área | Estado actual | Consecuencia |
|---|---|---|
| Reloj de sesión | SQLite guarda `day` y `minute_of_day`; no `second_of_minute` | No puede conservar intervalos de 1–59 segundos |
| Respuesta del narrador | `NarratorResponse` usa un único `elapsed_minutes`, con valor predeterminado 0 | No identifica qué acción consumió el tiempo |
| Aplicación del reloj | El servidor acepta y aplica una propuesta del narrador entre 0 y 15 minutos | La regla depende todavía de la estimación del modelo; no se verifica localmente la duración de cada acción |
| Eventos programados | `world_timeline_events` exige día y minuto | No representa un acontecimiento que solo tenga precisión de día |
| Activación de eventos | El programador comprueba eventos al cerrar/aplicar el avance de un turno | No puede interrumpir de forma exacta una actividad larga en un instante intermedio |
| Registro del evento | El ledger escribe el mismo instante programado en los campos programado/activado | No conserva por separado el momento real en que el runtime lo procesó |
| Movimiento | `MovementProposal` solo comunica entidad, destino, motivo y evento | No hay distancia, tramo, ruta, pendiente ni terreno para calcular el viaje |
| Uso de poder | `PowerUseProposal` comunica habilidad, objetivo, resultado y coste | No separa preparación, activación, concentración mantenida ni progreso |
| Definición de poderes | Existe registro de usos `ability_uses`, pero no una tabla dedicada de definiciones/progresión de habilidades en el esquema inspeccionado | El origen y evolución de PSICHO-Eco requieren un modelo posterior, no solo sumar usos |
| Entidades | `entities` conserva tipo y perfil de texto | Sirve para personajes generales; el demonio todavía no tiene una relación estructurada como fuente de una habilidad |
| Clima | No existe estado regional de clima en el esquema inspeccionado | No hay lluvia/nubes/viento persistentes ni efectos ambientales verificables |
| Agendas | No existe runtime de agenda autónoma en las tablas inspeccionadas | PR #38 sigue siendo diseño, no comportamiento ejecutable |
| UI | Hay interfaz local de chat y estado; el reloj se presenta con etiqueta horaria | Puede evolucionar con un HUD pequeño sin rehacer toda la interfaz |

### 3.1 Qué sí está bien encaminado

- La aplicación mantiene SQLite como fuente local del estado.
- La inicialización activa claves foráneas y modo WAL.
- Las escrituras de turno/restauración usan transacciones; el inicio de transacción usa `BEGIN IMMEDIATE`.
- Existen snapshots previos a turnos, undo y una API de backup/restore con validación.
- El programador evita activar dos veces el mismo evento por sesión mediante una clave única.
- El contrato narrativo limita operaciones sobre inventario, recursos y poderes mediante IDs y eventos fuente.
- PR #41 impide que un mensaje, por el mero hecho de ser un turno, tenga que gastar tiempo.

Estos cimientos deben conservarse. SQLite documenta transacciones serializables y escrituras atómicas; WAL permite lectores y escritores concurrentes, aunque requiere conservar correctamente el archivo WAL durante copias directas. El backup API ya usado por el proyecto es preferible a copiar archivos SQLite en caliente sin coordinar sus componentes. Referencias: https://www.sqlite.org/isolation.html y https://www.sqlite.org/wal.html

## 4. Prioridad P0 — Reloj y duración de acciones

**Recomendación: siguiente entrega técnica principal.**

### Objetivo

Que el reloj avance por acciones realizadas y cuantificables, no por mensajes, longitud de respuesta ni una cifra libre del narrador.

### Diseño recomendado

#### A. Unidad temporal

- Adoptar segundos enteros como unidad interna.
- Mantener `day` y `minute_of_day` para compatibilidad con la interfaz y datos existentes.
- Añadir `second_of_minute` persistente de 0 a 59.
- Centralizar conversiones a segundos absolutos en funciones puras.
- Conservar la etiqueta de franja horaria como dato derivado; nunca guardar una segunda etiqueta que pueda contradecir el reloj.

#### B. Segmentos de acción

En lugar de que el modelo entregue solo `elapsed_minutes`, preparar una lista de segmentos con, como mínimo:
- actor;
- tipo de acción;
- inicio/duración estimada en segundos;
- acción fuente que el usuario autorizó;
- relación temporal (secuencial, simultánea o fase interna);
- ubicación;
- resultado (ejecutada, parcial, interrumpida, fallida o no iniciada);
- base de la estimación y confianza.

**La IA puede describir qué acción ocurrió y proponer sus parámetros; la aplicación debe validar la autorización y calcular/validar el coste temporal usando reglas locales.** El modelo no debe poder inventar que caminar 100 metros tomó dos horas ni que una búsqueda exhaustiva duró diez segundos.

Las estimaciones pueden ser aproximadas cuando el mapa o los datos sean aproximados, pero deben quedar marcadas como tales. Ante datos insuficientes, el motor debe pedir precisión o dejar una duración pendiente; no inventarla.

#### C. Reglas de contabilización

- Acciones consecutivas se suman.
- Acciones simultáneas comparten el mismo intervalo global; no sumar horas-persona.
- Una fase incluida en otra acción no se cobra de nuevo.
- Una acción anunciada que nunca se ejecuta no consume tiempo.
- Una búsqueda fallida sí consume el tiempo de búsqueda que realmente se realizó.
- Un poder distingue preparación, activación, mantenimiento/concentración y duración del efecto; no son lo mismo.
- El tiempo de conversación refleja lo realmente hablado, no el tamaño del mensaje del jugador o del narrador.
- Un salto de tiempo grande continúa requiriendo autorización explícita del usuario.

#### D. Eventos que ocurren durante acciones

Una caminata o exploración de 40 minutos debe poder dividirse en segmentos temporales si hay un evento, encuentro o cambio ambiental en medio. El motor debe:
1. avanzar hasta el siguiente límite temporal;
2. resolver el evento pendiente;
3. actualizar conocimiento y condiciones;
4. continuar, interrumpir o detener la acción según el evento.

Acontecimientos con hora definida pueden ser puntos temporales exactos. Acontecimientos que solo tienen día definido deben mantener una ventana diaria y no recibir las 00:00 como hora ficticia.

### Criterios mínimos de aceptación

1. Un saludo o pregunta no avanza el reloj.
2. Una frase hablada breve consume segundos, no un minuto obligatorio.
3. Seis acciones secuenciales de 10 segundos suman exactamente 60 segundos.
4. Acciones de 30 y 20 segundos simultáneas avanzan 30 segundos globales.
5. Una fase interna de otra actividad no duplica duración.
6. 23:59:50 + 20 segundos produce el día siguiente a las 00:00:10.
7. Una acción interrumpida cobra solo el tramo realizado.
8. Un evento con hora exacta puede detener/interrumpir una acción segmentada.
9. Un evento de precisión diaria no se convierte en medianoche.
10. Reinicio, undo, reintento, backup y restore conservan los segundos y no duplican eventos.

## 5. Prioridad P1 — Rutas y desplazamiento

No es posible hacer realista el tiempo de caminata si el motor conoce solo el nombre del destino. Antes de una simulación de viajes compleja, necesitamos un **grafo de rutas sencillo**, aunque el mapa todavía no sea visual.

### Datos mínimos de un tramo

- origen y destino;
- longitud aproximada o banda de distancia (corta/media/larga);
- tipo de camino/terreno;
- pendiente/dificultad, si se conoce;
- si la ruta es conocida, dudosa, oculta o temporal;
- si está abierta, bloqueada o peligrosa;
- estimación y procedencia de la información.

### Cálculo del viaje

La velocidad efectiva depende de terreno, inclinación, carga, estado físico, ritmo del grupo, visibilidad, clima, obstáculos y método de desplazamiento.

No usar una velocidad única para todo el bosque. Tampoco inventar kilómetros exactos si el mapa solo registra que una ruta es corta o difícil. El motor puede mostrar rangos de llegada cuando los datos son incompletos.

### Orden recomendado

1. Crear tramos sin mapa visual, con distancias aproximadas.
2. Calcular duración y conservar el resultado en el ledger de acciones.
3. Añadir desvíos, bloqueos y caminos desconocidos.
4. Construir después un mapa visual interactivo que represente esos mismos nodos/conexiones, no un segundo mapa con datos diferentes.

## 6. Prioridad P2 — Hora ambiental, clima y peligro contextual

### Hora del día

La hora exacta debe seguir siendo autoritativa. La UI deriva madrugada, amanecer, mañana, mediodía, tarde, atardecer, noche y medianoche. Las franjas deben tener límites coherentes; el amanecer/atardecer podrán depender de estación y región en una fase posterior, no de una tabla astronómica compleja desde el primer prototipo.

### Clima regional persistente

El clima pertenece a una región o zona, no a todo el mundo simultáneamente. El estado debe guardar:
- condición: soleado, nublado, lluvia, niebla, tormenta o viento;
- intensidad;
- visibilidad;
- viento;
- estado del suelo (seco, húmedo, barro, inundado, helado u otros cuando proceda);
- momento de inicio/cambio y origen del cambio.

El clima no se vuelve a sortear en cada mensaje. Cambia por una transición ambiental justificada, permanece registrado y se conserva en guardados, undo y backups.

### Efectos contextuales, no penalizaciones automáticas

- Noche: afecta la visibilidad solo según luz, luna, iluminación y equipo.
- Lluvia: puede alterar huellas, tracción, fuego y estado de ropa/equipo.
- Niebla: reduce la distancia de detección y dificulta orientarse.
- Viento: puede afectar proyectiles, sonido y temperatura.
- Tormenta: puede exigir refugio cuando la exposición y el terreno lo justifiquen.

Cada estado ambiental puede aportar ventajas además de riesgos: la lluvia puede ocultar sonidos, la niebla cubrir una retirada y la noche dificultar la detección por parte de patrullas.

### Peligro de exploración

No usar una variable global de «peligro» que responda por sí sola a todas las situaciones. Evaluar por separado:
- amenazas conocidas o posibles;
- visibilidad y distancia de detección;
- cobertura y posibilidades de ocultación;
- ruido;
- terreno y vías de escape;
- rastros y señales;
- cansancio, heridas y equipo;
- conocimiento real del grupo.

## 7. Prioridad P3 — Entidades y agendas autónomas

PR #38 documenta agendas, pero el runtime aún no las ejecuta. Conviene implementar un sistema pequeño, no agentes independientes con memoria y prompts separados para cada PNJ.

### Motor genérico

Una agenda mínima puede contener:
- objetivo activo;
- actividad prevista;
- prioridad y motivo;
- ubicación;
- precondiciones;
- tiempo requerido;
- recursos/capacidades necesarias;
- conocimiento que habilita la decisión;
- resultado y evidencia;
- siguiente decisión posible.

El motor evalúa esas agendas solo cuando transcurre tiempo suficiente o hay un evento relevante. No debe simular una vida entera por cada mensaje ni generar una escena obligatoria en cada franja horaria.

### Implementación progresiva

- Primera prueba con **una entidad nueva cada vez**.
- Después validar el sistema con Brina, Maelis y Sera por separado.
- Solo luego permitir actividades simultáneas entre ellas.
- Los personajes deben poder esperar, fallar, negarse, cambiar de objetivo o no hacer nada relevante.
- El protagonista recibe solo lo que pudo ver, escuchar, deducir o descubrir; las escenas privadas siguen privadas.

### Criterios de aceptación

Una aventurera no cambia de ubicación sin tiempo/ruta. Maelis no investiga algo que desconoce. Sera no encuentra rastros que no existen. Brina no protege automáticamente a todo el mundo. Las agendas no heredan conocimiento de otros PNJ sin comunicación.

## 8. Prioridad P4 — Entidad demoníaca y desarrollo de PSICHO-Eco

La ficha de concepto está registrada en PR #43. La siguiente etapa narrativa no debería convertirla inmediatamente en una nueva mecánica global.

### Primero: cerrar una ficha jugable mínima

Datos ya confirmados:
- entidad pequeña de naturaleza demoníaca;
- origen directo de PSICHO-Eco;
- alianza con el protagonista;
- protagonista como tercer portador;
- dos portadores anteriores fallecidos por confiarse y no desarrollar el poder;
- motivación de la entidad: evitar una tercera muerte y ayudar al protagonista a desarrollar el poder.

Datos todavía abiertos:
- nombre y diseño anime 2D;
- personalidad y voz;
- cómo y cuándo se manifiesta;
- quién puede verla/oirla;
- si puede separarse o está vinculada al portador;
- qué sabe de los portadores anteriores;
- límites y capacidades propias;
- conexión exacta con la diosa chibi.

### Después: integración técnica

- Tratarla como una entidad del mundo Isekai, no como un agente especial global de Word Bot.
- Definir la relación entre la entidad y la fuente de habilidad mediante datos estructurados (por ejemplo, una definición de habilidad vinculada a una entidad de origen).
- Diferenciar la presencia física, manifestación y comunicación privada. No hacer que Brina, Maelis o Sera oigan al demonio si no pueden percibirlo.
- Mantener el registro de uso de poderes, pero añadir una definición/progresión explícita de la habilidad antes de sumar más contadores.
- Separar activación, intento, coste, resultado, duración, resistencia y progreso.
- No dar experiencia ni desbloquear ramas por hablar con el demonio; el progreso debe tener un criterio verificable aprobado.
- Los portadores uno y dos permanecen sin nombre ni biografía hasta decisión del autor.

La cantidad de portadores no debe confundirse con el antiguo límite de tres intentos de la Lorebook anterior.

## 9. Prioridad P5 — Necesidades y condición física

Hambre, sed, sueño, fatiga, heridas, recuperación y concentración son importantes, pero dependen del tiempo y de las acciones. Deben entrar después de P0–P2.

Empezar con pocas variables observables y fáciles de entender:
- hidratación;
- hambre;
- cansancio/sueño;
- fatiga física;
- estado de heridas.

Añadir frío/calor, carga, infección, energía mágica o estrés solo cuando una escena o sistema los necesite. Evitar 30 barras que no cambien decisiones.

Los cambios deben producirse por tasas y acciones explicables, no por una penalización arbitraria en cada turno.

## 10. Prioridad P6 — Exploración, mapa y contenido narrativo

Después de tiempo, rutas y ambiente:
- mapa interactivo del Bosque de las Bestias basado en el grafo de rutas;
- puntos de interés, zonas conocidas/desconocidas y rutas bloqueadas;
- exploración por acción (observar, examinar, buscar, rastrear, recolectar, entrar, retirarse);
- objetos con ubicación, portador, condición y causa de adquisición;
- descubrimiento gradual: el catálogo interno no equivale al conocimiento del protagonista;
- encuentros no obligatorios y probabilidades condicionadas por hábitat, hora, clima, ruido y actividad;
- cronología y agendas del Día 1 al Día 12;
- erupción del Día 12 como acontecimiento diario hasta que su hora sea definida;
- cinco finales como consecuencias emergentes, no como botones de ruta.

La historia previa del trío, los arcos individuales y los objetivos personales deben aprobarse por separado. No inventar una cronología compartida solo para llenar las agendas.

## 11. Prioridad P7 — Interfaz y experiencia de juego

Mantener el principio de bajo consumo y claridad:
- cabecera pequeña con día, hora, franja del día y clima local;
- lugar actual y una indicación contextual de visibilidad/peligro, sin una puntuación universal;
- acciones sugeridas (tres opciones) más acción libre;
- panel desplegable de grupo, inventario, relaciones y poderes;
- mapa liviano por nodos y rutas;
- registro de eventos y cambios con opción de revisar qué se guardó;
- indicador de duración estimada antes de confirmar viajes o tareas largas cuando la incertidumbre sea relevante.

No empezar con mapas 3D, animaciones pesadas, avatares en tiempo real o varios agentes de IA. Los personajes se representan mediante imágenes 2D de estilo anime coherente.

## 12. Arquitectura: qué debe ser global y qué pertenece a Isekai

**Word Bot debe seguir siendo el motor narrativo general.** No incorporar PSICHO-Eco, el volcán, el demonio ni las reglas del Bosque como lógica fija global.

| Motor global (reutilizable) | Datos/reglas propios de Isekai |
|---|---|
| Reloj, intervalos y ledger de acciones | Franja y condiciones del Bosque de las Bestias |
| Eventos programados y precisión temporal | Erupción del volcán Día 12 |
| Entidades, relaciones y conocimiento | Brina, Maelis, Sera y la entidad demoníaca |
| Agenda y resolución de actividades | Objetivos y decisiones particulares de cada personaje |
| Rutas, movimiento y terreno | Grafo geográfico del Bosque |
| Registro de habilidades y progreso | PSICHO-Eco, portadores y ramas de poder |
| Clima/ambiente regional | Patrones meteorológicos de cada región fantástica |
| Validación, snapshots, undo, backup/restore | Canon y decisiones narrativas de esta campaña |

La IA debe proponer y narrar; la aplicación mantiene el estado oficial, valida las operaciones y conserva la procedencia.

## 13. Qué conviene no añadir todavía

- Más personajes importantes antes de completar el primer personaje nuevo.
- Un agente de IA por PNJ o varios sistemas de memoria paralelos.
- Decenas de estadísticas físicas o emocionales sin efecto jugable.
- Mapa visual complejo antes de definir nodos, rutas y distancias.
- Horarios exactos de todos los NPC antes de que exista un reloj de acciones fiable.
- Clima aleatorio por mensaje o una llamada a meteorología real para un mundo ficticio.
- Árbol completo de PSICHO-Eco con niveles y costes numéricos inventados.
- Los nombres y biografías de los dos portadores anteriores sin definir.
- Una hora exacta de la erupción del Día 12.
- Automatizar romance, lealtad, reclutamiento o acompañamiento de las aventureras.
- Sincronizar automáticamente las propuestas con el Lorebook de SpicyChat antes de reconciliar la versión antigua y la nueva.

## 14. Plan de entregas pequeñas recomendado

| Orden | Entrega | Tamaño/alcance | Prueba de salida |
|---:|---|---|---|
| 1 | Contrato de acción y reloj por segundos | Migración y conversión temporal, sin clima ni agendas | Exactitud al segundo, undo y restore |
| 2 | Segmentos de acción y cálculo local | Un conjunto pequeño de acciones: hablar, observar, buscar, poder, caminar | Secuencia, simultaneidad, interrupción y no duplicación |
| 3 | Precisión y procesamiento de eventos | Evento de minuto y evento de día | Evento no se pierde ni recibe hora ficticia |
| 4 | Tramos de viaje | Grafo mínimo de ubicaciones conocidas | Mismo trayecto cambia según terreno/carga/estado |
| 5 | Ambiente regional | Clima y suelo persistentes | El clima no cambia en cada mensaje y sobrevive al reinicio |
| 6 | Primera entidad autónoma | Una ficha y una actividad por vez; comenzar con la entidad demoníaca cuando su ficha mínima esté cerrada | Privacidad, conocimiento, tiempo y persistencia |
| 7 | PSICHO-Eco progresivo | Definición de habilidad y registro de progresión | Sin desbloqueos ni costes duplicados |
| 8 | Agendas del trío | Una aventurera por iteración, luego tareas simultáneas | No omnisciencia ni teleportes |
| 9 | Campaña de integración | Día 1–12, eventos, clima, viaje y decisiones | 50–100 turnos y restauración consistente |

Esta secuencia es una recomendación. Los cambios de runtime de la primera entrega temporal necesitan una decisión de arquitectura clara y una PR técnica independiente; este documento no los implementa.

## 15. Referencias de diseño revisadas

Las siguientes herramientas aportan patrones concretos, no sistemas que haya que copiar enteros:

- **SillyTavern World Info:** activa entradas por palabras clave, admite fuentes ligadas a personaje/chat, recursión y presupuesto de contexto. Es una referencia útil para seleccionar lore pertinente y controlar el tamaño del prompt. La propia documentación advierte que insertar una entrada no garantiza que el modelo la utilice en la respuesta. Por eso Word Bot debe seguir validando el estado fuera del modelo. https://docs.sillytavern.app/usage/core-concepts/worldinfo/
- **Ink:** separa flujo narrativo y elección de la aplicación que lo ejecuta; permite consultar elecciones y serializar el estado de la historia a JSON. Es una referencia para conservar rutas y puntos de guardado sin convertir el motor narrativo en dueño de todo el estado de juego. https://github.com/inkle/ink/blob/master/Documentation/RunningYourInk.md
- **Ren'Py:** documenta guardado, carga y rollback por checkpoints de interacción. Es una referencia útil para pensar cuándo debe existir un punto reversible y qué variables deben entrar en el guardado. Word Bot ya conserva snapshots y transacciones y no necesita sustituir SQLite por el sistema de Ren'Py. https://www.renpy.org/doc/html/save_load_rollback.html
- **SQLite:** sus transacciones serializan escrituras y hacen atómicas las operaciones; WAL permite concurrencia de lectores/escritores con requisitos de checkpoint y conservación del archivo WAL. Es importante mantener el backup coordinado que ya usa el proyecto. https://www.sqlite.org/isolation.html y https://www.sqlite.org/wal.html

## 16. Conclusión y estado de aprobación

La mejor siguiente inversión es **cerrar tiempo por acción, precisión de eventos y viaje**. Son la base de la exploración realista, el clima, la autonomía y la cronología del volcán. Una vez estable, el demonio puede convertirse en la primera entidad nueva integrada de forma controlada y PSICHO-Eco puede evolucionar con datos persistentes, no solo con texto narrativo.

Este documento:
- registra hallazgos de código y una propuesta de prioridades;
- no cambia código ni esquema SQLite;
- no declara implementado el clima, las agendas, el mapa o la progresión de PSICHO-Eco;
- no añade nombres, historias o poderes no aprobados;
- no cambia la hora de la erupción;
- no actualiza por sí solo el Lorebook v1.19 de SpicyChat;
- no modifica `main`.

La implementación posterior debe mantenerse en PRs pequeñas, una responsabilidad por PR, con pruebas, registro de archivos modificados, CI real y estado de integración claro.
