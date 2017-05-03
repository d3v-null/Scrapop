"""
Core methods for scraping data from Popularity metrics websites and storing in google drive.
"""

from __future__ import print_function
from collections import OrderedDict
import re

import configargparse
from oauth2client import tools

from scrapop.utils import (GssUtils, AwisUtils, UrlUtils, ListUtils,
                           SanitationUtils)
from pprint import pformat
from tabulate import tabulate

def extract_targets(cells):
    """
    Extracts unique domains from list of gss cells.
    """
    cell_info = []
    unique_domains = set()
    for cell in ListUtils.get_firsts(cells):
        if not cell:
            # cell_info.append(CellInfo(cell, None, errors='empty cell'))
            cell_info.append({'cell':cell, 'errors':'empty cell'})
        try:
            domain = SanitationUtils.extract_target_gss_cell(cell)
        except Exception, exc:
            # cell_info.append(CellInfo(cell, None, errors=str(exc)))
            cell_info.append({'cell':cell, 'errors':str(exc)})
            continue
        if not domain:
            # cell_info.append(CellInfo(cell, None, errors='could not extract domain'))
            cell_info.append({'cell':cell, 'errors':'could not extract domain'})
            continue
        # cell_info.append(CellInfo(cell, domain.lower(), None))
        cell_info.append({'cell':cell, 'domain':domain.lower()})
        unique_domains.add(domain.lower())

    return list(unique_domains), cell_info

def main():
    """Main function for scraping Alexa popularity metric data."""

    # Parse arguments
    argparser = configargparse.ArgumentParser(
        description="Scrape and store popularity metrics",
        parents=[tools.argparser]
    )

    argparser.add_argument(
        '-c', '--my-config',
        is_config_file=True,
        help='config file path'
    )

    gdrive_group = argparser.add_argument_group('Google Drive Options')
    gdrive_group.add_argument(
        '--client-secret-file',
        help='Location of file containing Google Drive Auth info',
        default='./client_secret.json',
        metavar='FILE'
    )
    gdrive_group.add_argument(
        '--file-id',
        help='The ID of the file to store the popularity metrics',
        required=True,
        metavar='ID'
    )
    gdrive_group.add_argument(
        '--target-sheet',
        help='The name of the sheet containing popularity data',
        default='Sheet1',
        metavar='SHEET'
    )
    gdrive_group.add_argument(
        '--target-column',
        help='The column containing the target site name',
        default='A',
        metavar='COL'
    )

    awis_group = argparser.add_argument_group('Alexis Options')
    awis_group.add_argument(
        '--requests-limit',
        type=int,
        help='Limit the number of popularity metric api requests'
    )
    awis_group.add_argument(
        '--key-id',
        help='Key ID Provided by AWIS',
        metavar='ID',
        required=True
    )
    awis_group.add_argument(
        '--secret-key',
        help='Secret Key Provided by AWIS',
        metavar='KEY',
        required=True
    )

    argparser.add_argument(
        '-o', '--out-file',
        help='Location to store report',
        default='report.html'
    )

    options = argparser.parse_args()

    # options.flags = argparse.ArgumentParser(
    #
    # ).parse_args(options.gsheet_flags)

    print(options)
    print("----------")
    print(argparser.format_help())
    print("----------")
    print(argparser.format_values())

    options.scopes = 'https://www.googleapis.com/auth/spreadsheets'
    options.app_name = 'ScraPop'

    # get list of target cells from google drive

    range_name = "'{sheet}'!{col}:{col}".format(
        col=options.target_column,
        sheet=options.target_sheet
    )

    target_cells = GssUtils.get_range(
        options.file_id,
        range_name,
        options=options,
        value_render='FORMULA'
    )
    # print("target_cells:\n%s" % pformat(target_cells))
    unique_domains, cell_info = extract_targets(target_cells)

    # print("unique_domains:\n%s" % pformat(unique_domains))

    metrics = {}
    # metric_names = ['Rank']
    metric_names = ['Rank', 'LinksInCount', 'Speed']

    # TODO: get chunking working in the folliwng comment block:

    chunk_size = 5
    count = -1
    for index in range(0, len(unique_domains), chunk_size):
        count += 1
        if options.requests_limit and count >= options.requests_limit:
            print("reached limit")
            break
        domains = unique_domains[index:index + chunk_size]
        domains = [UrlUtils.only_domain(domain) for domain in domains]
        responses = AwisUtils.get_metrics(domains, metric_names, options)
        if responses:
            for domain, response in zip(domains, responses):
                metrics[domain] = response

    # for count, domain in enumerate(unique_domains):
    #     # print("count, req_limit: (%s, %s)" % (repr(count), repr(options.requests_limit)))
    #     if count >= options.requests_limit:
    #         print("reached limit")
    #         break
    #     response = AwisUtils.get_metrics(domain, metric_names, options)
    #     if response:
    #         metrics[domain] = response

    # print("metrics:\n%s" % pformat(metrics))
    for cell_datum in cell_info:
        if cell_datum.get('domain') and cell_datum['domain'] in metrics:
            cell_datum.update(metrics[cell_datum['domain']])


    report_headers = OrderedDict([
        ('domain', 'Domain'),
    ] \
    + [(metric_name, metric_name) for metric_name in metric_names] \
    + [
        ('errors', 'Errors'),
        ('cell', 'Cell')
    ])
    # report_headers = ['domain'] + metric_names + ['errors', 'cell']

    with open(options.out_file, 'w+') as report_handle:
        cell_table = [
            [info_row.get(header_key) for header_key in report_headers] \
            for info_row in cell_info
        ]
        report_contents = tabulate(cell_table, headers=report_headers, tablefmt="html")
        report_contents = re.sub("<table>", "<table class=\"table table-striped\">", report_contents)
        report_contents = "<h1>Metrics Report</h1><p>" + report_contents + "</p>"
        report_contents = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap-theme.min.css" integrity="sha384-fLW2N01lMqjakBkx3l/M9EahuwpSfeNvV63J5ezn3uZzapT0u7EYsXMjQV+0En5r" crossorigin="anonymous">
</head>
<body>
    <div class='col-sm-12'>""" + report_contents + """</div>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
</body>
</html>
"""
        report_handle.write(report_contents)
        print("wrote report to %s" % options.out_file)

if __name__ == '__main__':
    main()
