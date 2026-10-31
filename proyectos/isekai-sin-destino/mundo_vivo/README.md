# Isekai sin Destino — Mundo vivo

**Módulo:** diseño modular del mundo, simulación, exploración, ecología, magia y Psico-Eco.  
**Estado:** primera base documental creada; todavía no es código integrado en el motor de Word Bot.  
**Rama:** world/isekai-mundo-vivo-foundation.

## Propósito

Construir un mundo fantástico abierto en el que criaturas, PNJ, objetos, recursos, fenómenos mágicos y acontecimientos tengan estados propios. La IA narra y propone posibilidades; las reglas y el estado persistente determinan qué puede ocurrir. El protagonista no tiene protección narrativa.

## Decisiones aprobadas

### Enfoque mixto y descubrimiento gradual

- Diseño interno completo de regiones, subzonas, especies, plantas, recursos, peligros, secretos y reglas ecológicas.
- El protagonista descubre contenido gradualmente mediante exploración, pistas, encuentros y consecuencias.
- El conocimiento del personaje se mantiene separado del catálogo interno del mundo.
- La presencia de especies y recursos depende de hábitat, subzona, hora, clima, población y estado ecológico.
- La información no descubierta no se revela automáticamente.

### Estructura combinada del bosque

- Combina zonas de peligro dinámicas, caminos/rutas, territorios ecológicos y niveles naturales donde la geografía los permita.
- No es lineal ni se organiza en anillos concéntricos.
- Territorios pueden cruzar subzonas y cambiar con el tiempo; la distancia al borde no determina por sí sola el peligro.
- El mapa interno se modela mediante nodos, conexiones, territorios y puntos de interés.

### Presencia humana y civilizada combinada

El usuario eligió combinar **aldeas aisladas, campamentos temporales, ruinas y escondites**.

- Aldeas: comunidades pequeñas y relativamente estables, dentro del bosque o en sus límites.
- Campamentos: asentamientos temporales o móviles de aventureros, cazadores, comerciantes, exploradores u otros grupos.
- Ruinas: rastros de ocupaciones anteriores; su origen, antigüedad y función deben investigarse.
- Escondites: refugios, guaridas, depósitos, puestos discretos u otros lugares de ocultación.
- Estas categorías no fijan nombres, facciones, cifras de población ni ubicaciones concretas.
- Los lugares pueden estar ocupados, abandonados, disputados, ocultos o en transición.
- La presencia no se garantiza en cada zona ni en cada partida; el protagonista solo conoce lo que descubre.



### Densidad civilizada equilibrada

El usuario eligió una densidad **equilibrada** para la presencia civilizada del bosque.

- Habrá varias comunidades pequeñas, pero no una población continua ni asentamientos en cada subzona.
- Los campamentos serán relativamente habituales en rutas transitadas, zonas de expedición y puntos con recursos, pero su presencia será temporal y variable.
- Las ruinas y los escondites estarán repartidos por el territorio, aunque muchos permanecerán ocultos, inaccesibles o sin descubrir.
- Deben existir extensiones amplias de bosque salvaje entre los lugares habitados, con rutas y regiones donde la presencia civilizada sea escasa o inexistente.
- La densidad no se traduce todavía en cantidades exactas. La distribución concreta dependerá de geografía, recursos, seguridad, historia, accesibilidad y presión ecológica.
- La categoría equilibrada describe el diseño global, no garantiza que el protagonista encuentre pronto una aldea o un campamento.
- No se aprueban todavía nombres, número exacto de asentamientos, población, facciones ni ubicaciones específicas.

## Actualización de diseño — 30-10-2026

La premisa de inicio se actualizó: protagonista humano de la Tierra contemporánea, con ropa normal y celular; accidente con una caja promocional de cereal Dragon Ball Z/Goku al caer un estante; encuentro posterior con diosa chibi usuaria de celular; recibe PSICHO-Eco, poder incompleto/de oferta que crece con el usuario. El recuerdo completo aparece más adelante en una iglesia como flashback cómico. La versión anterior sin celular ni pertenencias terrestres queda reemplazada para esta campaña.

Se amplía el módulo como novela visual de mundo abierto: mapa explorable, grafo causal de acontecimientos, grupo y órdenes, profesiones/especialidades, aprendizaje, gremios, magia, PSICHO avanzado, accidentes, personalidades y rutas/finales. Las referencias de anime inspiran mecánicas generales; no se copian personajes ni sistemas propietarios.

## Mapa de documentos

1. [Reglas del mundo vivo](01_REGLAS_MUNDO_VIVO.md)
2. [Modelo de variables y estado](02_MODELO_VARIABLES.json)
3. [Ecología del Bosque de las Bestias](03_CATALOGO_50_ESPECIES.json)
4. [Sistema Psico-Eco](04_PSICO_ECO.md)
5. [Exploración, objetos y magia](05_EXPLORACION_OBJETOS_MAGIA.md)
6. [Rutas y cinco finales](06_RUTAS_Y_FINALES.md)
7. [Acciones y comandos](07_ACCIONES_Y_COMANDOS.md)
8. [Pendientes y conflictos de canon](08_PENDIENTES_Y_CONFLICTOS.md)
9. [Estructura y mapa ecológico](09_ESTRUCTURA_Y_MAPA_ECOLOGICO.md)
10. [Presencia humana y lugares habitados](10_PRESENCIA_HUMANA_Y_ASENTAMIENTOS.md)

