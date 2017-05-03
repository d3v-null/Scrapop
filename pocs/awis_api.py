import configargparse

from awis import AwisApi
#pylint: disable=no-name-in-module
from lxml.etree import tostring as etree_tostring
from lxml.etree import ElementTree

def main():

    argparser = configargparse.ArgumentParser(
        description="AWIS API Proof of Concept"
    )

    argparser.add_argument('--key-id', required=True)
    argparser.add_argument('--secret-key', required=True)
    argparser.add_argument('--sites', required=True, nargs='+')
    args = argparser.parse_args()

    client = AwisApi(args.key_id, args.secret_key)

    tree = client.url_info(args.sites, "Rank", "LinksInCount", "Speed")
    print etree_tostring(tree)

    print "client ns_prefixes: ", client.NS_PREFIXES
    alexa_prefix = client.NS_PREFIXES['alexa']
    awis_prefix = client.NS_PREFIXES['awis']

    elem = tree.find('//{%s}StatusCode' % alexa_prefix)
    assert elem.text == 'Success'

    for elem_result in tree.findall('//{%s}UrlInfoResult' % awis_prefix):
        # print etree_tostring(elem_result)
        print "elem_result tag: %s, text: %s" % (elem_result.tag, elem_result.text)

        tree_result = ElementTree(elem_result)
        elem_url = tree_result.find('//{%s}DataUrl' % awis_prefix)
        if elem_url is not None:
            print "elem_url tag: %s, text: %s" % (elem_url.tag, elem_url.text)
        elem_metric = tree_result.find('//{%s}Rank' % awis_prefix)
        if elem_metric is not None:
            print "elem_metric tag: %s, text: %s " % (elem_metric.tag, elem_metric.text)

if __name__ == '__main__':
    main()
