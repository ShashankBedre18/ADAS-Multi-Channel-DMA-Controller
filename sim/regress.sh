#!/bin/bash
# Full regression: build, run every test (random test with several seeds), merge coverage, report.
export PATH="$PATH:/d/Vivado/2025.2/Vivado/bin"
cd "$(dirname "$0")"
./build.sh || exit 1   # (rebuild also resets the cumulative code-coverage database)
rm -rf logs cov report; mkdir -p logs cov
TESTS="regs smoke sensor_fusion burst_sweep priority error cfg_err backpressure"
pass=0; fail=0; : > logs/summary.txt
for t in $TESTS; do
  r=$(./run_test.sh dma_${t}_test 1); echo "$r" | tee -a logs/summary.txt
done
for s in 11 12 13 14 15; do
  r=$(./run_test.sh dma_random_test $s 40); echo "$r (seed $s)" | tee -a logs/summary.txt
done
echo "-----"; echo "PASSED: $(grep -c 'TEST PASSED' logs/summary.txt)   FAILED: $(grep -c 'TEST FAILED' logs/summary.txt)" | tee -a logs/summary.txt
./coverage_report.sh
