# Migración SpicyChat v1.20 — auditoría y parche maestro

**Estado:** propuesta; los archivos originales v1.19 permanecen intactos.  
**Rama:** `feat/isekai-open-world-vn-foundation`.

## Hallazgos verificados

- La Lorebook v1.19 conserva 77 entradas, UID únicos y keywords sin duplicar.
- La entrada JSON UID 68 aparece etiquetada como “Reloj narrativo y panorama visible”, pero su contenido repite el límite antiguo de Eco. La propuesta corrige ese contenido.
- El inventario viejo todavía fija pañuelo, bolsa y cordel, sin celular ni pertenencias de la Tierra.
- El poder viejo Eco establece tres intentos por persona, incluso con fallo. La especificación nueva dice expresamente que esta regla no se traslada automáticamente a PSICHO-Eco.
- El JSON UID 12 y múltiples bloques de la Lorebook fijan la erupción como máximo en Día 7. La documentación nueva del mundo vivo fija el acontecimiento ancla en Día 12.
- Personality y Scenario siguen repitiendo el inventario viejo y el Día 7.
- La escena de inicio y Greeting fijan a los cinco aventureros presentes, mientras que el nuevo puente registra conflicto abierto entre una composición inicial de tres y una de cinco.

## Texto maestro que debe sustituir la sección 2

```md
## 2. Protagonista, origen y PSICHO-Eco

El protagonista es una persona adulta procedente de la Tierra contemporánea; el usuario elige su género. La edad exacta no queda fijada en esta migración: la v1.19 decía 25 años o más, pero no se debe tratar esa cifra como una nueva confirmación. Llega con su ropa cotidiana, teléfono celular y los objetos personales que realmente llevaba. No inventes otros objetos ni declares que carecía de dinero, alimentos o pertenencias si no se han comprobado.

### Accidente en la Tierra
En un supermercado grande ve una caja promocional de cereal Dragon Ball Z con una figura de Goku, colocada en lo alto de un estante. Intenta subir para alcanzarla y el estante cae con los productos. El estado físico, posibles heridas y la forma exacta en que ocurre el traslado no se completan por cuenta del narrador.

### Encuentro con la diosa
Después aparece ante una diosa de apariencia chibi que está usando su teléfono. Se sorprende porque no esperaba recibir a nadie, revisa su pasado y concluye que no es un candidato adecuado para héroe. Al ver el cereal surge una disputa cómica: el protagonista protege la caja para que no se la quite. El protagonista pide un poder parecido, en concepto general, a las órdenes mentales de Code Geass; la diosa le entrega PSICHO-Eco, una versión barata/incompleta que evoluciona con su usuario. La diosa dice que enviará a alguien mejor, pero eso no confirma que otra persona llegue ni que salve el mundo.

### Memoria fragmentaria
Al inicio el protagonista no recuerda toda la conversación divina. Una visita posterior a una iglesia puede activar el flashback cómico completo. El recuerdo pertenece al protagonista: no se transmite a los aventureros ni a otros PNJ automáticamente.

### PSICHO-Eco
PSICHO-Eco es un poder sobrenatural incompleto y evolutivo, no la habilidad antigua «Eco» con otro nombre. No concede control absoluto ni garantiza obediencia, afecto, confianza, amistad o consentimiento. La antigua regla de tres intentos por persona humana pertenece a la versión anterior de SpicyChat y no se aplica automáticamente a todas las ramas, especies u objetivos de PSICHO-Eco.

**Balance pendiente:** límites por tipo de objetivo, coste, alcance, duración, resistencia, riesgos, condiciones de desbloqueo y progresión. Hasta que se definan, registra cada intento y su resultado; no inventes cargas, recuperaciones ni usos ilimitados.
```

## Cambios coordinados en el JSON v1.20 propuesto

| UID | Corrección |
|---:|---|
| 2 | Bosque de los Siete Ecos: llegada y pertenencias nuevas, lugar provisional |
| 12 | Acontecimiento ancla del volcán: Día 12 |
| 67 | PSICHO-Eco evolutivo, sin contador 3/3 heredado |
| 68 | Reloj narrativo: contenido correcto |
| 75 | Inventario terrestre confirmado y campos No registrados |
| 77 | Registro de poderes sin imponer un límite global antiguo |
| 78 | Nueva entrada: accidente, diosa y flashback de la iglesia |

Se mantienen las cinco fichas del reparto y los UID originales; no se renumera ni reutiliza el hueco UID 76.

## Pendientes que faltan antes de desplegar

1. Composición inicial del grupo: resuelta; Brina, Maelis y Sera están presentes en el primer encuentro. Ivar y Timo conservan sus fichas y no están allí.
2. Edad exacta del protagonista, si se desea fijarla.
3. Lista real de objetos terrestres adicionales, si los llevaba.
4. Heridas, estado del celular (batería, señal, daños) y estado de caja/figura tras accidente y traslado.
5. Qué recuerda al inicio y qué parte exacta revela la iglesia.
6. Primer efecto disponible de PSICHO-Eco, objetivos permitidos, costes, alcance, duración, resistencia, riesgos y progresión.
7. Recalendario completo: Día 12 es el ancla; los días 7–11 requieren hitos si se desean y las consecuencias posteriores deben comprobarse contra otros eventos, incluida la Feria del Día 15.
8. Nuevo Greeting, una vez resuelto el grupo y la secuencia del primer encuentro.

## Regla de despliegue

No importar a SpicyChat hasta resolver los pendientes narrativos y probar activación de keywords, continuidad del inventario, flashback, reloj, guardado y reanudación.

## Decisión confirmada el 31-10-2026 — grupo inicial de tres

El primer encuentro está formado por Brina Solcor (guerrera), Maelis Orven (maga) y Sera Linde (arquera). Las cinco fichas permanecen íntegras en Lorebook y JSON. Ivar Dalen (lancero) y Timo Venn (provisiones/logística) pertenecen al reparto, pero no están presentes en el claro. La aparición posterior de ambos debe tener causa, ubicación y momento coherentes; no se fija aquí el día ni la circunstancia concreta.
