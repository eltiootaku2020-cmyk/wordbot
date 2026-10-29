# Isekai sin Destino

**Revisión:** v1.18 — configuración, esquema cerrado y Lorebook auditados.  
**Estado:** validación estática en GitHub; la importación y el roleplay real aún deben probarse en SpicyChat.  
**Rama:** `docs/historias-organizadas` · **Lorebook:** 77 entradas con UID único (los UID no tienen que ser consecutivos).

## Archivos
- [Configuración ligera](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias](CUADRO_REGLAS_PRIORITARIAS.md)
- [Registro interno y esquema cerrado](REGISTRO_INTERNO_ESQUEMA.md)
- [Lorebook maestra](LOREBOOK_MAESTRA.md)
- [JSON de importación](LOREBOOK_IMPORT.json)
- [Investigación aplicada](INVESTIGACION_DIALOGO_MEMORIA_Y_ECO_VEGETAL.md)
- [Solución para historias largas](SOLUCION_HISTORIAS_LARGAS.md)

## Correcciones v1.18
- Personality: 4344 caracteres (aprox. 1086 tokens orientativos); bajo 5.000 y cerca de la recomendación oficial de 800–1.100 tokens.
- JSON con 77 entradas; cada Content <1.000 caracteres como margen conservador (máximo oficial actual publicado: 2.000).
- Eliminada la keyword duplicada `uso de Eco`.
- Δ = diferencia en puntos porcentuales: 20%→30% = +10 puntos. Δ0 es sin cambio por ese hecho; No registrado no equivale a 0%.
- Inventario inicial unificado: ropa corriente, pañuelo gastado, bolsita vacía y cordel corto; sin dinero, comida, agua, armas ni mochila.
- Estado cerrado: no inventar campos, no registrar historial de comidas ni asumir obediencia sin confirmación.
- Guardado cada 5–7 intercambios y tras cambios importantes; en Free se divide en partes por el máximo de 180 tokens por respuesta.

## Contexto y Lorebook
- Free: 4.096 tokens de contexto compartidos; máximo 180 tokens por respuesta.
- Lorebook activa: aproximadamente 740 tokens. Keywords se buscan en los últimos cuatro mensajes; una keyword duplicada puede cargar varias entradas.
- El estado «interno» no es base de datos oculta; copia `/guardar` fuera del chat.

## Validación
- JSON parseable: 77 entradas, UID únicos, cada Content <1.000 caracteres y keywords sin duplicados exactos.
- Personality: 4.344 caracteres; Scenario: 795; Greeting: 687; Example Dialogue: 1.044 caracteres.
- La CI aprobó el test del preset, el conteo de 77 entradas y las comprobaciones de longitud/keywords: [ver ejecución](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40930336007).
- Pendiente: importar en la cuenta real de SpicyChat y comprobar la continuidad de una partida; GitHub no instala la configuración automáticamente.
