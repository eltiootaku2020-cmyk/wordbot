# 08 — Pendientes y conflictos de canon

Este documento evita que una propuesta nueva sobrescriba silenciosamente datos anteriores. Los puntos se resuelven con el usuario antes de actualizar la configuración maestra o el Lorebook de SpicyChat.

## Decisiones expresadas por el usuario en la revisión actual

- La erupción del volcán pasa a estar fijada para el Día 12.
- Hay cinco finales principales: héroe, villano, monarca, cobarde y héroe trágico.
- **Decisión aprobada el 31-10-2026:** el primer encuentro tendrá tres aventureras: Brina, Maelis y Sera. Ivar y Timo mantienen sus fichas y aparecen en una etapa posterior.
- El mundo debe ser abierto, con rutas ramificadas y opción de acción libre.
- El primer bioma debe aspirar a unas 50 especies variadas.
- Criaturas y personajes tienen estados y comportamientos propios.
- La exploración incluye observación, búsqueda de objetos, rastros y enemigos ocultos.
- Psico-Eco incluye información personal, influencia/manipulación, recuerdos, particularidades individuales y usos biológicos y sobre el propio protagonista.
- El hambre, instintos, biología y otras necesidades pueden prevalecer sobre un recuerdo alterado.
- Debe haber riesgo real de muerte y bad endings.
- Se desea una interfaz de tres opciones sugeridas y una opción «Otro».
- **Decisión aprobada:** enfoque mixto: diseño interno completo y descubrimiento progresivo para el protagonista. El personaje solo conoce lo que descubre; presencia y encuentros dependen de condiciones ecológicas. No canoniza fichas individuales.
- **Decisión aprobada:** estructura combinada del bosque: zonas de peligro dinámicas, caminos y territorios ecológicos, y niveles naturales donde la geografía los permita. No es un mapa lineal ni concéntrico. El enfoque general está aprobado, pero los nombres y conexiones concretos de subzonas siguen siendo propuestas.

## Conflictos con documentos anteriores

### 1. Fecha de la erupción
- Documentos antiguos: erupción como máximo el Día 7.
- Decisión nueva: Día 12.
- Resolución propuesta: Día 12 sustituye la fecha antigua para la planificación nueva. Falta actualizar la configuración ligera, cuadro de reglas, Lorebook maestra y JSON de importación de forma coordinada.

### 2. Grupo principal — RESUELTO el 31-10-2026
- El primer encuentro incluye tres aventureras: **Brina Solcor, Maelis Orven y Sera Linde**.
- Se conservan las cinco fichas originales, sin eliminar ni modificar las identidades de **Ivar Dalen** y **Timo Venn**.
- Ivar y Timo no están presentes en el claro inicial; su entrada se reserva para una escena posterior con causa y ubicación coherentes. El momento exacto todavía no está fijado.

### 3. Nombres y personalidades
- Brina, Ivar, Maelis, Sera y Timo ya tienen datos en Lorebook antigua.
- No sobrescribir sus fichas sin revisar los textos completos y el canon previo.
- Los nombres propuestos en el catálogo de especies son provisionales.

### 4. Psico-Eco
- La versión anterior de SpicyChat limitaba tres intentos por persona y describía Eco vegetal como mecanismo incierto.
- PSICHO-Eco es el nuevo poder incompleto que evoluciona con el usuario; la regla antigua no se traslada automáticamente a sus ramas, especies ni objetivos.
- Tampoco se consideran ilimitados los usos nuevos: coste, alcance, duración, resistencia y progresión deben definirse por separado.
- El ejemplo de los linfocitos B se modela como ficción mágica inspirada en memoria inmunológica, no como biología literal.

### 5. Inventario inicial
- Documento anterior fija ropa básica, pañuelo gastado, bolsita vacía y cordel corto; sin comida, dinero, armas ni equipo.
- No cambiar el inventario inicial sin autorización.

### 6. Mundo y geografía
- La geografía anterior contiene el Bosque de las Bestias, regiones exteriores y lugares ocultos.
- El catálogo de 50 especies no establece aún en qué subzona vive cada una.
- No inventar una conexión geográfica ni revelar lugares desconocidos al protagonista.

