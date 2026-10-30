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

## 6. Distribución y densidad equilibrada

**Decisión aprobada:** densidad equilibrada de presencia civilizada.

- Varias aldeas pequeñas, separadas entre sí, sin formar una red continua de población.
- Campamentos relativamente habituales cerca de rutas transitadas, recursos y zonas de expedición; su ocupación y ubicación pueden cambiar.
- Ruinas y escondites repartidos por el bosque, muchos de ellos ocultos, inaccesibles o todavía no descubiertos.
- Extensiones amplias de bosque salvaje y subzonas sin presencia civilizada estable.
- La distribución responde a geografía, distancias, recursos, seguridad, historia, rutas y presión ecológica; no se asigna una cuota idéntica a cada zona.
- La densidad global no garantiza que el protagonista encuentre un lugar habitado en un momento concreto.

Siguen pendientes las cantidades exactas, ubicaciones, población, pueblos, razas, gremios, facciones y accesibilidad inicial. No poblar cada nodo solo para llenar el mapa.



## 6.1. Patrón espacial de trabajo (propuesta, no canon)

Para convertir la densidad equilibrada en un mapa coherente, se propone distribuir la presencia de forma desigual según accesibilidad y riesgo, sin fijar todavía localizaciones:

- **Límites y accesos:** candidatos preferentes para aldeas pequeñas o puestos estables, porque facilitan intercambio, abastecimiento y contacto con el exterior. No todos los accesos tienen que estar habitados.
- **Rutas conocidas y cruces:** lugares adecuados para campamentos temporales, refugios de viajeros y puntos de intercambio. La actividad atrae tanto oportunidades como depredadores y conflictos.
- **Subzonas intermedias:** pueden contener asentamientos aislados, puestos abandonados, ruinas accesibles y escondites cuya ubicación dependa de recursos o rutas secundarias.
- **Zonas profundas o peligrosas:** menor presencia estable; pueden existir campamentos de expedición, ruinas remotas y escondites difíciles de alcanzar, pero no se presupone que estén presentes ni que sean accesibles.
- **Áreas ecológicas sensibles:** la presencia civilizada debe ser escasa o estar condicionada por la dificultad de obtener recursos y por el riesgo de alterar hábitats.

Este patrón es una hipótesis de distribución para orientar el diseño posterior. No determina que haya una aldea en el borde, una ruina en el centro ni un campamento en una ruta concreta. Se revisará al definir el mapa de nodos y subzonas.

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


## 6.2. Decisión aprobada: ubicación repartida de las aldeas

**Decisión del usuario:** las aldeas estarán repartidas entre los límites y el interior del Bosque de las Bestias.

- La distribución será desigual, no uniforme.
- Habrá una mayor concentración relativa de aldeas pequeñas cerca de los límites y accesos, donde el intercambio, el abastecimiento y el contacto con el exterior resultan más viables.
- También podrán existir comunidades aisladas en subzonas interiores cuando la disponibilidad de agua, alimento, refugio, rutas y seguridad lo justifique.
- En zonas profundas o especialmente peligrosas la presencia estable será muy escasa; cualquier comunidad allí requerirá una explicación excepcional de supervivencia y acceso.
- Las rutas conocidas pueden conectar comunidades, pero no implican que todas estén habitadas ni que exista una red continua.
- Esta decisión fija el patrón general de distribución, no nombres, cantidades, población, coordenadas, facciones ni localizaciones concretas.

La propuesta espacial anterior queda refinada por esta decisión: los límites tienen mayor peso relativo, pero el interior no queda vacío.

## 6.3. Decisión aprobada: sistema combinado de rutas

**Decisión del usuario:** las conexiones del Bosque de las Bestias seguirán un sistema combinado.

- **Caminos principales:** relativamente estables y capaces de conectar algunas aldeas, accesos y puntos de intercambio. Su estabilidad no significa que sean siempre seguros ni que todos los asentamientos estén conectados.
- **Senderos secundarios:** menos transitados y más variables; pueden cambiar, quedar cubiertos o desaparecer por vegetación, clima, erosión, actividad de criaturas y acontecimientos.
- **Rutas ocultas o temporales:** pueden ser conocidas solo por habitantes, exploradores o criaturas concretas. Pueden aparecer, bloquearse o dejar de ser transitables según las condiciones.
- No todas las aldeas tendrán conexión directa. Algunas comunidades interiores podrán depender de senderos difíciles o quedar aisladas durante ciertos periodos.
- La existencia, trazado, estado y conocimiento de cada ruta concreta siguen pendientes. Esta decisión aprueba la estructura general, no un mapa definitivo ni ubicaciones concretas.

