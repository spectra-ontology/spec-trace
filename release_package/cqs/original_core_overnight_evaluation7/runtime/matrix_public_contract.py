"""Value-free public schema for explicitly declared matrix representations."""
from copy import deepcopy

def public_matrix_representation(task):
    descriptor=task.get('collection',{}).get('matrix_representation')
    if descriptor is None:
        return None
    roles=[descriptor[k] for k in ('row_field','column_field','value_field')]
    fields={f['name']:f for f in task['required_fields']}
    if descriptor['kind']!='cartesian_cells' or len(set(roles))!=3 or set(roles)!=set(fields):
        raise ValueError('matrix descriptor must bind its exact three requested roles')
    if descriptor['equivalent_encodings']!=['dense_named_records','explicit_axes_default_cells']:
        raise ValueError('unsupported declared matrix encodings')
    def schema(name):
        field=fields[name]
        if field['type'] not in {'string','integer','number','boolean'}:
            raise ValueError('matrix axis/cell must have a declared scalar schema')
        types=[field['type'],'null'] if field.get('nullable') else field['type']
        return {'type':types}
    row,column,value=roles
    props={
      'rowField':{'const':row},'columnField':{'const':column},'valueField':{'const':value},
      'rowValues':{'type':'array','items':schema(row)},
      'columnValues':{'type':'array','items':schema(column)},
      'default':{'const':descriptor['default_value']},
      'cells':{'type':'array','items':{'type':'object','required':roles,
         'properties':{name:schema(name) for name in roles},'additionalProperties':False}}}
    matrix={'type':'object','required':list(props),'properties':props,'additionalProperties':False}
    public={k:deepcopy(descriptor[k]) for k in
      ('kind','row_field','column_field','value_field','default_value','equivalent_encodings')}
    public['sparse_record_json_schema']={'type':'object','required':['matrix'],
      'properties':{'matrix':matrix},'additionalProperties':False}
    public['representation_rule']='Either dense named cell records, or records:[{matrix:...}] matching sparse_record_json_schema. Sparse output must explicitly list every row-axis and column-axis value for the complete requested population; default applies only within those supplied axes. No axes or nonzero cell values are inferred. Identical repeated labels/cells are idempotent; conflicting cell values are invalid.'
    return public