## Decisiones técnicas pendientes

- Estructura exacta de variables por tipo de entidad.
- Rangos y umbrales para hambre, miedo, dolor, confianza y agresividad.
- Modelo de aleatoriedad reproducible y persistencia de semilla.
- Población y pesos de encuentro por subzona.
- Reproducción, migración, depredación y regeneración de recursos.
- Costes, duración, resistencias y detección de Psico-Eco.
- Modelo de objetos mágicos y compatibilidad de semillas.
- Condiciones exactas para detener el volcán.
- Esquema de almacenamiento SQLite y migraciones.
- Contrato entre motor de reglas, IA y estado persistente.
- Pruebas de regresión y simulaciones de campaña.

## Estado de implementación

Todo el contenido de esta carpeta es documentación y datos de diseño. No debe etiquetarse como función ejecutable ni como integración terminada. Para implementarlo en Word Bot habrá que diseñar módulos, migraciones, validadores, API, interfaz y pruebas en una fase técnica separada.


- **Decisión aprobada:** presencia humana y civilizada combinada en el Bosque de las Bestias: aldeas aisladas, campamentos temporales, ruinas y escondites. Se aprueban las categorías y su coexistencia posible, no sus nombres, cantidades, ubicaciones, poblaciones, facciones ni historias concretas. Cada lugar tendrá estado propio y conocimiento separado del protagonista.

- **Decisión aprobada:** densidad equilibrada de presencia civilizada. Habrá varias comunidades pequeñas, campamentos relativamente habituales en rutas y zonas de expedición, y ruinas/escondites repartidos; también se conservarán extensiones amplias de bosque salvaje. No se fijan cantidades, población, facciones ni ubicaciones concretas.


- **Decisión aprobada:** ubicación repartida de las aldeas entre límites e interior del Bosque de las Bestias. La distribución será desigual, con mayor concentración relativa cerca de límites y accesos, algunas comunidades aisladas en el interior cuando la ecología y la seguridad lo permitan, y presencia estable muy escasa en zonas profundas/peligrosas. No se fijan nombres, cantidades, población, coordenadas, facciones ni ubicaciones concretas.

- **Decisión aprobada:** sistema combinado de rutas del Bosque de las Bestias: caminos principales relativamente estables, senderos secundarios variables y rutas ocultas o temporales. No todas las aldeas estarán conectadas directamente; algunas comunidades interiores podrán quedar aisladas temporalmente. Se aprueba el patrón general, no trazados, distancias, tiempos ni ubicaciones concretas.



## Decisiones aprobadas en conversación el 30-10-2026 — pendientes de implementación

### Coherencia contextual, fama y relaciones
- **Aprobado:** el mundo reacciona según gravedad, contexto, conocimiento, cultura, leyes, intereses, recursos y momento; no hay respuestas universales de NPC, guardias, ciudades o facciones.
- **Aprobado:** separar hechos reales, observaciones individuales, recuerdos, rumores, atribución y conocimiento del protagonista.
- **Aprobado:** la fama pública no cambia por un hecho que nadie presenció, descubrió ni pudo atribuir. Un crimen puede ser conocido sin que se conozca al autor.
- **Aprobado:** reputación localizada por grupos y regiones; la difusión requiere canales y tiempo plausibles. Los rumores pueden deformarse o ser falsos.
- **Aprobado:** las relaciones individuales mantienen ejes independientes (cariño, confianza, atracción, respeto, miedo, incomodidad, sospecha, resentimiento, lealtad, cuando sean aplicables).
- **Aprobado:** un éxito privado de Psico-Eco puede cambiar los ejes internos del objetivo sin alterar automáticamente la fama pública. Cariño no implica confianza, obediencia ni lealtad.
- **Aprobado:** un fallo de Psico-Eco deja incomodidad, inquietud o perturbación en el objetivo; eso no se convierte automáticamente en rumor público.
- **Aprobado:** los personajes conservan conocimiento, recuerdos, secretos y opiniones individuales; no heredan información de otros sin comunicación.
- **Aprobado:** no fragmentar el diseño en microencuestas para cada procedimiento menor. Las circunstancias concretas se resuelven con las reglas generales según gravedad, contexto y estado actual.

