import configargparse
import awis
from awis import AwisApi
from lxml.etree import tostring as etree_tostring

def main():

    argparser = configargparse.ArgumentParser(
        description="AWIS API Proof of Concept"
    )

    argparser.add_argument('--key-id', required=True)
    argparser.add_argument('--secret-key', required=True)
    argparser.add_argument('--site', required=True)
    args = argparser.parse_args()

    client = AwisApi(args.key_id, args.secret_key)

    tree = client.url_info(args.site, "Rank", "LinksInCount", "Speed")
    print etree_tostring(tree)

    print "client ns_prefixes: ", client.NS_PREFIXES
    alexa_prefix = client.NS_PREFIXES['alexa']
    awis_prefix = client.NS_PREFIXES['awis']

    # elem = tree.find('//{%s}StatusCode' % alexa_prefix)
    # assert elem.text == 'Success'

    elem = tree.find('//{%s}Rank' % awis_prefix)
    print repr(elem)
    if elem is not None:
        print elem.tag, elem.text

if __name__ == '__main__':
    main()
