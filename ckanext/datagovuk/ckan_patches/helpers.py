import dominate
import dominate.tags as dom_tags
from markupsafe import Markup, escape
from typing import Any

from ckan.lib.helpers import _preprocess_dom_attrs, literal, core_helper


@core_helper
def link_to(label: str, url: str, **attrs: Any) -> Markup:
    attrs = _preprocess_dom_attrs(attrs)
    attrs['href'] = url
    if label == '' or label is None:
        label = url

    # without dominate.util.raw the returned literal has encoding within it
    return literal(dom_tags.a(dominate.util.raw(label), **attrs))


import ckan.lib.helpers
ckan.lib.helpers.link_to = link_to
