import os
import shutil
import unittest
import numpy as np

from pytest import raises

from laserchicken import keys


def read(path):
    if not os.path.exists(path):
        raise FileNotFoundError('File not found: {}'.format(path))

    with open(path, 'r') as ply:
        try:
            first_line = ply.readline()
        except UnicodeDecodeError:
            first_line = ''

        if 'ply' not in first_line:
            raise ValueError('Not a valid ply file: {}'.format(path))

        index = read_header(ply)
        result = {block['type']: read_block(block, ply) for block in index}
        return result


def read_header(ply):
    index = []
    for line in ply:
        if line[:8] == 'element ':
            element_type = line.split()[1]
            number_of_elements = int(line.split()[2])
            current_properties = []
            index.append(
                {'type': element_type, 'number_of_elements': number_of_elements, 'properties': current_properties})

        if line[:9] == 'property ':
            property_type, property_name = line[9:].strip('\n').split(' ')
            current_properties.append({'type': property_type, 'name': property_name})

        if line.strip() == 'end_header':
            break
    return index


def read_block(block, ply_body):
    properties, property_names = get_properties(block)
    block_type = block['type']
    number_of_elements = block['number_of_elements']

    read_elements(ply_body, properties, property_names, block_type, number_of_elements)
    return properties


def cast(value, value_type):
    if value_type == 'float':
        dtype = np.float32
    elif value_type == 'double':
        dtype = np.float64
    elif value_type == 'int':
        dtype = np.int32
    else:
        raise ValueError('Invalid type: {}'.format(value_type))
    return dtype(value)


def read_elements(ply_body, properties, property_names, block_type, number_of_elements):
    for i in range(number_of_elements):
        line = ply_body.readline()
        values = line.split(' ')
        if len(values) != len(property_names):
            raise ValueError('Error reading line {} of {} list.'.format(i, block_type))
        for p, property_name in enumerate(property_names):
            property_type = properties[property_name]['type']
            value = cast(values[p], property_type)
            properties[property_name]['data'][i] = value


def get_properties(block):
    properties = {}
    property_names = []
    for prop in block['properties']:
        if prop['type'] == 'float':
            dtype = np.float32
        elif prop['type'] == 'double':
            dtype = np.float64
        elif prop['type'] == 'int':
            dtype = np.int32
        else:
            raise ValueError('Property has no valid type: {}'.format(prop))
        property_name = prop['name']
        properties[property_name] = {'type': prop['type'], 'data': np.zeros(block['number_of_elements'], dtype)}
        property_names.append(property_name)
    return properties, property_names


class TestReadPly(unittest.TestCase):
    _test_dir = 'TestLoad_dir'
    _test_file_name = 'example.ply'
    _las_file_name = '5points.las'
    _test_data_source = 'testdata'
    las_file_path = os.path.join(_test_dir, _las_file_name)
    test_file_path = os.path.join(_test_dir, _test_file_name)

    def test_unexistentFile_error(self):
        with raises(OSError):
            read('nonexistentfile.ply')

    def test_wrongFormat_error(self):
        with raises(ValueError):
            read(self.las_file_path)

    def test_existentPly_noError(self):
        read(self.test_file_path)

    def test_containsPointsElement(self):
        data = read(self.test_file_path)
        self.assertIn(keys.point, data)

    def test_containsXElement(self):
        data = read(self.test_file_path)
        self.assertIn('x', data[keys.point])

    def test_rightNumberOfPoints(self):
        data = read(self.test_file_path)
        self.assertEqual(len(data[keys.point]['x']['data']), 3)

    def test_correctPoints(self):
        data = read(self.test_file_path)
        points = data[keys.point]
        point = np.array(
            [points['x']['data'][0], points['y']['data'][0], points['z']['data'][0], points['return']['data'][0]])
        np.testing.assert_allclose(point, np.array([0.11, 0.12, 0.13, 1]))

    def setUp(self):
        os.mkdir(self._test_dir)
        shutil.copyfile(os.path.join(self._test_data_source, self._test_file_name), self.test_file_path)
        shutil.copyfile(os.path.join(self._test_data_source, self._las_file_name), self.las_file_path)

    def tearDown(self):
        shutil.rmtree(self._test_dir)
