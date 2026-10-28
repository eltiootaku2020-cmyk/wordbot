# Isekai sin Destino

**Versión propuesta:** v1.11 (registro interno con porcentajes, objetos, ubicaciones y órdenes; pendiente de probar en SpicyChat)  
**Rama:** `docs/historias-organizadas`  
**Carpeta:** `proyectos/isekai-sin-destino/`

## Archivos
- [Configuración ligera](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias v1.11](CUADRO_REGLAS_PRIORITARIAS.md)
- [Registro interno y esquema cerrado v1.11](REGISTRO_INTERNO_ESQUEMA.md)
- [Lorebook maestra, 73 entradas](LOREBOOK_MAESTRA.md)
- [JSON de importación de Lorebook](LOREBOOK_IMPORT.json)
- [Solución para historias largas](SOLUCION_HISTORIAS_LARGAS.md)

## Registro v1.11
- Porcentajes independientes 0–100 por eje: relaciones por pareja/dirección; habilidad solo tras demostración; interés tras declaración/patrón; sospecha con motivo y evidencia.
- 50% neutral solo cuando exista base para medir. Sin evidencia = «No registrado». Un porcentaje de sospecha no prueba culpabilidad.
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
- El volcán es un punto culminante del primer arco; cualquier causa sobrenatural —incluido un dragón antiguo— permanece pendiente hasta confirmación del autor.

## Validación
- JSON válido sintácticamente; 73 entradas. Las entradas de registro se han compactado para limitar el contexto activo.
- Personality por debajo de 5.000 caracteres.
- Pendiente: probar la importación y el comportamiento real dentro de SpicyChat. Los cambios en GitHub no se instalan automáticamente.
