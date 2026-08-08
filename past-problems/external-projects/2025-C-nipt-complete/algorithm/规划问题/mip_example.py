from ortools.linear_solver import pywraplp


def main():
    solver = pywraplp.Solver.CreateSolver("SAT")
    if not solver:
        return

    infinity = solver.infinity()
    x = solver.IntVar(0.0, infinity, "x")
    y = solver.IntVar(0.0, infinity, "y")
    solver.Add(x + 7 * y <= 17.5)
    solver.Add(x <= 3.5)
    solver.Maximize(x + 10 * y)
    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("Objective value =", solver.Objective().Value())
        print("x =", x.solution_value())
        print("y =", y.solution_value())
    else:
        print("The problem does not have an optimal solution.")


if __name__ == "__main__":
    main()
