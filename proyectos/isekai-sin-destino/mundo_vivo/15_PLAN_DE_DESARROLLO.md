# 15 — Plan de desarrollo

1. **Canon de campaña:** registrar nuevo origen, pertenencias, diosa y PSICHO-Eco; reconciliar comienzo anterior sin celular. Conservar bosque, ecología, viajes, reputación, rutas y ancla del Día 12 donde no haya contradicción.
2. **Personajes:** atributos, profesiones, clases/roles, especialidades, habilidades, estado físico, personalidad, agenda, conocimientos.
3. **Grupos:** reclutamiento, aliados, contratos, órdenes, autonomía y expediciones.
4. **Mundo abierto:** grafo de lugares/conexiones, búsqueda, objetos, encuentros, rutas, viajes y acciones de PNJ fuera de escena.
5. **Gremios y aprendizaje:** contratos, rangos, tiendas, maestros, favores, práctica y progresión.
6. **Magia y PSICHO:** escuelas, afinidades, recursos, panel, objetivos, resistencia, experimentos y límites.
7. **Novela visual:** UI ligera, fondos y retratos PNG, diálogos, opciones sugeridas y acciones libres, mapa y diario.
8. **Acontecimientos y rutas:** accidentes, banderas, condiciones, escenas reutilizables, rutas personales/facciones y cinco finales emergentes.
9. **Validación:** pruebas automatizadas, campaña larga manual con ChatGPT/Gemini, Windows/Chromium, undo/backup/restore y continuidad.

La implementación debe preservar SQLite como fuente de verdad y mantener Isekai como configuración de mundo, no como reglas hardcodeadas en el motor genérico. Cada fase requiere criterios de aceptación y pruebas antes de marcarse como terminada.

**No está implementado aún:** ficha numérica de personajes, profesiones/especialidades, grupo y órdenes, combate, gremios, aprendizaje, mapa explorable, ecología, magia completa, PSICHO avanzado, UI de novela visual, accidentes emergentes y rutas/finales ejecutables.

La nueva rama es dependiente de PR #21; no integra PR #21 ni modifica main. No sincronizar automáticamente con la Lorebook de SpicyChat, que conserva un comienzo anterior incompatible.


## Reconciliación prioritaria — antes de implementar la campaña

- Conectar el accidente del supermercado, el encuentro divino y la entrega de PSICHO-Eco con la llegada física al claro del Bosque de los Siete Ecos.
- Conservar celular, ropa normal y caja/figura de Goku; no restaurar el inventario pobre anterior sin confirmar los objetos.
- Conservar el reparto existente de Brina, Ivar, Maelis, Sera y Timo. La composición simultánea de cinco o tres sigue siendo un conflicto documental.
- Mantener la Maelis existente como maga; el ejemplo de campesina fue conceptual.
- Reconciliar la antigua regla de tres intentos de Eco con el PSICHO-Eco evolutivo antes de fijar el balance.
- No actualizar Lorebook maestra/JSON de SpicyChat hasta terminar esa reconciliación y ejecutar auditorías de contenido.

Documento de continuidad: 16_PUENTE_PROLOGO_GRUPO_Y_CONTINUIDAD.md.
