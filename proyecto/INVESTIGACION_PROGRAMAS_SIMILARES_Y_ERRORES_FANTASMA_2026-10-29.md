# Investigación de programas similares y errores fantasma — 29 de octubre de 2026

## Conclusión ejecutiva

Word Bot ya tiene una base útil: FastAPI, SQLite, contexto de escena, filtro de audiencia, un inspector Lorebook, propuestas de estado validadas y snapshots para deshacer. La revisión más valiosa no es sumar más sistemas grandes; es probar qué ocurre cuando operaciones válidas se encadenan en distinto orden.

En esta ronda se encontró un defecto sutil: un turno fallido o anulado conservaba una instantánea anterior y podía intentar reutilizarse después de que el estado hubiera avanzado. Se corrigió en PR #9 y se reforzó en PR #10. La CI asociada a PR #10 aprobó **86 pruebas Python** y la comprobación sintáctica de JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40940906581.

La CI sigue usando proveedor simulado; no es todavía una validación visual en Windows ni una campaña real con cuentas web de ChatGPT/Gemini.

## Programas revisados y lecciones útiles

### 1. SillyTavern — World Info / Lorebooks

Fuente: https://docs.sillytavern.app/usage/core-concepts/worldinfo/

World Info inserta entradas al activarse sus claves; permite limitar la profundidad de búsqueda y presupuestar el contexto. Sus documentos advierten que activar una entrada no garantiza que el modelo la siga, y recomiendan que el contenido de cada entrada sea autónomo y suficientemente completo.

**Lección para Word Bot:** distinguir entre «ficha seleccionada» y «hecho obedecido/confirmado». El inspector debe seguir mostrando por qué una entrada se incluyó, qué presupuesto consumió y qué información se quedó afuera. El presupuesto actual está expresado en caracteres; una medición exacta de tokens queda pendiente si se necesita comparar proveedores.

### 2. Chronicler — privacidad de memoria durante campañas largas

Fuente: https://github.com/yantrikos/chronicler

El proyecto declara una política de memoria por capas, controles de visibilidad por memoria (`visible_to`) aplicados durante la recuperación y un inspector del prompt que expone qué se incluyó y por qué.

**Lección para Word Bot:** la privacidad debe filtrarse antes de la selección por relevancia, no depender de pedirle al modelo que ignore un secreto. La cobertura existente de destinatario, audiencia, testigos y eventos sin fuente debe seguir siendo conservadora. Las pruebas nuevas deben combinar privacidad con undo, regeneración, migración y restauración.

### 3. RPG Tracker for SillyTavern — snapshots y registro de deltas

Fuente: https://github.com/Soyo5800/rpg-tracker-for-sillytavern

La extensión registra estado de personaje/mundo, ofrece snapshots por mensaje y un registro de cambios; su README también advierte que está en fase experimental y que la estabilidad del JSON y el seguimiento de instrucciones varían según el modelo.

**Lección para Word Bot:** cualquier edición o regeneración tiene que mantener juntos tres elementos: estado autorizado, narración visible e historial de auditoría. No basta con que el inventario vuelva al número correcto si queda una narración o un evento activo que afirma lo contrario.

### 4. Open Dungeon — controles de edición y continuidad local

Fuente: https://github.com/newideas99/open-dungeon

El proyecto ofrece almacenamiento local, controles de continuar/reintentar/borrar/editar pasajes y compactación gradual del relato largo en un resumen. Incluye SQLite, aunque sus requisitos de hardware y generación local son distintos del objetivo ligero de Word Bot.

**Lección para Word Bot:** los controles para corregir una narración deben ser explícitos y reversibles. La compactación del historial puede ser útil más adelante, pero no conviene introducirla antes de medir fallos reales de selección o límites de contexto. No hace falta adoptar su arquitectura de imágenes o modelos locales para arreglar la fiabilidad actual.

### 5. Openovel — historia persistente fuera del prompt

Fuente: https://github.com/Feed-Scription/openovel

Openovel separa la narración de primer plano de un ciclo que mantiene archivos Markdown/JSON de mundo y memoria; el repositorio se identifica como beta/demo y advierte que sus interfaces internas aún pueden cambiar.

