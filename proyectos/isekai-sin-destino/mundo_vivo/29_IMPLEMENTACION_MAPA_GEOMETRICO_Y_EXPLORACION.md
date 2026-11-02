# 29 — Primera implementación del mapa geométrico y la exploración

**Estado:** núcleo geométrico inicial añadido en código y pruebas automatizadas escritas. Integración con una partida guardada y una interfaz visual todavía pendientes.  
**Rama de trabajo:** `feat/isekai-geometric-world-map`, basada en la rama documental de PR #45.  
**Alcance:** sistema genérico reutilizable; los datos geográficos concretos de Isekai no se inventan aquí.

## 1. Qué se implementó

Archivo: `proyecto/app/src/canon_manager/world_map.py`.

- Coordenadas cartesianas locales expresadas en metros: X positiva hacia el este y Y positiva hacia el norte.
- Ocho direcciones cardinales y diagonales.
- Movimiento por longitud de trayecto. Una orden diagonal de 500 m recorre 500 m euclidianos, con componentes X/Y de (500/\sqrt{2}); no recorre 500 m por cada eje.
- Áreas geográficas representadas como polígonos. Una aldea, ruina o región se detecta si el segmento recorrido cruza su superficie, no por alcanzar un punto de activación ni por estar cerca.
- Zonas de terreno poligonales con modificador de velocidad. Si varias zonas se superponen, se aplica el modificador más lento para evitar multiplicar penalizaciones sin una regla aprobada.
- Rejilla de exploración configurable. Cada movimiento revela las celdas que intersecta su segmento.
- Estado de celdas descubiertas serializable a JSON y reconstruible, para que pueda incorporarse al sistema de guardado.

## 2. Reglas geométricas actuales

El plano es local a un mapa/región; no representa todavía coordenadas geodésicas ni una escala de planeta. Su origen y el emplazamiento real de cada aldea quedan pendientes de cartografía.

Para un desplazamiento diagonal de longitud (d):

[
\Delta x = \pm \frac{d}{\sqrt{2}},\qquad
\Delta y = \pm \frac{d}{\sqrt{2}}
]

La longitud real se verifica con:

[
d = \sqrt{(x_2-x_1)^2+(y_2-y_1)^2}
]

Las superficies se definen mediante polígonos. El motor comprueba intersecciones entre el recorrido completo y los bordes de cada área. Por ello, un desplazamiento puede atravesar una aldea y terminar más allá de ella; también puede pasar en diagonal fuera de sus límites sin descubrirla.

## 3. Tiempo de desplazamiento

El valor base actual es configurable y provisional: 1,25 m/s. Cada zona puede aplicar un multiplicador positivo. El cálculo divide el segmento en intervalos donde cambia el terreno y suma el tiempo de cada tramo.

Ejemplo de prueba: 500 m por terreno normal, con 200 m dentro de una zona que reduce la velocidad al 50 %:
- 300 m normales a 1,25 m/s = 240 s.
- 200 m de terreno lento a 0,625 m/s = 320 s.
- Total calculado = 560 s.

Este valor es una regla técnica inicial, no una decisión definitiva sobre la velocidad del protagonista. Carga, heridas, cansancio, clima, acompañantes, caminos, pendientes y obstáculos todavía no intervienen.

## 4. Niebla de guerra

La rejilla tiene tamaño configurable; el valor inicial predeterminado de 250 m es una base de desarrollo, no una escala aprobada para el mapa definitivo.

`ExplorationState` conserva las celdas descubiertas y admite conversión a/desde JSON. Esto prueba el formato de estado, pero **todavía no escribe automáticamente en SQLite ni se ha conectado a los guardados de campaña**. Tampoco hay aún una interfaz de minimapa, colores, iconos ni revelado visual.

## 5. Pruebas añadidas

Archivo: `proyecto/app/tests/test_world_map.py`.

