# Proyecto 1 - Búsqueda Adversarial

Implementación de Hoppers en Python. El objetivo final es construir un agente
con Minimax, poda alfa-beta, profundidad configurable y un máximo de 30 segundos
por jugada.

## Avance actual

La primera parte contiene el motor del juego y una consola para dos personas.
Todavía no incluye un agente inteligente.

El trabajo está dividido en cuatro avances:

| Parte | Commit | Contenido |
| --- | --- | --- |
| 1 | Agregar reglas y movimientos de Hoppers | Estado, movimientos, saltos, victoria y pruebas |
| 1 | Agregar consola y guía del juego | Partida manual e instrucciones |
| 2 (pendiente) | Agregar agente Minimax | Poda alfa-beta, heurística, profundidad y control del tiempo |
| 2 (pendiente) | Agregar modos de juego e informe | Humano contra agente, agente contra agente y resultados |

## Ejecutar

Se necesita Python 3.10 o posterior. No hay paquetes externos que instalar.
Desde la carpeta del proyecto:

```bash
python main.py
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
No se define un empate automático por repetición; dos personas pueden repetir
movimientos. `salir` interrumpe la sesión, no cuenta como victoria ni empate.

## Organización del código

- `hoppers.py`: funciones del juego, sin entrada por teclado ni lógica de agentes.
- `main.py`: visualización del tablero y lectura de jugadas.
- `tests/test_hoppers.py`: pruebas de las reglas.

`State` guarda un tablero de tuplas y el jugador en turno. Las tuplas evitan
modificaciones accidentales cuando el futuro agente explore distintas jugadas.

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
   modifica las demás cuando se implemente Minimax.
5. La utilidad usa siempre la perspectiva de P1. En la segunda parte habrá que
   mantener esa convención en los turnos maximizadores y minimizadores.

Las pruebas cubren el tablero inicial, bordes, pasos, saltos diagonales,
cadenas que cambian de dirección, ciclos, jugadas inválidas, cambio de turno,
conservación del estado anterior y las condiciones de victoria.
