# Isekai sin Destino

**Versión propuesta:** v1.10 (registro interno de esquema cerrado; pendiente de probar en SpicyChat)  
**Rama organizada:** `docs/historias-organizadas`  
**Carpeta:** `proyectos/isekai-sin-destino/`

## Archivos
- [Configuración ligera para SpicyChat](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias v1.10](CUADRO_REGLAS_PRIORITARIAS.md)
- [Registro interno y esquema cerrado](REGISTRO_INTERNO_ESQUEMA.md)
- [Lorebook maestra, 73 entradas](LOREBOOK_MAESTRA.md)
- [JSON de importación de Lorebook](LOREBOOK_IMPORT.json)
- [Solución para historias largas](SOLUCION_HISTORIAS_LARGAS.md)

## Registro interno v1.10
- Campos fijos para estado de partida y fichas de personajes/criaturas relevantes.
- Habilidades demostradas, intereses/objetivos declarados u observados, sospechas con evidencia, conocimiento con fuente y vínculos por pareja/dirección.
- Datos ausentes = «No registrado». No inventar valores ni crear campos nuevos.
- No existe campo «qué comió»; cambios de provisiones se reflejan solo en inventario.
- El registro permanece discreto mientras el contexto lo permita; `/estado`, `/vinculos` y `/guardar` lo muestran cuando se solicita.
- Un guardado copiable cada 8–10 intercambios y tras eventos importantes sigue siendo necesario: SpicyChat no ofrece una base de datos externa mediante instrucciones.

## Reglas de juego
- Reloj en seis bloques de cuatro horas y mapa textual progresivo.
- Encuentros abiertos: una criatura no conduce automáticamente a combate; los PNJ solo reaccionan a hechos presenciados o contados.
- Relaciones no solo románticas: confianza, sospecha, amistad, respeto, rivalidad, resentimiento, miedo, gratitud/deudas y cooperación.
- Los cambios de GitHub no se instalan automáticamente; falta probar la configuración y Lorebook en SpicyChat.

## Validación
- JSON de importación sintácticamente válido.
- Personality bajo 5.000 caracteres.
- Prueba real pendiente en SpicyChat.
