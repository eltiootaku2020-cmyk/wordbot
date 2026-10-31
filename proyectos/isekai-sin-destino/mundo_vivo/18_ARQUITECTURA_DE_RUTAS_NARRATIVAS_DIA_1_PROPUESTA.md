# 18 — Arquitectura de rutas narrativas del Día 1

**Estado:** propuesta de estructura narrativa; pendiente de revisión y aprobación del usuario.  
**Rama:** story/isekai-opening-branches.  
**Base:** feat/isekai-open-world-vn-foundation.  
**Alcance:** organizar posibilidades del primer día sin fijar sucesos, reacciones ni decisiones que todavía no forman parte del canon.

Este documento no sustituye la Lorebook ni el Greeting de SpicyChat. Tampoco afirma que las rutas estén implementadas en Word Bot.

## 1. Reglas que esta propuesta debe respetar

Se toman como límites de continuidad ya documentados:

- El protagonista procede de la Tierra contemporánea. El accidente del supermercado, el encuentro con la diosa chibi y la entrega de PSICHO-Eco ocurren antes de la llegada física al mundo.
- La llegada al claro del Bosque de los Siete Ecos, en la franja exterior del Bosque de las Bestias, se conserva como puente provisional. Día 1, 08:00, bruma y suelo húmedo son datos heredados sujetos a revisión, no detalles que deban ampliarse por suposición.
- En el primer encuentro solo están presentes Brina Solcor (guerrera), Maelis Orven (maga) y Sera Linde (arquera). Ivar Dalen y Timo Venn conservan sus fichas, pero no están allí ni reaccionan desde fuera de escena.
- El protagonista conserva ropa cotidiana, teléfono celular y la caja de cereal Dragon Ball Z con la figura de Goku vinculada al accidente. El estado de esos objetos, la batería, la señal, los daños y otras pertenencias no están registrados.
- El protagonista no recuerda necesariamente toda la conversación divina. El flashback de la iglesia queda para un estímulo y momento posteriores; no debe aparecer porque el narrador necesite explicar el origen.
- El grupo no conoce automáticamente la Tierra, la diosa ni PSICHO-Eco. Maelis puede investigar una anomalía solo después de observar algo que justifique esa investigación.
- Las tres aventureras conservan autonomía: no están obligadas a rescatar, reclutar, creer, proteger ni acompañar al protagonista.
- PSICHO-Eco no tiene todavía límites, costes, alcance, duración ni primer efecto concreto cerrados. No inventar usos gratuitos, control perfecto ni una rama desbloqueada.
- El mundo abierto debe permitir acción libre. Las tres sugerencias de interfaz nunca son las únicas acciones posibles.
- Todas las imágenes de personajes deberán respetar la regla obligatoria de ilustración anime 2D. No usar imágenes fotográficas, hiperrealistas ni renders 3D realistas.

## 2. Principio de diseño: ramas con consecuencias, no respuestas prefijadas

La ruta no debe ser una secuencia de diálogos donde cada opción conduce al mismo resultado. Una acción cambia lo que los personajes saben, sienten, deciden o hacen, y también puede cambiar la ubicación, el tiempo, los objetos y los riesgos.

Las rutas pueden volver a encontrarse en una misma zona o situación, pero deben conservar sus diferencias. No se borran retroactivamente:

- lo que el protagonista dijo o hizo;
- lo que cada aventurera presenció;
- qué interpretación hizo cada una;
- qué información se compartió y con quién;
- el tiempo transcurrido, desplazamientos y objetos;
- heridas, recursos, sospechas, confianza u otras relaciones cuando exista evidencia para registrarlas.

No se asignan puntos numéricos ni umbrales en esta propuesta. Se usan hechos y estados descriptivos hasta que el sistema de atributos y relaciones tenga reglas numéricas aprobadas.

## 3. Grafo inicial propuesto

El siguiente esquema representa oportunidades, no una secuencia obligatoria. Las flechas indican transiciones posibles según la acción del protagonista y la situación real.

