# 10 — Presencia humana y lugares habitados

**Estado:** categorías generales aprobadas; localizaciones y fichas concretas aún propuestas.  
**Decisión del usuario:** combinado — aldeas, campamentos, ruinas y escondites.

## 1. Propósito

El Bosque de las Bestias debe sentirse como un territorio recorrido, utilizado y disputado por seres inteligentes, sin perder su carácter salvaje. La presencia civilizada no debe convertirlo en una ciudad extensa ni reducirlo a cuatro puntos fijos de una aventura lineal.

## 2. Categorías aprobadas

### Aldeas aisladas
Comunidades pequeñas y relativamente estables, dentro del bosque o en sus límites. Cada aldea futura deberá explicar cómo obtiene agua, alimento, materiales, seguridad y comunicación. Sus habitantes, tamaño, economía, ubicación y relaciones quedan pendientes.

### Campamentos temporales
Asentamientos de duración limitada o desplazables. Pueden pertenecer a aventureros, cazadores, comerciantes, exploradores, investigadores, viajeros u otros grupos. Su estado depende de motivo, objetivo, suministros, vigilancia, rastros, rutas y acontecimientos. Pueden estar ocupados, vacíos, desplazados o abandonados.

### Ruinas
Restos de actividad anterior. Su origen, edad, función y constructores no se conocen automáticamente. Viviendas antiguas, puestos de vigilancia, santuarios o instalaciones son posibilidades de diseño, no hechos históricos canonizados. Las conclusiones deben surgir de evidencias.

### Escondites
Lugares discretos, naturales, adaptados o construidos. Pueden servir como refugio, guarida, depósito, escondite de fugitivos, puesto de observación o lugar para ocultar objetos o personas. No se presupone que sean hostiles ni que contengan tesoros.

## 3. Estado de cada lugar

Toda localización concreta deberá registrar, cuando se conozca:

- Identificador estable y nombre (el nombre puede ser desconocido para el protagonista).
- Categoría principal y categorías secundarias.
- Ubicación mediante nodo/subzona y conexiones.
- Estado físico: intacto, deteriorado, dañado, derrumbado u otro valor justificado.
- Ocupación: ocupado, temporalmente ocupado, abandonado, disputado, oculto o no determinado.
- Habitantes o responsables, si están identificados.
- Propósito real y propósito conocido por el protagonista; pueden diferir.
- Recursos, suministros y limitaciones.
- Defensas, peligros y accesos.
- Relaciones con rutas, territorios ecológicos y acontecimientos.
- Evidencias, fuentes de conocimiento y última causa de cambio.

Los campos desconocidos deben conservarse como No registrado, no completarse por intuición.

## 4. Coexistencia con el ecosistema

- Una aldea, campamento o ruina altera el entorno mediante ruido, residuos, fuego, caminos y extracción de recursos.
- La fauna puede acercarse por comida, evitar actividad humana, atacar, ocupar estructuras o convertirlas en guaridas.
- Territorios de criaturas y rutas humanas pueden superponerse y generar conflictos.
- La presencia de un asentamiento requiere una explicación de recursos y supervivencia.
- Los campamentos pueden dejar rastros después de marcharse.
- Una ruina puede ser peligrosa sin contener enemigos; un escondite puede ser seguro sin ser conocido.
- Los habitantes tienen objetivos, conocimientos y versiones parciales de los hechos.

## 5. Descubrimiento y conocimiento

Separar:
1. Diseño interno: lo definido en documentos y futuro motor.
2. Estado real: lo que existe y ocurre en ese momento.
3. Conocimiento del protagonista: lo que vio, oyó, investigó o dedujo.

Una aldea puede existir sin ser conocida; un campamento puede haber sido abandonado y dejar rastros; unas ruinas pueden encontrarse sin conocer su origen; señales de un escondite no equivalen a descubrir la entrada. Los rumores son pistas con fuente y fiabilidad, no confirmaciones.

## 6. Distribución y densidad pendientes

No se fija todavía cuántas aldeas, campamentos, ruinas o escondites existen; qué subzonas contienen; qué pueblos, razas, gremios o facciones los ocupan; ni cuáles son accesibles al comienzo. La densidad deberá responder al tamaño del bosque, distancias, rutas, suministro, historia y presión ecológica. No poblar cada nodo solo para llenar el mapa.

## 7. Plantilla conceptual

```yaml
id: PLACE-UNKNOWN
name: No registrado
category: village | camp | ruin | hideout
design_status: proposal
canonical_status: pending_approval
map_node: No registrado
occupancy: unknown
physical_condition: unknown
purpose_real: No registrado
purpose_known_to_protagonist: No registrado
inhabitants_or_owners: []
resources: []
access_routes: []
defenses_and_hazards: []
ecological_effects: []
evidence: []
knowledge_state: undiscovered
last_state_change: No registrado
```

La plantilla es conceptual; no es todavía un esquema JSON validado ni una tabla SQLite.

## 8. Próximas tareas

1. Proponer escala y densidad de presencia civilizada.
2. Diseñar la relación entre rutas, aldeas y campamentos sin cerrar alternativas.
3. Crear localizaciones de ejemplo marcadas como propuestas.
4. Revisar cómo las comunidades obtienen recursos y reaccionan a criaturas y acontecimientos.
5. Convertir las fichas a datos estructurados y validarlas antes de conectarlas al motor.
