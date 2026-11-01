# 28 — Arquitectura local de PC sin IA generativa

**Dirección confirmada por el usuario el 31-10-2026.**  
**Proyecto:** Isekai sin Destino, desarrollado dentro del repositorio Word Bot.  
**Estado técnico:** decisión de producto registrada; arquitectura propuesta, todavía no implementada como juego completo.  
**Alcance:** definir cómo funciona el juego enteramente desde el PC, sin modelos generativos ni dependencia de servicios externos.

## 1. Decisión principal

Isekai sin Destino será un juego/programa de PC cuyo mundo se simula localmente. **No se utilizará IA generativa** para escribir cada respuesta, decidir acciones, manejar personajes o mantener la continuidad.

No serán dependencias del juego:
- ChatGPT o Gemini como narradores;
- llamadas a APIs de modelos;
- modelos locales generativos;
- chat web externo;
- conexión a Internet para que funcione la partida;
- claves API, cuentas o cuotas de mensajes.

El juego debe iniciar, jugar, guardar, cargar y continuar una campaña desde el PC sin tener que comunicarse con un modelo de lenguaje.

## 2. Qué significa que los personajes actúen solos sin IA generativa

Los personajes no estarán congelados esperando al protagonista. Tendrán comportamiento autónomo mediante **lógica de juego programada**:
- estados y transiciones;
- condiciones de entrada/salida;
- objetivos activos;
- prioridades configuradas;
- agendas flexibles;
- reglas de percepción y conocimiento;
- selección entre acciones válidas;
- resultados, costes y consecuencias;
- eventos programados;
- variación reproducible mediante semilla local cuando corresponda.

No se necesita un modelo generativo para decidir si Brina sigue una ruta conocida, si Maelis continúa estudiando o si Sera abandona un rastreo. Estas decisiones se resuelven con sus datos, el contexto y reglas creadas por el diseñador.

Se recomienda evitar el término ambiguo «IA de PNJ» en las especificaciones del juego. Utilizar «comportamiento programado», «motor de decisiones» o «lógica de personajes». En desarrollo de videojuegos algunos llaman «game AI» a estas rutinas, pero aquí no significa IA generativa.

## 3. Narración y diálogos sin generación automática

El contenido narrativo se construye a partir de:
- escenas escritas por el autor;
- diálogos y respuestas por personaje;
- opciones de conversación;
- condiciones de disponibilidad;
- variantes según relación, conocimientos, estado, lugar y hora;
- escenas alternativas por decisiones anteriores;
- textos de descripción por ambiente, clima y descubrimientos;
- eventos y consecuencias definidos en datos.

Ejemplo de una conversación:
1. El jugador elige hablar con Brina.
2. El motor comprueba si está presente, ocupada, herida o dispuesta a hablar.
3. Comprueba el estado de la relación y los hechos que cada personaje conoce.
4. Selecciona un nodo de diálogo válido.
5. Muestra el texto escrito y las opciones permitidas.
6. Al elegir una respuesta, ejecuta las operaciones locales asociadas y registra los cambios.

No se genera texto libre en tiempo real mediante un LLM. La variedad proviene de diálogos alternativos, líneas contextuales, combinaciones de escenas, descripciones escritas y consecuencias reales.

Las frases de relleno no deben ocultar falta de contenido. Cuando no exista una respuesta específica, se puede usar una respuesta breve y coherente ya escrita, una opción de espera o una salida de diálogo; no inventar una narración de modelo.

## 4. Componentes locales propuestos

### 4.1 Motor de mundo

Responsabilidades:
- mantener el estado actual de la partida;
- validar que una acción sea posible;
- aplicar reglas y consecuencias;
- gestionar día, hora, clima y eventos;
- ejecutar movimientos y encuentros;
- resolver actividades simultáneas;
- mantener inventario, recursos, heridas, relaciones y conocimiento;
- guardar el historial y permitir rollback/restauración.

Debe ser determinista para las mismas entradas y semilla, salvo que una fuente externa se añada explícitamente en una función no necesaria para jugar.

### 4.2 Motor temporal

- Usa segundos enteros como unidad interna una vez aprobada su implementación.
- Calcula duración desde la acción local realizada, no desde la extensión del texto.
- Resuelve tareas secuenciales, simultáneas y fases internas sin doble conteo.
- Divide actividades largas cuando se aproxima un evento.
- Deriva mañana, tarde, noche y otras franjas desde la hora y la región.
- Conserva segundos, eventos y estado temporal al guardar y restaurar.

### 4.3 Motor de movimiento y mapa

- Mapa como grafo de ubicaciones y conexiones.
- Los tramos almacenan distancia o banda aproximada, terreno, pendiente, dificultad y disponibilidad.
- La velocidad efectiva depende del personaje/grupo, carga, condición física, clima y ruta.
- Búsqueda, rastreo y exploración tienen costes temporales propios.
- El mapa visual representa los mismos nodos y rutas que el simulador; no existe un mapa decorativo desconectado del estado.