**Lección para Word Bot:** una historia no debería depender de que el modelo recuerde texto antiguo dentro de la conversación. Word Bot ya mantiene canon y estado en SQLite; la siguiente mejora debe reforzar trazabilidad y restauración de esos datos, no sumar agentes de fondo sin necesidad demostrada.

### 6. Gamentic — pruebas contra base real y modelo simulado

Fuente: https://github.com/hec-ovi/gamentic

El README describe un motor con FastAPI, SQLite y JavaScript, pruebas de rutas contra una base SQLite real con el modelo simulado en la frontera de LLM, además de pruebas de recorrido completo/soak sobre su stack.

**Lección para Word Bot:** las pruebas unitarias de reglas, las pruebas de API contra SQLite y una campaña de larga duración validan riesgos diferentes. La CI actual hace lo primero y lo segundo y tiene 100 turnos breves simulados con restauración exacta; eso no demuestra todavía una historia larga real en el navegador. La campaña manual con reinicios sigue siendo necesaria.

## Error fantasma detectado y corrección

### Síntoma

1. El jugador completa un turno A.
2. Deshace A, devolviendo el estado a su snapshot anterior.
3. Juega un turno B o aprueba una propuesta que modifica el estado fuera del flujo narrativo.
4. Intenta de nuevo A con el mismo `request_id`.

Antes de la corrección, el turno antiguo podía intentar reutilizar su snapshot y entrar fuera de orden en la cronología. El riesgo no se limitaba a que la hora se equivocara: una futura operación de undo podía recuperar un estado demasiado antiguo y borrar efectos posteriores. El mismo patrón podía ocurrir al reintentar una petición fallida después de que la partida hubiera avanzado.

### Corrección integrada

- **PR #9:** rechazar la regeneración de un turno anulado si ya existe un turno de usuario posterior.
  https://github.com/eltiootaku2020-cmyk/wordbot/pull/9
- **PR #10:** extender la protección a turnos fallidos y exigir que el snapshot exista, se pueda leer y coincida exactamente con el estado mutable actual antes de permitir un reintento antiguo.
  https://github.com/eltiootaku2020-cmyk/wordbot/pull/10
- **CI de PR #10:** 86 pruebas Python aprobadas, una advertencia no bloqueante y sintaxis JavaScript correcta.
  https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40940906581

La protección no desactiva el reintento normal: si falla un proveedor, no hubo un turno posterior ni cambió el estado y el snapshot sigue coincidiendo, la misma solicitud puede volver a intentarse. Si el estado ya no coincide, la aplicación rechaza el turno antiguo y pide continuar con una acción nueva o restaurar una copia.

## Próximos escenarios de búsqueda de errores fantasma

Estos son candidatos de pruebas, no defectos confirmados:

1. **Pérdida de respuesta después de guardar:** el servidor termina de aplicar la compra, pero se pierde la respuesta HTTP. Repetir el mismo `request_id` debe devolver el resultado guardado sin cobrar de nuevo.
2. **Cambios de aprobación fuera del turno:** aprobar una relación, recurso o inventario mientras hay una respuesta preparada; comprobar que no se sobrescribe después con un contexto o snapshot antiguo.
3. **Privacidad restaurada desde backup antiguo:** datos de audiencia incompletos o contradictorios deben fallar de forma conservadora, sin filtrarse por el camino de recuperación por relevancia.
4. **Dos partidas abiertas:** los mensajes, eventos, copias y bloqueos de una partida no deben bloquear ni mutar otra.
5. **Fallo de restauración a mitad de camino:** forzar una restricción de SQLite y verificar que la transacción revierte toda la restauración.
6. **Historia larga real:** alternar diálogo privado y grupal, compras, gastos, viajes, usos de poder, cambios pendientes, reinicio y restore durante 50–100 intercambios. Comparar la narración con el estado autorizado en cada checkpoint.

## Estado

