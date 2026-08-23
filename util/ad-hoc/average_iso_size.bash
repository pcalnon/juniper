#!/usr/bin/env bash

COUNT=0; TOTAL=0; for i in $(l -h *.iso | awk -F " " '{print $5;}' | tr -d "G."); do echo "Value: ${i}"; COUNT=$(( 10#${COUNT} + 1 )); TOTAL=$(( 10#${TOTAL} + 10#${i} )); echo "Count: ${COUNT}, Value: ${i}, Total: ${TOTAL}"; done; COUNT_ADJ=$(( 10#${COUNT} * 10#10 )); MEAN=$(( 10#${TOTAL} / 10#${COUNT} )); echo "Iso Count: ${COUNT}, Total Size: ${TOTAL}, Mean Size: ${MEAN}"
