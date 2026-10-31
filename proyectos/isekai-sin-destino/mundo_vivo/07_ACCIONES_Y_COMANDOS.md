# 07 — Acciones, decisiones y comandos

**Estado:** propuesta de interfaz y vocabulario. No todos estos comandos existen todavía en Word Bot.

## 1. Decisiones sugeridas + acción libre

Cuando la escena tenga una decisión clara, la interfaz puede ofrecer tres acciones sugeridas y siempre permitir **Otro** para escribir libremente.

Ejemplo:
1. Observar al oso.
2. Prepararse para luchar.
3. Retroceder lentamente.
4. Otro: escribir una acción libre.

Las opciones deben surgir de la escena, no de una lista fija. No mostrar opciones irrelevantes ni ocultar acciones que el jugador ya conoce. La opción libre no debe penalizarse por no coincidir con las sugerencias.

## 2. Acciones por etapas

Una acción puede abrir decisiones más específicas.

Ejemplo:
- Situación: oso a pocos metros.
- Intención: luchar.
- Método: daga, piedra, rama, arma disponible o sin arma.
- Táctica: atacar, esperar, fintar, apuntar, distraer, retroceder.
- Resolución: reacción del oso, resultado, consecuencias.

El jugador puede cambiar de idea si el tiempo y la situación lo permiten. Una acción no debe ejecutarse automáticamente hasta que el jugador confirme lo que intenta.

## 3. Vocabulario de acciones

### Exploración
- `/observar [objetivo]`
- `/mirar_alrededor`
- `/escuchar`
- `/buscar [objeto/recurso]`
- `/buscar_ocultos`
- `/examinar [objetivo]`
- `/rastrear [rastro]`
- `/inspeccionar [zona]`

### Interacción
- `/hablar [personaje]`
- `/preguntar [tema]`
- `/negociar [objetivo]`
- `/ofrecer [objeto]`
- `/ordenar [entidad] [orden]`
- `/esperar [duración]`

### Psico-Eco
- `/psicoeco informacion [objetivo]`
- `/psicoeco influencia [objetivo] [intención]`
- `/psicoeco memoria [objetivo] [recuerdo]`
- `/psicoeco percepcion [objetivo] [intención]`
- `/psicoeco biologico [objetivo/proceso]`
- `/psicoeco propio [modo] [intención]`
- `/psicoeco ficha [objetivo]`

### Estado y continuidad
- `/estado`
- `/ficha [ID/nombre]`
- `/mapa`
- `/vinculos`
- `/inventario`
- `/guardar`
- `/continuar`

Los comandos son una interfaz abreviada. El jugador también puede escribir lenguaje natural. Los comandos existentes en la configuración actual deben mantenerse compatibles hasta que se haga una migración revisada.

## 4. Resolución del intento

Cada acción se registra como:
- ID de acción.
- Tiempo y lugar.
- Intención del jugador.
- Método/herramienta.
- Objetivo.
- Información disponible para el protagonista.
- Factores relevantes.
- Riesgo comunicado o señal perceptible.
- Resultado validado.
- Cambios de estado.
- Consecuencias y testigos.

No inferir que el jugador quiso hacer una acción distinta. Si la intención es ambigua y afecta mucho el resultado, pedir aclaración breve.

## 5. Señales y opciones

El narrador puede sugerir acciones, pero no revelar información que el protagonista no conoce. Las opciones pueden incluir riesgos evidentes y pistas observables; no deben incluir la solución secreta si el personaje aún no la descubrió.

## 6. Errores, fallos y muerte

El sistema puede producir éxito, éxito parcial, fallo, complicación, lesión, pérdida, detección por enemigo o muerte cuando sea coherente. No usar un fallo como castigo arbitrario ni proteger al protagonista de consecuencias razonables.

## 7. Comandos existentes a preservar

La configuración previa ya documenta `/accion`, `/mapa`, `/ruta`, `/estado`, `/ficha`, `/vinculos`, `/guardar` y `/continuar`. Esta propuesta los amplía; no afirma que todos los comandos nuevos estén implementados.
