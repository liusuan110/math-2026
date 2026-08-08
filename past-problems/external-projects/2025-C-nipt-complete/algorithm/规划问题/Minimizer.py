from scipy.optimize import minimize
import numpy as np


def fun(args):
    a, b = args
    v = lambda x: ((x[12] - a[0]) ** 2 + (x[13] - b[0]) ** 2) ** 0.5 * x[0] + \
                  ((x[12] - a[1]) ** 2 + (x[13] - b[1]) ** 2) ** 0.5 * x[1] + \
                  ((x[12] - a[2]) ** 2 + (x[13] - b[2]) ** 2) ** 0.5 * x[2] + \
                  ((x[12] - a[3]) ** 2 + (x[13] - b[3]) ** 2) ** 0.5 * x[3] + \
                  ((x[12] - a[4]) ** 2 + (x[13] - b[4]) ** 2) ** 0.5 * x[4] + \
                  ((x[12] - a[5]) ** 2 + (x[13] - b[5]) ** 2) ** 0.5 * x[5] + \
                  ((x[14] - a[0]) ** 2 + (x[15] - b[0]) ** 2) ** 0.5 * x[6] + \
                  ((x[14] - a[1]) ** 2 + (x[15] - b[1]) ** 2) ** 0.5 * x[7] + \
                  ((x[14] - a[2]) ** 2 + (x[15] - b[2]) ** 2) ** 0.5 * x[8] + \
                  ((x[14] - a[3]) ** 2 + (x[15] - b[3]) ** 2) ** 0.5 * x[9] + \
                  ((x[14] - a[4]) ** 2 + (x[15] - b[4]) ** 2) ** 0.5 * x[10] + \
                  ((x[14] - a[5]) ** 2 + (x[15] - b[5]) ** 2) ** 0.5 * x[11]
    return v


def cons(args):
    d, e = args
    con = ({'type': 'eq', 'fun': lambda x: (x[0] + x[6]) - d[0]},
           {'type': 'eq', 'fun': lambda x: (x[1] + x[7]) - d[1]},
           {'type': 'eq', 'fun': lambda x: (x[2] + x[8]) - d[2]},
           {'type': 'eq', 'fun': lambda x: (x[3] + x[9]) - d[3]},
           {'type': 'eq', 'fun': lambda x: (x[4] + x[10]) - d[4]},
           {'type': 'eq', 'fun': lambda x: (x[5] + x[11]) - d[5]},
           {'type': 'ineq', 'fun': lambda x: e[0] - (x[0] + x[1] + x[2] + x[3] + x[4] + x[5])},
           {'type': 'ineq', 'fun': lambda x: e[1] - (x[6] + x[7] + x[8] + x[9] + x[10] + x[11])})
    return con


if __name__ == '__main__':
    a = [1.25, 8.75, 0.5, 5.75, 3, 7.25]
    b = [1.25, 0.75, 4.75, 5, 6.5, 7.75]
    d = [3, 5, 4, 7, 6, 11]
    e = [20, 20]
    x0 = np.asarray((3, 5, 0, 7, 0, 1, 0, 0, 4, 0, 6, 10, 5, 1, 2, 7))
    bounds = ((0, None), (0, None), (0, None), (0, None), (0, None), (0, None),
              (0, None), (0, None), (0, None), (0, None), (0, None), (0, None),
              (0, None), (0, None), (0, None), (0, None))
    args_1 = (a, b)
    args_2 = (d, e)
    con = cons(args_2)
    res = minimize(fun(args_1), x0, method='SLSQP', constraints=con, bounds=bounds)
    print(res)
