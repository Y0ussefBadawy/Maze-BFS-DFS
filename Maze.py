import tkinter as tk
from tkinter import ttk
import time
import threading
from collections import deque
import heapq

# ── Grid config ───────────────────────────────────────────────────────────────
COLS, ROWS = 7, 7
DEFAULT_START = (0, 0)
DEFAULT_GOAL  = (6, 0)

# Walls read directly from the slide (x, y)
DEFAULT_WALLS = {
    (1,0),(4,0),
    (1,1),(4,1),
    (2,2),(4,2),
    (2,3),(4,3),
    (2,4),
    (2,5),
    (2,6),
}

# ── Colors ────────────────────────────────────────────────────────────────────
BG          = "#F8F8F6"
PANEL_BG    = "#EEECEA"
CELL_EMPTY  = "#FFFFFF"
CELL_WALL   = "#F7C1C1"
CELL_START  = "#CECBF6"
CELL_GOAL   = "#FAC775"
CELL_VISIT  = "#B5D4F4"
CELL_FRONT  = "#DCF0FF"
CELL_PATH   = "#C0DD97"
TEXT_MAIN   = "#2C2C2A"
TEXT_MUTED  = "#888780"
BORDER      = "#D3D1C7"
BTN_PRIMARY = "#185FA5"
BTN_DANGER  = "#A32D2D"

CELL_SIZE  = 56
CELL_PAD   = 3
COORD_FONT = ("Helvetica", 7)


# ── Pathfinding ───────────────────────────────────────────────────────────────
def get_neighbors(x, y, walls):
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < COLS and 0 <= ny < ROWS and (nx,ny) not in walls:
            yield nx, ny

def _trace(parent, goal):
    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return list(reversed(path))

def bfs_steps(start, goal, walls):
    visited = {start}
    parent  = {start: None}
    queue   = deque([start])
    steps   = []
    while queue:
        cx, cy = queue.popleft()
        steps.append(("visit", cx, cy))
        if (cx, cy) == goal:
            return steps + [("path", _trace(parent, goal))]
        for nx, ny in get_neighbors(cx, cy, walls):
            if (nx,ny) not in visited:
                visited.add((nx,ny))
                parent[(nx,ny)] = (cx,cy)
                steps.append(("frontier", nx, ny))
                queue.append((nx,ny))
    return steps + [("nofound",)]

def dfs_steps(start, goal, walls):
    visited = set()
    parent  = {start: None}
    stack   = [start]
    steps   = []
    while stack:
        cx, cy = stack.pop()
        if (cx,cy) in visited:
            continue
        visited.add((cx,cy))
        steps.append(("visit", cx, cy))
        if (cx,cy) == goal:
            return steps + [("path", _trace(parent, goal))]
        for nx, ny in get_neighbors(cx, cy, walls):
            if (nx,ny) not in visited:
                parent.setdefault((nx,ny), (cx,cy))
                steps.append(("frontier", nx, ny))
                stack.append((nx,ny))
    return steps + [("nofound",)]

def astar_steps(start, goal, walls):
    def h(x, y): return abs(x-goal[0]) + abs(y-goal[1])
    g_cost = {start: 0}
    parent = {start: None}
    open_h = [(h(*start), start)]
    closed = set()
    steps  = []
    while open_h:
        _, (cx,cy) = heapq.heappop(open_h)
        if (cx,cy) in closed:
            continue
        closed.add((cx,cy))
        steps.append(("visit", cx, cy))
        if (cx,cy) == goal:
            return steps + [("path", _trace(parent, goal))]
        for nx, ny in get_neighbors(cx, cy, walls):
            if (nx,ny) in closed:
                continue
            ng = g_cost[(cx,cy)] + 1
            if ng < g_cost.get((nx,ny), float('inf')):
                g_cost[(nx,ny)] = ng
                parent[(nx,ny)] = (cx,cy)
                steps.append(("frontier", nx, ny))
                heapq.heappush(open_h, (ng + h(nx,ny), (nx,ny)))
    return steps + [("nofound",)]


