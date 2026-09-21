# Informe: Hoppers y búsqueda adversarial

## Representación y reglas

El tablero tiene 10 filas y 10 columnas. Cada casilla contiene 0 si está vacía,
1 si pertenece a P1 y 2 si pertenece a P2. El estado guarda ese tablero y el turno.
Cada jugador empieza con 15 fichas en un campamento triangular. El objetivo es
ocupar completamente el campamento contrario con las propias fichas.

Las acciones se representan con origen y destino. Se permiten pasos a cualquiera
de las ocho casillas vecinas, saltos sobre fichas de ambos jugadores y cadenas
de saltos. No hay capturas. Si dos cadenas terminan en la misma casilla, producen
el mismo estado y se guardan como una sola acción.

## Minimax y poda alfa-beta

P1 maximiza la evaluación y P2 la minimiza. Por cada acción se genera una copia
del estado y se estudia la mejor respuesta del rival. No se modifica el tablero
real durante la búsqueda.

Alfa guarda la mejor puntuación que ya puede conseguir el maximizador y beta
la mejor que puede asegurar el minimizador. Cuando `alpha >= beta`, las acciones
restantes de esa rama no pueden mejorar la decisión que ya está disponible y
se dejan de explorar. La poda no cambia el resultado de Minimax para una misma
profundidad completa y la misma evaluación.

Las acciones se ordenan para explorar primero la mejor de la iteración anterior,
las que entran al campamento y las que avanzan. Esto ayuda a podar antes, pero
no elimina jugadas legales de la búsqueda.

## Heurística

Para cada jugador se calcula:

`puntuación = 30 × fichas_en_meta - 10 × distancia_total_asignada`

La evaluación del tablero es `puntuación_P1 - puntuación_P2`. Un resultado
positivo favorece a P1; uno negativo favorece a P2. Los pesos son una elección
manual para premiar llegar y reducir el recorrido pendiente; no fueron aprendidos
de datos ni ajustados mediante un torneo.

La distancia entre una ficha `(r, c)` y una meta `(tr, tc)` es
`max(abs(r - tr), abs(c - tc))`, llamada distancia de Chebyshev. Cuenta cuántos
pasos se necesitarían en un tablero libre cuando se permite mover en diagonal.
No es una predicción exacta de turnos: los saltos pueden acortar el recorrido y
otras fichas pueden bloquearlo.

Cada ficha se asigna a una meta distinta. Se busca la asignación de menor costo
con el algoritmo húngaro, implementado en `assignment_distance`. Sin esta
asignación, varias fichas podrían considerarse cerca de la misma casilla y el
agente no distinguiría bien los huecos pendientes. Este algoritmo cuesta O(n³),
con n = 15. Se guardan hasta 30 000 evaluaciones parciales de equipos en caché
para no recalcular posiciones de fichas que ya se evaluaron.

Ejemplo: si P1 tiene 4 fichas en meta y distancia 35, su puntuación es
`30 × 4 - 10 × 35 = -230`. Si P2 tiene 3 fichas en meta y distancia 40,
obtiene `-310`. La evaluación es `-230 - (-310) = 80`, favorable a P1.

Una victoria tiene valor base +100 000 para P1 y -100 000 para P2, muy superior
a cualquier evaluación no terminal. Se suma o resta la profundidad restante
para preferir ganar antes o retrasar una derrota inevitable dentro de la búsqueda.

## Profundidad y tiempo

Una profundidad de 1 considera una jugada individual; una de 2 incluye la
respuesta del rival. La profundidad es un máximo configurable, no una promesa de
alcanzarlo: un límite de tiempo corto puede detener la búsqueda antes.

Se usa profundización iterativa: primero se completa profundidad 1, luego 2,
y así sucesivamente hasta el límite. Solo se conserva el resultado de una
iteración terminada. Antes de empezar se guarda una jugada legal de respaldo,
por lo que una interrupción temprana también tiene respuesta.

El reloj utilizado es `perf_counter`. Se comprueba el plazo al entrar en cada
nodo y después de evaluar o generar movimientos. El presupuesto interno es el
95 % del solicitado; con 30 segundos, se empieza a devolver la respuesta a los
28.5 segundos, dejando margen para terminar la llamada. No es un proceso de
tiempo real con interrupción del sistema operativo: una suspensión del equipo
puede afectar el tiempo observado. Las operaciones entre comprobaciones son
pequeñas y el margen fue verificado en esta computadora.

En la ventana, el agente calcula en un hilo de trabajo y comunica la respuesta
mediante una cola. Tkinter se actualiza únicamente desde el hilo de la interfaz.
Reiniciar cancela la búsqueda anterior y descarta sus resultados pendientes.

## Cierre de partidas

La victoria sigue la regla normal del material. La variante opcional contra
el bloqueo de campamentos no se activa.

La aplicación agrega tablas por tercera repetición del mismo tablero y turno,
600 jugadas individuales o falta de movimientos. Son convenciones para cerrar
sesiones, no reglas atribuidas al documento del curso. El límite de jugadas se
puede configurar por consola. La búsqueda reconoce terceras repeticiones con
el historial recibido; no anticipa el límite administrativo de 600 jugadas.

## Validación y observaciones

Pruebas realizadas en esta computadora:

- Las reglas y la consola conservan las verificaciones de la primera parte.
- Alfa-beta coincide con Minimax sin poda a profundidad 2 para ambos turnos
  sobre el tablero inicial, y efectivamente realiza cortes.
- Ambos jugadores eligen una victoria inmediata cuando está disponible.
- La asignación de metas coincide con una enumeración exhaustiva en un caso
  pequeño de cuatro fichas.
- Un presupuesto de 0.001 segundos y una cancelación anticipada siguen
  devolviendo una jugada legal de respaldo.
- Con profundidad solicitada 50 y presupuesto 30 s, la búsqueda tardó 28.500 s,
  terminó profundidad 5, visitó 221 109 nodos y realizó 27 898 cortes.

Dos partidas completas desde el tablero inicial, con 0.15 segundos por decisión:

| Profundidad máxima | Resultado | Jugadas individuales | Duración total | Decisión más lenta |
| --- | --- | --- | --- | --- |
| 1 | Victoria de P1 | 83 | 2.682 s | 0.139 s |
| 2 | Victoria de P1 | 127 | 10.750 s | 0.144 s |

Cada jugada fue validada por el motor. Los tiempos, la caché y los cortes por
plazo pueden cambiar entre ejecuciones; estos datos describen las pruebas
observadas, no resultados garantizados. No se ha medido el desempeño frente
a agentes externos del torneo. Ganar contra sí mismo comprueba que puede
completar el objetivo, pero no demuestra fuerza competitiva.

## Guion breve para exponer

1. Mostrar el tablero y explicar los pasos y saltos sin capturas.
2. Señalar que cada nodo del árbol es un tablero con un jugador en turno.
3. Explicar que P1 busca valores altos y P2 valores bajos, suponiendo que el
   rival también toma buenas decisiones.
4. Mostrar la fórmula de evaluación: llegar al campamento suma y estar lejos resta.
5. Explicar que la poda evita analizar ramas que no cambiarían la decisión.
6. Cambiar profundidad y tiempo en la ventana, iniciar una partida y observar
   los nodos, las podas y la profundidad realmente completada.
7. Aclarar que este agente usa búsqueda y una heurística escrita manualmente;
   no entrena un modelo de machine learning.
