#!/bin/bash
# Compile and run the comparison: run.sh <out dir> [rr gain] [skid gain]
cd "$(dirname "$0")"
KL=kotlinc-dl/kotlinc/lib; CP="out/roadrunner-core.jar:$KL/kotlin-stdlib.jar:out/pedro:${SKID:-out/skid}"
javac -nowarn -cp "$CP" -d out/harness harness/Compare.java 2>&1 | grep -v JAVA_TOOL
java -cp "$CP:out/harness" Compare "$@" 2>&1 | grep -v "JAVA_TOOL\|^\s*at \|IllegalState"