~~~mermaid
flowchart TD
    A["A0 · Llegada al claro<br/>Estado físico y pertenencias por comprobar"]
    B["A1 · Primer contacto posible<br/>Brina, Maelis y Sera"]
    C{"A2 · Decisión libre del protagonista"}
    D["R1 · Cooperar o conversar"]
    E["R2 · Mantener reserva"]
    F["R3 · Observar e investigar"]
    G["R4 · Alejarse o evitar el contacto"]
    H["R5 · Confrontar o actuar de forma hostil"]
    I["R6 · Probar PSICHO-Eco"]
    J["A3 · Reacción contextual del mundo<br/>y de cada personaje"]
    K["A4 · Nuevo punto de decisión<br/>quedarse, partir, explorar o cambiar de plan"]
    L["A5 · Continuidad del Día 1<br/>sin final obligatorio"]

    A --> B
    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
    C --> I
    C -->|"Otra acción libre"| J
    D --> J
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J
    J --> K
    K -->|"Permanecer cerca"| L
    K -->|"Salir con consentimiento y acuerdo"| L
    K -->|"Explorar por cuenta propia"| L
    K -->|"Cambiar de objetivo"| L
~~~

**Importante:** el contacto inicial puede ocurrir porque el protagonista las ve, ellas lo descubren o una circunstancia válida los pone en contacto. No se fuerza una única forma de descubrimiento. Si el jugador actúa antes de que el grupo lo vea, el narrador resuelve desde esa situación.

## 4. Ramas de decisión inicial

### R1 — Cooperar o conversar

**Intención posible:** responder, presentarse, pedir ayuda, explicar parcialmente su situación o hacer preguntas.

**Consecuencias que deben evaluarse:**
- Qué información decide revelar el protagonista.
- Qué puede comprobar cada aventurera por sí misma.
- Si alguna ofrece ayuda, pregunta más, mantiene distancia o decide continuar su tarea.
- Si el protagonista acepta, rechaza o negocia cualquier ayuda.

**Límites:** contar la verdad no crea confianza automática. Una explicación extraña puede generar curiosidad, duda o incredulidad. No obliga a las tres a compartir la misma opinión.

### R2 — Mantener reserva

**Intención posible:** responder poco, ocultar el origen de los objetos, evitar preguntas o no explicar cómo llegó.

**Consecuencias que deben evaluarse:**
- La diferencia entre guardar silencio y mentir.
- Qué pueden inferir a partir de lo que sí observan.
- Si el silencio resulta prudente, sospechoso o irrelevante en ese contexto.
- Qué información deja de estar disponible para el grupo.

**Límites:** reservar información no equivale a una conducta criminal. Ninguna aventurera debe conocer el secreto solo porque el narrador lo conoce.

### R3 — Observar e investigar

**Intención posible:** mirar el entorno, estudiar al grupo, escuchar, examinar el claro, revisar las pertenencias o buscar un camino.

**Consecuencias que deben evaluarse:**
- Qué puede percibir realmente el protagonista desde su posición.
- Si observar requiere tiempo o expone su presencia.
- Qué rastros, sonidos u objetos existen de verdad en la escena.
- Si una acción interrumpe, retrasa o cambia la interacción con el grupo.

**Límites:** no colocar pistas, enemigos, tesoros ni peligros solo para premiar la exploración. Los hallazgos deben tener una causa y respetar la geografía documentada.

### R4 — Alejarse o evitar el contacto

**Intención posible:** retirarse, esconderse, tomar otro sendero o decidir que no quiere hablar.

**Consecuencias que deben evaluarse:**
- Si el protagonista puede retirarse sin ser visto o seguido.
- Qué caminos conoce y cuáles solo puede descubrir.
- Si las aventureras tienen motivos observables para seguirlo, advertirle o dejarlo ir.
- Qué coste temporal, físico o de orientación implica la decisión.

**Límites:** el grupo no debe perseguirlo por obligación narrativa. Tampoco debe aparecer de nuevo en el siguiente párrafo sin desplazamiento o causa.

### R5 — Confrontar o actuar de forma hostil

**Intención posible:** amenazar, acusar, intentar desarmar, atacar o impedir que alguien se acerque.

**Consecuencias que deben evaluarse:**
- La diferencia entre una amenaza verbal y una agresión física.
- Distancia, preparación, armas realmente presentes y capacidades de cada parte.
- Si el grupo intenta hablar, ponerse a salvo, defenderse, retirarse o responder.
- Lesiones, pérdidas, testigos y consecuencias posteriores cuando correspondan.