### Viajes y caravanas
- **Aprobado:** desplazamiento combinado según distancia, terreno, clima, hora, visibilidad, camino, estado del viajero, carga, método y obstáculos; duración estimada separada de duración real.
- **Aprobado:** orientación combinada; caminos conocidos ayudan, pero clima, oscuridad, cambios del terreno y falta de referencias pueden causar errores. Herramientas: referencias naturales, mapas, brújulas, señales y conocimiento local, todos falibles.
- **Aprobado:** información previa sobre rutas reunida de mapas, señales, rumores, habitantes y observación; puede ser incompleta, vieja, contradictoria o falsa.
- **Aprobado:** eventos dinámicos durante viajes, sin encuentros obligatorios; interrupciones pueden ser ignorables, exigir desvío o bloquear el paso, y tener consecuencias posteriores.
- **Aprobado:** el tiempo avanza por desplazamiento, encuentros, combates, conversaciones, descanso y desvíos; el resto del mundo continúa actuando.
- **Aprobado:** descanso contextual según refugio, seguridad, sueño, alimentación, heridas, clima y cansancio.
- **Aprobado:** carga combina peso, volumen, distribución, contenedores y efectos en movimiento/combate; sin valores numéricos aún.
- **Aprobado:** mundo con transporte organizado (a pie, monturas, animales de carga, carros/vehículos, caravanas, comerciantes, servicios y rutas), disponible según lugar y circunstancias.
- **Aprobado:** horarios y frecuencia de transporte combinan estabilidad relativa de rutas principales con variación de rutas secundarias y caravanas por demanda, clima, seguridad y recursos.
- **Aprobado:** costos y acceso combinan tarifas habituales variables, negociación, trueque, favores y trabajo; no se fijaron precios.
- **Aprobado:** protección de caravanas variable y reacción adaptativa a amenazas: negociar, esconderse, huir, desviarse, defenderse o pedir ayuda.
- **Aprobado:** participación libre del protagonista; separación con consecuencias y reencuentro mediante rutas, horarios, contactos, rumores y rastros sin garantía.
- **Aprobado:** miembros de caravanas tienen vida social, secretos, relaciones y conflictos propios. Los conflictos evolucionan y pueden afectar cooperación, economía, vigilancia, seguridad, liderazgo y viaje.
- **Aprobado:** liderazgo y organización de caravanas se adaptan a tamaño, origen, contratos, costumbres, capacidades y circunstancias. Sucesión, autoridad provisional, responsabilidad y revisión se resuelven según contexto; no se fija un procedimiento único para todas.

## Nuevos documentos de diseño

- [11_REPUTACION_RELACIONES_Y_CONOCIMIENTO.md](11_REPUTACION_RELACIONES_Y_CONOCIMIENTO.md): reglas de testigos, fama, rumores, relaciones individuales y consecuencias sociales de Psico-Eco.
- [12_VIAJES_TRANSPORTE_Y_CARAVANAS.md](12_VIAJES_TRANSPORTE_Y_CARAVANAS.md): reglas de desplazamiento, orientación, tiempo, descanso, carga, transporte, caravanas, vida social y liderazgo.

## Estado real

Las decisiones anteriores están aprobadas en conversación y ahora descritas en documentación de esta rama. **No están implementadas en el motor ni conectadas a SQLite.** Siguen pendientes el diseño ejecutable, migraciones, servicios de resolución, API, interfaz, pruebas unitarias y pruebas de campaña. No actualizar la configuración maestra ni el Lorebook de SpicyChat hasta una reconciliación coordinada.


## Actualización confirmada — origen del protagonista (30-10-2026)

