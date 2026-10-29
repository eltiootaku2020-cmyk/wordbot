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
