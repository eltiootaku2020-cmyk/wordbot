# 14 — Mundo abierto, grupo, progresión, magia y PSICHO

**Estado:** dirección de diseño aprobada; todavía no es subsistema ejecutable.

## Mundo abierto y novela visual
La experiencia combina escenas, retratos, diálogos, decisiones clave, rutas y finales con exploración libre. El mapa es un grafo de regiones, subzonas, caminos, aldeas, tiendas, cuevas, ruinas y puntos de interés. Los acontecimientos forman un grafo causal conectado: acciones, hallazgos, accidentes, decisiones, condiciones y consecuencias. Las rutas pueden converger, pero conservan diferencias de tiempo, objetos, conocimiento, heridas y relaciones. No existe un camino correcto protegido por el guion.

La interfaz futura tendrá fondo PNG, sprites/retratos y expresiones, caja de diálogo, tres acciones sugeridas y acción libre. Paneles: explorar, examinar/buscar, interactuar, grupo, inventario, mapa, objetivos/diario y PSICHO. El jugador puede intentar acciones no previstas.

## Personajes y especialidades
Distinguir profesión/ocupación, clase/rol, especialidad, atributo, habilidad aprendida y poder único. Fichas incluyen identidad, especie, edad adulta cuando corresponda, atributos, habilidades, equipo, heridas, necesidades, personalidad, objetivos, relaciones, conocimientos, agenda y autonomía.

Familias de especialidades: combate, exploración, supervivencia, oficios, conocimiento, social y magia/poderes únicos. Una aventurera y una campesina no tienen capacidades equivalentes por cambiar una etiqueta; cada una puede ganar, fallar, huir, perderse, resultar herida o morir según sus capacidades y el peligro.

## Grupos y órdenes
Distinguir compañero voluntario, aliado temporal, contratado, miembro de organización y objetivo bajo PSICHO. Un objetivo dominado no es amigo ni compañero voluntario. Los integrantes conservan autonomía y pueden negarse, fallar, marcharse o actuar por iniciativa propia.

Órdenes posibles: explorar, buscar, rastrear, vigilar, recolectar, atacar, defender, cubrir, evadir, retirarse, asistir, entrenar, comprar, reparar y regresar. Resolver según especialidad, atributos, equipo, salud, miedo, voluntad, terreno, oposición y contexto.

## Gremios y aprendizaje
Gremios registran aventureros y encargos; el rango no es fuerza absoluta. Se puede aprender mediante tiendas, libros, maestros, compañeros, gremios, academias, favores, contratos, observación, práctica y descubrimientos. La enseñanza depende del conocimiento y disponibilidad del maestro; tiempo, confianza, afecto cuando corresponda, pago, favor y materiales pueden influir. No hay dominio instantáneo.

## Magia y progresión
Separar hechizos aprendidos, habilidades especiales, poderes únicos y PSICHO-Eco. Escuelas originales propuestas: elemental, curativa, defensiva, ofensiva, ilusoria/sensorial, espiritual, ritual, invocación, alquímica y prohibida. Cada poder tiene requisitos, afinidad, coste, alcance, preparación, duración, resistencia, riesgos y fuente de aprendizaje. Las referencias a DanMachi, Code Geass, Re:Zero, Overlord, Slime y KonoSuba inspiran mecánicas generales; no copiar personajes, nombres, hechizos ni organizaciones.

## PSICHO-Eco
Panel propio separado de las acciones normales. Ramas de diseño: eco/información, influencia, memoria, percepción, control limitado, intervención biológica ficticia y autointervención. Permite intentar leer sensaciones de un árbol, influir en asociaciones de un animal, imponer órdenes limitadas o experimentar con una semilla mágica. No garantiza éxito, no equivale a control absoluto y no borra las necesidades, instintos ni personalidad del objetivo.

Interferir con funciones motoras/vitales o modificar la biología mediante PSICHO son efectos sobrenaturales ficticios de alto riesgo, no instrucciones científicas o médicas. Resistencia, compatibilidad, coste, duración, alcance y límites por tipo de objetivo quedan pendientes. Un objetivo dominado no adquiere amistad, confianza, lealtad ni consentimiento. Una acción incompatible con la especie puede fallar.

## Accidentes, personalidad, comedia y ecchi
Accidentes cotidianos, mágicos, sociales y de aventura pueden surgir por contexto: tropiezos, objetos caídos, hechizos fallidos, malentendidos, encuentros inoportunos, trampas o desvíos. No deben forzarse por cuota; cada accidente necesita causa y registro.

Los arquetipos anime (tsundere, kuudere, genki, dandere y otros) son ingredientes, no scripts rígidos. Personajes mantienen rasgos, objetivos, miedos, contradicciones y autonomía.

Romance y ecchi son opcionales y contextuales. Escenas adultas requieren personajes adultos, consentimiento explícito y advertencia previa con ubicación y presentes. Una escena adulta pública se bloquea o avisa antes de generarse. PSICHO, miedo, obediencia o atracción inducida no equivalen a consentimiento sexual. La diosa chibi no participa en contenido adulto.

## Relaciones y consecuencias
El runtime ya tiene relaciones dirigidas con diez ejes: confianza, sospecha, amistad, respeto, rivalidad, resentimiento, miedo, gratitud/deuda, cooperación y atracción; también impresiones descriptivas. Honor y reputación pública localizada aún son diseño pendiente. Reputación necesita testigos, evidencia y canales de difusión plausibles; un personaje ausente no sabe un hecho sin recibir información.

## Estado técnico
Existe parcialmente: entidades/perfiles, relaciones dirigidas, inventario, recursos, presencia, movimientos, eventos, usos genéricos de poder, contexto selectivo, prompt manual, snapshots/undo y cronología fija mundial en rama de PR #21.

No existe todavía como sistema completo: atributos, profesiones, especialidades, progreso, grupos/órdenes, combate, gremios, enseñanza, mapa explorable, simulación ecológica, escuelas mágicas, PSICHO avanzado, accidentes emergentes, UI de novela visual y rutas/finales ejecutables.
