# Pruebas de aceptación del gestor local

La CI más reciente validó **87 pruebas Python** y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40943636768.

## A. Persistencia y recuperación

1. Crear un mundo y una partida nueva.
2. Registrar 50–100 intercambios y cerrar la aplicación.
3. Abrirla y comprobar que conserva mensajes, hora, lugar, inventario, relaciones, personajes presentes y eventos.
4. Crear un punto de guardado y restaurarlo en una copia de la partida.
5. Verificar que restaurar no duplica eventos ni costes de recursos.

**Criterio:** ningún dato confirmado se pierde al reiniciar la aplicación; el estado restaurado coincide con la secuencia seleccionada.

## B. Contexto selectivo

1. Hablar con Maelis: debe recuperar su ficha y la relación actual.
2. Comprar una herramienta: debe recuperar precios/inventario y las reglas de comercio relevantes.
3. Usar Eco: debe recuperar reglas del poder y contador del objetivo.
4. Viajar: debe recuperar el mapa, rutas conocidas, duración y escena actual.
5. Hablar de una región no visitada: no debe cargar ni revelar secretos como conocimientos del protagonista.

**Criterio:** se envían al modelo solo entradas útiles para la escena, sin copiar toda la Lorebook por defecto.

## C. Mensaje social: «Hola, linda»

1. El usuario dirige el mensaje a Maelis.
2. La IA genera un diálogo coherente con su personalidad y con lo que ha visto.
3. Se registran la intervención y las reacciones de los PNJ presentes.
4. La confianza solo cambia si la reacción y las reglas justifican el cambio; una impresión temporal se guarda separada.
5. El programa muestra el resultado normal en el chat y un indicador de guardado discreto.

**Criterio:** no se fuerza el mismo resultado cada vez; no se inventa atracción, odio ni una etiqueta permanente por una sola frase.

## D. Agencia del protagonista

1. La IA no debe hacer que el protagonista acepte una misión, camine, compre, hable o piense algo que no haya indicado el usuario.
2. Un salto de tiempo solo aplica el intervalo y el destino autorizados.
3. Si falta información, el sistema pregunta o marca la propuesta pendiente.

**Criterio:** ninguna decisión atribuida al protagonista sin entrada explícita del usuario.

## E. Inventario

1. El protagonista comienza con los objetos iniciales confirmados por el mundo; sin equipo adicional.
2. Comprar un objeto reduce el dinero y añade exactamente la cantidad comprada.
3. Dejar, entregar, usar o perder un objeto actualiza cantidad, portador y ubicación.
4. Un objeto meramente mencionado en la Lorebook no aparece automáticamente en el inventario.

**Criterio:** ninguna cantidad cambia sin un evento causante y válido.

## F. Eco y poderes limitados

1. Usar Eco sobre una persona registra el intento aunque falle.
2. Un reintento técnico del mismo turno no descuenta el uso por segunda vez.
3. El programa rechaza usos humanos adicionales cuando se alcanza el límite configurado.
4. Eco vegetal no hereda un contador humano sin una regla aprobada.
5. La IA no puede restaurar usos ni crear poderes nuevos.

**Criterio:** el contador se calcula y se valida localmente, no se acepta desde el texto libre del modelo.

## G. Continuidad temporal y geográfica

1. Conversar brevemente no avanza automáticamente horas.
2. Una acción larga cambia el reloj según duración validada.
3. Cambiar de región requiere una ruta y un tiempo plausible.
4. El bot no reinicia la partida al día inicial tras una respuesta larga.
5. Los acontecimientos ancla pueden ocurrir fuera de cámara sin obligar al protagonista a participar.

**Criterio:** el estado temporal persiste y no contradice acciones anteriores.

## H. Contrato y errores del modelo

1. Entregar una respuesta JSON inválida.
2. Entregar un ID de personaje inexistente.
3. Proponer un cambio fuera de rango.
4. Proponer que un objeto apareció sin causa.
5. Proponer que una relación cambie sin motivo.
6. Simular un timeout del proveedor.
7. Repetir el mismo turno para comprobar idempotencia.

