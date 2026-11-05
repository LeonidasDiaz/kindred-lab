# Migración del archivo manual de objetos (parche 16.15.1)

De `referencia/objetos_16.15.1_manual.json` (original sin cambios) a `reglas/objetos_mecanicas.json`.

- Objetos: 214, 157 con mecánicas.
- Descripciones editadas a mano, conservadas como `descripcion_manual`: 58.
- Todas las mecánicas quedan con `parche_verificado` = el del archivo manual.

## Objetos que no coinciden con Data Dragon 16.15.1 (10)

Manda Data Dragon: el valor del archivo manual se queda solo en `referencia/`.

| id | Objeto | Estadística | Manual | Data Dragon |
|---|---|---|---|---|
| 1086 | Arco de Doran | AD_plano | 6 | 8 |
| 1120 | Casco de Doran | Armadura_plana | 10 | 8 |
| 1120 | Casco de Doran | Resist_Magica_plana | 10 | 8 |
| 1120 | Casco de Doran | Vida_maxima_plana | 110 | 150 |
| 3032 | Flechas Salvajes de Yun Tal | Vel_Ataque | 0.4 | 0.45 |
| 3087 | Daga de Statikk | AD_plano | 40 | 45 |
| 3100 | Maldición del Liche | Vel_Movimiento_Porcentual | 0.04 | 0.06 |
| 3114 | Ídolo Prohibido | Poder_Curaciones_Escudos_Porcentual | – | 0.08 |
| 3114 | Ídolo Prohibido | Regen_Mana_Básica_Porcentual | – | 0.5 |
| 3152 | Cinturón Cohete Hextech | AP_plano | 70 | 60 |
| 3152 | Cinturón Cohete Hextech | Vida_maxima_plana | 300 | 350 |
| 3177 | Espada del Guardián | Aceleracion_de_habilidad_plana | – | 15 |
| 3190 | Relicario de los Solari de Hierro | Armadura_plana | 25 | 30 |
| 3190 | Relicario de los Solari de Hierro | Resist_Magica_plana | 25 | 30 |
| 4005 | Mandato Imperial | Aceleracion_de_habilidad_plana | 20 | 15 |
| 4005 | Mandato Imperial | Regen_Mana_Básica_Porcentual | 1.25 | 1.5 |

## Nombres unificados

| Antes | Ahora | Usos |
|---|---|---|
| `AD` | `AD_plano` | 2 |
| `Aceleracion_Habilidad_Definitiva` | `Aceleracion_Habilidad_Definitiva_plana` | 2 |
| `Armadura` | `Armadura_plana` | 1 |
| `Omnivampirismo_porcentual` | `Omnivampirismo_Porcentual` | 1 |
| `Prob_Critico_Porcentual` | `Prob_Critico` | 1 |
| `Regen_Vida_Basica_Porcentual` | `Regen_Vida_Básica_Porcentual` | 1 |
| `Robo_Vida` | `Robo_Vida_Porcentual` | 1 |
| `Vel_Ataque_Porcentual` | `Vel_Ataque` | 8 |
| `Vel_Movimiento_Plana` | `Vel_Movimiento_plana` | 2 |
| `Vida` | `Vida_maxima_plana` | 2 |
| `mana_maximo_plano` | `Mana_maximo_plano` | 5 |

## Sin descripción en Data Dragon 16.15.1

Data Dragon no dice nada de estos objetos: se conserva el valor manual de `referencia/`.

- 3865 Mapamundi
