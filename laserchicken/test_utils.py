from laserchicken.keys import point


def generate_test_point_cloud():
    pc = {point: {'x': {'type': 'double', 'data': [1, 2, 3]}, 'y': {'type': 'double', 'data': [2, 3, 4]},
                     'z': {'type': 'double', 'data': [3, 4, 5]}}}
    return pc
