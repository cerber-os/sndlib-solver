#!/usr/bin/env python3
"""
Utility for converting multiple CSV files outputted by solver
to one XLSX file with useful formulas inserted
"""

import argparse
import os

from typing import Dict

try:
    import xlsxwriter as xlsx
except ImportError:
    print('[-] This utility requires xlsxwriter library. Install it first')
    raise


def main():
    parser = argparse.ArgumentParser(description='Convert solver output to easy-to-use Excel worksheet')
    parser.add_argument('--input', metavar='DIR', dest='input_dir', type=str, required=True,
                        help='Directory of containing CSV files generated by network solver')
    parser.add_argument('--output', metavar='FILE', dest='output_file', type=str, default='result.xlsx',
                        help='Output file name')
    args = parser.parse_args()

    # Create new workbook and clone CSV files to it
    workbook = xlsx.Workbook(args.output_file)
    bold = workbook.add_format({'bold': True})
    worksheets: Dict[str, object] = {}

    for fileName in ['summary.csv', 'path_choices.csv',
                     'cost_history.csv', 'demand_diff_per_link.csv',
                     'modules_per_link.csv', 'modules_per_link_per_demand.csv', 'links_per_demand.csv']:
        worksheet = workbook.add_worksheet(fileName.replace('.csv', ''))
        with open(os.path.join(args.input_dir, fileName), 'r') as f:
            for y, line in enumerate(f.read().split('\n')):
                for x, cell in enumerate(line.split(',')):
                    if y == 0:
                        # Make header row bold
                        worksheet.write(y, x, cell, bold)
                    else:
                        worksheet.write(y, x, cell)
        worksheets[fileName] = worksheet

    activePathsModules = workbook.add_worksheet('active_paths_modules')
    activePathsModules.write('A1', 'Demand name', bold)
    # TODO:
    #  =IF(COUNTIF($links_per_demand.$B20:$I20, $modules_per_link_per_demand.C$1) > 0, $modules_per_link_per_demand.C20, 0)

    worksheets['activePathsModules'] = activePathsModules

    workbook.close()
    print('[i] Done!')


if __name__ == '__main__':
    main()
