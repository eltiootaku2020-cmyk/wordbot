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
