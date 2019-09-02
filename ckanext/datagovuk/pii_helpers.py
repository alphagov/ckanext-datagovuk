PII_LIST = [
    'author',
    'author_email',
    'contact-name',
    'contact-phone',
    'contact-email',
    'maintainer',
    'maintainer_email'
]


def remove_pii_from_list(search_results):
    for element in search_results['results']:
        remove_pii(element)
    return search_results


def remove_pii(element):
    for key in element.keys():
        if key in PII_LIST:
            del element[key]
    return element
