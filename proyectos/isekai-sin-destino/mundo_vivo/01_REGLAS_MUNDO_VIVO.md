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
