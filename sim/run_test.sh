#!/bin/bash
# Run one UVM test on the built snapshot.   Usage: ./run_test.sh <test_name> [seed] [random_iterations]
# (xsim.bat splits arguments at '=', so plusargs are handed over in an args file)
export PATH="$PATH:/d/Vivado/2025.2/Vivado/bin"
cd "$(dirname "$0")/work" || exit 1
T=$1; SEED=${2:-1}; ITER=${3:-25}
mkdir -p ../logs ../cov
{ echo "-testplusarg UVM_TESTNAME=$T"; echo "-testplusarg ITER=$ITER"; echo "-sv_seed $SEED";
  echo "-log ../logs/${T}_s${SEED}.log"; echo "-cov_db_dir ../cov"; echo "-cov_db_name ${T}_s${SEED}"; echo "-R"; } > args_${T}.txt
xsim.bat tb_snap -f args_${T}.txt > /dev/null 2>&1
grep -h "TEST PASSED\|TEST FAILED" ../logs/${T}_s${SEED}.log | sed 's/.*\[RESULT\] //'
