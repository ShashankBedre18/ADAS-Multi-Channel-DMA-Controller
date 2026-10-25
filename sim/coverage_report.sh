#!/bin/bash
# Merge the functional + code coverage of every test in cov/ and write HTML reports to sim/report/
export PATH="$PATH:/d/Vivado/2025.2/Vivado/bin"
cd "$(dirname "$0")"
rm -rf report merged; mkdir -p report merged
args=""
for d in cov/xsim.covdb/*/; do args="$args -cov_db_dir cov -cov_db_name $(basename $d)"; done
xcrg.bat -report_format html -report_dir report/functional -merge_dir merged -merge_db_name all_tests $args -log logs/xcrg_func.log >/dev/null 2>&1
cargs="-cov_db_dir work -cov_db_name tb_snap"
xcrg.bat -report_format html -report_dir report/code $cargs -log logs/xcrg_code.log >/dev/null 2>&1
echo "coverage reports: sim/report/functional/functionalCoverageReport/dashboard.html , sim/report/code/codeCoverageReport/dashboard.html"
