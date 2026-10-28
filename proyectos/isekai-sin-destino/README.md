# Isekai sin Destino

**Versión propuesta:** v1.9 (encuentros emergentes y registro completo de vínculos; pendiente de probar en SpicyChat)  
**Rama organizada:** `docs/historias-organizadas`  
**Carpeta:** `proyectos/isekai-sin-destino/`

## Archivos
- [Configuración ligera para SpicyChat](CONFIG_LIGERA.md)
- [Cuadro de reglas prioritarias v1.9](CUADRO_REGLAS_PRIORITARIAS.md)
- [Lorebook maestra, 72 entradas](LOREBOOK_MAESTRA.md)
- [JSON de importación de Lorebook](LOREBOOK_IMPORT.json)
- [Solución para historias largas](SOLUCION_HISTORIAS_LARGAS.md)

## Reglas principales
- Reloj en seis bloques de cuatro horas; las charlas breves no hacen avanzar el horario.
- Mini mapa progresivo con estados visitado, ruta conocida, rumor o bloqueado/peligroso. Los sitios desconocidos y Nhal-Seren permanecen ocultos.
- Encuentros variables. No todo conduce a combate: un goblin puede gruñir, bromear, negociar o marcharse. El protagonista elige cómo responder y un encuentro puede ser solo una anécdota.
- Los acompañantes solo reaccionan a encuentros que presenciaron o que alguien les contó. Si se enteran después, reaccionan entonces según su personalidad y creencias, nunca retroactivamente.
- Vínculos no solo románticos: confianza, sospecha, amistad, respeto, rivalidad/hostilidad, resentimiento, miedo, gratitud/deudas, cooperación y atracción si surge. Se registran por pareja y dirección, con discusiones, posturas, disculpas, promesas, favores y conflictos.
- Personalidades diferenciadas para Brina, Ivar, Maelis, Sera y Timo. Ivar es lancero de cabello largo rubio casi blanco, rudo e irónico; el objeto de su odio sigue pendiente.
- Eco/hipnosis se registra por objetivo, con intento, resultado, efecto y usos restantes.
- Comandos personalizados por instrucciones: `/mapa`, `/ruta`, `/estado`, `/vinculos`, `/guardar` y `/continuar`.
- Guardado externo recomendado cada 8–10 intercambios y tras cambios importantes.

## Validación
- JSON de importación sintácticamente válido.
- Personality debe quedar bajo 5.000 caracteres.
- Los cambios de GitHub no se instalan automáticamente; falta probar configuración y Lorebook dentro de SpicyChat.
