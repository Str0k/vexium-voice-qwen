# Estado de desarrollo

Actualizado el 11 de septiembre de 2026.

Este es el repositorio público Qwen de Vexium Voice. No representa ni modifica las
otras instalaciones de Vexium. Los documentos del hackathon de julio son históricos;
el README actual no promete disponibilidad de aquel demo.

## Base técnica

- Dependencias reproducibles mediante `uv.lock` y `web/package-lock.json`.
- CI con Python 3.12/3.13 en Linux, Python 3.12 en Windows y frontend con Node 24.
- Validación de entradas HTTP y manejo del cierre de ambos extremos del puente de voz.
- Pruebas de navegador para modo texto, cambio de tenant y movimiento reducido.
- README, CONTRIBUTING y arquitectura describen comportamiento y límites comprobables.

## Próximo trabajo

Consulta `docs/ARCHITECTURE.md`. Quedan necesidades concretas de zonas horarias,
control de acceso, concurrencia de recordatorios y pruebas adicionales de voz.
La suite usa simulaciones: no demuestra llamadas, cobros ni SMS reales.

## Verificación

Usa los comandos de AGENTS.md y CONTRIBUTING.md. No repitas conteos históricos de
pruebas ni afirmaciones de rendimiento; consulta la ejecución más reciente.
