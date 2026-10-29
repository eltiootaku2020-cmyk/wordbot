# 01 — Reglas del mundo vivo

**Estado:** especificación de diseño. Las reglas marcadas como propuestas necesitan revisión antes de convertirse en canon.

## 1. Principio central

El mundo existe independientemente del protagonista. Cada entidad puede tener identidad, estado, necesidades, objetivos, conocimiento, capacidades y relaciones. El protagonista puede influir en el mundo, pero no es el centro obligatorio de todos los acontecimientos.

Un paso en falso puede generar una amistad improbable con un duende gruñón o una muerte causada por un oso hambriento. Ambos resultados deben surgir de circunstancias y decisiones comprensibles.

## 2. Capas de simulación

1. **Entorno:** región, subzona, hora, clima, visibilidad, terreno, refugios, recursos y energía mágica.
2. **Ecología:** especies, poblaciones, presas, depredadores, territorios, ciclos, reproducción y migración.
3. **Organismos:** salud, heridas, hambre, sed, fatiga, sueño, temperatura, instintos y necesidades propias de la especie.
4. **Psicología:** personalidad, objetivos, recuerdos, emociones, confianza, miedo, sospecha y conocimiento.
5. **Magia:** afinidad, reserva, compatibilidad, exposición, efectos, resistencia y consecuencias.
6. **Sociedad:** grupos, jerarquías, economía, reputación, leyes, conflictos y rumores.
7. **Historia:** cronología, acontecimientos ancla, decisiones, testigos y consecuencias persistentes.

No todas las entidades usan todas las variables. Cada especie y tipo de entidad declara qué campos aplican.

## 3. Variables y escalas

- Las variables cuantificables pueden utilizar escala 0–100 cuando tenga sentido.
- 0 y 100 representan extremos del eje definido, no resultados universales.
- No existe un umbral único que determine automáticamente una acción.
- Un valor ausente es `No registrado`, no cero ni neutralidad.
- Los cambios deben registrar valor anterior, valor nuevo, causa y evidencia.
- Una variable de intensidad no es una probabilidad. Si se necesita probabilidad de éxito, se calcula aparte con capacidades, contexto, oposición y azar controlado.
- El sistema no debe mostrar números al jugador salvo que la interfaz o el personaje tenga una forma justificada de conocerlos.

Ejemplos de ejes: hambre, sed, fatiga, miedo, confianza, agresividad, dolor, curiosidad, alerta, afinidad mágica y exposición a una sustancia. Son ejemplos de diseño, no valores iniciales fijados.

## 4. Aleatoriedad con causalidad

La aleatoriedad decide entre posibilidades válidas; no sustituye la lógica del mundo.

Cada generación de encuentro considera, cuando corresponda:
- Bioma y subzona.
- Hora y estación, si están definidas.
- Clima y condiciones del terreno.
- Especies presentes y densidad conocida.
- Huellas, ruidos, cadáveres, alimento y refugios.
- Estado de las criaturas y eventos recientes.
- Acciones del protagonista y de otros agentes.
- Probabilidad de no encontrar nada.

Reglas:
- No generar una especie fuera de su hábitat sin explicar migración, transporte o excepción.
- No hacer aparecer siempre un encuentro. El resultado válido puede ser silencio, rastros o ningún hallazgo.
- No repetir el mismo individuo después de huir, morir o desplazarse, salvo explicación.
- La población y el estado ecológico cambian por caza, hambre, reproducción, clima y catástrofes.
- Un evento aleatorio importante debe registrarse para que no se contradiga después.
- La semilla aleatoria y el registro de resultados deberán persistir cuando el motor ejecutable se implemente, para poder reproducir errores y pruebas.

## 5. Comportamiento por estado

La etiqueta de especie no dicta una única reacción. El comportamiento depende de:
- Temperamento individual.
- Hambre, sed, dolor, heridas y fatiga.
- Crías, pareja, manada o territorio.
- Percepción del protagonista y distancia.
- Experiencias y recuerdos.
- Diferencia de fuerza y riesgo percibido.
- Olor, ruido, postura, armas y magia.
- Rutas de huida, escondites y condiciones del terreno.

