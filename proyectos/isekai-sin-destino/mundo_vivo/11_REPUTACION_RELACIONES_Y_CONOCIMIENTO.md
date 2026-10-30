# 11 — Reputación, relaciones, conocimiento y consecuencias sociales

**Estado:** reglas generales aprobadas en conversación el 30-10-2026 e incorporadas a esta especificación documental. No son todavía comportamiento implementado del motor. Los valores numéricos, fórmulas de propagación y umbrales quedan pendientes.

## 1. Principio central: el mundo no es omnisciente

Un hecho puede ocurrir sin que nadie lo conozca. El sistema debe separar rigurosamente:

1. **Hecho real:** lo que ocurrió objetivamente en el mundo.
2. **Percepción individual:** lo que cada personaje vio, oyó o experimentó.
3. **Recuerdo e interpretación:** lo que cada personaje conserva y cree que sucedió.
4. **Información comunicada:** lo que alguien contó, escribió, denunció o difundió.
5. **Rumor:** una versión transmitida de segunda o posterior mano, susceptible de errores y deformaciones.
6. **Conocimiento del protagonista:** lo que el protagonista descubrió por experiencia, investigación o fuentes.

La narración no puede convertir una capa en otra automáticamente. El motor puede conocer un asesinato; un guardia que no estuvo presente no lo conoce por ese solo hecho. El protagonista tampoco obtiene información por el mero hecho de que exista en los datos internos.

## 2. Atribución de hechos, testigos y pruebas

Cada acontecimiento con posibles efectos sociales debe registrar, cuando corresponda:

- ID del hecho y tipo de acontecimiento.
- Momento y lugar.
- Participantes y afectados.
- Testigos directos, observadores parciales y personas que solo oyeron algo.
- Qué pudo percibir cada testigo (rostro, voz, ropa, arma, dirección de huida, detalles parciales, etc.).
- Identificación atribuida y grado de certeza: no identificado, descripción parcial, sospechoso, identificado o confirmado.
- Evidencias físicas o documentales que queden disponibles.
- Quién descubrió cada evidencia y cuándo.
- Quién conoce el hecho, por qué fuente y con qué fiabilidad.
- Alteraciones, contradicciones o pérdidas posteriores de información.

**Ver un hecho no equivale siempre a identificar al responsable.** Un testigo puede haber visto un ataque sin reconocer al atacante; otro puede conocer al sospechoso por reputación o por una descripción. La atribución debe tener una fuente plausible.

**Encontrar una consecuencia no revela automáticamente su causa.** Hallar un cadáver puede provocar una investigación o un rumor sobre una muerte, pero no identifica por sí solo al asesino. Rastros, heridas, objetos abandonados y testimonios pueden aportar pistas, sin garantizar una conclusión correcta.

## 3. Fama y reputación pública

La fama no es una puntuación mundial que cambie porque el motor conoce un acontecimiento.

- Un hecho secreto sin testigos, descubrimiento ni evidencia atribuible no modifica automáticamente la fama pública del protagonista.
- Un acto cometido a la vista de una multitud puede producir testigos, denuncias, testimonios y rumores, pero la identidad del responsable todavía debe atribuirse.
- Si solo se conoce que ocurrió un delito, la gente puede hablar del delito sin conocer quién lo cometió.
- La reputación puede ser distinta por ciudad, aldea, gremio, facción, caravana, profesión o grupo social.
- Una comunidad aislada puede desconocer la fama que existe en otra región.
- La información viaja por canales concretos: viajeros, comerciantes, cartas, mensajeros, tablones, autoridades, gremios y conversaciones.
- La difusión depende de distancia, tiempo, tránsito, interés, acceso a comunicación, control de rutas y acontecimientos. No se presupone difusión instantánea.
- Los rumores pueden ser falsos, exagerados, incompletos, contradictorios o atribuir un hecho a la persona equivocada.
- Una investigación puede descubrir hechos anteriores y cambiar una reputación después; también puede fracasar, estancarse o señalar a un inocente.

No deben fijarse por ahora valores numéricos de fama, umbrales de búsqueda, alcance de rumores o velocidades de propagación. Deben derivarse de las reglas y del contexto de cada mundo.

## 4. Relaciones personales: cada personaje recuerda por separado

Las relaciones son individuales, específicas y pueden ser asimétricas. El protagonista puede confiar en alguien que no confía en él, o sentir cariño por una persona que le teme.

No reducir todos los vínculos a una única puntuación. Mantener ejes separados cuando sean relevantes:

- Cariño o afecto.
- Confianza.
- Atracción romántica.
- Respeto.
- Miedo.
- Incomodidad.
- Sospecha.
- Resentimiento o rencor.
- Lealtad o disposición a colaborar.

Estos ejes no se implican automáticamente entre sí. Por ejemplo:
- Cariño alto no significa confianza alta.
- Atracción no significa obediencia.
- Respeto no significa amistad.
- Miedo no significa lealtad.
- Una persona puede conservar afecto y, a la vez, sentir miedo o desconfiar.
- Un favor puede aumentar gratitud sin borrar un daño anterior.

Los cambios deben depender de interacciones, experiencias, historia compartida, personalidad, necesidades, expectativas, pruebas y contexto. No se modifica la relación de todos los personajes por una sola acción que solo uno presenció.

Cada personaje conserva recuerdos, interpretaciones, secretos y vínculos propios. No recibe automáticamente los recuerdos ni las conclusiones de otros.

## 5. Psico-Eco, efectos privados y consecuencias públicas

Psico-Eco puede cambiar estados internos del objetivo si el intento tiene éxito, pero **un cambio privado no crea por sí solo fama pública**.

