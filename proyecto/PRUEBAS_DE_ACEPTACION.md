# Pruebas de aceptación del gestor local

La aplicación no se considerará fiable por una demostración breve. La CI actual pasa 12 pruebas automatizadas con datos simulados: persistencia/backups, esquema estricto, comportamiento del narrador, turno de extremo a extremo, reintentos idempotentes, revisión de eventos y creación atómica de mundos con reparto/inventario inicial. Eso no valida las llamadas reales a OpenAI/Gemini, el uso manual en Windows ni los casos de aceptación pendientes. Las pruebas de estado deben poder repetirse sin llamadas pagas.

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
