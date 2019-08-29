import json

PII_LIST = [
    'author',
    'author_email',
    'contact-name',
    'contact-phone',
    'contact-email',
    'maintainer',
    'maintainer_email'
]


def remove_pii_from_api_search_dataset(data):
        json_data = json.loads(data)

        for element in json_data['results']:
            element['data_dict'] = remove_pii_block(element['data_dict'])
            element['validated_data_dict'] = remove_pii_block(element['validated_data_dict'])
            element['extras'] = remove_pii(element['extras'])

        return json.dumps(json_data)


def remove_pii_from_list(search_results):
    for element in search_results['results']:
        remove_pii(element)
    return search_results


def remove_pii(element):
    for key in element.keys():
        if key in PII_LIST:
            del element[key]
    return element


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
