import re
from ckan.lib.munge import munge_tag

def remove_duplicates_in_a_list(list_):
    seen = []
    seen_add = seen.append
    return [x for x in list_ if not (x in seen or seen_add(x))]

def munge_tags(package_dict):
    tags = package_dict.get('tags', [])
    tags = [munge_tag(t['name']) for t in tags if t]
    tags = [t for t in tags if t != '__']  # i.e. just padding
    tags = remove_duplicates_in_a_list(tags)
    package_dict['tags'] = [dict(name=name) for name in tags]

def get_licence_fields_from_free_text(licence_str):
    '''Using a free text licence (e.g. harvested), this func returns license_id
    and licence extra ready to be saved to the dataset dict. It returns a blank
    licence if it is wholely expressed by the license_id.

    return (license_id, licence)
    '''
    license_id, is_wholely_identified = \
        detect_license_id(licence_str)
    if license_id and is_wholely_identified:
        licence = None
    else:
        licence = licence_str
    return (license_id, licence)


licence_regexes = None


def detect_license_id(licence_str):
    '''Given licence free text, detects if it mentions a known licence.

    :returns (license_id, is_wholely_identified)
    '''
    license_id = ''

    global licence_regexes
    if licence_regexes is None:
        licence_regexes = {}
        licence_regexes['ogl'] = [
            re.compile('open government licen[sc]e', re.IGNORECASE),
            re.compile(r'\b\(ogl\)\b', re.IGNORECASE),
            re.compile(r'\bogl\b', re.IGNORECASE),
            re.compile(r'<?https?\:\/\/www.nationalarchives\.gov\.uk\/doc\/open-government-licence[^\s]*'),
            re.compile(r'<?http\:\/\/www.ordnancesurvey\.co\.uk\/oswebsite\/docs\/licences\/os-opendata-licence.pdf'),  # because it redirects to OGL now
            ]
        licence_regexes['ogl-detritus'] = re.compile(
            r'(%s)' % '|'.join((
                'OGL Terms and Conditions apply',
                r'\bUK\b',
                'v3\.0',
                'v3',
                'version 3',
                'for public sector information',
                'Link to the',
                'Ordnance Survey Open Data Licence',
                'Licence',
                'None',
                'OGLs and agreements explained',
                'In accessing or using this data, you are deemed to have accepted the terms of the',
                'attribution required',
                'Use of data subject to the Terms and Conditions of the OGL',
                'data is free to use for provided the source is acknowledged as specified in said document',
                'Released under the OGL',
                'citation of publisher and online resource required on reuse',
                'conditions',
                'Public data \(Crown Copyright\)',
                '[;\.\-:\(\),]*',
                )), re.IGNORECASE
            )
        licence_regexes['spaces'] = re.compile(r'\s+')
    is_ogl = False
    for ogl_regex in licence_regexes['ogl']:
        licence_str, replacements = ogl_regex.subn('OGL', licence_str)
        if replacements:
            is_ogl = True
    if is_ogl:
        license_id = 'uk-ogl'
        # get rid of phrases that just repeat existing OGL meaning
        licence_str = licence_regexes['ogl-detritus'].sub('', licence_str)
        licence_str = licence_str.replace('OGL', '')
        licence_str = licence_regexes['spaces'].sub(' ', licence_str)
        is_wholely_identified = bool(len(licence_str) < 2)
    else:
        is_wholely_identified = None

    return license_id, is_wholely_identified

def themes():
    themes_dict = {
        "business-and-economy": "Business and economy",
        "environment": "Environment",
        "mapping": "Mapping",
        "crime-and-justice": "Crime and justice",
        "government": "Government",
        "society": "Society",
        "defence": "Defence",
        "government-spending": "Government spending",
        "towns-and-cities": "Towns and cities",
        "education": "Education",
        "health": "Health",
        "transport": "Transport",
    }
    return themes_dict

