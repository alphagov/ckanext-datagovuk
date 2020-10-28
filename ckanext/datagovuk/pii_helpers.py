import json

PII_LIST = [
    'author',
    'author_email',
    'maintainer',
    'maintainer_email'
]


def remove_pii_from_api_search_dataset(json_data):
    if 'result' in json_data.keys():
        json_data = json_data["result"]

    for element in json_data['results']:
        if 'data_dict' in element:
            element['data_dict'] = remove_pii_block(element['data_dict'])
        if 'validated_data_dict' in element:
            element['validated_data_dict'] = remove_pii_block(element['validated_data_dict'])
        if 'extras' in element:
            element['extras'] = remove_pii(element['extras'])
        if hasattr(element, 'keys'):
            element = remove_pii(element)

    return json.dumps(json_data)


def remove_pii_from_list(search_results):
    for element in search_results['results']:
        remove_pii(element)
    return search_results


def remove_pii(element):
    valid_element = {}
    for key in element.keys():
        if key not in PII_LIST:
            valid_element[key] = element[key]
    return valid_element


def remove_pii_block(data):
    json_data = json.loads(data)
    new_json_data = {}
    for key in json_data.keys():
        if key == 'extras':
            extras = [e for e in json_data['extras'] if e['key'] not in PII_LIST]
            new_json_data['extras'] = extras
        elif key not in PII_LIST:
            new_json_data[key] = json_data[key]

    return json.dumps(new_json_data)
