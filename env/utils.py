def dist_point(p1: list(int), target: list(int)):
    x = abs(p1[0] - target[0])
    y = abs(p1[1] - target[1])
    return (x + y)**2