11. [Reputación, relaciones, conocimiento y consecuencias sociales](11_REPUTACION_RELACIONES_Y_CONOCIMIENTO.md)
12. [Viajes, transporte y caravanas](12_VIAJES_TRANSPORTE_Y_CARAVANAS.md)
13. [Origen del protagonista y primer encuentro divino](13_ORIGEN_PROTAGONISTA.md)
14. [Mundo abierto, grupo, progresión, magia y PSICHO](14_MUNDO_ABIERTO_GRUPO_MAGIA_Y_PSICHO.md)
15. [Plan de desarrollo](15_PLAN_DE_DESARROLLO.md)

## Regla de autoridad y canon

- Las decisiones explícitas del usuario prevalecen sobre documentos antiguos cuando existe contradicción.
- Las propuestas no son canon aprobado.
- Los documentos anteriores se conservan y sus conflictos se señalan; no se borran silenciosamente.
- Los datos desconocidos se registran como No registrado, propuesto o pendiente de aprobación.
- No afirmar que una regla está implementada hasta que exista código, integración y pruebas.

## Principio de simulación

El motor mantiene datos estructurados y persistentes. La IA interpreta la situación, genera diálogo y describe consecuencias dentro de esos datos. No debe inventar éxitos, propiedades, recuerdos, muertes o relaciones sin una causa plausible.

## Alcance y límites actuales

Hay documentación, modelo inicial de variables, catálogo de 50 especies propuestas, especificación Psico-Eco, exploración, magia, rutas, finales, comandos y diseño de estructura ecológica y presencia civilizada.

Todavía no hay simulador ejecutable de ecosistemas o asentamientos, motor probabilístico, conexión de estas fichas a SQLite ni validación de una partida real. La rama main no se ha modificado.


### Ubicación repartida de las aldeas

El usuario aprobó repartir las aldeas entre los límites y el interior del Bosque de las Bestias, sin distribución uniforme:

- Mayor concentración relativa cerca de límites y accesos.
- Algunas comunidades aisladas en el interior, solo donde recursos, rutas y seguridad lo justifiquen.
- Presencia estable muy escasa en zonas profundas o especialmente peligrosas.
- No se crea una red continua ni se fijan nombres, cantidades, población, coordenadas, facciones o localizaciones concretas.

### Sistema combinado de rutas

El usuario aprobó tres clases generales de conexiones:

- Caminos principales relativamente estables entre algunas aldeas, accesos y puntos de intercambio.
- Senderos secundarios menos transitados y variables por vegetación, clima, erosión, criaturas y acontecimientos.
- Rutas ocultas o temporales, conocidas por personas o criaturas concretas y sujetas a cambios de disponibilidad.

No todas las aldeas estarán conectadas directamente; algunas comunidades interiores podrán quedar aisladas temporalmente. La decisión no fija trazados, distancias, tiempos ni ubicaciones concretas.


### Coherencia contextual, reputación y relaciones

El usuario aprobó que el mundo no tenga respuestas universales ni conocimiento omnisciente. Los hechos, observaciones, recuerdos, rumores y conocimiento del protagonista deben permanecer separados. La fama depende de testigos, evidencias, atribución y canales reales de difusión; las relaciones son individuales y mantienen ejes independientes. Un uso privado de Psico-Eco puede modificar el estado interno del objetivo sin alterar automáticamente la fama pública. Un fallo provoca incomodidad o inquietud en el objetivo, sin crear por sí solo rumores externos.

- [11 — Reputación, relaciones, conocimiento y consecuencias sociales](11_REPUTACION_RELACIONES_Y_CONOCIMIENTO.md)

### Viajes, transporte y caravanas

Se aprobaron los criterios generales de desplazamiento, orientación, fuentes de información sobre rutas, acontecimientos dinámicos, interrupciones, paso del tiempo, descanso, carga, transporte organizado, servicios, caravanas, autonomía de sus integrantes, vida social y liderazgo contextual.

- [12 — Viajes, transporte y caravanas](12_VIAJES_TRANSPORTE_Y_CARAVANAS.md)

### Regla de diseño: menos microencuestas, más coherencia contextual

No se preguntará por cada procedimiento menor. Las reglas generales deben permitir resolver situaciones según gravedad, contexto, información disponible, personajes, cultura, recursos, organización y estado actual del mundo. Las encuestas quedan reservadas para decisiones que cambien sustancialmente el diseño o el canon.

## Estado tras la actualización del 30-10-2026

- Documentación ampliada y enlazada.
- Modelo JSON actualizado a la versión 0.2.0 y parseado correctamente.
- No es implementación ejecutable: aún faltan motor de simulación, persistencia SQLite específica del mundo, servicios, API, interfaz y pruebas de campaña.
- La rama main permanece fuera del alcance de esta entrega.