- **Verificado por CI:** 86 pruebas Python y comprobación sintáctica JavaScript en la revisión de PR #10; restauración tras 100 turnos breves simulados sigue siendo una prueba sintética.
- **Pendiente:** prueba manual de instalación e interfaz en Windows/Chromium; flujo real copiar/pegar con ChatGPT web y Gemini web; campaña de 50–100 intercambios con cierre/reinicio/restauración; y comprobación de compatibilidad con otros formatos históricos que aún no estén cubiertos.
- **Alcance de rama:** todos estos cambios pertenecen a `docs/historias-organizadas`; `main` no se modificó.


## Segundo error fantasma: versión mostrada distinta de la versión importada (PR #11)

La interfaz mostraba `Isekai sin Destino v1.16`; el README de la app decía v1.18, mientras que el JSON usado por el endpoint de importación y el README del proyecto declaran v1.19. La carga era real y correcta: el defecto era que la etiqueta visible describía otra versión, lo que podía confundir al usuario durante pruebas o al reportar errores.

Se corrigió el botón a v1.19, se actualizó la documentación y se añadió una aserción que extrae el número de versión de la descripción del JSON y lo compara con el HTML. Así, una futura actualización del JSON sin la etiqueta correspondiente hará fallar la CI.

- PR #11: https://github.com/eltiootaku2020-cmyk/wordbot/pull/11
- CI: 86 pruebas Python y sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934304
- Auditoría del Lorebook v1.19: 659 comprobaciones aprobadas: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934333


## Tercer error fantasma: undo que borra una aprobación posterior (PR #12)

### Secuencia reproducible
1. Turno A crea una propuesta pendiente de amistad para Maelis, con evento fuente registrado.
2. Turno B avanza el reloj hasta las 08:12 y termina correctamente.
3. Se aprueba la propuesta pendiente de A después de B, creando una relación de valor 55 y marcando la fila como `accepted`.
4. Antes del arreglo, el endpoint de undo de B respondía 200, restauraba el snapshot anterior a B (08:05) y eliminaba la relación recién aprobada, pero la propuesta A seguía en estado `accepted`.

El defecto no era solo narrativo: contradecía el registro de auditoría y podía borrar hechos aprobados. La regresión se ejecutó primero contra el código anterior y falló exactamente porque devolvía 200 en lugar de 409.

### Corrección integrada
- PR #12: https://github.com/eltiootaku2020-cmyk/wordbot/pull/12
- Se guarda una huella SHA-256 del estado mutable posterior a cada turno completado dentro del snapshot existente.
- Undo compara el estado actual con esa huella y no modifica nada cuando el estado cambió tras el turno.
- Los snapshots antiguos sin huella se pueden deshacer si no existe una aprobación aceptada posterior de otro turno; la huella se añade durante el undo protegido. Si el registro indica una aprobación posterior, se rechaza el undo por seguridad.
- Se conservan los reintentos seguros, quitando la metadata de huella al comparar el snapshot preturno, y se actualiza la huella al terminar la regeneración.
- CI: 87 pruebas Python aprobadas y sintaxis JavaScript correcta: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40943636768.

## Siguientes posibles errores fantasma (candidatos, no defectos confirmados)

7. Restauración de backup mientras hay una propuesta pendiente; comprobar que el registro accepted/pending se mantiene sincronizado con inventario, recursos, relaciones y presencia.
8. Undo de un turno que contiene varios cambios relacionados con el mismo evento y luego rechazo/aprobación parcial de propuestas de otro turno.
9. Respuestas manuales web generadas con contexto antiguo después de aprobar/rechazar una propuesta; la huella del prompt debería rechazar aplicar la respuesta si cualquier dato usado en ese contexto cambió.


## Actualización de auditoría — PR #13 y PR #14 (29 de octubre de 2026)

### PR #13: revisión concurrente con la generación

Se reprodujo que una generación ya había guardado `generation_status='processing'` y estaba esperando al narrador, mientras una operación independiente podía aceptar/rechazar un cambio de estado o un evento. La IA trabajaba con una vista anterior, y una posterior operación de deshacer podía interpretar mal la secuencia. PR #13 bloquea las cuatro rutas de revisión con HTTP 409 mientras hay un turno en curso. La CI posterior al merge pasó 88 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40944609761.