Ejemplo: un oso hambriento puede seguir atacando aunque un recuerdo agradable reduzca momentáneamente su hostilidad. El hambre y el instinto de supervivencia no desaparecen porque se altere un recuerdo.

## 6. Conocimiento y percepción

- Cada personaje solo conoce lo que percibió, dedujo razonablemente o le contaron.
- Registrar fuente: visto, oído, leído, deducido, rumor o manipulado.
- Una sospecha no equivale a una verdad.
- Buscar un enemigo oculto no garantiza detectarlo; el resultado depende de percepción, cobertura, ruido, preparación y habilidad del oculto.
- El jugador puede descubrir objetos, huellas, trampas, asesinos, criaturas camufladas y fenómenos mágicos sin que todo esté conectado a la trama principal.

## 7. Acciones, opciones y libertad

La interfaz puede ofrecer tres acciones sugeridas y una opción libre **Otro**. Las opciones son atajos, no límites. La acción libre siempre debe poder describirse en lenguaje natural.

Las acciones complejas se resuelven por etapas:
1. Intención.
2. Método o herramienta.
3. Ejecución.
4. Reacción del entorno o entidad.
5. Resultado y consecuencias.

El jugador puede detenerse, cambiar de idea, retroceder o intentar otra cosa cuando la situación lo permita.

## 8. Justicia y muerte

- No hay protección automática del protagonista ni de compañeros importantes.
- Una acción peligrosa puede causar lesión grave o muerte.
- La muerte debe tener una causa interna coherente y, cuando sea posible, señales o riesgos que el jugador pudiera observar.
- No se garantiza que todo peligro sea anunciado; sigilo, sorpresa y mala suerte existen.
- No se debe convertir una mala tirada arbitraria en muerte inevitable si las circunstancias no la justifican.
- Personajes muertos no reaparecen como el mismo individuo sin una regla de resurrección establecida.
- El resultado debe conservar consecuencias: cadáver, desaparición, testigos, pérdida de equipo, cambios sociales y reacciones.

## 9. Acontecimientos del mundo y libertad

El volcán es un acontecimiento ancla fijado para el Día 12 en la planificación actual. El jugador puede investigar, ignorar, huir, preparar evacuaciones, intentar intervenir o cambiar las consecuencias mediante acciones causalmente suficientes.

La fecha no debe forzar una escena sin continuidad. El sistema debe explicar señales previas y registrar qué puede cambiarse y qué no. La mecánica exacta para detener la erupción aún debe diseñarse.

## 10. Separación entre simulación y narración

- El motor de reglas valida estado y resultados.
- La IA redacta la escena, diálogo y opciones.
- La IA no puede actualizar arbitrariamente salud, inventario, relaciones, recuerdos, muertes o variables sin un resultado validado.
- Si falta información, el motor solicita datos o usa un resultado incierto; no rellena huecos como hechos.
- El registro estructurado es la fuente de verdad; el texto narrativo no reemplaza el estado.

## 11. Decisión aprobada: mundo mixto y descubrimiento gradual

El usuario eligió un enfoque mixto para el Bosque de las Bestias. Esto se convierte en una regla de diseño del módulo:

- **Diseño interno completo:** el equipo puede definir el mapa ecológico, subzonas, especies, plantas, recursos, amenazas, secretos, ciclos y relaciones entre elementos antes de que el protagonista los encuentre.
- **Conocimiento gradual:** el protagonista solo conoce lugares, especies, objetos y reglas que haya observado, investigado, experimentado o aprendido de una fuente.
- **Separación de estados:** mantener por separado el catálogo/diseño del mundo, el estado real actual del mundo y el conocimiento del protagonista. Un dato puede existir en el diseño sin estar presente ahora; puede estar presente sin haber sido descubierto.
- **Sin revelación automática:** la narración y la interfaz del personaje no deben mostrar información desconocida solo porque exista en los archivos de diseño.
- **Presencia condicionada:** las especies y recursos aparecen según hábitat, subzona, hora, clima, población y estado ecológico. No se presupone que las 50 especies estén juntas ni que un encuentro concreto esté garantizado.
- **Descubrimiento verificable:** un hallazgo añade conocimiento con fuente y grado de certeza; una huella puede sugerir una especie sin confirmar su identidad.

