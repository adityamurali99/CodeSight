def calculate(x, y, op):
    # Bad variable names, no docstrings, and nested logic
    if op == "add":
        return x + y
    elif op == "sub":
        if x > 0:
            if y > 0:
                return x - y
            else:
                return x - y # Redundant logic
    return None

def global_variable_mess():
    global data
    data = [i for i in range(100)]
    for x in data:
        print(x)