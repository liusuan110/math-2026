from scipy.optimize import minimize
import numpy as np


def example():
    func = lambda x: (x[0] - 1) ** 2 + (x[1] - 2.5) ** 2
    x0 = np.asarray([0, 0])  # 设定初始解
    bounds = np.asarray([[0, None], [0, None]])  # 无上界, x[0], x[1] >= 0
    cons = ({'type': 'ineq', 'fun': lambda x: x[0] - 2 * x[1] + 2},  # x[0] - 2*x[1] + 2 >= 0
            {'type': 'ineq', 'fun': lambda x: -x[0] - 2 * x[1] + 6},  # -x[0] - 2*x[1] + 6 >= 0
            {'type': 'ineq', 'fun': lambda x: -x[0] + 2 * x[1] + 2})  # -x[0] + 2*x[1] + 2 >= 0

    res = minimize(func, x0, bounds=bounds, constraints=cons)
    return res


if __name__ == '__main__':
    result = example()
    print(result)
