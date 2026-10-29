# Isekai sin Destino — Mundo vivo

**Módulo:** diseño modular del mundo, simulación, exploración, ecología, magia y Psico-Eco.  
**Estado:** primera base documental creada; todavía no es código integrado en el motor de Word Bot.  
**Rama:** `world/isekai-mundo-vivo-foundation`.

## Propósito

Construir un mundo fantástico abierto en el que criaturas, PNJ, objetos, recursos, fenómenos mágicos y acontecimientos tengan estados propios. La IA narra y propone posibilidades; las reglas y el estado persistente determinan qué puede ocurrir. El protagonista no tiene protección narrativa.

Este módulo evita convertir la aventura en una secuencia de escenas prefijadas. Un encuentro puede producir amistad, comercio, huida, combate, descubrimiento, lesión o muerte, según causas y circunstancias.

## Mapa de documentos

1. [Reglas del mundo vivo](01_REGLAS_MUNDO_VIVO.md) — principios de simulación, causalidad, aleatoriedad y justicia.
2. [Modelo de variables y estado](02_MODELO_VARIABLES.json) — estructura inicial de variables y entidades.
3. [Ecología del Bosque de las Bestias](03_CATALOGO_50_ESPECIES.json) — catálogo de 50 especies propuestas, aún no canon aprobado.
4. [Sistema Psico-Eco](04_PSICO_ECO.md) — lectura, influencia, memoria, percepción, biología, autointervención y resistencias.
5. [Exploración, objetos y magia](05_EXPLORACION_OBJETOS_MAGIA.md) — búsqueda, observación, amenazas ocultas, hallazgos y recursos.
6. [Rutas y cinco finales](06_RUTAS_Y_FINALES.md) — estructura abierta, rutas cruzadas y erupción del Día 12.
7. [Acciones y comandos](07_ACCIONES_Y_COMANDOS.md) — lenguaje de acciones y decisiones encadenadas.
8. [Pendientes y conflictos de canon](08_PENDIENTES_Y_CONFLICTOS.md) — decisiones que no deben inventarse ni aprobarse automáticamente.

## Regla de autoridad y canon

- Las decisiones explícitas del usuario en la conversación actual prevalecen sobre documentos antiguos cuando existe contradicción.
- Los elementos etiquetados como **propuesta** no son canon aprobado.
- Los documentos anteriores de Isekai sin Destino se conservan; este módulo los complementa y señala contradicciones para reconciliarlas, no los borra.
- Ningún dato desconocido se completa por intuición. Usar `No registrado`, `propuesto` o `pendiente de aprobación`.
- No se debe afirmar que una regla está implementada en Word Bot hasta que exista código, integración y pruebas.

## Principio de simulación

El motor mantiene datos estructurados y persistentes. La IA interpreta la situación, genera diálogo y describe consecuencias dentro de los límites de esos datos. No debe inventar un éxito, una propiedad de objeto, una memoria, una muerte o una relación sin una causa plausible.

## Alcance de esta primera entrega

- Estructura documental modular.
- Modelo inicial de variables.
- Catálogo de 50 especies propuestas para el primer bioma.
- Especificación funcional de Psico-Eco.
- Exploración, magia, rutas, finales y comandos.
- Lista de conflictos históricos que requieren reconciliación.

## No incluido todavía

- No hay simulador ejecutable de ecosistemas.
- No hay tiradas ni motor probabilístico implementado.
- No hay conexión de estas fichas a SQLite ni a la generación de turnos.
- No se ha validado una partida real con este sistema.
- No se ha modificado la rama `main`.