### PR #14: cancelación de la tarea del proveedor

**Defecto reproducido en código:** `submit_turn` marca la solicitud como `processing`, confirma la transacción y espera a `provider.generate()`. Las ramas existentes capturaban `ProviderError` y `Exception`; una `asyncio.CancelledError` puede eludir el manejador `Exception` porque deriva de `BaseException`. Si la tarea se cancela sin cerrar el proceso completo, el marcador persistido podía bloquear la sesión hasta el siguiente reinicio.

**Cambio propuesto en PR #14:** la cancelación se captura explícitamente, el mensaje original se marca `failed` en una transacción SQLite separada, se registra un aviso y se vuelve a lanzar la cancelación. No se crea una narración ficticia ni se aplican cambios de estado durante la recuperación. La regresión comprueba estado sin cambios y reintento idempotente con el mismo `request_id`.

- PR #14: https://github.com/eltiootaku2020-cmyk/wordbot/pull/14.
- CI del HEAD del PR: **89 pruebas Python aprobadas**, sintaxis JavaScript correcta y una advertencia no bloqueante de Starlette/httpx: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40946590907.
- Fuente técnica: [documentación oficial de cancelación de tareas asyncio](https://docs.python.org/3/library/asyncio-task.html#task-cancellation), que aconseja limpiar recursos y propagar la cancelación.

### Lecciones contrastadas con proyectos comparables

- [Chronicler](https://github.com/yantrikos/chronicler): filtrar ACL/visibilidad al recuperar memoria antes de aplicar relevancia; distinguir recuerdos de distinta confianza. Esto refuerza la separación de Word Bot entre canon confirmado, propuestas y hechos visibles para cada personaje.
- [AI Adventure](https://github.com/CaoRuiming/ai-adventure): estado estructurado y registro histórico/replay separados de la narración. La respuesta del modelo debe tratarse como eventos propuestos, pasar por un validador local y solo entonces modificar el estado autorizado.
- [SillyTavern World Info](https://docs.sillytavern.app/usage/core-concepts/worldinfo/): una entrada Lorebook activada se inserta en el contexto, pero eso no obliga al modelo a obedecerla. La solución es validar acciones/estado fuera del prompt e inspeccionar qué se incluyó.
- [Open Dungeon](https://github.com/newideas99/open-dungeon): controles explícitos para reintentar/editar/borrar y persistencia local, útiles como referencia de recuperación comprensible.
- [API de backup SQLite](https://www.sqlite.org/backup.html): la copia online consistente es apropiada para preservar una base activa; Word Bot ya usa `sqlite3.Connection.backup` a un archivo temporal y reemplazo atómico.

### Riesgos pendientes, aún no demostrados como defectos

1. Cancelaciones repetidas durante el apagado real de Windows/ASGI y proveedor de red: verificar que la limpieza puede escribir SQLite mientras se cancela el proceso; si el proceso muere antes de finalizar esa transacción, la recuperación al arrancar sigue siendo la red de seguridad.
2. Doble instancia de la aplicación apuntando a la misma base: comprobar que una instancia no marque como fallidas las generaciones vivas de la otra durante el arranque. El recuperador actual cambia todos los marcadores `processing` de la base al iniciar; con dos procesos simultáneos podría requerirse un identificador/lease de propietario y caducidad. Es candidato de prueba, no un fallo confirmado en uso normal de instancia única.
3. Respuesta HTTP perdida después de confirmar el turno: repetir el mismo `request_id` debe devolver la respuesta ya guardada sin repetir costes o cambios.
4. Ejecución completa de 50–100 turnos en Windows/Chromium con ChatGPT y Gemini web, incluyendo cambios de ubicación, compras, eventos privados/grupales, interrupciones, reinicio y restauración.

**Estado honesto:** 89 pruebas automáticas y sintaxis JavaScript aprobadas en el HEAD de PR #14. La prueba de cancelación usa proveedor simulado. La campaña de navegador con chats externos reales, la restauración visual y los casos de varias instancias siguen pendientes. PR #14 está integrado en `docs/historias-organizadas`; `main` no se modificó.