**Criterio:** las operaciones inválidas no alteran parcialmente el estado; los errores quedan registrados para diagnóstico.

## I. Separación de mundos

1. Crear dos mundos con personajes de nombres similares.
2. Cambiar de uno a otro.
3. Consultar la misma palabra clave en ambos.
4. Reiniciar la aplicación.

**Criterio:** no se filtran reglas, relaciones, objetos ni personajes entre mundos.

## Definición de «listo para usar»

Se considera apto para una primera partida cuando A, C, D, E, F, G, H e I pasan sin pérdida de datos; B demuestra que el contexto es selectivo; existe copia de seguridad/restauración; y los cambios pendientes se pueden revisar sin alterar el estado oficial.


## J. Salida estructurada y adaptadores de proveedor

1. Recibir JSON válido conforme al contrato y comprobar que se puede validar.
2. Recibir JSON sintácticamente correcto pero con un ID de entidad inexistente.
3. Proponer una clave no admitida o un campo desconocido.
4. Proponer confianza −1 sin evento de fuente.
5. Proponer un uso de Eco cuando el contador local ya se agotó.
6. Simular una respuesta que no cumple el esquema y un timeout del proveedor.

**Criterio:** los errores estructurales o semánticos no modifican el estado; se registra la respuesta para diagnóstico y se mantiene visible el error.

## K. Idempotencia

1. Procesar un turno que baja un valor de relación en 1 y consume un recurso.
2. Simular un timeout de respuesta de la aplicación y reintentar el mismo turno.
3. Comprobar la clave de idempotencia y el historial de operaciones.

**Criterio:** ningún cambio ni coste se aplica dos veces por el mismo turno.

## L. Copia y restauración SQLite

1. Crear varios mensajes y cambios de estado con la base en uso.
2. Crear una copia con el mecanismo de backup admitido.
3. Abrir la copia en una base temporal y comprobar integridad, secuencia de eventos y relaciones entre filas.
4. Restaurar en una partida de prueba.

**Criterio:** la copia es consistente, no pierde cambios confirmados y no mezcla datos de mundos.

## M. Seguridad y proveedor

1. Iniciar la aplicación y comprobar que el servidor solo escucha en loopback por defecto.
2. Verificar que no hay claves en el repositorio, logs, prompts ni exportaciones.
3. Desactivar conexión al proveedor y comprobar que la base local sigue siendo legible.
4. Cambiar proveedor sin cambiar el modelo canónico de datos.
5. Registrar el uso devuelto por el proveedor cuando esté disponible.

**Criterio:** la base permanece local, los secretos no se publican y una caída del proveedor no altera una partida guardada.

## N. Presupuesto de contexto

1. Hablar con Maelis, luego consultar el precio de un objeto y después usar Eco.
2. Comprobar que cada turno recupera fichas distintas según el contexto.
3. Superar el presupuesto de contexto configurado con una gran Lorebook.
4. Verificar la prioridad: canon/estado/fichas presentes antes que lore secundaria.

**Criterio:** no se envía toda la biblioteca por defecto y el sistema registra qué fichas se incluyeron en cada solicitud.


## O. Crear una partida desde cero

1. Crear un mundo con canon breve, protagonista, dos personajes y varios objetos iniciales.
2. Consultar el estado y comprobar que las entidades, ubicación/hora y objetos quedaron registrados.
3. Intentar crear un mundo con dos entidades de nombre duplicado.

**Criterio:** la creación válida guarda mundo y sesión completos; un error de unicidad hace rollback y no deja un mundo incompleto. Está cubierto por pruebas de integración simuladas, pero falta el ensayo manual en Windows.


## P. Cargar el preset de Isekai sin Destino

