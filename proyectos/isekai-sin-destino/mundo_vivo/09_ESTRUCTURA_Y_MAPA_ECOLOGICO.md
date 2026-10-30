# 09 — Estructura y mapa ecológico del Bosque de las Bestias

**Estado:** estructura de diseño aprobada en su enfoque general; nombres, posiciones exactas y conexiones concretas siguen siendo propuestas hasta su revisión.  
**Decisión del usuario:** organización combinada: zonas de peligro + caminos y territorios + niveles naturales.

## 1. Principio de organización

El bosque no es una mazmorra lineal ni una serie de anillos concéntricos. Se modela como un territorio tridimensional conectado por rutas, con zonas de distinta presión ecológica y peligro.

La distancia al borde no determina por sí sola el riesgo. Un barranco próximo puede ser mortal; una hondonada profunda puede ofrecer refugio; un sendero transitado puede ser seguro de día y peligroso de noche.

## 2. Cuatro dimensiones del mapa

1. **Regiones y subzonas:** sectores geográficos con clima local, terreno, recursos y condiciones propias.
2. **Rutas y conexiones:** senderos, cauces, pasos, túneles, puentes naturales, trepadas y atajos. Cada conexión tiene condiciones y riesgos.
3. **Niveles naturales:** suelo, sotobosque, copas, cavidades, subsuelo y cavernas cuando existan. No todas las zonas tienen todos los niveles.
4. **Territorios ecológicos:** áreas de alimentación, caza, anidación, refugio, reproducción y tránsito de especies. Los territorios pueden cruzar varias subzonas y cambiar con el tiempo.

Las zonas de peligro son una capa adicional, no una dimensión geográfica rígida. El peligro puede cambiar por hora, estación, clima, población, heridas, hambre, presencia de crías o acontecimientos recientes.

## 3. Modelo de nodos y conexiones

El mapa interno debe representarse como un grafo:

- **Nodo:** lugar o subzona identificable, con terreno, niveles disponibles, condiciones, recursos potenciales y estado de descubrimiento.
- **Conexión:** paso entre dos nodos, con distancia aproximada si se conoce, duración estimada, dificultad, visibilidad, restricciones y amenazas.
- **Territorio:** relación espacial dinámica de una o más entidades/especies con nodos o áreas, no necesariamente una frontera visible.
- **Punto de interés:** objeto, ruina, refugio, recurso, fenómeno, guarida o secreto que puede existir sin estar descubierto.

No se debe inventar una conexión transitable solo porque dos lugares estén próximos en el mapa. Barreras, desniveles, agua, vegetación, derrumbes y criaturas pueden bloquear o modificar rutas.

## 4. Capas de peligro

En vez de asignar una dificultad fija a cada anillo, cada lugar calcula o describe su peligro a partir de factores:

- Criaturas presentes y actividad reciente.
- Territorialidad, hambre, crías y conducta de caza.
- Visibilidad, ruido, cobertura y rutas de escape.
- Terreno, altura, agua, barro, clima y hora.
- Trampas naturales, venenos, esporas y fenómenos mágicos.
- Recursos disponibles y competencia entre especies.
- Huellas, cadáveres, disputas y otros indicios.

Una etiqueta como «bajo», «medio» o «alto» puede servir como resumen orientativo del diseño, pero no sustituye las causas concretas ni garantiza seguridad.

## 5. Niveles naturales

Los niveles son posibilidades de exploración, no pisos obligatorios:

- **Suelo y claros:** desplazamiento, rastros, plantas, madrigueras y encuentros visibles.
- **Sotobosque:** vegetación densa, cobertura, emboscadas, escondites y caminos difíciles de ver.
- **Copas y alturas:** nidos, rutas arbóreas, depredadores trepadores, observación y riesgo de caída.
- **Cavidades y troncos huecos:** refugios pequeños, colonias, reservas y espacios de difícil acceso.
- **Subsuelo y cavernas:** túneles, raíces profundas, agua subterránea, minerales, hongos y organismos adaptados a la oscuridad.

La presencia de cada nivel y su contenido debe definirse por subzona. No se asume que toda cueva conecte con otra ni que todo árbol permita recorrer las copas.

## 6. Descubrimiento y conocimiento

Cada nodo, conexión y punto de interés mantiene al menos dos estados distintos:

- **Estado real del mundo:** existe/no existe, accesible/bloqueado, ocupado/desocupado, alterado/intacto, conocido por el motor.
- **Conocimiento del protagonista:** desconocido, sospechado, visto parcialmente, identificado, cartografiado o confirmado por una fuente.

Una huella puede revelar que algo pasó por allí sin identificar con certeza la especie. Ver una entrada no revela el tamaño ni la extensión de una cueva. Un rumor puede orientar, pero no equivale a una observación.