# ── App ───────────────────────────────────────────────────────────────────────
class MazeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Maze Pathfinder")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.start = DEFAULT_START
        self.goal  = DEFAULT_GOAL
        self.walls = set(DEFAULT_WALLS)

        self._running = False
        self._rects   = {}
        self._icons   = {}

        self._build_ui()
        self._draw_grid()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        tk.Label(self, text="Maze Pathfinder", font=("Helvetica",17,"bold"),
                 bg=BG, fg=TEXT_MAIN).pack(anchor="w", padx=20, pady=(10,2))
        tk.Label(self, text="Click a free cell to move the goal  ·  Use toolbar to add/remove walls",
                 font=("Helvetica",10), bg=BG, fg=TEXT_MUTED).pack(anchor="w", padx=20, pady=(0,6))

        # Controls row
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=(0,5))

        self.btn_start = self._mkbtn(ctrl, "▶  Start", BTN_PRIMARY, "white", self._on_start)
        self.btn_start.pack(side="left", padx=(0,6))
        self._mkbtn(ctrl, "↺  Reset", CELL_EMPTY, TEXT_MAIN, self._on_reset).pack(side="left", padx=(0,16))

        tk.Label(ctrl, text="Algorithm:", font=("Helvetica",10), bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0,5))
        self.algo_var = tk.StringVar(value="bfs")
        ttk.Combobox(ctrl, textvariable=self.algo_var, state="readonly",
                     values=["bfs","dfs","astar"], width=13,
                     font=("Helvetica",10)).pack(side="left", padx=(0,16))

        tk.Label(ctrl, text="Speed:", font=("Helvetica",10), bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0,5))
        self.speed_var = tk.IntVar(value=5)
        tk.Scale(ctrl, from_=1, to=10, orient="horizontal", variable=self.speed_var,
                 length=90, bg=BG, fg=TEXT_MAIN, highlightthickness=0,
                 troughcolor=PANEL_BG, sliderrelief="flat").pack(side="left", padx=(0,16))

        self.status_var = tk.StringVar(value="Ready")
        self.status_lbl = tk.Label(ctrl, textvariable=self.status_var,
                                    font=("Helvetica",10,"bold"), bg=PANEL_BG, fg=TEXT_MUTED,
                                    highlightthickness=1, highlightbackground=BORDER,
                                    padx=12, pady=5)
        self.status_lbl.pack(side="left")

        # Edit-mode toolbar
        edit = tk.Frame(self, bg=BG)
        edit.pack(fill="x", padx=20, pady=(0,5))
        tk.Label(edit, text="Click cells to:", font=("Helvetica",10), bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0,8))
        self.mode_var = tk.StringVar(value="goal")
        for label, val in [("Move goal ⭐","goal"),("Add wall ✕","wall"),("Clear cell ✓","clear")]:
            tk.Radiobutton(edit, text=label, variable=self.mode_var, value=val,
                           font=("Helvetica",10), bg=BG, fg=TEXT_MAIN,
                           activebackground=BG, selectcolor=BG,
                           cursor="hand2").pack(side="left", padx=(0,14))

        # Canvas
        cw = COLS*(CELL_SIZE+CELL_PAD)+CELL_PAD
        ch = ROWS*(CELL_SIZE+CELL_PAD)+CELL_PAD
        cf = tk.Frame(self, bg=PANEL_BG, highlightthickness=1, highlightbackground=BORDER)
        cf.pack(padx=20, pady=(0,6))
        self.canvas = tk.Canvas(cf, width=cw, height=ch, bg=PANEL_BG,
                                 bd=0, highlightthickness=0, cursor="hand2")
        self.canvas.pack(padx=4, pady=4)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Stats
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=20, pady=(0,6))
        self._sv = self._stat_card(sf, "Cells visited", "0")
        self._sp = self._stat_card(sf, "Path length",   "—")
        self._sc = self._stat_card(sf, "Path cost",     "—")

        # Legend
        leg = tk.Frame(self, bg=BG)
        leg.pack(fill="x", padx=20, pady=(4,12))
        for label, color in [("Start",CELL_START),("Goal",CELL_GOAL),("Wall",CELL_WALL),
                              ("Explored",CELL_VISIT),("Frontier",CELL_FRONT),("Path",CELL_PATH)]:
            d = tk.Canvas(leg, width=14, height=14, bg=BG, bd=0, highlightthickness=0)
            d.create_rectangle(0,0,14,14, fill=color, outline=BORDER, width=1)
            d.pack(side="left", padx=(0,4))
            tk.Label(leg, text=label, font=("Helvetica",10), bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0,12))

    def _mkbtn(self, parent, text, bg, fg, cmd):
        return tk.Button(parent, text=text, font=("Helvetica",11,"bold"),
                         bg=bg, fg=fg,
                         activebackground="#0c447c" if bg == BTN_PRIMARY else PANEL_BG,
                         activeforeground=fg, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         padx=14, pady=6, cursor="hand2", command=cmd)

    def _stat_card(self, parent, label, init):
        f = tk.Frame(parent, bg=PANEL_BG, highlightthickness=1, highlightbackground=BORDER)
        f.pack(side="left", padx=(0,10), ipadx=14, ipady=8)
        tk.Label(f, text=label, font=("Helvetica",9), bg=PANEL_BG, fg=TEXT_MUTED).pack()
        v = tk.StringVar(value=init)
        tk.Label(f, textvariable=v, font=("Helvetica",18,"bold"), bg=PANEL_BG, fg=TEXT_MAIN).pack()
        return v

    # ── Grid ──────────────────────────────────────────────────────────────────
    def _cell_bbox(self, x, y):
        x0 = CELL_PAD + x*(CELL_SIZE+CELL_PAD)
        y0 = CELL_PAD + y*(CELL_SIZE+CELL_PAD)
        return x0, y0, x0+CELL_SIZE, y0+CELL_SIZE

    def _cell_fill(self, x, y):
        if (x,y) in self.walls: return CELL_WALL
        if (x,y) == self.start: return CELL_START
        if (x,y) == self.goal:  return CELL_GOAL
        return CELL_EMPTY

    def _draw_grid(self):
        self.canvas.delete("all")
        self._rects.clear()
        self._icons.clear()
        for y in range(ROWS):
            for x in range(COLS):
                self._draw_cell(x, y)

    def _draw_cell(self, x, y):
        x0,y0,x1,y1 = self._cell_bbox(x,y)
        cx, cy = (x0+x1)//2, (y0+y1)//2
        rid = self.canvas.create_rectangle(x0,y0,x1,y1,
                                            fill=self._cell_fill(x,y),
                                            outline=BORDER, width=1)
        self._rects[(x,y)] = rid
        self.canvas.create_text(cx, y1-9, text=f"({x},{y})", font=COORD_FONT, fill=TEXT_MUTED)
        iid = None
        if (x,y) in self.walls:
            iid = self.canvas.create_text(cx, cy-6, text="✕", font=("Helvetica",16), fill="#A32D2D")
        elif (x,y) == self.start:
            iid = self.canvas.create_text(cx, cy-6, text="🤖", font=("Helvetica",20))
        elif (x,y) == self.goal:
            iid = self.canvas.create_text(cx, cy-6, text="⭐", font=("Helvetica",20))
        self._icons[(x,y)] = iid

    def _refresh_cell(self, x, y):
        x0,y0,x1,y1 = self._cell_bbox(x,y)
        cx, cy = (x0+x1)//2, (y0+y1)//2
        self.canvas.itemconfig(self._rects[(x,y)], fill=self._cell_fill(x,y))
        if self._icons.get((x,y)):
            self.canvas.delete(self._icons[(x,y)])
            self._icons[(x,y)] = None
        if (x,y) in self.walls:
            self._icons[(x,y)] = self.canvas.create_text(cx, cy-6, text="✕", font=("Helvetica",16), fill="#A32D2D")
        elif (x,y) == self.start:
            self._icons[(x,y)] = self.canvas.create_text(cx, cy-6, text="🤖", font=("Helvetica",20))
        elif (x,y) == self.goal:
            self._icons[(x,y)] = self.canvas.create_text(cx, cy-6, text="⭐", font=("Helvetica",20))

    def _set_cell_color(self, x, y, color):
        if (x,y) in self.walls or (x,y) == self.start or (x,y) == self.goal:
            return
        self.canvas.itemconfig(self._rects[(x,y)], fill=color)

    def _reset_colors(self):
        for y in range(ROWS):
            for x in range(COLS):
                if (x,y) not in self.walls and (x,y) != self.start and (x,y) != self.goal:
                    self.canvas.itemconfig(self._rects[(x,y)], fill=CELL_EMPTY)

    # ── Canvas click ──────────────────────────────────────────────────────────
    def _on_canvas_click(self, event):
        if self._running:
            return
        for y in range(ROWS):
            for x in range(COLS):
                x0,y0,x1,y1 = self._cell_bbox(x,y)
                if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                    self._handle_click(x, y)
                    return

    def _handle_click(self, x, y):
        if (x,y) == self.start:
            return
        mode = self.mode_var.get()

        if mode == "goal":
            if (x,y) in self.walls:
                return
            old = self.goal
            self.goal = (x,y)
            self._refresh_cell(*old)
            self._refresh_cell(x, y)
            self._set_status(f"Goal → ({x},{y})", BTN_PRIMARY)

        elif mode == "wall":
            if (x,y) == self.goal:
                return
            self.walls.add((x,y))
            self._refresh_cell(x, y)

        elif mode == "clear":
            if (x,y) in self.walls:
                self.walls.discard((x,y))
                self._refresh_cell(x, y)

        self._reset_colors()
        self._sv.set("0"); self._sp.set("—"); self._sc.set("—")
        self._set_status("Ready", TEXT_MUTED)

    # ── Controls ──────────────────────────────────────────────────────────────
    def _on_reset(self):
        self._running = False
        self.start = DEFAULT_START
        self.goal  = DEFAULT_GOAL
        self.walls = set(DEFAULT_WALLS)
        self._draw_grid()
        self._set_status("Ready", TEXT_MUTED)
        self.btn_start.configure(state="normal")
        self._sv.set("0"); self._sp.set("—"); self._sc.set("—")

    def _on_start(self):
        if self._running:
            return
        self._reset_colors()
        self._sv.set("0"); self._sp.set("—"); self._sc.set("—")
        self._running = True
        self.btn_start.configure(state="disabled")
        self._set_status("Running…", BTN_PRIMARY)
        algo  = self.algo_var.get()
        fn    = {"bfs": bfs_steps, "dfs": dfs_steps, "astar": astar_steps}[algo]
        steps = fn(self.start, self.goal, self.walls)
        threading.Thread(target=self._animate, args=(steps,), daemon=True).start()

    def _set_status(self, text, color=None):
        self.status_var.set(text)
        self.status_lbl.configure(fg=color or TEXT_MUTED)

    # ── Animation ─────────────────────────────────────────────────────────────
    def _animate(self, steps):
        visited_n = 0
        for step in steps:
            if not self._running:
                return
            ms = max(20, int(1000 / (self.speed_var.get() * 2.5 + 1)))

            kind = step[0]
            if kind == "visit":
                _, x, y = step
                self.after(0, self._set_cell_color, x, y, CELL_VISIT)
                visited_n += 1
                self.after(0, self._sv.set, str(visited_n))

            elif kind == "frontier":
                _, x, y = step
                self.after(0, self._paint_frontier, x, y)

            elif kind == "path":
                for px, py in step[1]:
                    if not self._running:
                        return
                    self.after(0, self._set_cell_color, px, py, CELL_PATH)
                    time.sleep(0.07)
                self.after(0, self._finish, True, len(step[1]), len(step[1])-1)
                return

            elif kind == "nofound":
                self.after(0, self._finish, False, 0, 0)
                return

            time.sleep(ms / 1000)

    def _paint_frontier(self, x, y):
        cur = self.canvas.itemcget(self._rects[(x,y)], "fill")
        if cur == CELL_EMPTY:
            self._set_cell_color(x, y, CELL_FRONT)

    def _finish(self, found, path_len, cost):
        self._running = False
        self.btn_start.configure(state="normal")
        if found:
            self._set_status("Path found!", "#3B6D11")
            self._sp.set(str(path_len))
            self._sc.set(str(cost))
        else:
            self._set_status("No path found", BTN_DANGER)


if __name__ == "__main__":
    app = MazeApp()
    app.mainloop()