1. Pulsar «Cargar Isekai sin Destino v1.16».
2. Verificar 77 entradas de Lorebook, protagonista y cinco aventureros, cinco objetos iniciales, lugar inicial y Día 1 a las 08:00.
3. Pulsar de nuevo y comprobar que se crea una segunda sesión en el mismo mundo sin mezclar mensajes/inventario de partidas anteriores.

**Criterio:** canon y Lorebook compartidos, estado de cada partida aislado. La prueba de CI usa el Lorebook versionado en el repositorio y el narrador simulado; aún falta una prueba manual en Windows y una llamada real al proveedor.


## Q. Recursos, monedas y compras transaccionales (implementado, CI simulada)

1. Una partida Isekai nueva registra explícitamente 0 monedas.
2. Crear una partida personalizada con una cantidad inicial de monedas y consultar el panel de estado.
3. Comprar un objeto con precio positivo y saldo suficiente: registrar pago y añadir la cantidad exacta del objeto.
4. Comprar sin saldo suficiente: dejar la propuesta pendiente y comprobar que ni saldo ni inventario cambian.
5. Cobrar una recompensa explícita con evento fuente de tipo `resource` y comprobar que el saldo aumenta exactamente una vez.
6. Proponer además un segundo gasto de recurso asociado al mismo evento de compra y verificar que no duplique el cargo.

**Cobertura actual:** CI valida los casos de compra suficiente, insuficiente y recompensa explícita con narrador simulado. La idempotencia se verifica al repetir el mismo request_id en la API usando proveedor simulado. Pendiente simular pérdida real de respuesta y probar proveedor remoto.


## R. Undo y regeneración segura de turnos

1. Enviar un turno que compre un objeto y avance el reloj.
2. Pulsar «Deshacer último turno». Reloj, monedas, inventario y presencia deben volver al snapshot anterior; las relaciones y usos de poderes también deben restaurarse.
3. Comprobar que los mensajes anulados quedan etiquetados y que eventos/cambios de la versión anulada quedan fuera del contexto activo.
4. Reenviar el mismo `request_id` y comprobar que la operación se regenera sin duplicar eventos ni cobrar dos veces.
5. Intentar deshacer un turno anterior mientras hay turnos posteriores activos: el programa debe responder 409 y no modificar el estado.
6. Reiniciar y comprobar que los snapshots persisten; completar después una campaña de 50–100 turnos.

**Cobertura actual:** CI valida inventario, recursos, reloj, una relación y el uso de Eco; auditoría de eventos/cambios; regeneración; y rechazo de undo fuera de orden. Falta probar manualmente la UI en Windows y realizar campaña larga.


## S. Presupuesto local configurable de Lorebook

1. Consultar `GET /api/settings`: por defecto muestra 4.500 caracteres y máximo ocho entradas.
2. Guardar 500 caracteres y comprobar que persiste al volver a consultar el endpoint.
3. Previsualizar una escena que activa dos entradas cuya suma excede el presupuesto; solo entra la primera que cabe y la segunda aparece en `omitted_lore_by_limit`.
4. Intentar guardar 499 caracteres: la API responde 422 y no altera la preferencia anterior.
5. Confirmar que el mismo presupuesto afecta el contexto de los turnos narrativos.

**Cobertura actual:** CI valida persistencia, rango mínimo, selección de entradas y motivo de omisión. Pendiente ensayo manual de la interfaz en Windows y conteo exacto de tokens por proveedor.



## T. Uso manual de ChatGPT/Gemini web, recuperación y continuidad

1. Seleccionar ChatGPT web o Gemini web en modo manual y preparar un prompt sin configurar ninguna clave API.
2. Copiar el prompt a la conversación web normal, traer la respuesta y pegar su JSON en Wordbot.
3. Pegar primero una respuesta no válida; comprobar que no se guarda una narración ni se modifica el estado. Pegar luego un JSON corregido con el mismo `request_id` y la misma huella de contexto; el turno debe recuperarse sin duplicar el mensaje ni aplicar efectos dos veces.
4. Completar al menos tres intercambios manuales consecutivos, preparando cada contexto desde el estado vigente, y verificar que todos quedan guardados en la misma partida.
5. Preparar un prompt, avanzar la partida por otra vía y después pegar la respuesta antigua; debe responder 409 sin guardar el turno. Preparar un prompt nuevo y repetirlo correctamente.
6. Reiniciar Wordbot y comprobar que el estado y los turnos aceptados se conservan.