### 4.4 Motor ambiental

- Clima persistente por región.
- Estados: soleado, nublado, lluvia, niebla, tormenta, viento u otros definidos para cada bioma.
- Intensidad, visibilidad, viento y estado del suelo cuando importen.
- Transiciones programadas o basadas en reglas locales; nunca un sorteo nuevo por mensaje.
- Las condiciones afectan rutas, rastreo, proyectiles, refugio, visibilidad y encuentros solo cuando corresponda.

### 4.5 Motor de comportamiento de personajes

Cada entidad puede tener:
- ficha y personalidad en datos;
- objetivos;
- necesidades;
- conocimiento y recuerdos;
- relaciones;
- agenda;
- ubicación y capacidades;
- reglas de percepción;
- acciones posibles y sus requisitos.

El motor evalúa oportunidades y condiciones, y selecciona acciones válidas. Un personaje puede esperar, rechazar una tarea, cambiar de prioridad, fracasar o no hacer nada relevante. No se fuerza una escena cada cierto tiempo.

### 4.6 Motor de escenas y diálogos

- Diálogos en archivos de datos estructurados, separados del código.
- Condiciones: personaje, ubicación, hora, evento, relación, objeto, conocimiento y estado de misión.
- Opciones que activan resultados y transiciones.
- Reutilización de fragmentos de descripción, pero sin repetir el mismo bloque cuando el contexto exige una variante.
- Las escenas importantes admiten rutas y resultados alternativos.

### 4.7 Motor de PSICHO-Eco

- PSICHO-Eco se define como habilidad del mundo, no como un prompt.
- Se registran origen, modos, requisitos, coste, alcance, duración, riesgo, resistencia y progreso.
- El demonio se registra como entidad origen y compañero asociado al poder.
- Los dos portadores anteriores constan como fallecidos; no se inventan nombres o historias.
- El tercer portador es el protagonista actual.
- Las mejoras se desbloquean por reglas y condiciones verificables, no por decisión espontánea de un modelo.
- Se diferencia activar el poder, mantenerlo, conseguir un efecto, fallar, resistirse, recuperarse y aprender.

## 5. Guardado y arquitectura local

SQLite es una opción adecuada para el estado local inicial, porque el prototipo ya tiene tablas, transacciones, snapshots y mecanismos de backup. El juego deberá almacenar:
- partida, mundo y versión del contenido;
- ubicación, hora exacta y clima regional;
- entidades, estados, necesidades y relaciones;
- inventario y recursos;
- eventos, testigos, conocimiento y rumores;
- misiones y objetivos;
- agendas y actividades pendientes;
- uso, progresión y estado de poderes;
- semilla y secuencia de aleatoriedad;
- estado de escenas y diálogos;
- snapshots, undo y datos de backup.

Las copias deben ser restaurables y versionadas. Cada campaña debe seguir funcionando aunque el programa se cierre, Windows se reinicie o una actualización falle.

No almacenar el único guardado de la partida dentro de archivos de caché ni depender de un servicio en la nube.

## 6. Contenido separado de reglas

Separar tres capas:
1. **Motor:** reglas genéricas reutilizables y código.
2. **Datos del mundo:** bosque, regiones, criaturas, clima, personajes y objetos.
3. **Contenido narrativo:** escenas, diálogos, rutas, decisiones y finales.

Isekai puede utilizar las funciones genéricas de Word Bot, pero PSICHO-Eco, la entidad demoníaca, el volcán y el Bosque de las Bestias pertenecen a sus datos y contenidos, no a reglas globales del motor.

Esta separación permite desarrollar otro mundo sin heredar las reglas particulares de Isekai.

## 7. Arquitectura de aplicación para PC

Primera versión recomendada:
- aplicación de escritorio local;
- interfaz liviana 2D;
- motor de reglas ejecutado en el mismo equipo;
- archivos de contenido locales;
- base SQLite local;
- recursos visuales PNG/WebP anime 2D;
- controles de guardado, carga, backup y ajustes;
- funcionamiento sin conexión después de instalar el programa.

La tecnología definitiva de empaquetado, motor gráfico y distribución queda por evaluar. No se decide aquí migrar a Godot, Unity, Electron, Tauri u otro framework sin una comparación técnica previa con los requisitos de PC, facilidad de desarrollo y consumo de recursos.

No hacen falta renders 3D, personajes hiperrealistas ni generación de imágenes durante la partida.

## 8. Orden de implementación recomendado

