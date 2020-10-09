"""Tests for user_auth API"""
from ckan import model
from ckan import logic
from ckan.tests import factories, helpers
from ckanext.harvest import model as harvest_model

from ckanext.datagovuk.tests.db_test import DBTest
import ckanext.datagovuk.helpers as h

class TestHelpers(DBTest):
    def setUp(self):
        super(self.__class__, self).setUp()

        harvest_model.setup()
        self.context = {
            "user": factories.Sysadmin()["name"]
        }

    def test_split_values_multiple(self):
        string_to_test = '{value_a,value_b,value_c}'
        list_output = ['value_a', 'value_b', 'value_c']
        self.assertEqual(h.split_values(string_to_test), list_output)

    def test_split_values_single(self):
        string_to_test = 'value_a'
        list_output = ['value_a']
        self.assertEqual(h.split_values(string_to_test), list_output)

    def test_alphabetise_dict(self):
        some_dict = {
            "key_c": "value_c",
            "key_b": "value_b",
            "key_a": "value_a",
        }
        ordered_list = [
            ("key_a", "value_a"),
            ("key_b", "value_b"),
            ("key_c", "value_c"),
        ]
        self.assertEqual(h.alphabetise_dict(some_dict), ordered_list)

    def test_roles(self):
        roles_list = ['Admin', 'Editor']
        self.assertEqual(h.roles(), roles_list)

    def test_themes(self):
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
        self.assertEqual(h.themes(), themes_dict)

    def test_schemas(self):
        schemas_dict = {
            "eca31d0d-e78e-445f-957d-38b0463989a4": "Brownfield Land Register - 2017 Regulations - https://raw.githubusercontent.com/iStandUK/BrownfieldLandRegister/master/schema/brownfieldlandregister2017.json",
            "25c4b1eb-05b4-45dc-9c95-f0e0c0cf1c45": "Brownfield Site Register - 2017 Regulations - https://raw.githubusercontent.com/iStandUK/BrownfieldSiteRegister/master/schema/brownfieldsiteregister-v1.json",
            "e3e873c7-035d-4e6c-8037-d7d77e70ce59": "Clinics - https://raw.githubusercontent.com/datagovuk/health-schemas/master/Clinics.json",
            "4f43aae8-01be-4e3b-8aac-69899226a9e2": "Counter fraud activity (for LGTC) - https://github.com/datagovuk/schemas/raw/master/local-gov/fraud.json",
            "f0b8313f-8020-4e47-add7-091c066aa2fc": "Data Cube vocabulary for RDF - http://purl.org/linked-data/cube#",
            "f3f5139b-1603-4cdc-a092-882b205dc969": "Election Results - http://schemas.opendata.esd.org.uk/ElectionResults",
            "e1b2c7ab-6107-48d0-98b3-82358d00b4fe": "European Air Quality e-Reporting (by Eionet) - http://dd.eionet.europa.eu/schemas/id2011850eu-1.0/AirQualityReporting.xsd",
            "ba0055c2-fa2d-4b02-af01-c2904b4eab92": "GML - Geography Markup Language (by OGC) - http://www.opengeospatial.org/standards/gml",
            "2fbf0419-37a2-4299-a8fc-ee081fa91bb6": "GP - https://raw.githubusercontent.com/datagovuk/health-schemas/master/GP.json",
            "4145055b-3a32-4c80-80c4-95a04099de95": "GPOpeningTimes - https://raw.githubusercontent.com/datagovuk/health-schemas/master/GPOpeningTimes.json",
            "dfc41bd1-f68d-4202-89d4-a0147ca9ae27": "GPServices - https://raw.githubusercontent.com/datagovuk/health-schemas/master/GPServices.json",
            "9cb734b0-9667-41e3-b4b8-577e334be2e6": "GPStaff - https://raw.githubusercontent.com/datagovuk/health-schemas/master/GPStaff.json",
            "0365ac97-e11f-41c8-8f23-e207d87500bb": "General Transit Feed Specification (GTFS) - https://developers.google.com/transit/gtfs/",
            "9c4d8c86-7c6d-447f-b811-dece7e42a552": "HAJourneyTime - https://raw.githubusercontent.com/datagovuk/transport-schemas/master/HAJourneyTime.json",
            "2bf4046c-d3d2-44b3-872f-db5e1d68ec34": "Hospital - https://raw.githubusercontent.com/datagovuk/health-schemas/master/Hospital.json",
            "d033c234-7594-4e97-8969-56be0d3a0f03": "House Price Index ontology (Land Registry) - http://landregistry.data.gov.uk/def/hpi/",
            "d79ca75a-1d2e-42d5-b898-addc4f1e53df": "IF136 - https://raw.githubusercontent.com/datagovuk/transport-schemas/master/IF136.json",
            "719832eb-bcd4-4f77-9745-6f9250968b80": "IF145 - https://raw.githubusercontent.com/datagovuk/transport-schemas/master/IF145.json",
            "3c29cdc4-35cb-446d-a704-c520bee1dfcf": "IF157 - https://raw.githubusercontent.com/datagovuk/transport-schemas/master/IF157.json",
            "120a04c9-3f60-4f73-a575-bda4ee170f0f": "Land and building assets (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/LandAssets",
            "a90a56a0-0bea-4098-9bc6-2ffa6db59751": "NaPTAN - https://www.gov.uk/government/publications/national-public-transport-access-node-schema",
            "55118e63-5823-4d6e-bca4-c6f1f012b20b": "National Biodiversity Network Exchange Format - http://www.nbn.org.uk/Share-Data/Providing-Data/NBN-Data-Exchange-format.aspx",
            "ce3f1a4a-6eea-4df7-be88-307aba8b387b": "OWL 2 Schema RDF vocabulary - http://www.w3.org/2002/07/owl#",
            "9173d66d-0c54-4a95-a6b4-61e8ca9bb685": "Optician - https://raw.githubusercontent.com/datagovuk/health-schemas/master/Optician.json",
            "324d1f89-cbf3-4c93-aa6f-41c5abf68139": "OpticianOpeningTimes - https://raw.githubusercontent.com/datagovuk/health-schemas/master/OpticianOpeningTimes.json",
            "538b857a-64ba-490e-8440-0e32094a28a7": "Organisation structure (org chart / organogram for local authority) (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/OrganisationStructure",
            "d3c0b23f-6979-45e4-88ed-d2ab59b005d0": "Organisation structure including senior roles &amp; salaries (org chart / organogram for central government departments and agencies) - https://github.com/datagovuk/schemas/tree/master/organogram",
            "c7ae02ed-2d38-450a-a00f-24d707e093ee": "Pay multiples across an organisation (for LGTC) - https://github.com/datagovuk/schemas/raw/master/local-gov/pay_multiples.json",
            "db9476b0-a559-44c1-879a-02031605460f": "Pharmacy - https://raw.githubusercontent.com/datagovuk/health-schemas/master/Pharmacy.json",
            "bea6470a-42ef-47d0-9ca8-e30b017a92ea": "PharmacyOpeningTimes - https://raw.githubusercontent.com/datagovuk/health-schemas/master/PharmacyOpeningTimes.json",
            "acebf12d-2833-4ff0-899c-ce978c3973fb": "PharmacyServices - https://raw.githubusercontent.com/datagovuk/health-schemas/master/PharmacyServices.json",
            "81a5a4ef-35d7-4edb-8161-719dfb1342ce": "Planning Applications (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/planningapplications/PlanningApplications.json",
            "b1800329-58d0-4734-a407-3b8f1b53849c": "Premises Licences (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/premiseslicences/PremisesLicences.json",
            "95347050-b73d-4ef6-a97e-bf5de649344b": "Price Paid Data ontology (Land Registry) - http://landregistry.data.gov.uk/def/ppi/",
            "2c65118f-6cc5-4769-9933-01e8a2b61b7e": "Procurement Information (Local authority contracts) (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/Contracts",
            "0f36b093-0081-47e1-a050-189883a53f7a": "Public Toilets (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/publictoilets/PublicToilets.json",
            "4ef2066e-7ec6-4d15-8999-831f74a67736": "RDF Concepts vocabulary - http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "eb53ce9c-c263-4382-bec5-08e35492045e": "RDF Schema vocabulary (RDFS) - http://www.w3.org/2000/01/rdf-schema#",
            "31bd397b-d951-418c-bd4e-477934702009": "Rail Common Interface File (CIF) - http://www.atoc.org/clientfiles/files/RSPDocuments/20070801.pdf",
            "ac612ead-19ea-44e6-91f4-b7acbff46213": "SCL - https://raw.githubusercontent.com/datagovuk/health-schemas/master/SCL.json",
            "cb33335e-2e30-42f4-94b4-9fa5d592ca56": "SCLServices - https://raw.githubusercontent.com/datagovuk/health-schemas/master/SCLServices.json",
            "01e0137a-3679-475f-ab0c-e355dbe70938": "SCP - https://raw.githubusercontent.com/datagovuk/health-schemas/master/SCP.json",
            "6ad34b7c-c29b-4120-9da5-67fd44ce1a06": "STATS19 Road accident with injury (police)",
            "e39e5b58-6e15-4575-9e7d-3d02bd6d5018": "Salary counts of senior employees of a local authority (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/SeniorSalaryCount",
            "cc520a16-9511-4129-86de-4eb3edeb235c": "Senior employees of a local authority (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/SeniorEmployees",
            "bfa35ece-b4f4-4855-84f7-336d73238938": "Service Interface for Real Time Information (SIRI) (for public transport) - http://www.siri.org.uk/",
            "92f525c2-8830-4436-bedc-24581d733de6": "Simple Knowledge Organization System (SKOS) RDF vocabulary - http://www.w3.org/2004/02/skos/core#",
            "9d0a5055-46aa-4795-b8ae-f1f5b283967e": "Spend over &#163;25,000 by central government &amp; NHS (expenditure transactions exceeding &#163;25k) (HM Treasury guidelines) - https://github.com/datagovuk/schemas/raw/master/spend-hmt/spend-25k.json",
            "8e4fd0b6-ba36-4d06-a807-554a7c9fe679": "Spend over &#163;500 by local authority (Expenditure transactions exceeding &#163;500) (for LGTC by LGA) - http://schemas.opendata.esd.org.uk/Spend",
            "27dadbaf-e9df-4955-a485-309df39f80f0": "Trade union facility time (for LGTC) - https://github.com/datagovuk/schemas/raw/master/local-gov/trade_union_facility_time.json",
            "8a0ca7ce-9348-45c4-be21-d7eb289a2a99": "TransXChange - https://www.gov.uk/government/publications/transxchange-downloads-and-schema",
            "3b1417e9-4624-41d7-bd7e-9fc00f314d8e": "Transaction figures ontology (Land Registry) - http://landregistry.data.gov.uk/def/trans/",
            "c191e70d-83a3-47d8-97ca-3250132631bf": "eauth - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eauth.json",
            "67eed9ea-9de2-4a79-b7d5-86668e9e7e7c": "ebranch - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ebranch.json",
            "4ba73117-b400-4c09-890b-ffa2171393ea": "ecarehomehq - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ecarehomehq.json",
            "20da4052-0693-47e1-b218-55718766085d": "ecarehomesite - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ecarehomesite.json",
            "f5e97bbb-6868-4587-9435-7a29d1591cf6": "eccg - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eccg.json",
            "dd86e987-f511-4b07-aca8-b298569fa8d5": "eccgsite - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eccgsite.json",
            "3043a1bc-6b95-453d-a2df-acf988ff80b6": "econcur - https://raw.githubusercontent.com/datagovuk/health-schemas/master/econcur.json",
            "2355b5bc-34ea-48b0-b11f-58443131583e": "ecsu - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ecsu.json",
            "f6127793-e219-426f-85e9-c0f5944803c6": "ecsusite - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ecsusite.json",
            "790975c7-1241-4308-8f95-f39d9ceb19cb": "ect - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ect.json",
            "656c22ea-b781-4635-bb51-3ad101523282": "ectsite - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ectsite.json",
            "c5821fb0-e2ab-4acd-b2bc-65ccab53a04b": "edconcur - https://raw.githubusercontent.com/datagovuk/health-schemas/master/edconcur.json",
            "397bccd2-0117-4939-8070-8909ef3b205b": "edispensary - https://raw.githubusercontent.com/datagovuk/health-schemas/master/edispensary.json",
            "199dc347-1f17-4770-82d5-584fb356c886": "educate - https://raw.githubusercontent.com/datagovuk/health-schemas/master/educate.json",
            "04f3c6b9-19c9-40f0-b3ff-08f75a5e6847": "egdp - https://raw.githubusercontent.com/datagovuk/health-schemas/master/egdp.json",
            "e2a87d56-4dd2-488d-85d2-b5d14dd1e800": "egdpprac - https://raw.githubusercontent.com/datagovuk/health-schemas/master/egdpprac.json",
            "bb13e6f9-beac-4006-8dac-3b511f6175bd": "egdppracmem - https://raw.githubusercontent.com/datagovuk/health-schemas/master/egdppracmem.json",
            "19eba8f1-df9b-4799-a1dd-5398a9f62f0f": "egpcur - https://raw.githubusercontent.com/datagovuk/health-schemas/master/egpcur.json",
            "d77808c2-d2b6-43cd-adc0-00c6448ce24a": "ehospice - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ehospice.json",
            "3c24eef6-7ecb-40d5-925e-70adb9965863": "ensa - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ensa.json",
            "dc774dfe-944a-44a7-9cff-13cd5354b5df": "enurse - https://raw.githubusercontent.com/datagovuk/health-schemas/master/enurse.json",
            "71331f7f-f5fe-4b89-8488-a4e19544dad0": "eopthq - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eopthq.json",
            "6b3743d5-ad33-4ef4-9d7b-b3896d7a8e67": "eoptsite - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eoptsite",
            "73f664b8-ae7d-4d6b-9462-3008455ae1fa": "eother - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eother.json",
            "fe935f0a-1a9e-4f16-8a8b-e344d6759f07": "epcdp - https://raw.githubusercontent.com/datagovuk/health-schemas/master/epcdp.json",
            "ecff5d1d-9091-4b96-a4d5-cd45a669b1b5": "epcmem - https://raw.githubusercontent.com/datagovuk/health-schemas/master/epcmem.json",
            "ed6a2e6c-3d4d-4a13-bf9b-fdc9cf269e2f": "epharmacyhq - https://raw.githubusercontent.com/datagovuk/health-schemas/master/epharmacyhq.json",
            "52b88e30-5469-45b9-9326-532e9adf46a0": "ephp - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ephp.json",
            "c09bf61b-ac22-4949-bcd6-8afdd7648678": "ephpsite - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ephpsite.json",
            "4a340405-3f4f-47d9-a44d-9d4ea93f38a1": "eplab - https://raw.githubusercontent.com/datagovuk/health-schemas/master/eplab.json",
            "50ab71af-0833-479f-890b-0904ad6b9b31": "epraccur - https://raw.githubusercontent.com/datagovuk/health-schemas/master/epraccur.json",
            "7be00b41-af4f-4282-b09b-394ab0b5d6ed": "epracmem - https://raw.githubusercontent.com/datagovuk/health-schemas/master/epracmem.json",
            "98ae6704-3184-4bc6-85e8-e61c6c01e7b7": "espha - https://raw.githubusercontent.com/datagovuk/health-schemas/master/espha.json",
            "8e67323d-0730-4c10-aeb1-1b9ec847d4f9": "etr - https://raw.githubusercontent.com/datagovuk/health-schemas/master/etr.json",
            "b349b66d-b0bb-4796-b559-933adfbda14e": "etreat - https://raw.githubusercontent.com/datagovuk/health-schemas/master/etreat.json",
            "15c283eb-2831-4817-9d64-c5821c8b121e": "ets - https://raw.githubusercontent.com/datagovuk/health-schemas/master/ets.json",
            "515fd756-1cf9-491c-8223-49cf435b6926": "localities - https://raw.githubusercontent.com/datagovuk/transport-schemas/master/localities.json",
            "fc3043a5-52e7-42fe-be7c-d3e0ef576c1d": "stops - https://raw.githubusercontent.com/datagovuk/transport-schemas/master/stops.json",
            "b22f3320-ab9f-4f48-b1c7-1f4732133d8c": "GC-Data-Catalogue-csv-schema - https://raw.githubusercontent.com/OrdnanceSurvey/discoverability/master/GC-Data-Catalogue-csv-schema.json",
        }
        self.assertEqual(h.schemas(), schemas_dict)

    def test_codelist(self):
            codelist_dict = {
                "7a3ce9e2-a383-4cd7-9ced-eef1b6769fe2": "Current Care Organisation Code: Clinical Commissioning Groups -",
                "f882a403-724c-4d72-bdec-413248637faf": "Current Care Organisation: Clinical Commissioning Groups -",
                "c52ccb62-03bb-4846-ae40-4d46d0118ceb": "Estate Type (Land Registry) - http://landregistry.data.gov.uk/def/ppi/estateType",
                "9b870ab5-2d5f-4d87-918a-c1f2ffebe647": "GDC Code -",
                "4622615d-d211-495b-ab07-9b7629dcb86b": "GDC Code: The Practitioners General Dental Council Code -",
                "e4a870ca-c4c8-498d-b820-f273157b8026": "GMC Code -",
                "55804660-bef5-4d38-835a-732aac634366": "GMCNumber: http://www.gmc-uk.org/doctors/register/LRMP.asp -",
                "6bb235ba-4997-41a6-9229-0e9d52ba9440": "GOR Code: Commissioning Regions, Area Teams, Government Office Regions -",
                "8223c8ac-106f-4dbd-8779-01e64c5dfe0c": "High Level Health Geography: Commissioning Regions, Area Teams, Government Office Regions -",
                "bcf8a2dd-1a63-48f2-9178-692c705074e8": "Land Registry Application counts - http://landregistry.data.gov.uk/def/trans/ApplicationCounts",
                "4d321c5a-c47f-4f7c-ac91-cff5c6cf9c34": "Location Organisation Code: NHS Trusts/Care Trusts -",
                "7d9abd07-2cb2-4eba-99d7-8edb1e7bdb6d": "National Grouping: Commissioning Regions, Area Teams, Government Office Regions -",
                "356e7994-9fbf-49ee-912b-c322da4a55d0": "OrganisationCode: General Medical Practices -",
                "9b9d4619-59ef-412f-bb4c-351f5c693865": "OrganisationCode: NHS Trust Sites -",
                "2b94685b-91c2-40d3-8ae0-71676c8a49a2": "OrganisationCode: Regulated Care Providers -",
                "6a854309-9267-4814-96db-74c2e896c2c6": "OrganisationID: Social care locations -",
                "3ae301b2-dbdd-42fc-b9b9-1d359e92edd7": "OrganisationId: GP practice and surgeries -",
                "59cf2da9-d7c0-4a75-babc-4528bc8c1b52": "OrganisationId: Opticians -",
                "4cdb87aa-963b-4433-a71a-4d5e453f532b": "OrganisationId: Pharmacies -",
                "5ebf102f-7545-4ad1-8fe6-96b0092ae3ed": "Parent Organisation Code: Care Home HQ -",
                "d69b32a7-f343-4fdf-9747-ebbf497f68ef": "Parent Organisation Code: Care Trusts -",
                "e3375fff-ef92-454f-99af-667c09f30c42": "Parent Organisation Code: Clinical Commissioning Groups -",
                "2c96d638-b1be-4baa-808f-0c083e8ffaab": "Parent Organisation Code: Commissioning Regions, Area Teams, Government Office Regions -",
                "96325be0-33de-425d-8ca0-3a2957fcc59e": "Parent Organisation Code: Commissioning Support Units -",
                "7ba0f3de-1793-4da7-83cf-a11cb7c51028": "Parent Organisation Code: General Dental Practices -",
                "b6e36b4f-eac1-49fa-b7c7-f1327e5aa81d": "Parent Organisation Code: General Medical Practices -",
                "3d85cb83-c23a-4e25-9ad7-80dbcea4542c": "Parent Organisation Code: Independent Sector Healthcare Providers -",
                "f08fdf34-11fd-48b7-80e5-6685779dc95d": "Parent Organisation Code: NHS Trusts -",
                "30d9e072-ad9e-49c6-aa07-62f7a301a285": "Parent Organisation Code: Optical Headquarters -",
                "337c85e4-1e32-47bc-a699-479c5f32918b": "Parent Organisation Code: Pharmacy headquarters -",
                "d7d80931-4b88-44cf-b8f5-4c83fd2e1245": "Parent Organisation Code: Special Health Authorities -",
                "90cf2737-db06-4d6e-99be-23fd3a2ddda1": "ParentODSCode: Commissioning Regions, Area Teams, Government Office Regions -",
                "b39a0ede-9220-4264-b1ef-a0056f19aab4": "ParentODSCode: NHS Trusts -",
                "77533c3e-3f43-46e9-b414-cf4a067a0175": "ParentODSCode: Social care providers -",
                "72991ee5-73ce-4e32-b2da-4382f28270b8": "Practicioner Code: General Dental Practicioners -",
                "fded9c2d-1fed-4e80-bd38-2114eae165ce": "Property Type (Land Registry) - http://landregistry.data.gov.uk/def/ppi/propertyType",
                "50c6c13f-b1a1-4b78-9c62-5c7eb2097e40": "Record Status (Land Registry) - http://landregistry.data.gov.uk/def/ppi/recordStatus",
                "3b063793-61ec-47ca-bbd1-784ba4b5960b": "Speciality Function Code: NHS Data Model &amp; Dictionary -",
            }
            self.assertEqual(h.codelist(), codelist_dict)

    def test_activate_upload_government(self):
        dataset = factories.Dataset(name='government-organogram', title='An organogram uploaded by a government department')
        dataset['schema-vocabulary'] = 'd3c0b23f-6979-45e4-88ed-d2ab59b005d0'
        helpers.call_action('package_update', self.context, **dataset)
        self.assertTrue(h.activate_upload('government-organogram'))

    def test_activate_upload_local_authority(self):
        dataset = factories.Dataset(name='la-organogram', title='An organogram uploaded by a local authority')
        dataset['schema-vocabulary'] = '538b857a-64ba-490e-8440-0e32094a28a7'
        helpers.call_action('package_update', self.context, **dataset)
        self.assertTrue(h.activate_upload('la-organogram'))

    def test_activate_upload_false(self):
        dataset = factories.Dataset(name='not-an-organogram', title='A dataset that is not an organogram')
        dataset['schema-vocabulary'] = 'fc3043a5-52e7-42fe-be7c-d3e0ef576c1d'
        helpers.call_action('package_update', self.context, **dataset)
        self.assertFalse(h.activate_upload('not-an-organogram'))