**Criterio de aceptación:** Wordbot no impone una cuota local de mensajes ni corta los intercambios manuales por haber alcanzado un número fijo. Los límites propios de ChatGPT/Gemini quedan fuera del programa. Una respuesta incorrecta puede corregirse; solo se conserva una vez el turno que supera las validaciones y una respuesta basada en un contexto antiguo se rechaza.

**Cobertura automatizada actual:** las pruebas de recuperación y de tres turnos consecutivos pasan en CI. Pendiente ejecutar estas acciones con las interfaces reales de ChatGPT y Gemini en Windows/Chromium y realizar la campaña completa de 50–100 intercambios con reinicio y restauración.

## U. Evidencia afirmativa del usuario antes de alterar el estado

1. Preguntar si se puede comprar un objeto, recoger un hallazgo, pagar/gastar recursos o usar un poder, sin ordenar la acción.
2. Repetir con una negativa explícita, por ejemplo «No compro», «No recojo», «No pago» o «No uso Eco».
3. Hacer que la respuesta simulada del narrador proponga igualmente la compra, el hallazgo, el ingreso, el gasto, el uso del poder y un efecto de relación asociado.
4. Verificar que el saldo y el inventario permanecen iguales, el contador de usos no aumenta, las relaciones no cambian y los eventos propuestos quedan pendientes.
5. Enviar una orden afirmativa posterior que nombre la acción y el objeto/recurso correcto; comprobar que solo se aplica la operación correspondiente, sujeta a las validaciones de coste y saldo.

**Criterio:** una pregunta, intención hipotética o acción negada no autoriza por sí sola una operación. Las descripciones del narrador y los motivos de sus propuestas pueden servir como información para revisar el turno, pero nunca sustituyen la evidencia afirmativa en el mensaje del usuario.

**Cobertura automatizada actual:** CI posterior al PR #7 aprobó 82 pruebas Python y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743); se mantiene la cobertura de acción afirmativa y se añade control de audiencia para mensajes/eventos heredados.

## V. Continuidad extendida, respuestas incompletas y restauración con rollback

1. Enviar una respuesta de ChatGPT/Gemini web con JSON truncado. El turno debe fallar sin modificar el estado del juego ni insertar narración o cambios. Luego pegar JSON completo con el mismo `request_id`: se completa un único turno y no se duplican mensajes.
2. Para una orden hipotética o interrogativa como «Si compro una manzana por dos monedas, ¿me alcanza?», hacer que el narrador afirme que la compra ocurrió. El inventario y el saldo permanecen intactos; el evento y la operación quedan pendientes.
3. Proponer dos cambios distintos y contradictorios sobre el mismo eje de relación del mismo personaje en una respuesta. Ninguno de los cambios debe aplicarse y el valor confirmado debe conservarse.
4. Ejecutar 100 turnos breves con el proveedor simulado, reinicializar SQLite y comprobar que el estado y todos los mensajes siguen idénticos. Crear copia, aplicar un turno posterior y restaurar; comparar el estado, mensajes y todas las tablas listadas en `RESTORE_SESSION_TABLES` con la instantánea anterior.
5. Construir una copia SQLite que pase la validación de lectura pero contenga una fila que incumpla una restricción del esquema activo. La restauración debe revertir la transacción completa, devolver un error 422 controlado y dejar el estado y las tablas activas exactamente iguales a la instantánea anterior.

**Cobertura automatizada actual:** CI posterior al PR #7 aprobó 82 pruebas Python y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743). Incluye los cinco escenarios de continuidad del PR #5, migración de presencia del PR #6 y controles de audiencia histórica del PR #7. Los 100 turnos automatizados usan proveedor simulado.

