# Isekai sin Destino

**Versión propuesta:** v1.8 (pendiente de prueba en SpicyChat)  
**Rama organizada:** \`docs/historias-organizadas\`  
**Carpeta:** \`proyectos/isekai-sin-destino/\`

## Archivos

- [Configuración ligera para SpicyChat](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias v1.8: mapa, reloj, PNJ y registros](CUADRO_REGLAS_PRIORITARIAS.md)
- [Lorebook maestra, 72 entradas](LOREBOOK_MAESTRA.md)
- [JSON de importación de Lorebook](LOREBOOK_IMPORT.json)

## Cambios conservados de v1.7

## Propuesta v1.8

- Bloque de Personality compacto con reloj por seis bloques de cuatro horas.
- Mini mapa progresivo con estados de rutas; los lugares no visitados no se marcan como explorados y Nhal-Seren sigue oculta.
- Seguimiento de promesas, encuentros por lugar/ruta, objetos y objetivos afectados por Eco/hipnosis.
- Ivar con cabello largo rubio casi blanco, rudeza e ironía; el objetivo de su odio permanece pendiente.

- Cabecera dinámica: el saludo del Día 1 a las 08:00 no debe repetirse como estado fijo.
- Seis franjas por día: Mañana I, Mañana II, Tarde I, Tarde II, Noche I y Noche II.
- Los encuentros se improvisan de forma controlada según lugar, horario, riesgo, ruidos y rastros.
- Las criaturas y PNJ relevantes conservan identidad, estado y recuerdos; los muertos no reaparecen como el mismo individuo sin causa.
- Los efectos y usos de Eco permanecen ligados al objetivo.
- El punto de guardado sigue siendo una copia manual: SpicyChat no obtiene persistencia externa automáticamente.

## Solución para historias largas

- [Diagnóstico y opciones de continuidad](SOLUCION_HISTORIAS_LARGAS.md) — compara SpicyChat con guardados manuales, SillyTavern para una partida personal y una aplicación propia con base de datos.

## Estado de validación

Los archivos se han comprobado en GitHub; el JSON se valida sintácticamente. La propuesta v1.8 aún requiere prueba dentro de la cuenta de SpicyChat.
