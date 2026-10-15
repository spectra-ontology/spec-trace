"""Lossless explicit-axis matrix decoding; never reads gold or source data.

Dense named records are returned unchanged. Sparse records need complete explicit
axes and a declared default. No missing axis or source value is inferred.
"""
class MatrixRepresentationError(ValueError):
    pass


def normalize_matrix_records(contract, records, typed):
    descriptor = contract.get('collection', {}).get('matrix_representation')
    if descriptor is None:
        return records
    if type(records) is not list:
        raise MatrixRepresentationError('records must be a list')
    if not (len(records) == 1 and type(records[0]) is dict and set(records[0]) == {'matrix'}):
        return records
    if set(records[0]) != {'matrix'}:
        raise MatrixRepresentationError('sparse wrapper must contain its matrix')
    matrix = records[0]['matrix']
    keys = {'rowField', 'columnField', 'valueField', 'rowValues', 'columnValues', 'default', 'cells'}
    if type(matrix) is not dict or set(matrix) != keys:
        raise MatrixRepresentationError('sparse matrix needs fields, axes, default and cells')
    names = [descriptor[k] for k in ('row_field', 'column_field', 'value_field')]
    if len(set(names)) != 3 or descriptor['kind'] != 'cartesian_cells':
        raise MatrixRepresentationError('invalid declared matrix roles')
    if [matrix[k] for k in ('rowField', 'columnField', 'valueField')] != names:
        raise MatrixRepresentationError('sparse fields differ from declared roles')
    fields = {f['name']: f for f in contract['required_fields']}
    if set(fields) != set(names):
        raise MatrixRepresentationError('declared matrix must have its three cell roles')
    schemas = {name: typed.field_schema(fields[name]) for name in names}
    row, column, value = names

    def token(name, cell):
        try:
            return typed.typed_token(cell, schemas[name], fields[name].get('nested_array_semantics'), '$')
        except (ValueError, TypeError, KeyError) as exc:
            raise MatrixRepresentationError('wrong typed ' + name) from exc

    if token(value, matrix['default']) != token(value, descriptor['default_value']):
        raise MatrixRepresentationError('matrix default differs from declared value')

    def axis(name, values):
        if type(values) is not list:
            raise MatrixRepresentationError('axis must be explicit list')
        # Identical repeated axis labels are the same set member.
        unique = {}
        for item in values:
            unique.setdefault(token(name, item), item)
        return unique

    row_values = axis(row, matrix['rowValues'])
    column_values = axis(column, matrix['columnValues'])
    if type(matrix['cells']) is not list:
        raise MatrixRepresentationError('cells must be named records')
    cells = {}
    for cell in matrix['cells']:
        if type(cell) is not dict or set(cell) != set(names):
            raise MatrixRepresentationError('cell needs exactly its declared roles')
        rt, ct, vt = (token(name, cell[name]) for name in names)
        if rt not in row_values or ct not in column_values:
            raise MatrixRepresentationError('cell lies outside explicit axes')
        coordinate = (rt, ct)
        if coordinate in cells and cells[coordinate][0] != vt:
            raise MatrixRepresentationError('conflicting values at one coordinate')
        cells[coordinate] = (vt, cell[value])
    return [{row: rv, column: cv, value: cells.get((rt, ct), (None, matrix['default']))[1]}
            for rt, rv in row_values.items() for ct, cv in column_values.items()]
