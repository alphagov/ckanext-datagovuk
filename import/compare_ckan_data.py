import argparse

import ckan
import ckanapi

def process(old_url, new_url):
    old_ckan = ckanapi.RemoteCKAN(old_url)
    new_ckan = ckanapi.RemoteCKAN(new_url)

    old_org_list = old_ckan.action.organization_list()
    new_org_list = new_ckan.action.organization_list()
    missing_orgs =  return_not_matches(old_org_list, new_org_list)
    print "*** Publishers in old CKAN and not in new CKAN (%s of %s) ***" % (len(missing_orgs[0]), len(old_org_list))
    print "\n".join(missing_orgs[0])
    print "*** Publishers in new CKAN and not in old CKAN (%s of %s) ***" % (len(missing_orgs[1]), len(new_org_list))
    print "\n".join(missing_orgs[1])

    old_package_list = old_ckan.action.package_list()
    new_package_list = new_ckan.action.package_list()
    missing_packages =  return_not_matches(old_package_list, new_package_list)
    missing_packages[0] = remove_harvesters(old_ckan, missing_packages[0])
    print "*** Datasets in old CKAN and not in new CKAN (%s of %s) ***" % (len(missing_packages[0]), len(old_package_list))
    print "\n".join(missing_packages[0])
    missing_packages[1] = remove_harvesters(new_ckan, missing_packages[1])
    print "*** Datasets in new CKAN and not in old CKAN (%s of %s) ***" % (len(missing_packages[1]), len(new_package_list))
    print "\n".join(missing_packages[1])

    return

def return_not_matches(a, b):
    return [[x for x in a if x not in b], [x for x in b if x not in a]]

def remove_harvesters(ckan_obj, package_list):
    for package in package_list[:]:
        if package_is_harvester(ckan_obj, package) == True:
            package_list.remove(package)
    return package_list

def package_is_harvester(ckan_obj, package_id):
    package = ckan_obj.action.package_show(id=package_id)
    if 'type' in package and package['type'] == 'harvest':
        return True
    else:
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare the content of two CKAN instances')
    parser.add_argument('-1', dest='old', required=True,
                        help='Specify the URL of the old CKAN instance')
    parser.add_argument('-2', dest='new', required=True,
                        help='Specify the URL of the new CKAN instance')

    args = parser.parse_args()
    process(args.old, args.new)

