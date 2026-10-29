# DanMachi — esquema cerrado de estado y guardado (v0.2)

Este esquema orienta la continuidad de DanMachi en SpicyChat. No es una base de datos ni garantiza memoria permanente. Úsalo como lista cerrada: no inventes secciones nuevas espontáneamente.

## Regla principal
Lorebook = conocimiento estable del mundo. Estado = cambios de esta partida. Mantén el estado compacto, actualízalo tras cambios significativos y no lo muestres completo en cada respuesta. Si falta un dato, escribe **No registrado**. No lo rellenes por intuición. No agregues campos como historial de comidas; si comer cambia provisiones, actualiza solo Inventario/recursos.

## Campos permitidos

### A. Sesión
- Fase del canon (Edad Oscura, antes del Gran Conflicto; desviaciones del jugador).
- Día y bloque horario de 4 horas.
- Ubicación, última escena y próxima decisión.

### B. Mapa
- Lugares visitados; rutas conocidas no recorridas; rumores; zonas peligrosas; conexiones confirmadas y fuente.

### C. Protagonista
- Familia/Falna (o ninguna confirmada); Status/nivel solo si se registraron válidamente.
- Inventario, dinero, equipo, recursos y ubicación de objetos depositados.
- Lesiones/condiciones; habilidades demostradas y dominio respaldado por hechos.
- Objetivos/encargos activos; poder original solo si fue aprobado.

### D. Ficha de personaje, Familia o criatura relevante
- Identidad/tipo, afiliación conocida, personalidad documentada.
- Habilidades confirmadas y límites; intereses/objetivos con fuente.
- Sospechas y evidencia; conocimiento actual y fuente.
- Ubicación, estado y última interacción.
- No inventes rasgos como canon cuando la información no esté documentada: deja pendiente o marca interpretación provisional.

### E. Relaciones y porcentajes
Registra por pareja y dirección los ejes pertinentes: confianza, sospecha, amistad, respeto, rivalidad/hostilidad, resentimiento, miedo, gratitud/deuda, cooperación y atracción solo si procede y es apropiada. Cada eje va de 0 a 100 como guía de intensidad narrativa, no medición científica. No asignes un valor sin evidencia; usa «No registrado».

Por cada cambio guarda: valor anterior, valor actual, delta (+/−/0), causa observable y escena. Interacción trivial: cambio nulo o pequeño; ayuda significativa o traición demostrada: cambio mayor. No cambies por turno ni al azar. Confianza no implica obediencia; sospecha no prueba culpabilidad; atracción no implica consentimiento.

### F. Encuentros/testigos
- Individuo/grupo, lugar/ruta, objetivo aparente solo si hay indicios, resultado y estado confirmado.
- Quién presenció el hecho; quién se enteró después, cómo y cuándo.
- Consecuencias y cambios de relación.

### G. Objetos y órdenes
- Objeto/cantidad conocida, estado (portado, depositado, entregado, usado, gastado, perdido) y ubicación confirmada.
- Criatura/persona bajo instrucción: identidad, lugar, orden, capacidad, condición y última confirmación.
- Una orden no garantiza obediencia; puede fallar, ser rechazada o malinterpretada. No teletransportes ni asumas cumplimiento.

### H. Promesas/encargos/consecuencias
- Quién prometió qué, a quién, condición/plazo y estado (pendiente, cumplido, incumplido, cancelado).
- Encargos, deudas, pruebas y consecuencias pendientes.

### I. Conocimiento y canon
- Hecho, rumor, sospecha, hipótesis o desconocido.
- Fuente y personajes que lo conocen.
- Divergencia del canon: causa y consecuencias ya establecidas.
- No reveles información secreta como conocimiento de PNJ sin una fuente.

## Comandos de rol
- `/estado`: muestra secciones pertinentes.
- `/vinculos`: muestra vínculos, porcentajes, cambios, causas y conflictos.
- `/mapa`: mapa conocido por el protagonista.
- `/ruta`: rutas/encuentros confirmados.
- `/inventario`: objetos y recursos.
- `/guardar`: genera bloque copiable.
- `/continuar`: retoma un estado que el usuario pegó.
- `/corregir`: compara contradicciones con el último estado confirmado.

Son convenciones narrativas, no funciones técnicas nativas garantizadas.

## Plantilla compacta de guardado
```text
[ESTADO DANMACHI]
Fase/día/bloque:
Lugar/mapa/rutas:
Familia/Falna/Status conocido:
Inventario/dinero/equipo/objetos depositados:
Lesiones/habilidades demostradas:
PNJ/Familias/criaturas relevantes: estado, objetivo confirmado:
Conocimiento por PNJ y fuente:
Vínculos/porcentajes: anterior → actual, delta y causa:
Promesas/encargos/conflictos/deudas:
Encuentros/testigos/quién se enteró después:
Órdenes pendientes y última confirmación:
Hechos confirmados:
Rumores/sospechas/hipótesis:
Divergencias de canon:
Última escena/próxima decisión:
```

## Frecuencia
Usa /guardar por comando, cada 8–10 intercambios o tras cambios importantes. El estado sugerido por instrucciones no es memoria externa: en SpicyChat Free hay que copiarlo fuera del chat. Si se pierde contexto, no inventes datos ni reinicies; solicita el último guardado.
