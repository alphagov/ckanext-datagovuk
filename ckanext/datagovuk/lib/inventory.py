import logging
from io import BytesIO
import os
from html.parser import HTMLParser
import datetime

import lxml.etree

log = logging.getLogger(__name__)

NSMAP = {'inv': 'http://schemas.esd.org.uk/inventory'}


class InventoryXmlError(Exception):
    pass


class InventoryDocument(object):
    """
    Represents an Inventory XML document. It can be validated and parsed to
    extract its content.
    """

    def __init__(self, inventory_xml_string):
        """
        Initialize with an Inventory XML string.
        It validates it against the schema and therefore may raise
        InventoryXmlError
        """
        # Load the XSD and make sure we use it to validate the incoming
        # XML
        schema_content = self._load_schema()
        schema = lxml.etree.XMLSchema(schema_content)
        parser = lxml.etree.XMLParser(schema=schema)

        # Load and parse the Inventory XML
        xml_file = BytesIO.StringIO(inventory_xml_string)
        try:
            self.doc = lxml.etree.parse(xml_file, parser=parser)
        except lxml.etree.XMLSyntaxError as e:
            raise InventoryXmlError(unicode(e))
        finally:
            xml_file.close()

    def _load_schema(self):
        d = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))
        f = os.path.join(d, "inventory.xsd")
        return lxml.etree.parse(f)

    def top_level_metadata(self):
        """
        Extracts the top-level inv:Metadata from the XML document, and returns
        it in a dictionary.
        """
        md = {}

        root = self.doc.getroot()
        modified_str = root.get('Modified')
        md['modified'] = datetime.datetime.strptime(modified_str, '%Y-%m-%d').date() if modified_str else None
        md['identifier'] = self._get_node_text(root.xpath('inv:Identifier', namespaces=NSMAP))
        md['title'] = self._get_node_text(root.xpath('inv:Metadata/inv:Title', namespaces=NSMAP))
        md['publisher'] = self._get_node_text(root.xpath('inv:Metadata/inv:Publisher', namespaces=NSMAP))
        md['description'] = self._get_node_text(root.xpath('inv:Metadata/inv:Description', namespaces=NSMAP))
        md['spatial-coverage-url'] = self._get_node_text(root.xpath('inv:Metadata/inv:Coverage/inv:Spatial', namespaces=NSMAP))

        return md

    def dataset_nodes(self):
        """
        Yields each inv:Dataset within the XML document as a node
        """
        for node in self.doc.xpath('/inv:Inventory/inv:Datasets/inv:Dataset', namespaces=NSMAP):
            yield node

    @staticmethod
    def serialize_node(node):
        # using the inclusive_ns_prefixes option so that it adds in the inv
        # namespace in the top-level tag:
        #   xmlns:inv="http://schemas.esd.org.uk/inventory"
        # since otherwise it complains when parsing it
        return lxml.etree.tostring(node, inclusive_ns_prefixes=['inv'])

    @staticmethod
    def _get_node_text(node, default=''):
        """
        Retrieves the text from the result of an xpath query, or
        the default value.
        """
        if node:
            return node[0].text
        return default

    @classmethod
    def parse_xml_string(cls, node_xml_string):
        """
        Converts a Dataset node serialized as an XML string to an etree node.
        """
        # do getroot() so that we return an Element rather than an ElementTree,
        # since thats what dataset_to_dict wants.
        return lxml.etree.parse(BytesIO.StringIO(node_xml_string)).getroot()


    @classmethod
    def dataset_to_dict(cls, node):
        """
        Converts a Dataset node to a dictionary, complete with the resources
        """
        d = {}
        d['identifier'] = cls._get_node_text(node.xpath('inv:Identifier',namespaces=NSMAP))
        d['title'] = cls._get_node_text(node.xpath('inv:Title',namespaces=NSMAP))
        modified_str = node.get('Modified')
        d['modified'] = datetime.datetime.strptime(modified_str, '%Y-%m-%d').date() if modified_str else None
        d['active'] = node.get('Active') in ['True', 'Yes']
        d['description'] = cls._get_node_text(node.xpath('inv:Description',namespaces=NSMAP))
        d['rights'] = cls._get_node_text(node.xpath('inv:Rights',namespaces=NSMAP))
        if d['rights'] == 'http://www.nationalarchives.gov.uk/doc/open-government-licence':
            d['rights'] = 'http://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/'

        # Clean description to decode any encoded HTML
        h = HTMLParser()
        d['description'] = h.unescape(d.get('description', ''))

        services = []
        functions = []
        svc = cls._get_node_text(node.xpath('inv:Subjects/inv:Subject/inv:Service', namespaces=NSMAP))
        fn = cls._get_node_text(node.xpath('inv:Subjects/inv:Subject/inv:Function', namespaces=NSMAP))
        if svc:
            services.append(svc)
        if fn:
            functions.append(fn)

        d['services'] = services
        d['functions'] = functions
        d['resources'] = []
        for resnode in node.xpath('inv:Resources/inv:Resource', namespaces=NSMAP):
            d['resources'].extend(cls.resource_to_dict(resnode))
        return d

    @classmethod
    def resource_to_dict(cls, node):
        """
        When passed an inv:Resource node this method will flatten down all of the
        inv:Renditions into CKAN resources.
        """

        res = {}
        for n in node.xpath('inv:Renditions/inv:Rendition', namespaces=NSMAP):
            res['url'] = cls._get_node_text(n.xpath('inv:Identifier', namespaces=NSMAP))
            # If no active flag, default to active.
            res['active'] = n.get('Active') in ['Yes', 'True', '', None]
            res['resource_type'] = n.get('Type')
            res['title'] = cls._get_node_text(n.xpath('inv:Title', namespaces=NSMAP))
            res['description'] = cls._get_node_text(n.xpath('inv:Description', namespaces=NSMAP))
            res['mimetype'] = cls._get_node_text(n.xpath('inv:MimeType', namespaces=NSMAP))
            res['availability'] = cls._get_node_text(n.xpath('inv:Availability', namespaces=NSMAP))
            res['conforms_to'] = cls._get_node_text(n.xpath('inv:ConformsTo', namespaces=NSMAP))
            yield res
