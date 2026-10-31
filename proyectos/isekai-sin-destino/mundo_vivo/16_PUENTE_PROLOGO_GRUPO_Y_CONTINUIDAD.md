# 16 — Puente de continuidad entre el origen terrestre y la primera aventura

**Estado:** regla de continuidad provisional que conserva el comienzo anterior compatible con la premisa confirmada el 30-10-2026. No introduce nuevos hechos de canon que el usuario no haya establecido.

## 1. Secuencia temporal

1. **Tierra contemporánea — supermercado.** El protagonista ve en oferta una caja de cereal Dragon Ball Z con figura de Goku, situada en un estante alto. Se sube para alcanzarla; el estante cae con productos.
2. **Espacio divino/espera — diosa chibi.** Aparece ante la diosa que utiliza su celular, no esperaba recibir a nadie, revisa su pasado, lo considera inadecuado como héroe, se interesa por el cereal y recibe su petición de un poder tipo órdenes mentales. Le da PSICHO-Eco, versión barata/incompleta que crece con el usuario, y afirma que enviará a alguien mejor.
3. **Traslado al mundo físico.** La conversación termina y el protagonista aparece en el mundo fantástico con sus pertenencias confirmadas. No se repite el accidente del supermercado.
4. **Primer punto de llegada heredado.** Para mantener la continuidad previa, se utiliza provisionalmente un claro del Bosque de los Siete Ecos, franja exterior del Bosque de las Bestias. La configuración antigua lo ubica en Día 1, 08:00, con bruma y suelo húmedo; esos detalles se conservan como marco heredado, no como nuevos datos confirmados por la última descripción.
5. **Primer encuentro.** El grupo de aventureros del módulo anterior viaja por la zona y puede descubrir al protagonista. No tiene obligación de rescatarlo, aceptarlo o incorporarlo.

## 2. Inventario de llegada

**Confirmado por la nueva premisa:**
- Ropa normal contemporánea que lleva puesta.
- Teléfono celular.
- Caja de cereal Dragon Ball Z y figura de Goku, vinculadas al accidente y a la escena de la diosa.

**Estado no registrado:**
- Estado de embalaje, cereal y figura tras la caída/traslado.
- Batería, daños, señal, conectividad y almacenamiento del teléfono.
- Otros objetos pequeños que pudiera llevar en bolsillos o manos.

**No agregar por defecto:**
- Dinero, comida adicional, agua, mochila, armas, armadura, equipo de aventura.
- Pañuelo gastado, bolsa vacía y cordel corto de la antigua configuración, salvo que se confirme que los llevaba desde la Tierra.

No duplicar el cereal ni la figura entre la escena divina y el inventario terrestre: se trata del mismo objeto.

## 3. Grupo inicial heredado

La Lorebook v1.19 y la escena antigua del Día 1 describen cinco integrantes adultos que viajan juntos:

| Nombre | Edad documentada | Rol y competencia documentada |
|---|---:|---|
| Brina Solcor | 26 | Guerrera; espada, defensa de línea y retirada ordenada |
| Ivar Dalen | 27 | Lancero; control de distancia y vigilancia de flancos |
| Maelis Orven | 24 | Maga; Luz tenue (Brasa) y Soplo (Viento) |
| Sera Linde | 25 | Arquera; arco, rastreo y observación |
| Timo Venn | 22 | Encargado de provisiones; inventario, cuentas, comercio y campamento |

Las reacciones de diseño anteriores se conservan: Brina prioriza seguridad; Ivar sospecha posibles emboscadas; Maelis siente curiosidad por anomalías, pero no identifica PSICHO-Eco automáticamente; Sera vigila el perímetro; Timo evalúa recursos y logística.

Este grupo es el **reparto documentado existente**, no una obligación de reclutamiento. Cada persona puede ayudar, negociar, desconfiar, marcharse o separarse según la escena.

### Conflicto todavía sin resolver

En los documentos anteriores existen notas de una posible composición reducida del grupo inicial (Brina, Maelis y Sera) y una composición de cinco (Brina, Ivar, Maelis, Sera y Timo). Para no borrar personajes, se conserva el roster completo como reparto conocido, pero la presencia simultánea de los cinco en el primer encuentro queda marcada como pendiente de reconciliación narrativa. La antigua escena dice que los cinco encuentran al protagonista; ninguna modificación nueva confirmó su eliminación.

**Maelis no es campesina en la ficha heredada:** es la maga de 24 años. El ejemplo «Maelis aventurera/campesina» usado al explicar especialidades es conceptual. No crea una segunda Maelis ni cambia la profesión de la Maelis existente. Versiones de personaje diferentes deben tener IDs distintos; un cambio de profesión de la misma persona conserva identidad e historial.

## 4. Memoria fragmentaria y flashback de la iglesia

Al comenzar la aventura:
- El protagonista recuerda de forma incompleta la escena divina.
- Puede conservar el nombre PSICHO-Eco y una impresión general del poder, pero no conoce todas sus ramas, reglas ni límites.
- No tiene que explicar al grupo la escena completa ni el origen de sus objetos.
- La visita posterior a una iglesia puede activar un recuerdo más claro y cómico de la diosa con el celular, la revisión del pasado, la disputa por el cereal, la petición de poder, la versión de oferta y la despedida.

El flashback revela algo que el protagonista vivió; no es una transmisión de conocimiento al resto del grupo.

## 5. Regla de conocimiento

- Los aventureros ven el estado físico del protagonista y los objetos que realmente puedan observar.
- No reconocen automáticamente el teléfono, el cereal, Goku ni la tecnología terrestre.
- No conocen la escena divina ni el nombre PSICHO-Eco salvo que el protagonista lo cuente o presencien una manifestación y lo aprendan por una vía válida.
- Maelis puede investigar una anomalía, pero su curiosidad no equivale a saber la respuesta.
- La historia conserva separados los hechos del mundo, lo que cada integrante percibe, lo que interpreta y lo que le cuentan.

## 6. PSICHO-Eco: regla heredada frente al poder nuevo

La versión vieja de «Eco» de la Lorebook de SpicyChat limita a tres intentos por persona humana, incluso si fallan. El PSICHO-Eco nuevo se define como poder de oferta/incompleto que evoluciona con el usuario y tiene ramas más amplias.

Hasta reconciliar ambas reglas:
- No codificar un límite global de tres usos como regla universal de PSICHO-Eco.
- Mantener el límite antiguo solo como regla heredada del preset SpicyChat, no como regla automáticamente trasladada al nuevo runtime.
- No asumir tampoco usos ilimitados, recargas o control perfecto.
- Los costes, intentos, duración y desbloqueos por rama quedan pendientes de balance y prueba.
- Cualquier intento se registra con objetivo, modo, coste si existe, resultado, resistencia, testigos y consecuencias.

## 7. Alcance y estado

Este documento reconcilia textos y continuidad; no implementa el prólogo, grupo ni inventario dentro de SQLite. La sincronización con `LOREBOOK_MAESTRA.md`, `LOREBOOK_IMPORT.json` y `CONFIG_LIGERA.md` se mantiene pendiente, porque esos artefactos todavía describen el Eco limitado antiguo y el inicio sin celular. Se necesita un cambio coordinado y validación de la importación antes de reemplazarlos.