Las pruebas cubren:
1. Desplazamiento cardinal de 500 m con coordenadas y tiempo calculados.
2. Diagonal normalizada a 500 m euclidianos.
3. Detección de una aldea atravesada aunque el destino quede fuera.
4. No activar una aldea cercana que el recorrido diagonal no intersecta.
5. Modificación del tiempo al cruzar terreno más lento.
6. Serialización y restauración del descubrimiento de celdas sin redescubrirlas.
7. Rechazo de distancias y tamaños de celda inválidos.
8. Rechazo de coordenadas de celda mal formadas.

Las pruebas están definidas; su resultado de CI se registrará después de abrir la PR. No se afirma todavía que hayan pasado.

## 6. Límites deliberados de esta primera entrega

Todavía no implementa:
- guardar/cargar este estado desde las tablas SQLite de una partida;
- mapa dibujado, minimapa o interfaz de selección de 500 m / 1 km;
- definición de coordenadas reales de aldeas, caminos, ruinas o límites del bosque;
- caminos curvos, búsqueda de ruta, puentes, ríos, montañas u obstáculos infranqueables;
- exploración por visibilidad, altura, iluminación, clima o avistamientos a distancia;
- cambios de terreno por clima o acontecimientos;
- encuentros, eventos o decisiones narrativas durante un desplazamiento;
- movimiento de compañeros y NPC.

No se altera el canon geográfico al añadir esta infraestructura. Ninguna localización recibe coordenadas ficticias y ninguna mecánica pendiente se considera aprobada automáticamente.

## 7. Siguiente orden recomendado

1. Ejecutar CI y corregir cualquier fallo del núcleo geométrico.
2. Añadir pruebas basadas en casos reales de rutas y bordes de polígonos.
3. Diseñar límites y bloqueos de terreno, y luego un sistema de caminos con desvíos.
4. Integrar las celdas descubiertas en un guardado de campaña con migración/versionado.
5. Definir un mapa de referencia de una zona pequeña del Bosque de los Siete Ecos con geometría y distancias verificables.
6. Dibujar el minimapa sobre los mismos datos; la interfaz no debe mantener un mapa paralelo.


## 8. Persistencia SQLite de la exploración — actualización 01-11-2026

Se incorporó una capa de guardado por partida y región.

- Tabla `session_map_states`, creada mediante el esquema idempotente de `Database.initialize()`.
- Clave primaria compuesta por `session_id` y `region_id`: la misma partida puede conservar estados de exploración separados por región.
- Se guardan posición X/Y en metros, tamaño de celda, identificador del sistema de coordenadas, JSON de celdas descubiertas, versión del formato y fecha de actualización.
- Las escrituras usan la transacción `BEGIN IMMEDIATE` ya centralizada en `Database.transaction()` y un UPSERT, de modo que re-guardar una región actualiza su estado sin crear duplicados.
- La clave foránea elimina el registro de mapa al eliminar la sesión; no se mantienen exploraciones huérfanas.
- El servicio `canon_manager.map_persistence` valida el formato al cargar y rechaza versiones/sistemas de coordenadas desconocidos en vez de interpretar datos incompatibles.

### Pruebas adicionales

Archivo: `proyecto/app/tests/test_map_persistence.py`.

Se añadieron siete pruebas para recuperar coordenadas, escala y niebla de guerra; actualizar el mismo estado; separar regiones; devolver estado vacío antes del primer guardado; respetar claves foráneas; eliminar por cascada con la sesión y rechazar versiones de guardado desconocidas.

### Resultado de CI registrado

