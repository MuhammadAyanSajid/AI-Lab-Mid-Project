from collections import deque
import heapq
import time


class MazeSolver:
    """Solve a 2D grid maze using classic AI search strategies.

    The maze uses 0 for open cells and 1 for blocked cells.
    States are represented as (row, col) tuples.
    """

    def __init__(self, grid, initial_state, goal_state):
        self.grid = grid
        self.initial_state = initial_state
        self.goal_state = goal_state
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0

    def in_bounds(self, state):
        row, col = state
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_open(self, state):
        row, col = state
        return self.grid[row][col] == 0

    def is_valid_state(self, state):
        return self.in_bounds(state) and self.is_open(state)

    def neighbors(self, state):
        row, col = state
        candidate_moves = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]

        valid_neighbors = []
        for next_state in candidate_moves:
            if self.is_valid_state(next_state):
                valid_neighbors.append(next_state)
        return valid_neighbors

    def manhattan_distance(self, state):
        return abs(state[0] - self.goal_state[0]) + abs(state[1] - self.goal_state[1])

    def reconstruct_path(self, parents, end_state):
        path = [end_state]
        while path[-1] != self.initial_state:
            path.append(parents[path[-1]])
        path.reverse()
        return path

    def format_path(self, path):
        return " -> ".join(f"{state}" for state in path)

    def run_bfs(self):
        """Breadth-First Search using a FIFO queue implemented with deque."""
        start_time = time.time()
        frontier = deque([self.initial_state])
        parents = {self.initial_state: None}
        visited = {self.initial_state}
        nodes_explored = 0

        while frontier:
            current_state = frontier.popleft()
            nodes_explored += 1

            if current_state == self.goal_state:
                elapsed_time = time.time() - start_time
                path = self.reconstruct_path(parents, current_state)
                return {
                    "algorithm": "BFS",
                    "path": path,
                    "path_cost": len(path) - 1,
                    "nodes_explored": nodes_explored,
                    "time": elapsed_time,
                }

            for next_state in self.neighbors(current_state):
                if next_state not in visited:
                    visited.add(next_state)
                    parents[next_state] = current_state
                    frontier.append(next_state)

        elapsed_time = time.time() - start_time
        return self.no_solution_result("BFS", nodes_explored, elapsed_time)

    def run_dfs(self):
        """Depth-First Search using an explicit LIFO stack."""
        start_time = time.time()
        stack = [self.initial_state]
        parents = {self.initial_state: None}
        visited = set()
        nodes_explored = 0

        while stack:
            current_state = stack.pop()

            if current_state in visited:
                continue

            visited.add(current_state)
            nodes_explored += 1

            if current_state == self.goal_state:
                elapsed_time = time.time() - start_time
                path = self.reconstruct_path(parents, current_state)
                return {
                    "algorithm": "DFS",
                    "path": path,
                    "path_cost": len(path) - 1,
                    "nodes_explored": nodes_explored,
                    "time": elapsed_time,
                }

            # Reverse neighbor order so the pop sequence remains easy to explain.
            for next_state in reversed(self.neighbors(current_state)):
                if next_state not in visited and next_state not in stack:
                    parents[next_state] = current_state
                    stack.append(next_state)

        elapsed_time = time.time() - start_time
        return self.no_solution_result("DFS", nodes_explored, elapsed_time)

    def depth_limited_search(self, limit):
        """Perform one Depth-Limited Search pass up to a given depth."""
        stack = [(self.initial_state, 0)]
        parents = {self.initial_state: None}
        visited = set()
        nodes_explored = 0

        while stack:
            current_state, depth = stack.pop()

            if current_state in visited:
                continue

            visited.add(current_state)
            nodes_explored += 1

            if current_state == self.goal_state:
                path = self.reconstruct_path(parents, current_state)
                return {
                    "found": True,
                    "path": path,
                    "path_cost": len(path) - 1,
                    "nodes_explored": nodes_explored,
                }

            if depth < limit:
                for next_state in reversed(self.neighbors(current_state)):
                    if next_state not in visited:
                        if next_state not in parents:
                            parents[next_state] = current_state
                        stack.append((next_state, depth + 1))

        return {
            "found": False,
            "path": [],
            "path_cost": 0,
            "nodes_explored": nodes_explored,
        }

    def run_ids(self):
        """Iterative Deepening Search built from repeated DLS passes."""
        start_time = time.time()
        total_nodes_explored = 0

        for limit in range(self.rows * self.cols):
            result = self.depth_limited_search(limit)
            total_nodes_explored += result["nodes_explored"]

            if result["found"]:
                elapsed_time = time.time() - start_time
                return {
                    "algorithm": "IDS",
                    "path": result["path"],
                    "path_cost": result["path_cost"],
                    "nodes_explored": total_nodes_explored,
                    "time": elapsed_time,
                }

        elapsed_time = time.time() - start_time
        return self.no_solution_result("IDS", total_nodes_explored, elapsed_time)

    def run_a_star(self):
        """A* Search using heapq as a priority queue and Manhattan distance."""
        start_time = time.time()
        frontier = []
        heapq.heappush(
            frontier,
            (self.manhattan_distance(self.initial_state), 0, self.initial_state),
        )
        parents = {self.initial_state: None}
        best_cost = {self.initial_state: 0}
        closed_set = set()
        nodes_explored = 0

        while frontier:
            f_cost, g_cost, current_state = heapq.heappop(frontier)

            if current_state in closed_set:
                continue

            closed_set.add(current_state)
            nodes_explored += 1

            if current_state == self.goal_state:
                elapsed_time = time.time() - start_time
                path = self.reconstruct_path(parents, current_state)
                return {
                    "algorithm": "A*",
                    "path": path,
                    "path_cost": len(path) - 1,
                    "nodes_explored": nodes_explored,
                    "time": elapsed_time,
                }

            for next_state in self.neighbors(current_state):
                tentative_g_cost = g_cost + 1
                if (
                    next_state not in best_cost
                    or tentative_g_cost < best_cost[next_state]
                ):
                    best_cost[next_state] = tentative_g_cost
                    parents[next_state] = current_state
                    tentative_f_cost = tentative_g_cost + self.manhattan_distance(
                        next_state
                    )
                    heapq.heappush(
                        frontier, (tentative_f_cost, tentative_g_cost, next_state)
                    )

        elapsed_time = time.time() - start_time
        return self.no_solution_result("A*", nodes_explored, elapsed_time)

    def no_solution_result(self, algorithm_name, nodes_explored, elapsed_time):
        return {
            "algorithm": algorithm_name,
            "path": [],
            "path_cost": 0,
            "nodes_explored": nodes_explored,
            "time": elapsed_time,
        }

    def run_all_algorithms(self):
        """Execute all four search strategies on the same maze."""
        results = self.get_all_results()
        self.print_results(results)
        return results

    def get_all_results(self):
        """Run all four algorithms and return their raw result records."""
        return [
            self.run_bfs(),
            self.run_dfs(),
            self.run_ids(),
            self.run_a_star(),
        ]

    def print_results(self, results):
        print("Solution Paths:\n")
        for result in results:
            print(f"{result['algorithm']} Path:")
            if result["path"]:
                print(self.format_path(result["path"]))
            else:
                print("No path found.")
            print(f"Path Cost: {result['path_cost']}")
            print(f"Nodes Explored: {result['nodes_explored']}")
            print(f"Time: {result['time']:.6f} seconds")
            print()

        print("Algorithm Comparison Table")
        print("Algorithm | Nodes Explored | Path Cost | Time")
        print("-" * 55)
        for result in results:
            print(
                f"{result['algorithm']} | {result['nodes_explored']} | {result['path_cost']} | {result['time']:.6f}"
            )


def get_default_maze():
    """Provide a reproducible maze for algorithm comparison."""
    return [
        [0, 0, 1, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 0, 1],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0, 0, 1],
        [0, 0, 0, 1, 1, 0, 0],
        [1, 1, 0, 0, 0, 1, 0],
    ]


def main():
    maze = get_default_maze()
    initial_state = (0, 0)
    goal_state = (5, 6)

    solver = MazeSolver(maze, initial_state, goal_state)
    if not solver.is_valid_state(initial_state):
        print("Error: The initial state is not on an open cell.")
        return
    if not solver.is_valid_state(goal_state):
        print("Error: The goal state is not on an open cell.")
        return

    print("Maze Search Problem Solver")
    print(f"Initial State: {initial_state}")
    print(f"Goal State: {goal_state}")
    print()
    solver.run_all_algorithms()


if __name__ == "__main__":
    main()
