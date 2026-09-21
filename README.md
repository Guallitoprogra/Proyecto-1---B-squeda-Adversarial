# Proyecto 1 - Búsqueda Adversarial

Implementación de Hoppers en Python. El objetivo final es construir un agente
con Minimax, poda alfa-beta, profundidad configurable y un máximo de 30 segundos
por jugada.

## Avance actual

El proyecto incluye el motor del juego, un agente Minimax con poda alfa-beta,
consola y una ventana para jugar con el mouse. El informe está en `INFORME.md`.

El trabajo está dividido en cuatro avances:

| Parte | Commit | Contenido |
| --- | --- | --- |
| 1 | Agregar reglas y movimientos de Hoppers | Estado, movimientos, saltos, victoria y pruebas |
| 1 | Agregar consola y guía del juego | Partida manual e instrucciones |
| 2 | Agregar agente Minimax | Poda alfa-beta, heurística, profundidad y control del tiempo |
| 2 | Agregar modos de juego e informe | Humano contra agente, agente contra agente y resultados |

## Ejecutar

Se necesita Python 3.10 o posterior. No hay paquetes externos que instalar.
Desde la carpeta del proyecto:

```bash
python gui.py
```

En la ventana, selecciona una ficha y después un destino verde. Puedes elegir
humano contra agente, agente contra agente o humano contra humano. La profundidad,
el tiempo y tu jugador se aplican al pulsar **Nueva partida**. El valor inicial es
profundidad 3 y 2 segundos por decisión. El tiempo configurable no puede superar 30.
Tkinter viene con la instalación habitual de Python para Windows; en Linux puede
requerir el paquete `python3-tk` del sistema.

También puedes jugar por consola:

```bash
python main.py --mode humano-agente --depth 3 --seconds 2 --human 1
python main.py --mode agente-agente --depth 2 --seconds 1
python main.py --mode humano-humano
```

Se escribe una jugada con cuatro números: fila y columna de origen, seguidas
por fila y columna de destino. Las coordenadas van de 0 a 9.
Por ejemplo, `0 3 0 5` es un salto legal del jugador 1 al empezar.

- `ayuda` muestra todas las jugadas legales del turno.
- `salir` termina la sesión.
- Un dato incorrecto muestra un mensaje y permite intentarlo de nuevo.

Para ejecutar las pruebas:

```bash
python -m unittest discover -s tests -v
```

## Reglas utilizadas

- Tablero de 10 × 10 con 15 fichas por jugador.
- P1 empieza arriba a la izquierda y P2 abajo a la derecha.
- Un paso mueve una ficha a una casilla vecina vacía, incluso en diagonal.
- Un salto pasa sobre una ficha vecina propia o rival y aterriza en la casilla
  vacía inmediatamente posterior, en la misma dirección.
- Se pueden encadenar saltos con la misma ficha y cambiar de dirección.
  El jugador puede detenerse después de cualquier salto.
- No se capturan fichas y no se mezclan pasos con saltos en un mismo turno.
- Las mismas reglas de movimiento se aplican dentro de los campamentos.
- Gana quien llena las 15 casillas del campamento contrario con sus fichas.

El material incluye una regla opcional contra el bloqueo de un campamento con
fichas propias. Esta versión usa la condición normal de victoria y no activa esa
variante. Tampoco añade restricciones para salir del campamento de destino.
Para cerrar partidas que no progresan, la sesión declara tablas en la tercera
repetición del mismo tablero y turno, al llegar a 600 jugadas individuales o si
no hay acciones legales. Estas son convenciones de la aplicación, adicionales
al material del curso; no cambian las reglas de movimiento ni `terminal(state)`,
que identifica victorias. El historial de la sesión permite al agente reconocer
una tercera repetición durante la búsqueda. `salir` solo interrumpe la sesión.

## Organización del código

- `hoppers.py`: funciones del juego, sin entrada por teclado ni lógica de agentes.
- `main.py`: visualización del tablero y lectura de jugadas.
- `agent.py`: evaluación, Minimax, poda y manejo del tiempo.
- `game.py`: turnos, historial y cierre de una sesión.
- `gui.py`: ventana con tablero interactivo.
- `comprobar_partida.py`: partida automática con un resumen de tiempos.
- `tests/`: pruebas de reglas, agente, consola y cierre de partidas.

`State` guarda un tablero de tuplas y el jugador en turno. Las tuplas evitan
modificaciones accidentales cuando el agente explora distintas jugadas.

| Función | Responsabilidad |
| --- | --- |
| `initial_state()` | Crear el tablero inicial |
| `player(state)` | Indicar quién mueve |
| `actions(state)` | Devolver el conjunto de jugadas legales |
| `result(state, action)` | Validar la jugada y crear un estado nuevo |
| `terminal(state)` | Comprobar si alguien ganó |
| `winner(state)` | Devolver 1, 2 o `None` |
| `utility(state)` | Devolver +1 para victoria de P1, -1 para P2 y 0 en estados sin ganador |

Una acción tiene la forma `((fila_origen, columna_origen), (fila_destino,
columna_destino))`. Si varias cadenas de saltos llevan al mismo destino,
se guarda una sola acción: todas dejan exactamente el mismo tablero porque
no hay capturas. Los destinos intermedios también se incluyen como opciones.

## Apuntes para explicar la primera parte

1. El estado inicial coloca las fichas de P1 donde `fila + columna <= 4`.
   El campamento de P2 es el reflejo de esas coordenadas.
2. Los pasos se revisan con ocho pares de cambios de fila y columna.
3. Para los saltos se recorre una lista de posiciones pendientes. Cada destino
   descubierto puede ser el inicio de otro salto. El conjunto de visitados
   evita ciclos y trabajo repetido. La casilla de origen se considera vacía
   al comprobar las fichas que sirven de apoyo.
4. `result` copia el tablero antes de mover. Así una rama de búsqueda no
   modifica las demás dentro de Minimax. La búsqueda usa `apply_action` para
   acciones que ya obtuvo de `actions`, evitando validarlas de nuevo en cada nodo.
5. La utilidad usa siempre la perspectiva de P1. Minimax mantiene esa convención:
   P1 maximiza y P2 minimiza.

Las pruebas cubren el tablero inicial, bordes, pasos, saltos diagonales,
cadenas que cambian de dirección, ciclos, jugadas inválidas, cambio de turno,
conservación del estado anterior y las condiciones de victoria.

## Usar el agente desde otro programa

```python
from agent import choose_action
from hoppers import initial_state, result

state = initial_state()
move = choose_action(state, depth=3, time_limit=2)
state = result(state, move)
```

`choose_action` devuelve una acción legal en estados válidos con movimientos
disponibles. Devuelve `None` en estados terminales o sin movimientos. El evaluador
supone las 15 fichas de cada jugador, que se conservan durante una partida legal.

Para comprobar una partida completa sin imprimir todos los tableros:

```bash
python comprobar_partida.py --depth 1 --seconds 0.15
```