**Pendiente:** probar manualmente la instalación e intercambio copiar/pegar en Windows/Chromium con las páginas reales de ChatGPT y Gemini y ejecutar una campaña narrativa prolongada. Las API reales son opcionales y no se requieren para los casos cubiertos por CI.


## W. Compatibilidad de presencia histórica y restauración de backups antiguos

1. Crear una base histórica cuya tabla `session_presence` tenga solo `session_id`, `entity_id` y `location`, sin `presence_status` ni `updated_at`.
2. Inicializar la aplicación y verificar que migra las columnas sin perder las filas ni las ubicaciones originales.
3. Comprobar que cada estado se deriva de la ubicación registrada respecto de la ubicación actual de la partida: el protagonista en la escena figura como `present` y un PNJ en otra ubicación como `away`.
4. Alterar intencionalmente un estado almacenado para que contradiga la ubicación, volver a inicializar y comprobar que se normaliza sin cambiar la ubicación.
5. Crear una copia de seguridad, sustituir su tabla de presencia por el formato histórico sin `presence_status`, modificar la partida activa y restaurar. El endpoint debe aceptar la copia y reconstruir el estado de presencia derivado.

**Cobertura automatizada actual:** los cinco puntos tienen cobertura con pruebas de migración SQLite y restauración API. CI posterior a PR #7 aprobó 82 pruebas Python y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743). La prueba cubre formatos específicos y no certifica todas las variantes históricas posibles.

**Pendiente:** instalar y probar visualmente en Windows/Chromium, completar el intercambio manual con ChatGPT/Gemini web y ejecutar una campaña narrativa real de 50–100 turnos.


## X. Audiencia de mensajes y eventos históricos sin metadatos

1. Insertar mensajes heredados sin `visibility` ni `audience_ids`, pero conservando `recipient_entity_id` para una conversación dirigida a Maelis.
2. Preparar contexto para Maelis y comprobar que el diálogo heredado es recuperable; preparar contexto para Ivar y comprobar que no recibe el contenido privado de Maelis.
3. Insertar un evento con mensaje fuente dirigido a Maelis y sin nuevos metadatos: el destinatario conservado debe seguir limitándolo a Maelis.
4. Insertar un evento antiguo sin mensaje fuente resoluble ni testigos. Debe omitirse del contexto de cualquier personaje y el diagnóstico debe indicar que se excluyó por carecer de fuente y testigos.
5. Confirmar que el evento excluido no se borra de la base y sigue disponible para inspección/auditoría.
6. Confirmar que un evento antiguo con testigos identificables sí puede recuperarse, incluso cuando se selecciona por relevancia más allá de la ventana reciente.

**Cobertura automatizada actual:** CI posterior al PR #7 aprobó 82 pruebas Python y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40937190743). Se prueba la exclusión de eventos sin procedencia, el acceso por destinatario de mensajes heredados y la recuperación por relevancia cuando hay testigos explícitos. La regla evita inventar una audiencia ausente; no pretende certificar todos los formatos históricos posibles.

**Pendiente:** revisar otras variantes de migración, prueba manual de Windows/Chromium con ChatGPT/Gemini web, restauración visual con vista previa y campaña narrativa real de 50–100 turnos.


## Y. Privacidad al deshacer y regenerar un turno privado

1. Crear un turno privado dirigido a Maelis, con una cadena confidencial identificable en la narración y en un evento que registre a los testigos correctos.
2. Preparar el contexto compartido de Ivar. No debe contener la cadena ni en mensajes ni en eventos.
3. Deshacer el último turno completado. El evento original debe trasladarse al turno de auditoría y quedar rechazado; la narración y el evento no deben aparecer en el contexto activo de Ivar.
4. Regenerar la misma solicitud usando el mismo `request_id`. Debe reutilizar el turno, no duplicar efectos y conservar la visibilidad privada original.
5. Volver a preparar el contexto compartido de Ivar y comprobar que sigue sin recibir la cadena confidencial.
6. Preparar el contexto privado de Maelis y comprobar que la narración y el evento privados regenerados siguen disponibles para su destinataria.