Esta decisión fija el enfoque general, no aprueba automáticamente nombres, estadísticas ni fichas individuales del catálogo.


## 12. Decisión aprobada: estructura combinada del bosque

El usuario eligió organizar el Bosque de las Bestias mediante una combinación de zonas de peligro, caminos y territorios, y niveles naturales.

- El bosque no se divide en anillos concéntricos ni en niveles de dificultad lineales.
- La geografía se organiza mediante regiones y subzonas conectadas por rutas transitables con condiciones propias.
- Los niveles naturales (suelo, sotobosque, copas, cavidades, subsuelo y cavernas) existen solo donde la geografía los permita.
- Los territorios ecológicos de criaturas pueden cruzar varias subzonas y cambiar con el tiempo.
- El peligro es una capa dinámica determinada por criaturas, clima, hora, terreno, recursos, rastros y acontecimientos; la distancia al borde no determina por sí sola la dificultad.
- El mapa completo pertenece al diseño interno. El protagonista descubre rutas, territorios y puntos de interés mediante experiencia y fuentes; no recibe el mapa completo automáticamente.
- Se modelará el mapa como nodos, conexiones, territorios y puntos de interés, con estado real separado del conocimiento del protagonista.

La estructura general está aprobada. Los nombres, posiciones, conexiones y fichas de subzonas concretas siguen siendo propuestas hasta su revisión.

## Decisión aprobada: presencia humana y civilizada combinada

El usuario eligió combinar cuatro formas de presencia dentro del Bosque de las Bestias: **aldeas aisladas, campamentos temporales, ruinas y escondites**.

- El bosque no será exclusivamente salvaje ni estará cubierto por una red continua de poblaciones.
- Las aldeas son comunidades pequeñas y relativamente estables; pueden estar dentro del bosque o en sus límites. Sus habitantes, ubicación, tamaño, economía y relaciones quedan por diseñar.
- Los campamentos son temporales o móviles y pueden pertenecer a aventureros, cazadores, comerciantes, exploradores u otros grupos. Su permanencia depende de motivos y condiciones.
- Las ruinas indican ocupaciones o actividades pasadas. Su origen, época, función y peligros son desconocidos hasta reunir evidencia.
- Los escondites son lugares discretos que pueden servir de refugio, guarida, depósito, puesto de observación u ocultación. No se presupone quién los construyó ni para qué.
- Cada lugar tendrá estado propio: conocimiento del protagonista, ocupación, condición física, accesibilidad, recursos, riesgos, ocupantes y vínculos con rutas y territorios.
- No todas las categorías tienen que aparecer en cada zona ni en todas las partidas. La presencia debe tener causas geográficas, históricas, ecológicas y sociales.
- Un lugar diseñado no equivale a un lugar descubierto; la narración no revelará automáticamente su existencia, ocupantes o propósito.

La decisión aprueba las cuatro categorías y su coexistencia posible. No aprueba todavía nombres, número de aldeas, población, facciones, coordenadas, edificios ni historias concretas.


## Decisión aprobada: densidad equilibrada de presencia civilizada

El usuario eligió una densidad **equilibrada** para las aldeas, campamentos, ruinas y escondites del Bosque de las Bestias.

- Habrá varias comunidades pequeñas, pero no una población continua ni asentamientos en cada subzona.
- Los campamentos serán relativamente habituales en rutas transitadas, zonas de expedición y puntos con recursos, pero su presencia será temporal y variable.
- Ruinas y escondites estarán repartidos, aunque muchos permanecerán ocultos, inaccesibles o sin descubrir.
- Se conservarán extensiones amplias de bosque salvaje entre los lugares habitados.
- La densidad global no fija cantidades exactas ni garantiza encuentros; la distribución dependerá de geografía, recursos, seguridad, historia, accesibilidad y presión ecológica.
- Los nombres, cifras, poblaciones, facciones y ubicaciones concretas siguen pendientes de diseño y aprobación.
