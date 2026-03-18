# Maze Pathfinder

A Python desktop application that visualises BFS, DFS, and A* pathfinding algorithms on a 7×7 grid. Built with `tkinter` — no external dependencies required.

---

## Requirements

- Python 3.7+
- `tkinter` (bundled with Python on Windows and macOS)

On Linux (Ubuntu/Debian), install tkinter if missing:

```bash
sudo apt install python3-tk
```

---

## Running the app

```bash
python maze_pathfinder.py
```

---

## Features

- **Three algorithms** — BFS, DFS, and A*, selectable from a dropdown
- **Step-by-step animation** — watch the frontier expand in real time
- **Adjustable speed** — slider from 1 (slow) to 10 (fast)
- **Interactive grid editing** — click cells to move the goal, add walls, or clear walls
- **Live stats** — cells visited, path length, and path cost update as the algorithm runs
- **Color-coded cells** — distinct colors for start, goal, walls, explored cells, frontier, and final path
- **Reset** — restores the original grid layout from the slide at any time

---

## Grid layout

The default maze is a 7×7 grid based on a search problem definition slide:

| Property     | Value                  |
|--------------|------------------------|
| Start        | (0, 0) — top-left      |
| Goal         | (6, 0) — top-right     |
| Actions      | Up, Down, Left, Right  |
| Cost per move | 1                     |

Coordinates are (x, y) where x increases rightward and y increases downward.

### Default walls

```
(1,0)  (4,0)
(1,1)  (4,1)
(2,2)  (4,2)
(2,3)  (4,3)
(2,4)
(2,5)
(2,6)
```

The wall column at x=2 (rows 2–6) combined with the walls at x=1 (rows 0–1) forms a complete barrier between the left and right sides of the grid, making the default layout unsolvable. Use the grid editor to clear a wall and open a path.

---

## Grid editor

Select a mode using the radio buttons above the grid, then click any cell:

| Mode          | Effect                                      |
|---------------|---------------------------------------------|
| Move goal ⭐  | Relocates the goal to the clicked cell       |
| Add wall ✕    | Blocks the clicked cell                      |
| Clear cell ✓  | Removes a wall from the clicked cell         |

The start cell (0,0) is fixed and cannot be moved or blocked. The goal cannot be placed on a wall. Editing the grid resets any animation in progress.

---

## Algorithms

### BFS — Breadth-First Search

Explores cells level by level using a FIFO queue. Every cell one move away is visited before any cell two moves away. Guarantees the shortest path when one exists.

```
Time:  O(V + E)
Space: O(V)        ← stores the entire frontier
```

### DFS — Depth-First Search

Explores cells by diving deep using a LIFO stack. Always follows the most recently discovered cell before backtracking. Does not guarantee the shortest path.

```
Time:  O(V + E)
Space: O(V)        ← in the worst case
```

### A* — A-Star

Uses a priority queue sorted by `f = g + h`, where `g` is the actual cost from the start and `h` is the Manhattan distance heuristic to the goal. Guided toward the goal — visits far fewer cells than BFS on open grids while still guaranteeing the shortest path.

```
Time:  O(E log V)  ← due to priority queue operations
Space: O(V)
Heuristic: h(x,y) = |x - goal_x| + |y - goal_y|
```

---

## Color reference

| Color       | Meaning             |
|-------------|---------------------|
| Purple      | Start cell          |
| Amber       | Goal cell           |
| Red/pink    | Wall (blocked)      |
| Blue        | Explored (visited)  |
| Light blue  | Frontier (queued)   |
| Green       | Final path          |

---

## File structure

```
maze_pathfinder.py   ← entire application, single file
README.md            ← this file
```

---

## Key implementation notes

- The algorithm runs on a **background thread** so the UI stays responsive during animation. All canvas updates are scheduled back onto the main thread via `self.after(0, ...)` to keep tkinter thread-safe.
- All three algorithm functions (`bfs_steps`, `dfs_steps`, `astar_steps`) compute the full list of steps upfront and return them as a list of tuples. The animator then replays this list — decoupling the logic from the rendering.
- Cells are added to `visited` at **discovery time** (when enqueued), not at processing time. This prevents duplicate entries in the queue.
- The `parent` dictionary maps each visited cell back to the cell it was reached from, enabling O(path length) path reconstruction via backtracking from the goal.