**Cobertura automatizada actual:** CI posterior al PR #8 aprobó 83 pruebas Python y sintaxis JavaScript (https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40939319271). Esta prueba usa un proveedor simulado y verifica mensajes, eventos, auditoría, undo y regeneración dentro de un único flujo. No sustituye una prueba real con el navegador.

**Pendiente:** probar manualmente Windows/Chromium con ChatGPT/Gemini web y ejecutar una campaña narrativa real de 50–100 turnos con reinicio y restauración.


## AC. Reintentos seguros y snapshots obsoletos (PR #9/#10)

1. Completar un turno A, deshacerlo y regenerarlo inmediatamente con el mismo `request_id` mientras el estado siga igual. El reintento debe poder continuar y no duplicar eventos/operaciones.
2. Completar A, deshacer A, completar un turno B y volver a enviar A. La aplicación debe responder 409 sin llamar al proveedor ni cambiar la hora, recursos o inventario de B.
3. Hacer que A falle en el proveedor; después completar B y reintentar A. Debe responder 409 y preservar B.
4. Hacer que A falle; modificar el estado mediante una aprobación que no cree turno; reintentar A. Debe responder 409 porque la instantánea ya no coincide.
5. Verificar por API que un snapshot ausente o ilegible también impide un reintento antiguo con mutación.

**Criterio:** el reintento solo se acepta cuando no hay turnos posteriores y el estado mutable actual coincide con el snapshot previo. No debe ejecutarse el proveedor ni mutarse el estado en casos rechazados.

**Cobertura automatizada:** PR #10 ejecutó 86 pruebas Python y sintaxis JavaScript en CI: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40940906581. La ejecución usa proveedor simulado; campaña manual real sigue pendiente.


## AD. Coherencia de versión del preset

1. Leer la versión `vX.Y` declarada en la descripción de `proyectos/isekai-sin-destino/LOREBOOK_IMPORT.json`.
2. Leer la versión mostrada por el botón `isekaiPreset` en `proyecto/app/src/canon_manager/static/index.html`.
3. Comprobar que ambas coinciden. Si el JSON sube de versión y la interfaz no se actualiza, la suite debe fallar.

**Cobertura automatizada:** CI PR #11 aprobó 86 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934304. La auditoría separada del Lorebook v1.19 aprobó 659 comprobaciones: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40941934333.


## AE. Deshacer después de una aprobación fuera del turno (PR #12)

1. Completar un turno A que deje pendiente una propuesta de relación, inventario, recurso o movimiento.
2. Completar un turno B posterior que cambie el reloj y cree su snapshot preturno.
3. Aprobar la propuesta pendiente de A después de B, comprobar que el cambio se aplica y queda `accepted`.
4. Intentar deshacer B. Debe devolver 409, conservar el reloj posterior a B y mantener el cambio aceptado; no se permite que el snapshot de B borre un cambio posterior.
5. Repetir con una instantánea antigua que no contenga huella posterior. Si el registro muestra una aprobación aceptada posterior de otro turno, el undo también debe fallar de forma conservadora.
6. Probar compatibilidad antigua: retirar la huella de un snapshot de turno sin aprobaciones externas posteriores; el undo puede completar, guardar la huella faltante y permitir regeneración segura.

**Criterio:** el estado solo se restaura si coincide con la huella posterior del turno. Si el estado ya cambió, no se debe modificar nada. Snapshots antiguos sin huella pueden migrarse de forma perezosa solo cuando el registro de cambios no señala una aprobación posterior.

**Cobertura automatizada:** PR #12 aprobó 87 pruebas Python y sintaxis JavaScript: https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40943636768. El escenario usa proveedor simulado; la campaña larga con navegador real sigue pendiente.