La interfaz del personaje solo muestra lo descubierto. El mapa interno completo se utiliza para coherencia y simulación, no para revelar automáticamente secretos.

## 7. Rutas alternativas y consecuencias

- Un camino puede ser más corto pero más expuesto.
- Un rodeo puede consumir tiempo y recursos, pero evitar un territorio.
- Una ruta arbórea puede evitar depredadores terrestres y exponer al protagonista a otros peligros.
- Un cauce puede facilitar orientación y agua, pero dejar rastros, limitar cruces o atraer animales.
- Un derrumbe, incendio, inundación o migración puede cerrar y abrir rutas.
- Las criaturas pueden desplazarse entre nodos; su territorio no es una aparición fija de encuentro.

La elección de ruta debe tener costes, riesgos e información imperfecta. No se debe presentar una ruta como segura si el protagonista no tiene evidencia para saberlo.

## 8. Plantilla de ficha de subzona

Cada subzona futura debería completar:

- ID estable y nombre provisional.
- Región y nodos vecinos conocidos por el motor.
- Tipo de terreno, relieve, vegetación y agua.
- Niveles naturales disponibles.
- Clima y condiciones locales.
- Especies residentes, visitantes y posibles, separadas.
- Recursos y estacionalidad.
- Territorios, guaridas y puntos de interés.
- Amenazas ambientales y mágicas.
- Rutas de entrada/salida y obstáculos.
- Señales detectables y dificultad de observación.
- Estado de conocimiento del protagonista.
- Estado de canon: propuesta, revisada o aprobada.

Los campos sin definir deben quedar como «No registrado». No completar con valores inventados.

## 9. Propuestas de tipos de subzona (no canon)

Para construir el primer borrador del mapa pueden evaluarse arquetipos como claros, bosque denso, ribera, pantano, barranco, ladera rocosa, árboles gigantes, ruinas cubiertas, cuevas y red de raíces. Son opciones de diseño, no lugares confirmados ni una lista cerrada.

## 10. Reglas para el futuro motor

El motor deberá:
- Consultar conexiones válidas antes de permitir desplazamientos.
- Calcular tiempo y costes según terreno, estado y método de viaje.
- Actualizar posiciones, territorios y rastros después de acciones relevantes.
- Comprobar presencia y actividad ecológica antes de generar encuentros.
- Guardar cambios de accesibilidad y condiciones ambientales.
- Mantener el mapa completo separado del mapa descubierto por el protagonista.
- Permitir que dos partidas descubran rutas y secretos diferentes sin alterar arbitrariamente la geografía establecida.

Esta especificación es documental. Todavía no existe un grafo ejecutable ni una integración con SQLite.


## Decisión aprobada: densidad equilibrada de lugares civilizados

La distribución global de aldeas, campamentos, ruinas y escondites será **equilibrada**:
- Varias aldeas pequeñas, separadas entre sí; no habrá una cadena de poblaciones que cubra todo el bosque.
- Campamentos relativamente habituales cerca de rutas transitadas, recursos y áreas de expedición, con ocupación cambiante.
- Ruinas y escondites repartidos por el territorio, sin que todos sean visibles o accesibles.
- Amplias extensiones salvajes y subzonas sin presencia civilizada estable.
- La distribución se ajustará a nodos, conexiones, recursos, seguridad, historia y territorios ecológicos; no a una cuota uniforme por zona.
- La categoría equilibrada es una pauta de diseño global, no una probabilidad o garantía de encuentro para el protagonista.

No se fijan cantidades ni localizaciones concretas. La decisión no modifica el principio de descubrimiento gradual.

## Decisión aprobada: sistema combinado de rutas y conexiones

El usuario eligió un sistema combinado para conectar lugares del Bosque de las Bestias:

- **Caminos principales:** relativamente estables; conectan algunas aldeas, accesos y puntos de intercambio, sin garantizar seguridad ni conexión universal.
- **Senderos secundarios:** menos transitados y variables; la vegetación, el clima, la erosión, las criaturas y los acontecimientos pueden alterarlos o hacerlos desaparecer.
- **Rutas ocultas o temporales:** conocidas por habitantes, exploradores o criaturas concretas; pueden aparecer, bloquearse o dejar de ser transitables.
- No todas las aldeas estarán conectadas directamente. Algunas comunidades interiores podrán depender de senderos difíciles o quedar aisladas temporalmente.
- La decisión define categorías y comportamiento general, no nombres, trazados, distancias, tiempos, ubicaciones ni conexiones concretas.
- El motor futuro deberá distinguir existencia real, transitabilidad actual y conocimiento del protagonista para cada conexión.