La ejecución [CI #41327956847](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/41327956847), sobre el commit de código `25bb26870ffe6ef5273221d961947019c7d2f79f`, terminó correctamente:

- **124 pruebas aprobadas**.
- Comprobación de sintaxis JavaScript aprobada.
- Una advertencia de deprecación `Starlette/httpx` ya presente en la suite.
- Avisos del runner sobre Node.js 20 y dependencias de las acciones de GitHub; no bloquearon el trabajo.

Los commits posteriores de esta rama actualizaron solo documentación e información de la PR; no alteraron los archivos Python cubiertos por esa ejecución.

### Límite que permanece

La persistencia ya existe como servicio y tabla SQLite, pero todavía no está invocada por una interfaz de juego o un controlador de partida real. La próxima integración deberá llamar al servicio en los puntos de guardar/cargar y coordinar posición, tiempo y movimiento como una misma acción transaccional. No se afirma todavía que el usuario pueda abrir una partida jugable y ver el minimapa persistido.


## 9. Planificador de rutas, obstáculos y caminos — actualización 01-11-2026

Se añadió una primera capa de navegación determinista en `canon_manager.world_map.WorldMap.plan_route()`.

### Elementos implementados

- `ObstacleZone`: polígonos infranqueables para montañas, ríos sin cruce, acantilados, muros u otros bloqueos. La clase conserva un `kind` descriptivo; no asigna automáticamente reglas narrativas por tipo.
- `RoadZone`: corredores poligonales de caminos, senderos o puentes. Un corredor aplica un multiplicador de velocidad configurable y puede habilitar el cruce de la parte de un obstáculo que cubra geométricamente.
- Búsqueda A* sobre una rejilla cuya separación usa el tamaño de celda del mapa. Los puntos exactos de salida y destino se conservan como extremos del recorrido.
- Las rutas no atraviesan polígonos bloqueados. Para diagonales se comprueban también las dos celdas ortogonales contiguas, evitando cortar esquinas.
- El coste de ruta se calcula por tiempo estimado: combina terreno lento y bonificaciones de caminos. El algoritmo puede preferir un recorrido algo más largo si reduce el tiempo previsto.
- `walkable_bounds` permite definir una frontera poligonal. Si una pared, río u obstáculo cierra el paso dentro de esa frontera, el servicio devuelve `RouteNotFoundError` en vez de inventar una salida.
- Existe un presupuesto de expansiones configurable para acotar búsquedas muy grandes. Si se alcanza, se devuelve `RouteSearchLimitError`, que distingue el límite de cálculo de una ruta inexistente.
- `move()` rechaza un desplazamiento directo que atraviese un obstáculo sin un corredor de camino explícito. El llamador debe solicitar una ruta y recorrer sus waypoints.

### Pruebas añadidas

Se incorporaron siete casos nuevos a `proyecto/app/tests/test_world_map.py`:
1. Desvío alrededor de una montaña y resultado determinista.
2. Rechazo de un destino situado dentro de un obstáculo.
3. Ausencia de ruta cuando un muro sella una región acotada.
4. Rechazo de un movimiento directo que atraviesa un obstáculo.
5. Reducción del tiempo estimado dentro de un corredor de camino.
6. Validación del presupuesto de búsqueda.
7. Cruce de un río por un corredor de puente explícito.

### Límites que siguen pendientes

- Los caminos son actualmente corredores poligonales con coste preferente; todavía no existe una red topológica de caminos conectados, cruces, bifurcaciones y puentes con identificadores propios.
- La rejilla A* ofrece una ruta aproximada por waypoints. Todavía no hay suavizado de curvas ni navegación de alta precisión para vehículos o movimiento animado.
- El servicio devuelve la ruta, pero aún no hay controlador que ejecute los waypoints, avance el reloj por cada tramo, revele las celdas recorridas y guarde el nuevo estado de posición en una sola operación.
- No existe minimapa ni interfaz para seleccionar destino, ver la ruta o mostrar un mensaje de «camino bloqueado».
- Las localizaciones del canon siguen sin coordenadas inventadas. Obstáculos, caminos y fronteras reales del Bosque de los Siete Ecos deberán definirse con geometría aprobada.

La navegación es infraestructura genérica: no introduce ubicaciones, distancias ni hechos nuevos en el canon. La integración con el reloj, la exploración persistente y la interfaz de partida continúa como siguiente etapa.


## 10. Controlador transaccional de desplazamientos — actualización 01-11-2026

Se conectó el planificador con un controlador de viajes por partida. El avance es por tramos entre waypoints; cada llamada ejecuta como máximo un tramo. No se usa un trabajador en segundo plano. La interfaz puede pedir el siguiente tramo y ofrecer pausa, reanudación, cancelación o cambio de destino en cualquier punto de control.

### Datos persistidos

Se agregaron dos tablas:

- `world_map_regions`: geometría canónica de una región por mundo, con JSON versionado. El planificador y el futuro minimapa deben leer esta misma definición.
- `session_travel_states`: ruta activa de la partida, waypoint siguiente, destino, estado (running/paused/completed/cancelled), segundos recorridos y minutos ya aplicados al reloj.
- `session_travel_steps`: registro de idempotencia por petición. Repetir el mismo `request_id` devuelve el resultado original, sin repetir movimiento, tiempo ni eventos.

La posición y niebla de guerra siguen almacenadas en `session_map_states`; no se duplican dentro de la ruta.

### API disponible

1. `PUT /api/worlds/{world_id}/map/regions/{region_id}`: registrar o actualizar geometría poligonal compartida.
2. `GET /api/worlds/{world_id}/map/regions/{region_id}`: recuperar esa definición para navegación y futuro minimapa.
3. `POST /api/sessions/{session_id}/travel/plan`: planificar o reemplazar el destino desde la posición guardada. El cuerpo incluye `region_id`, `destination_x_m`, `destination_y_m` y una etiqueta opcional.
4. `GET /api/sessions/{session_id}/travel`: recuperar el estado del recorrido.
5. `POST /api/sessions/{session_id}/travel/step`: ejecutar un tramo. Requiere un `request_id` único y estable durante reintentos.
6. `POST /api/sessions/{session_id}/travel/pause`, `resume` y `cancel`: controlar el viaje entre tramos.
7. `GET /api/sessions/{session_id}/map/regions/{region_id}/state`: leer posición guardada, tamaño de celda y celdas descubiertas para el futuro minimapa.

Volver a llamar a `travel/plan` durante un viaje en curso o pausado equivale a cambiar el destino: se calcula una ruta desde la posición actual y se conserva el tiempo de viaje ya consumido.

### Qué ocurre al ejecutar un tramo

En una única transacción SQLite (`BEGIN IMMEDIATE`):

- valida que el recorrido esté en ejecución y recupera la geometría/posición actuales;
- recorre el siguiente segmento con las mismas reglas de obstáculos y caminos del planificador;
- revela las celdas atravesadas y detecta las áreas/terrenos cruzados;
- persiste la nueva posición y la niebla de guerra;
- acumula segundos y avanza el reloj en minutos completos; al terminar el viaje redondea el resto al minuto siguiente;
- activa eventos mundiales confirmados que vencieron durante ese avance, mediante el servicio de cronología existente;
- actualiza waypoint y estado de viaje, y registra el resultado asociado al `request_id`.

Si ocurre un error antes del commit, posición, reloj, exploración, progreso y disparo de eventos se revierten juntos. Una petición repetida devuelve el resultado guardado y no vuelve a aplicar efectos.

### Límites que permanecen

- El avance es por llamada de API; todavía no hay controles visuales de «viajar», «pausar», «reanudar» y «cambiar destino» en la interfaz.
- El origen geométrico inicial de una región es (0,0) cuando esa partida aún no tiene posición guardada. La definición y colocación de lugares reales del Bosque de los Siete Ecos sigue pendiente de coordenadas aprobadas.
- La etiqueta de destino solo actualiza la ubicación textual de la sesión al completar el recorrido; la posición espacial numérica sigue siendo la fuente de verdad del mapa.
- La persistencia/ejecución está conectada como servicio API, pero el minimapa todavía no existe. Su render deberá consumir `world_map_regions` y `session_map_states`, no mantener datos propios.


### Validación de controlador y API

CI de navegación [#41334499435](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/41334499435): **141 pruebas Python aprobadas** y comprobación de sintaxis JavaScript aprobada. Incluyó ejecución por tramos, guardado de posición/revelado/reloj, idempotencia de reintentos, pausa/reanudación/cancelación, cambio de destino, eventos de cronología, integridad de región y recorrido completo a través de la API. La advertencia Starlette/httpx y los avisos del runner sobre Node.js 20 fueron no bloqueantes.

La prueba de API también consulta el endpoint de estado espacial al finalizar el movimiento y comprueba que devuelve la posición y las celdas reveladas que se guardaron en SQLite. El minimapa puede construirse posteriormente a partir de estos mismos endpoints y datos.


## 11. Primera interfaz gráfica de exploración y viaje — actualización 02-11-2026

Se incorporó al cliente local una vista SVG interactiva que consume la API del controlador de viajes y la geometría persistida de la región. No mantiene un segundo estado espacial ni introduce ubicaciones canónicas.

### Presentación del mapa

- Proyección local cartesiana: +X hacia el este, +Y hacia el norte; la interfaz muestra el norte arriba y conserva la escala sin estirar las distancias.
- Dibuja las áreas conocidas (`areas`), terrenos (`terrain_zones`), obstáculos (`obstacles`), caminos y puentes (`roads`) usando las mismas figuras poligonales que usa A*.
- Los caminos se dibujan encima de los obstáculos para que un puente explícito pueda distinguirse visualmente de un río.
- La niebla cubre las celdas no exploradas. Las celdas descubiertas dejan ver la geometría que ya se conocía en el servidor.
- Los nombres de áreas, terrenos, obstáculos y caminos aparecen únicamente cuando la celda central de su polígono ha sido descubierta. No se revelan etiquetas escondidas detrás de la niebla.
- Muestra la posición actual, el destino seleccionado y la ruta calculada, incluidos los waypoints de los desvíos.
- Permite ajustar el zoom. El mapa se ajusta a la extensión de la geometría cuando se pulsa «Ajustar»; el acercamiento centra la vista en la posición actual.
- Los clics se transforman de coordenadas de pantalla a metros locales teniendo en cuenta el espacio de letterboxing del SVG; no se deforma el plano para hacer coincidir el clic.

### Controles de desplazamiento

- Seleccionar destino mediante clic en el mapa o introducir X/Y directamente.
- Planificar o cambiar el destino desde la posición confirmada.
- «Viajar» ejecuta los tramos uno por uno mediante la API; «Avanzar tramo» permite control manual.
- «Pausar», «Reanudar» y «Cancelar» operan entre waypoints confirmados. Cancelar conserva la última posición confirmada y el controlador contabiliza el tiempo parcial conforme a su regla de redondeo.
- La pantalla conserva el identificador de petición pendiente en `sessionStorage`; una recarga o reintento reutiliza la misma clave de idempotencia y evita duplicar el avance.
- Si se cambia el identificador de región mientras el viaje está activo, la pantalla vuelve a mostrar la región real del recorrido, en vez de dibujar su ruta sobre otro mapa.

### Configuración de geometría

La pantalla permite cargar un JSON desde archivo o editarlo directamente. La estructura versionada acepta:

- `areas`: polígonos con identificador y nombre, para aldeas, campamentos, ruinas u otras zonas.
- `terrain_zones`: polígonos con multiplicador de velocidad.
- `obstacles`: polígonos que impiden el paso salvo corredor explícito.
- `roads`: corredores de camino, senderos o puentes con su multiplicador.
- `walkable_bounds`: polígono opcional que limita las rutas.
- `points_of_interest`: marcadores puntuales independientes con `point_id`, `name`, `x_m`, `y_m`, `icon`, `category` y `description`. No alteran la navegación ni el terreno. Sus iconos, nombres y descripciones se representan únicamente cuando su celda está descubierta. El campo es opcional para conservar la compatibilidad con mapas anteriores.

La plantilla inicial está vacía: solo define escala y colecciones vacías. No trae ubicaciones ni coordenadas inventadas. El mapa puede mostrar el plano y el marcador inicial, pero no simula conocer un bosque que aún no tiene geometría aprobada.

### Editor visual de polígonos — actualización 02-11-2026

Se añadió una herramienta de dibujo integrada en el mapa SVG para crear geometría sin editar manualmente cada par de coordenadas:

- Selección del tipo: área/lugar, terreno, obstáculo, camino/puente o límite transitable.
- Cada clic sobre el plano añade un vértice en coordenadas locales; el borrador se representa con línea, relleno tenue, puntos y numeración.
- Permite deshacer el último vértice, cancelar el dibujo o cerrar el polígono.
- Los campos adicionales dependen del tipo: identificador y nombre, multiplicador de velocidad o clase de obstáculo.
- Comprueba al menos tres vértices distintos, área no nula y ausencia de auto-intersecciones antes de incorporar el polígono.
- El resultado se añade al mismo objeto de geometría JSON que consumen la API y el planificador. No se guarda automáticamente: el usuario debe pulsar «Guardar geometría de región».
- Mientras el JSON está modificado, la planificación queda deshabilitada. Así no se puede calcular una ruta sobre una geometría local que el servidor aún no ha recibido.
- Los clics del editor reutilizan la conversión SVG→metros que usa la selección de destinos; el área del mapa no cambia de escala durante el dibujo.
- Se pueden cargar polígonos existentes desde una lista y arrastrar sus vértices directamente en el SVG. Los cambios se validan antes de sustituir los vértices y se mantienen en el borrador hasta guardar la región.
- La edición de una figura conserva su identificador, nombre y propiedades; solo actualiza la lista de vértices de esa figura.
- Se pueden colocar puntos de interés con identificador, nombre, categoría, icono y descripción desde un único clic. Son marcadores independientes: no bloquean el paso ni alteran el cálculo de rutas.
- Los puntos de interés se guardan dentro de la geometría de la región existente en SQLite. No requieren una tabla paralela ni una migración de base de datos.
- Los marcadores se dibujan después de la máscara de niebla y solo cuando la celda de sus coordenadas ya fue descubierta. Los puntos desconocidos tampoco amplían la vista inicial del mapa.

### Límites actuales

- Es una vista cartográfica SVG funcional, no todavía un minimapa final pulido con fondos ilustrados, filtros de capas o fichas laterales de puntos de interés.
- La edición permite arrastrar vértices, pero todavía no ofrece añadir o quitar vértices individuales de polígonos ya existentes ni un editor de rutas lineales por nodos.
- Los lugares del canon no se precargan por nombre: hay que introducir sus coordenadas aprobadas. Las localizaciones canónicas del Bosque de los Siete Ecos siguen sin coordenadas confirmadas.

La interfaz se alimenta de `GET /api/worlds/{world_id}/map/regions/{region_id}`, `GET /api/sessions/{session_id}/map/regions/{region_id}/state` y los endpoints `/travel`. Toda mejora visual futura debe seguir escribiendo y leyendo las mismas definiciones, coordenadas y celdas descubiertas.


### Edición de figuras y puntos de interés — actualización 02-11-2026

El formato de región conserva los puntos de interés junto al resto de la geometría. `points_of_interest` es opcional al leer configuraciones antiguas; al guardar, el servidor normaliza el campo como una colección. Cada punto utiliza coordenadas locales en metros y se dibuja solo después de descubrir su celda. Los puntos no son obstáculos ni áreas de colisión.

La herramienta gráfica permite seleccionar una figura ya definida, mover sus vértices con el puntero y confirmar el contorno mediante el mismo validador geométrico que se usa al crear polígonos. Los cambios siguen siendo un borrador hasta guardar explícitamente la región.