- Si el protagonista manipula con éxito los sentimientos de una persona cuando nadie más puede observar la intervención, pueden cambiar los ejes internos afectados de esa persona; la fama pública del protagonista permanece sin cambios si no existe testigo, evidencia o comunicación que permita atribuir lo ocurrido.
- El cariño o la atracción inducidos pueden ser altos, incluso alcanzar el máximo definido más adelante, sin que eso implique automáticamente confianza, lealtad, obediencia, recuerdos compartidos o conocimiento de la manipulación por terceros.
- Una intervención privada no crea una relación real con los amigos, familiares o compañeros del objetivo. Esas personas mantienen sus propias experiencias y opiniones.
- Un intento fallido de Psico-Eco debe dejar una reacción de incomodidad, inquietud o perturbación en el objetivo; la intensidad y su interpretación dependen de la resistencia, el modo utilizado y las circunstancias. El objetivo puede no comprender qué ocurrió ni identificar al causante.
- Si un testigo presencia la intervención, podrá reaccionar según lo que realmente pudo percibir. No se transmite automáticamente el conocimiento a toda la comunidad.
- Si la víctima cuenta lo sucedido, alguien detecta contradicciones o aparece evidencia, la información puede difundirse y producir consecuencias sociales.
- Las manipulaciones pueden ser difíciles de detectar, pero no tienen una garantía universal de invisibilidad o permanencia. Hábitos, recuerdos ajenos, evidencias y contradicciones pueden revelar anomalías.

La resolución de Psico-Eco debe conservar separados: intención, efecto mental conseguido, reacción del objetivo, testigos, evidencia, conocimiento de terceros y reputación pública.

## 6. Ejemplos de aceptación obligatoria

### Caso A — asesinato no presenciado
El protagonista mata a una persona en un lugar aislado. Nadie lo ve, no deja evidencia reconocible y nadie descubre el hecho. El motor registra el asesinato y sus consecuencias materiales, pero la fama pública del protagonista no cambia por ese acontecimiento desconocido.

Si después alguien encuentra el cadáver, se conoce una muerte; todavía no se conoce necesariamente la identidad del asesino. La investigación puede producir pistas, sospechas o una atribución errónea.

### Caso B — asesinato en una plaza concurrida
Varias personas presencian el ataque. Algunas pueden reconocer al protagonista; otras solo describen a una persona. Pueden huir, pedir ayuda, denunciar, callar, mentir o difundir versiones distintas. La reputación cambia en los lugares y grupos a los que llegue información atribuible, no en todo el mundo instantáneamente.

### Caso C — manipulación exitosa en privado
El protagonista usa Psico-Eco a solas con un personaje y consigue aumentar su cariño o atracción. El cambio se registra en la relación individual. La fama pública no cambia por falta de testigos y difusión. El personaje no adquiere automáticamente confianza, lealtad ni obediencia.

### Caso D — intento fallido
El protagonista intenta influir en un personaje y falla. El objetivo experimenta incomodidad o inquietud, pero puede no comprender el origen. Si nadie más observa ni recibe información, no aparece automáticamente una fama pública de manipulador.

## 7. Reglas de narración y presentación

- No mostrar al jugador cifras sociales internas salvo que exista una interfaz o fuente que justifique que su personaje las conoce.
- No anunciar como hecho una acusación que solo es un rumor.
- Diferenciar «visto», «escuchado», «deducido», «sospechado», «denunciado» y «confirmado».
- No hacer que guardias, comerciantes, aldeanos o facciones reaccionen a crímenes que no conocen.
- No hacer que todos los NPC reaccionen igual: cada uno tiene información, objetivos, temores, intereses, carácter y relaciones propios.
- Un cambio de fama o relación necesita causa, fuente y momento; si no hay causa verificable, conservar el estado previo.
- La reacción social debe corresponder al contexto, gravedad, cultura, ley local, recursos y conocimiento disponible. No hay una respuesta universal para todas las ciudades o grupos.

## 8. Contrato para el futuro motor

El motor deberá poder representar, como mínimo:

- Hechos/eventos separados de las observaciones y de las versiones conocidas.
- Testigos individuales con percepción parcial y fiabilidad.
- Atribución de responsabilidad con fuente y grado de certeza.
- Reputación localizada por grupo o región, no un valor omnisciente global.
- Relaciones individuales con ejes independientes.
- Rumores con origen, cadena de transmisión, antigüedad y fiabilidad.
- Efectos privados de Psico-Eco separados de la difusión social.
- Historial de cambios con causa y evidencia.

## 9. Pruebas de aceptación futuras

1. Asesinato secreto sin descubrimiento: no cambia la fama pública.
2. Cadáver descubierto sin identificación: se conoce la muerte, no automáticamente el asesino.
3. Testigo parcial: su descripción no se convierte en identificación segura.
4. Crimen público con reconocimiento confirmado: la reputación puede cambiar entre testigos y redes que reciban el informe.
5. Rumor transmitido: conserva fuente, tiempo y posibilidad de distorsión.
6. Éxito privado de Psico-Eco: cambia solo los ejes afectados del objetivo; no la fama si no hay difusión.
7. Fallo de Psico-Eco: registra incomodidad/inquietud del objetivo; no crea fama pública sin información externa.
8. Una persona querida pero manipulada puede sentir cariño alto y confianza baja.
9. Un guardia sin información pertinente no trata al protagonista como criminal conocido.
10. Una localidad que recibe una descripción incompleta puede sospechar sin confirmar identidad.

## 10. Pendiente de implementación

Este documento define comportamiento esperado. No significa que Word Bot ya calcule fama, propague rumores, simule testigos o persista ejes sociales. Los esquemas SQLite, servicios, API, interfaz, migraciones y pruebas automatizadas deberán desarrollarse y validarse en una fase técnica posterior.
