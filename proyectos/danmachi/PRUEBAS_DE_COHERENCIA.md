# DanMachi — pruebas de coherencia antes de publicar

Ejecutar estas pruebas manualmente en SpicyChat. No marcar ninguna como aprobada antes de probarla en el bot real.

## Prueba 1 — La hora no se reinicia

**Preparación:** jugar hasta avanzar varias horas o al Día 2.  
**Acción:** enviar otro mensaje después de esperar varias horas reales.  
**Resultado esperado:** el reloj ficticio conserva el último estado confirmado y avanza solo por las acciones de la historia. Nunca reaparece el Día 1 a las 09:10 salvo que se haya iniciado expresamente una partida nueva.

## Prueba 2 — Preguntar por estadísticas

**Acción:** preguntar al mundo «¿cuáles son mis estadísticas?».  
**Resultado esperado:** no aparece un panel de videojuego ni números inventados. El narrador explica solo lo que el protagonista puede conocer mediante las reglas de Falna.

## Prueba 3 — No conceder Falna automáticamente

**Preparación:** el protagonista no se ha unido a una Familia.  
**Acción:** pedir un Status o preguntar qué nivel tiene.  
**Resultado esperado:** el bot no inventa una Falna, nivel o habilidades. Registra la información como desconocida o inexistente según los hechos de la partida.

## Prueba 4 — Poder inventado

**Acción:** el protagonista dice que intenta disparar fuego por las manos sin poseer magia establecida.  
**Resultado esperado:** el intento no se convierte en un hechizo real sin causa, conocimiento y capacidad compatibles con el universo.

## Prueba 5 — No controlar al protagonista

**Acción:** hablar con una deidad sobre una posible Familia.  
**Resultado esperado:** la deidad responde y el usuario decide si acepta, rechaza, hace preguntas o se marcha. El bot no toma la decisión en su nombre.

## Prueba 6 — Personajes canónicos con vida propia

**Acción:** el protagonista encuentra a un personaje conocido.  
**Resultado esperado:** el personaje actúa según su personalidad y el momento del canon. No se vuelve amigo, rival, mentor o interés romántico automáticamente.

## Prueba 7 — Evitar spoilers futuros

**Preparación:** fijar una cronología temprana.  
**Acción:** mencionar a una Familia, personaje o habilidad de una saga futura.  
**Resultado esperado:** no se revela información posterior a la cronología fijada. El narrador trata los detalles desconocidos como desconocidos.

## Prueba 8 — Reanudar con un punto de guardado

**Preparación:** generar /guardar al final de una sesión y copiar el bloque.  
**Acción:** en una nueva conversación, proporcionar ese punto de guardado y pedir que continúe.  
**Resultado esperado:** continúa desde ese estado, sin reponer objetos gastados, restaurar heridas, modificar relaciones ni inventar hechos intermedios.

## Prueba 9 — Falta de contexto

**Preparación:** retomar una conversación que ya no contiene los mensajes iniciales.  
**Acción:** pedir que continúe sin entregar un punto de guardado.  
**Resultado esperado:** si no puede verificar el estado, el bot pide el último registro o presenta los datos desconocidos. No reinicia silenciosamente la aventura.

## Prueba 10 — Lorebook demasiado amplia

**Acción:** hablar de una posada sin mencionar personajes o lugares canónicos no relacionados.  
**Resultado esperado:** se activa el contexto relevante; el bot no introduce de golpe varias Familias, poderes y secretos que no vienen al caso.

## Registro de resultado

Para cada prueba, anotar:
- Fecha:
- Modelo seleccionado:
- Prueba:
- Resultado: Pendiente / Aprobada / Fallida.
- Contradicción observada:
- Corrección necesaria:
