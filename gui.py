import threading
from queue import Empty, Queue
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from maze_solver import MazeSolver, get_default_maze


class MazeSolverGUI:
    """Tkinter front end for the maze search solver."""

    def __init__(self, root):
        self.root = root
        self.root.title("Maze Solver - Interactive AI Search")
        self.root.geometry("1280x860")
        self.root.minsize(1140, 780)

        self.default_maze = self._clone_grid(get_default_maze())
        self.maze = self._clone_grid(self.default_maze)
        self.initial_state = (0, 0)
        self.goal_state = (5, 6)
        self.result_queue = Queue()
        self.running = False
        self.interactions_enabled = True
        self._running_snapshot = None

        self.algorithm_colors = {
            "BFS": "#2563eb",
            "DFS": "#dc2626",
            "IDS": "#16a34a",
            "A*": "#f97316",
        }
        self.path_widths = {
            "BFS": 5,
            "DFS": 4,
            "IDS": 4,
            "A*": 6,
        }
        self.algorithm_methods = {
            "BFS": "run_bfs",
            "DFS": "run_dfs",
            "IDS": "run_ids",
            "A*": "run_a_star",
        }

        self._build_layout()
        self._sync_controls_with_maze()
        self.draw_maze()

    def _clone_grid(self, grid):
        return [row[:] for row in grid]

    def _build_layout(self):
        self.main_frame = ttk.Frame(self.root, padding=12)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.BOTH, expand=True)

        self.left_panel = ttk.Frame(self.top_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self.right_panel = ttk.Frame(self.top_frame)
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title_frame = ttk.Frame(self.left_panel)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            title_frame,
            text="Maze Search Visualizer",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            title_frame,
            text="Edit the maze, pick one algorithm, or compare all four.",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        controls = ttk.LabelFrame(self.left_panel, text="Controls", padding=10)
        controls.pack(fill=tk.X, pady=(0, 12))

        grid_row = ttk.Frame(controls)
        grid_row.pack(fill=tk.X)
        ttk.Label(grid_row, text="Rows").pack(side=tk.LEFT)
        self.rows_var = tk.StringVar()
        self.rows_spinbox = tk.Spinbox(
            grid_row,
            from_=2,
            to=20,
            width=5,
            textvariable=self.rows_var,
            command=self._on_grid_size_change,
        )
        self.rows_spinbox.pack(side=tk.LEFT, padx=(6, 14))
        ttk.Label(grid_row, text="Columns").pack(side=tk.LEFT)
        self.cols_var = tk.StringVar()
        self.cols_spinbox = tk.Spinbox(
            grid_row,
            from_=2,
            to=20,
            width=5,
            textvariable=self.cols_var,
            command=self._on_grid_size_change,
        )
        self.cols_spinbox.pack(side=tk.LEFT, padx=(6, 0))

        size_buttons = ttk.Frame(controls)
        size_buttons.pack(fill=tk.X, pady=(8, 0))
        self.apply_size_button = ttk.Button(
            size_buttons, text="Apply Size", command=self._apply_grid_size
        )
        self.apply_size_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.default_button = ttk.Button(
            size_buttons, text="Default Maze", command=self._load_default_maze
        )
        self.default_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.clear_button = ttk.Button(
            controls, text="Clear Maze", command=self._clear_maze
        )
        self.clear_button.pack(fill=tk.X, pady=(8, 0))

        coords = ttk.LabelFrame(self.left_panel, text="Start / Goal", padding=10)
        coords.pack(fill=tk.X, pady=(0, 12))

        start_row = ttk.Frame(coords)
        start_row.pack(fill=tk.X)
        ttk.Label(start_row, text="Start Row").pack(side=tk.LEFT)
        self.start_row_var = tk.StringVar()
        self.start_row_spinbox = tk.Spinbox(
            start_row,
            from_=0,
            to=0,
            width=5,
            textvariable=self.start_row_var,
            command=self._on_state_change,
        )
        self.start_row_spinbox.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(start_row, text="Start Col").pack(side=tk.LEFT)
        self.start_col_var = tk.StringVar()
        self.start_col_spinbox = tk.Spinbox(
            start_row,
            from_=0,
            to=0,
            width=5,
            textvariable=self.start_col_var,
            command=self._on_state_change,
        )
        self.start_col_spinbox.pack(side=tk.LEFT, padx=(6, 0))

        goal_row = ttk.Frame(coords)
        goal_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(goal_row, text="Goal Row").pack(side=tk.LEFT)
        self.goal_row_var = tk.StringVar()
        self.goal_row_spinbox = tk.Spinbox(
            goal_row,
            from_=0,
            to=0,
            width=5,
            textvariable=self.goal_row_var,
            command=self._on_state_change,
        )
        self.goal_row_spinbox.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(goal_row, text="Goal Col").pack(side=tk.LEFT)
        self.goal_col_var = tk.StringVar()
        self.goal_col_spinbox = tk.Spinbox(
            goal_row,
            from_=0,
            to=0,
            width=5,
            textvariable=self.goal_col_var,
            command=self._on_state_change,
        )
        self.goal_col_spinbox.pack(side=tk.LEFT, padx=(6, 0))

        algorithm_frame = ttk.LabelFrame(self.left_panel, text="Algorithm", padding=10)
        algorithm_frame.pack(fill=tk.X, pady=(0, 12))
        self.algorithm_var = tk.StringVar(value="All Algorithms")
        self.algorithm_combo = ttk.Combobox(
            algorithm_frame,
            textvariable=self.algorithm_var,
            values=("All Algorithms", "BFS", "DFS", "IDS", "A*"),
            state="readonly",
        )
        self.algorithm_combo.pack(fill=tk.X)

        self.run_button = ttk.Button(
            algorithm_frame, text="Run Selected Search", command=self.start_search
        )
        self.run_button.pack(fill=tk.X, pady=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        status_row = ttk.Frame(self.left_panel)
        status_row.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(status_row, text="Status:").pack(side=tk.LEFT)
        ttk.Label(
            status_row, textvariable=self.status_var, font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=(6, 0))

        info = ttk.LabelFrame(self.left_panel, text="Interaction", padding=10)
        info.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(info, text="Click any non-special cell to toggle wall/open.").pack(
            anchor="w"
        )
        ttk.Label(info, text="Start and goal cells stay open automatically.").pack(
            anchor="w", pady=(4, 0)
        )

        legend = ttk.LabelFrame(self.left_panel, text="Legend", padding=10)
        legend.pack(fill=tk.X)
        self._add_legend_row(legend, "Wall", "#111827")
        self._add_legend_row(legend, "Open Cell", "#ffffff")
        self._add_legend_row(legend, "Start", "#22c55e")
        self._add_legend_row(legend, "Goal", "#ef4444")
        for algorithm, color in self.algorithm_colors.items():
            self._add_legend_row(legend, algorithm, color)

        canvas_frame = ttk.LabelFrame(
            self.right_panel, text="Maze Visualization", padding=10
        )
        canvas_frame.pack(fill=tk.BOTH, expand=False)
        self.cell_size = self._compute_cell_size(len(self.maze), len(self.maze[0]))
        self.canvas = tk.Canvas(
            canvas_frame,
            width=1,
            height=1,
            bg="#f8fafc",
            highlightthickness=0,
        )
        self.canvas.pack(anchor="nw")
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        results_frame = ttk.LabelFrame(
            self.right_panel, text="Algorithm Comparison", padding=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        columns = ("algorithm", "nodes", "cost", "time")
        self.tree = ttk.Treeview(
            results_frame, columns=columns, show="headings", height=5
        )
        self.tree.heading("algorithm", text="Algorithm")
        self.tree.heading("nodes", text="Nodes Explored")
        self.tree.heading("cost", text="Path Cost")
        self.tree.heading("time", text="Time")
        self.tree.column("algorithm", width=120, anchor="center")
        self.tree.column("nodes", width=140, anchor="center")
        self.tree.column("cost", width=120, anchor="center")
        self.tree.column("time", width=120, anchor="center")
        self.tree.pack(fill=tk.X)

        paths_frame = ttk.LabelFrame(results_frame, text="Solution Paths", padding=8)
        paths_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.paths_text = scrolledtext.ScrolledText(
            paths_frame, height=12, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.paths_text.pack(fill=tk.BOTH, expand=True)
        self.paths_text.configure(state=tk.DISABLED)

    def _add_legend_row(self, parent, label, color):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=1)
        swatch = tk.Canvas(row, width=16, height=16, highlightthickness=0)
        swatch.pack(side=tk.LEFT)
        swatch.create_rectangle(2, 2, 14, 14, fill=color, outline=color)
        ttk.Label(row, text=label).pack(side=tk.LEFT, padx=(8, 0))

    def _compute_cell_size(self, rows, cols):
        max_dimension = max(rows, cols, 1)
        return max(24, min(48, 600 // max_dimension))

    def _sync_controls_with_maze(self):
        rows = len(self.maze)
        cols = len(self.maze[0]) if self.maze else 0
        self.rows_var.set(str(rows))
        self.cols_var.set(str(cols))
        self._set_spinbox_limits(rows, cols)

        start_row, start_col = self._clamp_state(self.initial_state)
        goal_row, goal_col = self._clamp_state(self.goal_state)
        self.initial_state = (start_row, start_col)
        self.goal_state = (goal_row, goal_col)
        self.start_row_var.set(str(start_row))
        self.start_col_var.set(str(start_col))
        self.goal_row_var.set(str(goal_row))
        self.goal_col_var.set(str(goal_col))

        self._ensure_special_cells_open(self.maze, self.initial_state, self.goal_state)

    def _set_spinbox_limits(self, rows, cols):
        max_row = max(rows - 1, 0)
        max_col = max(cols - 1, 0)
        self.rows_spinbox.configure(from_=2, to=max(2, rows * 2))
        self.cols_spinbox.configure(from_=2, to=max(2, cols * 2))
        self.start_row_spinbox.configure(from_=0, to=max_row)
        self.start_col_spinbox.configure(from_=0, to=max_col)
        self.goal_row_spinbox.configure(from_=0, to=max_row)
        self.goal_col_spinbox.configure(from_=0, to=max_col)

    def _read_int(self, var, label):
        try:
            return int(var.get())
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be an integer.")

    def _clamp_state(self, state):
        if not self.maze:
            return (0, 0)
        row = min(max(state[0], 0), len(self.maze) - 1)
        col = min(max(state[1], 0), len(self.maze[0]) - 1)
        return row, col

    def _clamp_state_to_size(self, state, rows, cols):
        row = min(max(state[0], 0), rows - 1)
        col = min(max(state[1], 0), cols - 1)
        return row, col

    def _ensure_special_cells_open(self, maze, start_state, goal_state):
        for row, col in (start_state, goal_state):
            if 0 <= row < len(maze) and 0 <= col < len(maze[0]):
                maze[row][col] = 0

    def _update_canvas_size(self):
        rows = len(self.maze)
        cols = len(self.maze[0]) if self.maze else 0
        self.cell_size = self._compute_cell_size(rows, cols)
        width = cols * self.cell_size + 2
        height = rows * self.cell_size + 2
        self.canvas.configure(width=width, height=height)

    def _refresh_after_maze_change(self):
        self._update_canvas_size()
        self.draw_maze()
        self._set_paths_text("Maze updated. Run a search to refresh the results.\n")
        self.tree.delete(*self.tree.get_children())
        self.status_var.set("Ready")

    def _clear_result_display(
        self, message="Maze updated. Run a search to refresh the results.\n"
    ):
        self.tree.delete(*self.tree.get_children())
        self._set_paths_text(message)
        self.status_var.set("Ready")

    def _on_grid_size_change(self):
        if self.running:
            return
        self._apply_grid_size(redraw_only=False)

    def _on_state_change(self):
        if self.running:
            return
        self._apply_states_from_controls()

    def _parse_controls(self):
        rows = self._read_int(self.rows_var, "Rows")
        cols = self._read_int(self.cols_var, "Columns")
        start_row = self._read_int(self.start_row_var, "Start row")
        start_col = self._read_int(self.start_col_var, "Start column")
        goal_row = self._read_int(self.goal_row_var, "Goal row")
        goal_col = self._read_int(self.goal_col_var, "Goal column")
        return rows, cols, (start_row, start_col), (goal_row, goal_col)

    def _build_maze_from_size(self, rows, cols):
        if rows < 2 or cols < 2:
            raise ValueError("Maze dimensions must be at least 2 x 2.")

        previous = self._clone_grid(self.maze)
        new_maze = [[0 for _ in range(cols)] for _ in range(rows)]
        for row in range(min(rows, len(previous))):
            for col in range(min(cols, len(previous[0]))):
                new_maze[row][col] = previous[row][col]
        return new_maze

    def _apply_grid_size(self, redraw_only=True):
        if self.running:
            return

        try:
            rows = self._read_int(self.rows_var, "Rows")
            cols = self._read_int(self.cols_var, "Columns")
        except ValueError as exc:
            messagebox.showerror("Invalid Maze Size", str(exc))
            return

        try:
            self.maze = self._build_maze_from_size(rows, cols)
        except ValueError as exc:
            messagebox.showerror("Invalid Maze Size", str(exc))
            return

        self.initial_state = self._clamp_state(self.initial_state)
        self.goal_state = self._clamp_state(self.goal_state)
        self._sync_controls_with_maze()
        if redraw_only:
            self._refresh_after_maze_change()
        else:
            self._update_canvas_size()
            self.draw_maze()

    def _apply_states_from_controls(self):
        try:
            _, _, start_state, goal_state = self._parse_controls()
        except ValueError as exc:
            messagebox.showerror("Invalid Coordinate", str(exc))
            return

        if not self.maze:
            return

        start_state = self._clamp_state(start_state)
        goal_state = self._clamp_state(goal_state)
        self.initial_state = start_state
        self.goal_state = goal_state
        self._ensure_special_cells_open(self.maze, self.initial_state, self.goal_state)
        self.draw_maze()
        self._clear_result_display()

    def _load_default_maze(self):
        if self.running:
            return

        self.maze = self._clone_grid(self.default_maze)
        self.initial_state = (0, 0)
        self.goal_state = (5, 6)
        self._sync_controls_with_maze()
        self._refresh_after_maze_change()

    def _clear_maze(self):
        if self.running:
            return

        rows = len(self.maze)
        cols = len(self.maze[0]) if self.maze else 0
        self.maze = [[0 for _ in range(cols)] for _ in range(rows)]
        self._ensure_special_cells_open(self.maze, self.initial_state, self.goal_state)
        self._refresh_after_maze_change()

    def _on_canvas_click(self, event):
        if not self.interactions_enabled or not self.maze:
            return

        row = event.y // self.cell_size
        col = event.x // self.cell_size
        if row < 0 or col < 0 or row >= len(self.maze) or col >= len(self.maze[0]):
            return

        if (row, col) in {self.initial_state, self.goal_state}:
            return

        self.maze[row][col] = 0 if self.maze[row][col] == 1 else 1
        self.draw_maze()
        self._clear_result_display()

    def draw_maze(self):
        self.canvas.delete("all")
        self._update_canvas_size()

        for row_index, row in enumerate(self.maze):
            for col_index, cell in enumerate(row):
                x1 = col_index * self.cell_size
                y1 = row_index * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                fill_color = "#ffffff" if cell == 0 else "#111827"
                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill_color,
                    outline="#cbd5e1",
                )

        self._draw_special_cell(self.initial_state, "#22c55e", "S")
        self._draw_special_cell(self.goal_state, "#ef4444", "G")

    def _draw_special_cell(self, state, color, label):
        row, col = state
        if not self.maze:
            return
        if not (0 <= row < len(self.maze) and 0 <= col < len(self.maze[0])):
            return

        x1 = col * self.cell_size
        y1 = row * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        self.canvas.create_oval(
            x1 + 8, y1 + 8, x2 - 8, y2 - 8, fill=color, outline=color
        )
        self.canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text=label,
            fill="white",
            font=("Segoe UI", 12, "bold"),
        )

    def _build_snapshot(self):
        rows, cols, start_state, goal_state = self._parse_controls()
        if rows < 2 or cols < 2:
            raise ValueError("Maze dimensions must be at least 2 x 2.")

        if rows != len(self.maze) or cols != len(self.maze[0]):
            maze = self._build_maze_from_size(rows, cols)
        else:
            maze = self._clone_grid(self.maze)

        start_state = self._clamp_state_to_size(start_state, rows, cols)
        goal_state = self._clamp_state_to_size(goal_state, rows, cols)
        self._ensure_special_cells_open(maze, start_state, goal_state)
        return maze, start_state, goal_state

    def _selected_algorithm(self):
        selected = self.algorithm_var.get().strip()
        if selected == "":
            raise ValueError("Please select an algorithm.")
        return selected

    def _set_controls_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        for widget in (
            self.rows_spinbox,
            self.cols_spinbox,
            self.start_row_spinbox,
            self.start_col_spinbox,
            self.goal_row_spinbox,
            self.goal_col_spinbox,
        ):
            widget.configure(state=state)

        if enabled:
            self.algorithm_combo.configure(state="readonly")
            self.run_button.configure(state=tk.NORMAL)
            self.apply_size_button.configure(state=tk.NORMAL)
            self.default_button.configure(state=tk.NORMAL)
            self.clear_button.configure(state=tk.NORMAL)
            self.interactions_enabled = True
        else:
            self.algorithm_combo.configure(state=tk.DISABLED)
            self.run_button.configure(state=tk.DISABLED)
            self.apply_size_button.configure(state=tk.DISABLED)
            self.default_button.configure(state=tk.DISABLED)
            self.clear_button.configure(state=tk.DISABLED)
            self.interactions_enabled = False

    def start_search(self):
        if self.running:
            return

        try:
            maze_snapshot, start_state, goal_state = self._build_snapshot()
            selection = self._selected_algorithm()
        except ValueError as exc:
            messagebox.showerror("Invalid Maze", str(exc))
            return

        self.maze = self._clone_grid(maze_snapshot)
        self.initial_state = start_state
        self.goal_state = goal_state
        self._running_snapshot = (maze_snapshot, start_state, goal_state)

        self.running = True
        self.status_var.set("Running search...")
        self._set_controls_enabled(False)
        self.tree.delete(*self.tree.get_children())
        self._set_paths_text(f"Running {selection}...\nPlease wait for the results.\n")
        self.draw_maze()

        worker = threading.Thread(
            target=self._run_solver_worker,
            args=(maze_snapshot, start_state, goal_state, selection),
            daemon=True,
        )
        worker.start()
        self.root.after(80, self.check_result_queue)

    def _run_solver_worker(self, maze_snapshot, start_state, goal_state, selection):
        try:
            solver = MazeSolver(maze_snapshot, start_state, goal_state)
            if selection == "All Algorithms":
                results = solver.get_all_results()
            else:
                method_name = self.algorithm_methods[selection]
                results = [getattr(solver, method_name)()]
            self.result_queue.put(("success", results))
        except Exception as exc:  # pragma: no cover - UI safety net
            self.result_queue.put(("error", str(exc)))

    def check_result_queue(self):
        try:
            status, payload = self.result_queue.get_nowait()
        except Empty:
            if self.running:
                self.root.after(80, self.check_result_queue)
            return

        self.running = False
        self._set_controls_enabled(True)

        if status == "error":
            self.status_var.set("Error")
            messagebox.showerror("Search Error", payload)
            self._set_paths_text("Search failed. Fix the maze or try again.\n")
            self.draw_maze()
            return

        results = payload
        self.status_var.set("Complete")
        self.populate_results(results)
        self.render_paths(results)

    def populate_results(self, results):
        self.tree.delete(*self.tree.get_children())
        for result in results:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    result["algorithm"],
                    result["nodes_explored"],
                    result["path_cost"],
                    f"{result['time']:.6f}",
                ),
            )

        lines = ["Solution Paths", ""]
        for result in results:
            lines.append(f"{result['algorithm']} Path:")
            if result["path"]:
                lines.append(self._format_path(result["path"]))
            else:
                lines.append("No path found.")
            lines.append(f"Path Cost: {result['path_cost']}")
            lines.append(f"Nodes Explored: {result['nodes_explored']}")
            lines.append(f"Time: {result['time']:.6f} seconds")
            lines.append("")

        lines.append("Algorithm Comparison Table")
        lines.append("Algorithm | Nodes Explored | Path Cost | Time")
        lines.append("-" * 55)
        for result in results:
            lines.append(
                f"{result['algorithm']} | {result['nodes_explored']} | {result['path_cost']} | {result['time']:.6f}"
            )

        self._set_paths_text("\n".join(lines))

    def _format_path(self, path):
        return " -> ".join(f"{state}" for state in path)

    def render_paths(self, results):
        if self._running_snapshot is None:
            self.draw_maze()
        else:
            maze_snapshot, start_state, goal_state = self._running_snapshot
            self.maze = self._clone_grid(maze_snapshot)
            self.initial_state = start_state
            self.goal_state = goal_state
            self.draw_maze()

        for result in results:
            path = result["path"]
            if len(path) < 2:
                continue
            color = self.algorithm_colors.get(result["algorithm"], "#0f172a")
            width = self.path_widths.get(result["algorithm"], 4)
            self._draw_path(path, color, width)

        self._draw_special_cell(self.initial_state, "#22c55e", "S")
        self._draw_special_cell(self.goal_state, "#ef4444", "G")

    def _draw_path(self, path, color, width):
        points = []
        for row, col in path:
            center_x = col * self.cell_size + self.cell_size / 2
            center_y = row * self.cell_size + self.cell_size / 2
            points.extend([center_x, center_y])

        if len(points) >= 4:
            self.canvas.create_line(
                *points,
                fill=color,
                width=width,
                smooth=False,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
            )

    def _set_paths_text(self, content):
        self.paths_text.configure(state=tk.NORMAL)
        self.paths_text.delete("1.0", tk.END)
        self.paths_text.insert(tk.END, content)
        self.paths_text.configure(state=tk.DISABLED)


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    MazeSolverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