**Límites:** no convertir una discusión en combate automáticamente. Tampoco proteger al protagonista de una reacción razonable ni hacer que las aventureras actúen como enemigas sin motivo.

### R6 — Experimentar con PSICHO-Eco

**Intención posible:** intentar comprender el poder, usarlo sobre sí mismo, un objetivo o el entorno.

**Consecuencias que deben evaluarse:** únicamente después de definir el modo intentado, el objetivo válido, las condiciones, el coste y la resistencia aplicables. Registrar el intento y su resultado, incluso si falla.

**Límites:** esta rama no declara desbloqueada ninguna función. No permite controlar a las tres aventureras, crear lealtad ni conocer secretos sin un mecanismo aprobado. No aplicar automáticamente el límite antiguo de tres intentos de la versión SpicyChat v1.19, ni asumir usos ilimitados.

### R0 — Acción libre

El jugador puede proponer cualquier acción que tenga sentido dentro del mundo, aunque no figure entre las ramas sugeridas. Se interpreta su intención sin transformarla en otra acción. Si falta un dato esencial y el resultado cambia mucho según ese dato, se pregunta brevemente antes de resolver.

## 5. Reacciones individuales del trío

Las respuestas se calculan por personaje y por contexto. Esta tabla no dicta diálogos ni garantiza un resultado.

| Personaje | Prioridad documentada | Puede considerar según lo que observe | No debe hacer automáticamente |
|---|---|---|---|
| Brina Solcor | Seguridad, defensa y retirada ordenada | Mantener distancia, evaluar riesgo, protegerse o ayudar si tiene motivos | Adoptar al protagonista, confiar en él o combatir sin causa |
| Maelis Orven | Curiosidad y estudio; magia sencilla conocida | Preguntar, observar un fenómeno o investigar una anomalía visible | Identificar PSICHO-Eco, conocer su origen o dominar magia que no aprendió |
| Sera Linde | Vigilar perímetro, arco y rastros | Examinar el sendero, comprobar señales o advertir un riesgo visible | Conocer sucesos fuera de su percepción o aceptar órdenes sin motivo |

Una decisión del protagonista puede afectar a las tres de forma distinta. Una conversación privada con Maelis no entrega esa información automáticamente a Brina y Sera.

## 6. Convergencia sin borrar consecuencias

Las rutas iniciales pueden converger cuando el protagonista llega a una nueva decisión práctica. La convergencia no significa que todos terminen viajando juntos.

Puntos posibles de convergencia:

1. **Punto de conversación:** solo si ambas partes siguen dispuestas a hablar.
2. **Punto de separación:** el protagonista y el trío toman caminos distintos, con conocimiento limitado a lo que intercambiaron.
3. **Punto de cooperación temporal:** colaboran en una tarea concreta sin que eso signifique unirse al mismo grupo.
4. **Punto de exploración independiente:** el protagonista sigue por su cuenta con la información que realmente consiguió.
5. **Punto de conflicto no resuelto:** una amenaza o agresión puede dejar una relación deteriorada y una situación abierta.

El narrador no debe forzar la opción 1 o 3 como desenlace correcto. Cualquiera puede seguir jugando desde la situación resultante.

## 7. Registro mínimo de continuidad por rama

Cada escena importante debería dejar un registro breve, sin crear estadísticas ficticias:

| Campo | Qué conservar |
|---|---|
| scene_id | Identificador estable de escena |
| branch_id | Rama narrativa recorrida, si corresponde |
| time_place | Tiempo y ubicación confirmados o marcados como provisionales |
| player_action | Acción e intención del jugador |
| observed_facts | Hechos que el protagonista pudo percibir |
| witnesses | Quién estuvo presente y qué pudo observar |
| knowledge_changes | Quién aprendió qué, y por qué medio |
| relationship_evidence | Hechos que justifican un cambio relacional, sin inventar puntos |
| inventory_changes | Objetos realmente adquiridos, usados, dañados o perdidos |
| health_risk | Heridas, cansancio, peligro o ausencia de cambio, si se conoce |
| open_threads | Preguntas y situaciones que siguen pendientes |
| next_choices | Acciones que siguen siendo posibles desde la situación actual |

