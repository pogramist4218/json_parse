import os
import json
import pathlib
import difflib
import jsonschema

messages = {}
schemas = {}

rows = ''

types = {
    'integer': 'число (целое)',
    'string': 'строку',
    'number': 'число (вещественное)',
    'boolean': 'булевое значение',
    'array': 'массив',
    'object': 'объект',
    'null': 'нулевое значение'
}

def degreeOfSimularity(check, exist):
    return difflib.SequenceMatcher(None, check.lower(), exist.lower()).ratio()


def schemaExist(name):
    schema_path = './schema/' + name + '.schema'
    if not os.path.isfile(schema_path):
        degree = 0.0
        for f in os.listdir('./schema/'):
            _ = str(pathlib.Path(f).stem)
            if degreeOfSimularity(name, _) > degree and degreeOfSimularity(name, _) >= 0.5:
                degree = degreeOfSimularity(name, _)
                schema_path = './schema/' + _ + '.schema'
        if degree < 0.5:
            return False
    return schema_path


def loadSchema(schema_path):
    with open(schema_path, 'r', encoding='utf-8') as file:
        _ = json.load(file)
    return _


for data in os.listdir('./event/'):
    with open('./event/' + data, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    messages[data] = []
    if json_data and json_data['data']:
        schema_path = schemaExist(json_data['event'])
        if schema_path:
            schemas[data] = schema_path
            schema = loadSchema(schema_path)
            validator = jsonschema.Draft4Validator(schema)
            errors = sorted(validator.iter_errors(json_data['data']), key=lambda e: e.validator)
            if errors:
                for err in errors:
                    if err.validator == 'required':
                        for item in err.validator_value:
                            if not item in err.instance:
                                if err.absolute_path:
                                    messages[data].append('Нет параметра {param} из списка обязательных параметров {required} у элемента №{index} родительского элемента {parent}'
                                                          .format(param=item, required=err.validator_value, index=err.absolute_path.pop(), parent=err.absolute_path.pop()))
                                else:
                                    messages[data].append(
                                        'Нет параметра {param} из списка обязательных параметров {required} у родительского элемента data'
                                        .format(param=item, required=err.validator_value))
                    elif err.validator == 'type':
                        messages[data].append('Ошибка типа значения параметра {param}: измените значение "{value}" параметра на {type}'
                                              .format(param=err.absolute_path.pop(), value=err.instance, type=types[err.validator_value]))
            else:
                messages[data].append('Ошибок не найдено')
        else:
            messages[data].append('Нет подходящей схемы для валидации')
            schemas[data] = ''
    else:
        messages[data].append('Пустой JSON-файл')
        schemas[data] = ''

for data in messages:
    rows += '<tr><td rowspan="{count}">./event/{data}</td><td rowspan="{count}">{schema}</td>'.format(count=len(messages[data]), data=data, schema=schemas[data])
    for message in messages[data]:
        rows += '<td>{message}</td></tr><tr>'.format(message=message)
    rows += '</tr>'

with open('./errors_old.html', 'r', encoding='utf-8') as file:
    table = file.read()

table = table.format(messages=rows)

with open('./errors.html', 'w', encoding='utf-8') as file:
    file.write(table)
