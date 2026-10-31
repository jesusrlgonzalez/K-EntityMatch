# EntityMatch · Resolución de identidad empresarial y relaciones

**Mejorar la calidad de información de empresas y contrapartes mediante la identificación de posibles duplicados, alias y relaciones documentadas.**

## Qué resuelve
Normalizar registros, comparar identificadores, evaluar similitud de nombres y explorar relaciones mediante grafos, conservando evidencia de cada propuesta de vinculación.

Resolución de entidades: normaliza nombres y alias, genera pares candidatos, puntúa similitud y representa relaciones en grafo, separando recuperación de candidatos y decisión de vínculo.

## Hacia dónde va
Ser una herramienta de referencia para vinculación auditable de entidades dentro de procesos de gobierno de datos, cumplimiento y administración de proveedores.

**Objetivo:** Desarrollar y validar algoritmos de coincidencia que aumenten la recuperación de candidatos legítimos, controlen falsos vínculos y permitan revisión humana de casos ambiguos.

**Valor que persigue:** Mejorar la calidad de registros maestros y reducir errores derivados de identidades duplicadas o inconsistentes.

## Resultados de la demo
Sobre un conjunto de datos sintéticos diseñado con errores y casos difíciles: **640 clientes, 620 registros y 180 entradas de lista sintética: 9 075 pares candidatos, 591 registros válidos, 14 a revisión, 35 en cuarentena**.

## Pruébalo en 2 minutos
```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py test     # 54 tests automatizados
python run.py demo     # demo de punta a punta → demo_output/
python run.py api      # API REST → http://127.0.0.1:8000/docs
```

## Diseñado para decisiones responsables
- **Siempre con una persona al mando:** no determina identidad legal ni certifica sanciones; los vínculos requieren revisión humana.
- **Trazable:** cada registro conserva su motivo de aceptación, revisión o cuarentena.
- **Probado:** 54 tests automatizados en Linux y Windows en cada cambio.
- **Contenedor:** la imagen Docker se construye en cada cambio.
- **Windows:** la suite tiene un caso conocido pendiente de corrección; en Linux pasa completa.

## Estado
Prototipo funcional demostrado con datos sintéticos. El siguiente paso es un **piloto con datos reales** de su organización, bajo acuerdo de uso y confidencialidad.

**¿Le interesa un piloto?** Contacte a **Kriter Systems**.

---
I24 · Kriter Systems · Los datos incluidos son sintéticos y no representan a personas ni empresas reales.