Un personaje ausente no se convierte en testigo. Un rumor requiere una vía de transmisión. Una impresión no se registra como hecho objetivo.

## 8. Uso de las tres opciones y «Otro»

Cuando la interfaz sugiera acciones, debe hacerlo desde la posición real del protagonista. Ejemplo ilustrativo, no texto definitivo del Greeting:

1. Responder con cautela y preguntar quiénes son.
2. Observar el claro y comprobar si hay un camino seguro.
3. Preguntar si conocen algún asentamiento cercano.
4. **Otro:** escribir una acción libre.

Las sugerencias pueden cambiar según la situación. No ofrecer «seguir al grupo» si todavía no han ofrecido acompañamiento. No ofrecer atacar si no existe una amenaza que lo justifique. No presentar como conocida una ruta que el protagonista no ha descubierto.

## 9. Semillas narrativas posteriores — no activadas

Son posibles líneas de desarrollo, no eventos confirmados ni escenas que deban suceder todas:

- **Conocer a Ivar y Timo:** su entrada requiere otra escena, causa, ubicación y momento coherentes. No fijar aquí cuándo aparecen ni hacerlos reaccionar al claro inicial.
- **Primer asentamiento:** el protagonista puede buscar un lugar habitado si descubre una ruta o recibe información fiable; no se fija todavía nombre, distancia ni localización.
- **Primer aprendizaje:** una aventurera, habitante, gremio o hallazgo podría abrir una oportunidad según disponibilidad, conocimiento y voluntad; nadie está obligado a enseñar.
- **Iglesia y recuerdo divino:** el flashback solo puede activarse cuando exista una visita y un estímulo narrativo apropiado. No se fija todavía dónde está la iglesia.
- **Primer uso de PSICHO-Eco:** permanece pendiente de una definición de balance; no se usa como atajo para resolver el prólogo.
- **Peligro ecológico:** puede aparecer por las condiciones reales de una zona, pero no es obligatorio que el Día 1 incluya monstruo, combate, herida o muerte.

La erupción del volcán continúa como acontecimiento ancla del Día 12 según la documentación vigente. Esta propuesta no agrega ni adelanta acontecimientos de ese calendario.

## 10. Criterios de revisión antes de canonizar

La propuesta estará lista para revisión cuando pueda comprobarse lo siguiente:

- No contradice el origen terrestre, el encuentro divino ni las pertenencias confirmadas.
- Solo Brina, Maelis y Sera están disponibles en el primer encuentro.
- Ivar y Timo no hablan, reaccionan ni aparecen por conveniencia.
- Ninguna respuesta del trío está fijada de antemano.
- El protagonista puede hablar, ocultarse, investigar, retirarse, confrontar o hacer otra acción razonable.
- Las rutas conservan consecuencias y no convergen borrando recuerdos, tiempo, objetos o relaciones.
- PSICHO-Eco no tiene límites ni facultades inventadas.
- Ningún encuentro, romance, combate, rescate o reclutamiento es obligatorio.
- Las imágenes asociadas al reparto respetan el estilo anime 2D obligatorio.
- Las escenas no aprobadas permanecen como propuestas y no se copian todavía a los originales de SpicyChat v1.19.

## 11. Decisiones que siguen abiertas

Esta arquitectura no resuelve por sí sola:

1. El texto definitivo del primer Greeting y el orden exacto de la primera interacción.
2. El estado físico del protagonista, la caja, la figura y el celular al llegar.
3. Qué objetos adicionales lleva realmente.
4. La hora y el clima finales del claro, actualmente heredados de la versión anterior.
5. Qué puede hacer PSICHO-Eco al inicio y cuáles son sus límites.
6. Qué rutas individuales o vínculos se desean desarrollar a largo plazo.
7. Cuándo y dónde aparecen Ivar y Timo.
8. Qué asentamientos, rutas o amenazas concretas descubre primero.

**Regla de aprobación:** seleccionar o comentar una rama no convierte todas las demás en canon ni autoriza a cambiar archivos originales de SpicyChat. Las decisiones se incorporan al documento maestro solo después de confirmación expresa.
