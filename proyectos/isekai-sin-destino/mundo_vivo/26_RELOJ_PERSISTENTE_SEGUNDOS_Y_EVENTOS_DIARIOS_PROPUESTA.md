# Reloj persistente con precisión de segundos y acontecimientos de precisión diaria

**Estado:** propuesta técnica pendiente de revisión.  
**Dependencia:** PR #41, rama `fix/isekai-time-neutral-turns`.  
**Alcance:** diseño y criterios de aceptación; no cambia el código ni fija horas canónicas.

## 1. Hallazgo del código actual

La corrección de PR #41 elimina el minuto automático por turno, pero el resto del runtime sigue usando minutos enteros:

- `sessions` persiste `day` y `minute_of_day`; no existe campo para segundos.
- `NarratorResponse` comunica `elapsed_minutes` como entero.
- `apply_narrator_result` convierte día y minuto a minutos absolutos y luego actualiza la sesión.
- `absolute_minute` y `fire_due_world_events` ordenan la cronología con minutos absolutos.
- Los eventos mundiales requieren `scheduled_minute`, incluso cuando la historia solo define un día.
- `capture_turn_state` incluye día/minuto en los snapshots; `restore_turn_state` los restaura.
- La restauración de backups lee y vuelve a escribir los campos de sesión; el esquema del backup se valida antes de aplicarlo.
- El contexto del narrador y la respuesta del endpoint de estado exponen `minute_of_day` y una etiqueta horaria HH:MM.

En la auditoría #40 ya se identificó un escenario de ocho intercambios de diez segundos (80 segundos). La base actual no puede conservar ese remanente tras un turno, reinicio o restauración.

## 2. Alternativas

### A. Mantener minutos enteros

Ventajas:
- Menos cambios de esquema y de contrato.
- Compatible con el programador actual.

Costes:
- Los intervalos inferiores a un minuto se pierden, se redondean o quedan acumulados en memoria externa.
- Para conservar el remanente haría falta igualmente un campo persistente de segundos.
- Si el combate, interrupciones y acciones breves se quieren medir con precisión, la aplicación termina manteniendo dos unidades de tiempo.

### B. Usar segundos enteros como unidad de cálculo — recomendación

Ventajas:
- Representa directamente combates, pausas e interrupciones inferiores al minuto.
- Evita redondeos acumulativos.
- Permite comparar acciones, reloj y eventos sobre una sola línea temporal.

Coste:
- Requiere una migración coordinada de sesión, contrato de respuesta, snapshots, backups, contexto y programador.

**Recomendación:** adoptar segundos enteros para cálculo y persistencia, conservando día/minuto como campos derivados o de compatibilidad para la interfaz.

## 3. Contrato de sesión propuesto

Añadir a `sessions`:

```sql
second_of_minute INTEGER NOT NULL DEFAULT 0
  CHECK(second_of_minute BETWEEN 0 AND 59)
```

Reglas:
- `day` sigue comenzando en 1.
- `minute_of_day` sigue en el rango 0..1439.
- `second_of_minute` expresa 0..59.
- El instante absoluto se calcula con:

```text
total_seconds =
  (day - 1) * 86400
  + minute_of_day * 60
  + second_of_minute
```

- Las conversiones de vuelta a fecha y hora deben centralizarse en funciones puras, probadas con medianoche, cambio de día, límites y grandes saltos.
- La etiqueta actual HH:MM puede mantenerse para no romper la interfaz; el estado debe exponer también `second_of_minute` o una etiqueta precisa separada.
- No depender solo de un contador en memoria: la hora exacta debe sobrevivir al reinicio del proceso.

## 4. Contrato temporal del narrador

Sustituir en una entrega coordinada el campo `elapsed_minutes` por `elapsed_seconds`:

- 0 significa que no se consumió tiempo de ficción.
- Las acciones breves usan segundos enteros.
- La propuesta automática sigue teniendo un límite corto y explícito; no sustituye a `/salto`.
- `/salto` continúa aceptando minutos, horas y días para el avance explícitamente autorizado. La aplicación convierte las unidades a segundos de forma determinista.
- El modelo no puede proponer una duración porque haya escrito un mensaje más largo, ni volver a cobrar una acción ya contabilizada.
- Hasta que se aprueben tablas de duración, una acción sin base cuantitativa suficiente deja el reloj en 0 y crea una nota pendiente. No se inventan cifras.

Los proveedores manuales deberán recibir el esquema nuevo al preparar el prompt. Una respuesta JSON antigua con el campo retirado debe fallar de forma clara y pedir que se regenere desde un prompt actualizado, en lugar de mezclar unidades silenciosamente.

## 5. Programador: precisión temporal y registro de procesamiento

El sistema debe distinguir dos conceptos:

1. **Cuándo está definido que sucede un acontecimiento.**
2. **Cuándo lo detectó/procesó una sesión el runtime.**

Para acontecimientos con hora definida (precisión de minuto en esta etapa):
- Mantener `scheduled_day` y `scheduled_minute`.
- Convertir la fecha programada a segundos absolutos.
- Activar cuando el reloj cruce el instante programado.
- Guardar por separado el instante programado y el instante real de procesamiento/catch-up.
- No etiquetar el instante de procesamiento como si fuera el instante histórico del acontecimiento.

### Acontecimientos con precisión de solo día

Propuesta de esquema:

- `time_precision`: `day` o `minute`.
- `scheduled_minute`: nullable; obligatorio solo con `time_precision='minute'`.
- `scheduled_day`: siempre obligatorio.
- La erupción del Día 12 debe poder guardarse con `time_precision='day'` y `scheduled_minute=NULL`.