| Orden | Módulo | Objetivo mínimo |
|---:|---|---|
| 1 | Base local y escenas | Iniciar una partida, guardar y cargar una escena preescrita |
| 2 | Acciones y reloj | Hablar, observar, buscar, usar poder y caminar con duraciones locales |
| 3 | Eventos y scheduler | Procesar eventos de hora/día durante acciones largas |
| 4 | Mapa y viajes | Moverse por tramos con distancia/terreno |
| 5 | Clima y ambiente | Clima regional persistente con efectos |
| 6 | Diálogos condicionados | Respuestas escritas por personaje y variables |
| 7 | Comportamiento autónomo | Una entidad decide entre acciones programadas |
| 8 | Grupo de aventureras | Brina, Maelis y Sera con autonomía individual |
| 9 | PSICHO-Eco y demonio | Progresión local verificable del poder |
| 10 | Exploración y ecología | Criaturas, recursos, encuentros y descubrimientos |
| 11 | Campaña completa | Día 1–12, volcán, rutas y cinco finales |
| 12 | Empaquetado de PC | Instalador, configuración, guardados, logs y recuperación |

Cada módulo tendrá pruebas automatizadas y una escena de juego verificable. No desarrollar todos a la vez.

## 9. Qué se puede reutilizar del prototipo Word Bot

Reutilizable con adaptación:
- SQLite y migraciones idempotentes;
- aislamiento de datos por mundo/partida;
- eventos con fuente, testigos y alcance de conocimiento;
- relaciones dirigidas por ejes;
- inventario y libro de recursos;
- snapshots, undo, backups y restauración;
- validador de operaciones e IDs;
- selección contextual de contenido.

No debe considerarse la arquitectura final de Isekai:
- adaptadores OpenAI/Gemini;
- prompts para narrador;
- esquema JSON de respuesta generada por modelo;
- modos manuales para copiar prompts a ChatGPT/Gemini web;
- dependencia de elapsed_minutes devuelto por el narrador.

La lógica temporal debe convertirse a acciones/segmentos locales. La narración pasa a escenas y diálogos locales.

## 10. Consecuencias y costes de la decisión

Ventajas:
- funciona sin Internet ni APIs;
- sin coste por mensaje o tokens;
- comportamiento repetible y depurable;
- continuidad controlada por reglas locales;
- privacidad de los guardados en el PC;
- posibilidad de diseñar una experiencia de juego más consistente.

Costes:
- hay que escribir los diálogos, escenas y variantes;
- la cantidad de contenido disponible depende del trabajo autoral;
- los NPC solo pueden realizar acciones que el motor y sus datos contemplen;
- crear herramientas de edición de escenas, reglas, mapas y personajes será parte del proyecto;
- la primera versión puede tener menos libertad de diálogo que una experiencia generativa, pero tendrá respuestas escritas coherentes y estados verificables.

La prioridad debe ser un juego pequeño con un bucle completo y consistente, no un mundo enorme sin contenido jugable.

## 11. Pruebas de aceptación

1. El juego inicia y continúa una partida sin conexión.
2. La aplicación no realiza llamadas a modelos ni pide claves API.
3. Las escenas y diálogos se cargan desde archivos locales versionados.
4. Una misma partida, semilla, estado y acción produce el mismo resultado.
5. Un NPC solo selecciona acciones cuyas condiciones se cumplen.
6. Un NPC no actúa sobre datos que no conoce.
7. Una conversación usa los nodos de diálogo válidos según relación, lugar y estado.
8. Acciones secuenciales y simultáneas actualizan el reloj correctamente.
9. Un evento interrumpe una acción larga en un límite temporal definido.
10. El clima persiste y afecta el mundo según reglas locales.
11. Las rutas calculan tiempos según su información estructurada.
12. Los guardados sobreviven al cierre y reinicio del programa.
13. Undo y restore recuperan el estado completo sin duplicar efectos.
14. El estado del demonio y la progresión de PSICHO-Eco sobreviven a la restauración.
15. No existe dependencia de un narrador externo para mostrar el siguiente diálogo o resolver una acción.

## 12. Estado y decisiones que siguen pendientes

**Confirmado por el usuario:** la experiencia de Isekai no se basará en IA generativa; será un programa/juego que funciona en PC.

**Recomendación técnica:** lógica de juego local, escenas y diálogos preparados, datos estructurados, reloj por acciones, mapas, clima y comportamiento autónomo programado.

**Pendiente de decisión técnica:** framework de escritorio/gráfico, empaquetado, formato de los archivos de escenas, editor de contenido y distribución.

**Pendiente de implementación:** casi todo el runtime de simulación local. El prototipo actual de Word Bot conserva infraestructura reutilizable, pero todavía está diseñado alrededor de proveedores generativos para narración.

Este documento no modifica código, no integra PRs, no modifica main y no convierte propuestas de mecánica en canon narrativo.
