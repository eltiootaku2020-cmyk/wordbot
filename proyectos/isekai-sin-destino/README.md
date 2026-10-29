# Isekai sin Destino

**Versión propuesta:** v1.15 (registro interno con porcentajes, objetos, ubicaciones y órdenes; pendiente de probar en SpicyChat)  
**Rama:** `docs/historias-organizadas`  
**Carpeta:** `proyectos/isekai-sin-destino/`

## Archivos
- [Configuración ligera](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias v1.15](CUADRO_REGLAS_PRIORITARIAS.md)
- [Registro interno y esquema cerrado v1.15](REGISTRO_INTERNO_ESQUEMA.md)
- [Lorebook maestra, 76 entradas](LOREBOOK_MAESTRA.md)
- [JSON de importación de Lorebook](LOREBOOK_IMPORT.json)
- [Solución para historias largas](SOLUCION_HISTORIAS_LARGAS.md)
- [Investigación aplicada: diálogo, continuidad y Eco vegetal](INVESTIGACION_DIALOGO_MEMORIA_Y_ECO_VEGETAL.md)

## Registro v1.15
- Porcentajes independientes 0–100 por eje: relaciones por pareja/dirección; habilidad solo tras demostración; interés tras declaración/patrón; sospecha con motivo y evidencia.
- Los porcentajes miden intensidad, no probabilidad; 50% no es neutral universal; Δ0 indica que ese hecho no cambia el valor. Delta +/−=subida/bajada; 0=sin cambio. Sin evidencia = «No registrado». La sospecha no prueba culpabilidad.
- Ficha por PNJ/criatura relevante: identidad, estado, ubicación actual o última confirmada, habilidades, intereses, sospechas, conocimiento/fuente, vínculos, órdenes dadas y cumplimiento confirmado/desconocido.
- Objetos: nombre, cantidad, condición, estado, portador/ubicación al obtener, dejar, guardar, entregar, usar, intercambiar o perder.
- Lugares y Lorebook separan datos fijos, observación directa y rumor. No inventar accesos, rasgos o secretos no confirmados.
- Historial de eventos reducido a 3–5 sucesos importantes; no transcribir cada mensaje ni registrar comidas. Si cambian las provisiones, actualizar el inventario.
- Datos ausentes = «No registrado»; no crear campos nuevos. El registro interno solo es útil mientras el contexto lo conserve.
- Guardado copiable cada 8–10 intercambios y tras cambios importantes. SpicyChat no crea una base de datos externa con instrucciones de texto.

## Reglas narrativas
- Seis bloques horarios de cuatro horas; mini mapa progresivo.
- Encuentros abiertos: no todo conduce a combate; los compañeros solo reaccionan a hechos presenciados o contados.
- Relaciones no solo románticas: confianza, sospecha, amistad, respeto, rivalidad, resentimiento, miedo, gratitud/deuda y cooperación.
- Iniciativa de PNJ: en escenas de grupo, personajes cercanos hablan o reaccionan espontáneamente sin que el jugador los nombre o mire; Ivar puede suspirar o comentar desde la primera línea. Se evitan frases sueltas y respuestas vacías.
- El volcán es un punto culminante del primer arco; cualquier causa sobrenatural —incluido un dragón antiguo— permanece pendiente hasta confirmación del autor.

## Coste de contexto y memoria
- La documentación oficial indica 4.096 tokens de contexto y máximo de 180 tokens por respuesta en el plan Free. El contexto se comparte entre definición, historial reciente, instrucciones y Lorebook activada.
- Las entradas de Lorebook se activan por palabras clave; no se carga toda la biblioteca en cada turno. En Free, la guía oficial estima alrededor de 740 tokens para Lorebook activa, así que conviene evitar que muchos registros se activen a la vez.

- El estado dinámico no se vuelve una base de datos oculta: puede mantenerse mientras siga en contexto, pero para recuperarlo tras un olvido hay que conservar `/guardar` fuera del chat.

Fuentes oficiales:
- https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-
- https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks
- https://support.spicychat.ai/support/solutions/articles/153000260533-plans-and-what-s-included

- Campos estáticos (caracteres): Personality 4516; Scenario 795; Greeting 687; Example Dialogue 1044. Caracteres no equivalen a tokens; verifica el coste real con el contador del editor SpicyChat.

## Validación
- JSON válido sintácticamente; 76 entradas. Las entradas de estado nuevo están compactadas.
- Personality por debajo de 5.000 caracteres.
- Pendiente: probar importación y comportamiento en SpicyChat. GitHub no instala los cambios automáticamente.


## Eco vegetal y objetos comunes v1.15
- El descubrimiento de recuerdos de árboles se registra como experiencia sensorial, no visual; alcance, coste y mecanismo siguen sin confirmar.
- Se añaden límites provisionales de prueba y un catálogo de objetos cotidianos posibles, y tres objetos comunes iniciales confirmados (pañuelo, bolsita vacía, cordel).
- Se amplía la investigación con documentación oficial de SpicyChat y referencias de diseño de PNJ/diálogo.
- JSON: 76 entradas; importación y comportamiento real siguen pendientes de probar en SpicyChat.
