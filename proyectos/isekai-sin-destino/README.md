# Isekai sin Destino

**Revisión:** v1.19 — porcentajes trazables, registro cerrado, diálogo proactivo y Lorebook auditada.  
**Estado:** validación estática en GitHub; importación y roleplay real aún deben probarse en SpicyChat.  
**Rama:** docs/historias-organizadas · Lorebook: 77 entradas con UID único.

## Módulo ampliado de mundo vivo
- [Mundo vivo: reglas, variables, 50 especies, Psico-Eco, exploración, magia, rutas y comandos](mundo_vivo/README.md). Diseño modular nuevo; propuestas aún pendientes de aprobación y sin integración ejecutable.

## Archivos
- [Configuración ligera](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias](CUADRO_REGLAS_PRIORITARIAS.md)
- [Registro interno y esquema cerrado](REGISTRO_INTERNO_ESQUEMA.md)
- [Lorebook maestra](LOREBOOK_MAESTRA.md)
- [JSON de importación](LOREBOOK_IMPORT.json)
- [Investigación aplicada](INVESTIGACION_DIALOGO_MEMORIA_Y_ECO_VEGETAL.md)
- [Solución para historias largas](SOLUCION_HISTORIAS_LARGAS.md)
- [Script de auditoría automática](tools/audit_lorebook.py) · [Workflow de GitHub Actions](../../.github/workflows/isekai-lorebook-audit.yml)

## Cambios v1.19
- Reloj en seis bloques de cuatro horas; eliminados ejemplos de cabecera a 08:03 y 08:15.
- PNJ cercanos intervienen por iniciativa propia cada 1–2 respuestas si hay motivo. Ivar puede suspirar o hablar desde delante del grupo; no hay palabras sueltas ni frases cortadas.
- Reacciones/emociones son generadas por la IA según personalidad y contexto; el registro conserva hechos, causas y efectos persistentes. Un PNJ solo sabe lo que vio o le contaron.
- Porcentajes independientes 0–100, no probabilidad: Δ positivo = sube, negativo = baja, cero = sin cambio por ese hecho. No registrado no equivale a 0, 50 ni neutralidad.
- Objetos, criaturas y órdenes quedan separados. Una criatura ordenada a esperar o volver al bosque conserva última ubicación, orden/destino y cumplimiento desconocido hasta confirmación.
- Eco vegetal: sensación interna vinculada a recuerdos de árboles; mecanismo, alcance, coste, duración y contador quedan por confirmar.
- Inventario inicial: ropa corriente, pañuelo gastado, bolsita vacía y cordel corto. Catálogo común = posibilidades, no regalos. Sin historial de comidas.
- Guardado recomendado cada 5–7 intercambios y tras cambios importantes; varias partes en Free no equivalen a almacenamiento externo.
- JSON: 77 entradas, contenido bajo 1.000 caracteres, UID únicos y keywords sin duplicados.
- Auditoría automática aprobada: 653 comprobaciones, incluido el cotejo entre Lorebook maestra y JSON. [Ver ejecución de GitHub Actions](https://github.com/eltiootaku2020-cmyk/wordbot/actions/runs/40935111216).

## Límites reales
El contexto gratuito comparte 4.096 tokens entre definición, instrucciones y conversación; cada respuesta tiene hasta 180 tokens según la documentación consultada. El registro «interno» no es una base de datos oculta. Los datos pueden perderse al salir del contexto; guarda una copia de /guardar fuera de SpicyChat. Fuentes: [contexto](https://support.spicychat.ai/support/solutions/articles/153000260636-why-characters-forget-things-tokens-and-context-) · [Lorebook](https://support.spicychat.ai/support/solutions/articles/153000260673-lorebooks).

## Validación
El script y GitHub Actions se usarán para verificar conteo de entradas, longitud, UID/keywords, campos y ejemplos horarios. La importación y el comportamiento real aún requieren prueba manual; los cambios de GitHub no se instalan automáticamente.