Reglas semánticas necesarias:
- Un evento de precisión diaria representa una ventana dentro de ese día, no un punto a las 00:00.
- No se le asigna una hora sustituta ni se utiliza un minuto técnico como si fuera canon.
- El contexto del narrador debe identificar expresamente la precisión: “día conocido; hora no registrada”.
- Los acontecimientos de precisión diaria no pueden interrumpir una acción larga en un segundo exacto que no está definido.
- Los acontecimientos de precisión de minuto sí pueden convertirse en límites exactos para la futura segmentación de acciones.
- Cuando una sesión alcanza el día programado o lo recupera después de un salto, el ledger debe registrar la fecha del hecho y, separadamente, cuándo lo procesó el runtime.
- El orden relativo entre un acontecimiento diario sin hora y otros sucesos del mismo día debe permanecer indeterminado salvo que una fuente posterior lo precise.

Esto evita inventar la hora de la erupción, pero deja explícito que una ancla de precisión diaria no puede producir una interrupción exacta sin una decisión posterior.

## 6. Snapshots, undo y backups

El segundo debe formar parte del estado autoritativo:

- `capture_turn_state` guarda `second_of_minute`.
- `restore_turn_state` lo restaura con día/minuto.
- El hash del estado posterior incluye el segundo.
- El backup incluye el nuevo campo; la restauración comprueba su estructura antes de modificar la sesión.
- Backups antiguos sin el campo nuevo pueden interpretarse con segundo 0 únicamente si el resto del esquema es una versión antigua reconocida y completa.
- No se deben aceptar backups parcialmente migrados.
- La restauración y el undo deben recuperar también el ledger de activaciones y los tiempos de procesamiento de eventos.
- Las definiciones compartidas del mundo siguen separadas del estado de cada sesión.

## 7. Migración y compatibilidad

Secuencia recomendada:

1. Añadir `second_of_minute DEFAULT 0` mediante una migración idempotente.
2. Mantener intactos los valores actuales de día/minuto.
3. Centralizar las conversiones a segundos absolutos.
4. Introducir `elapsed_seconds` en modelos, schemas, prompts, proveedores y API.
5. Migrar el ledger de eventos para separar programación y procesamiento.
6. Actualizar snapshots, undo, backup, restore, huellas de canon y contexto.
7. Mantener las respuestas públicas compatibles durante la transición: conservar `day`, `minute_of_day` y `time_label`; agregar los campos precisos sin cambiar silenciosamente el significado de los antiguos.
8. Retirar el contrato antiguo solo cuando todos los proveedores y pruebas usen el nuevo.

No se propone reconstruir tablas de SQLite si una columna con valor predeterminado y migración segura basta.

## 8. Pruebas de aceptación

1. Una respuesta conversacional por defecto mantiene el reloj idéntico.
2. Una acción de 10 segundos avanza 10 segundos, no un minuto.
3. Seis acciones sucesivas de 10 segundos avanzan exactamente 60 segundos.
4. Acciones simultáneas que duran 30 y 20 segundos avanzan 30 segundos globales, no 50.
5. Una actividad compuesta no vuelve a cobrar fases anidadas.
6. La conversión de 23:59:50 + 20 segundos produce el día siguiente a las 00:00:10.
7. Un combate de 80 segundos conserva la hora exacta tras reiniciar la aplicación.
8. Undo devuelve el segundo exacto anterior.
9. Backup y restore preservan el segundo exacto.
10. Un backup antiguo completamente válido restaura con segundo 0.
11. Un backup parcialmente migrado se rechaza sin mutar la sesión.
12. Los proveedores automáticos y manuales comparten el mismo contrato `elapsed_seconds`.
13. Un `/salto 2 minutos` suma exactamente 120 segundos.
14. Un salto mayor a 15 minutos solo ocurre cuando el usuario lo autoriza.
15. Un evento de minuto definido se activa una sola vez cuando se cruza su instante.
16. El instante programado y el instante de procesamiento se conservan como datos distintos.
17. Un evento de precisión diaria admite minuto nulo.
18. El evento diario no se transforma en 00:00 ni recibe una hora ficticia.
19. La erupción del Día 12 sigue siendo un hecho del día 12 sin hora añadida.
20. Un evento diario sin hora no provoca una interrupción exacta inventada.
21. Un evento de minuto puede interrumpir posteriormente una actividad segmentada en intervalos.
22. Reintento, replay y undo no duplican activaciones.
23. La restauración mantiene el ledger coherente con el reloj.
24. La etiqueta HH:MM existente sigue funcionando y la precisión nueva se expone sin romper clientes actuales.

## 9. Fuera de alcance

Esta propuesta no implementa:
- Agendas autónomas de Brina, Maelis o Sera.
- Velocidades y distancias de viaje.
- Hambre, sed, sueño, fatiga, curación ni tasas biológicas.
- Segmentación completa de actividades largas.
- Selección definitiva de duraciones por categorías.
- Cronología previa del trío.
- Una hora concreta para la erupción del Día 12.

## 10. Estado de aprobación

- La recomendación de arquitectura es **segundos enteros como unidad de cálculo**, conservando día/minuto como campos derivados y de compatibilidad.
- Es una recomendación técnica pendiente de aprobación; no modifica el canon ni el mundo narrativo.
- No se implementan migraciones ni cambios de runtime en esta entrega documental.