La premisa nueva sustituye el inicio anterior sin celular ni pertenencias terrestres. El protagonista es humano de la Tierra contemporánea, llega con ropa normal y teléfono, y su traslado se desencadena al intentar alcanzar una caja promocional de cereal Dragon Ball Z con figura de Goku en un estante alto de un supermercado que cae con sus productos. Después encuentra a una diosa chibi que estaba con su teléfono, no esperaba recibir a nadie, revisa su pasado y lo considera inadecuado como héroe. Al pedir un poder de órdenes mentales recibe PSICHO-Eco, versión barata/incompleta que crece con el usuario. La diosa dice que enviará a alguien mejor, pero la llegada y el éxito de esa persona no están confirmados. El protagonista recuerda parcialmente la charla y la escena completa se recupera más adelante en una iglesia mediante un flashback cómico. Ver 13_ORIGEN_PROTAGONISTA.md.

## Direcciones de diseño añadidas — pendientes de implementación

- Mundo abierto en presentación de novela visual, con tres sugerencias y acción libre; mapa como grafo de lugares y acontecimientos como grafo causal.
- Personajes con profesión, clase/rol, atributos, especialidades, habilidades, personalidad, agenda y autonomía.
- Grupo de compañeros voluntarios, aliados, contratados y objetivos dominados por PSICHO diferenciados.
- Órdenes de exploración, tareas y combate; los resultados dependen de capacidades, equipo, estado y circunstancias.
- Aprendizaje en tiendas, libros, maestros, compañeros, gremios, favores, observación y práctica.
- Magia aprendida, habilidades especiales y poderes únicos separados; gremios, rangos, contratos y progresión.
- PSICHO-Eco de origen con ramas de información, eco, influencia, memoria, percepción, control limitado, intervención biológica fantástica y autointervención.
- Accidentes cotidianos, mágicos, sociales y de aventura; humor, personalidades anime y romance/ecchi opcional no forzado.
- Controles de contenido adulto con advertencias previas, personajes adultos y consentimiento explícito; PSICHO no equivale a consentimiento sexual y la diosa chibi queda excluida del contenido adulto.

No se han definido todavía escalas, fórmulas, costes, balance, capacidad de grupo ni reglas cuantitativas.


## Reconciliación del prólogo y del grupo — 30-10-2026

- **Continuidad provisional:** se conserva el claro del Bosque de los Siete Ecos (franja exterior del Bosque de las Bestias) como primer punto físico de llegada, después de la escena divina. La configuración heredada lo sitúa en Día 1, 08:00, con bruma y suelo húmedo; no se vuelve a mostrar el accidente del supermercado.
- **Inventario actualizado:** ropa normal contemporánea, celular y la caja promocional de cereal/figura de Goku vinculada a la escena divina. El estado exacto de los objetos y teléfono queda pendiente. No agregar automáticamente pañuelo, bolsa, cordel, dinero, comida, armas, mochila ni equipo que pertenecía a la versión anterior.
- **Grupo heredado:** la Lorebook documenta a Brina Solcor (26), Ivar Dalen (27), Maelis Orven (24), Sera Linde (25) y Timo Venn (22). Se conserva a los cinco como reparto documentado; la presencia simultánea de todos en el primer encuentro queda pendiente porque hay notas históricas de una posible composición de tres.
- **Maelis:** la Maelis de la ficha actual es maga. El ejemplo anterior de «Maelis aventurera/campesina» se considera ilustrativo de que las profesiones cambian capacidades; no crea una Maelis campesina ni altera la ficha existente.
- **PSICHO-Eco:** la regla histórica de tres intentos por persona humana pertenece a la versión antigua de Eco de la Lorebook. No se traslada automáticamente como regla universal al PSICHO-Eco evolutivo nuevo. Tampoco se supone uso ilimitado; costes, intentos y progreso quedan pendientes.
- **Flashback:** la visita posterior a una iglesia revela mejor la conversación divina. No es la primera adquisición del poder; PSICHO-Eco ya fue entregado antes del primer despertar físico.

Ver [16 — Puente de continuidad entre el origen terrestre y la primera aventura](16_PUENTE_PROLOGO_GRUPO_Y_CONTINUIDAD.md).



### Decisión de grupo incorporada el 31-10-2026
El conflicto sobre la cantidad de integrantes del primer encuentro deja de estar pendiente. Brina, Maelis y Sera son las tres presentes. Ivar y Timo se conservan en el reparto de cinco fichas y su primera aparición posterior queda por diseñar.
