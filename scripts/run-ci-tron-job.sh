#!/bin/bash
# Shared CI-Tron job execution script
# This implements the core logic from GitLab's .ci-tron-job-v1
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Optionally load defaults from GitLab's dut.yml
if [ "${CI_TRON_LOAD_GITLAB_DEFAULTS:-true}" = "true" ]; then
  echo "=== Loading defaults from GitLab's dut.yml ==="

  # Export job type for the Python script
  export CI_TRON_JOB_TYPE="${CI_TRON_JOB_TYPE:-b2c}"

  eval "$(python3 "$SCRIPT_DIR/parse-defaults.py")"
fi

echo "=== Expanding CI_TRON_* variable references ==="
eval "$(python3 "$SCRIPT_DIR/expand-variables.py")"

# Validate configuration
echo "=== Validating CI-Tron Configuration ==="
for var in CI_TRON_PATTERN__SESSION_END__REGEX CI_TRON_PATTERN__JOB_SUCCESS__REGEX; do
  if [ -z "$(eval echo \$$var 2>/dev/null || echo)" ]; then
    echo "ERROR: Required variable '$var' is missing"
    exit 1
  fi
done

echo "=== Generating Job Script ==="

# Aggregate executorctl extra args
export CI_TRON_EXECUTORCTL_EXTRA_ARGS=""
for var_name in $(env | grep -e "^CI_TRON_EXECUTORCTL_EXTRA_ARGS__" | cut -d '=' -f 1 | sort); do
  CI_TRON_EXECUTORCTL_EXTRA_ARGS="$CI_TRON_EXECUTORCTL_EXTRA_ARGS $(eval echo \$$var_name)"
done

# Handle S3 credentials if provided
if [ -n "${CI_TRON_S3_CREDENTIALS:-}" ]; then
  CI_TRON_EXECUTORCTL_EXTRA_ARGS="$CI_TRON_EXECUTORCTL_EXTRA_ARGS --minio-auth $CI_TRON_S3_CREDENTIALS"

  if [ -n "${CI_TRON_S3_GROUPS_ADD:-}" ]; then
    for group in ${CI_TRON_S3_GROUPS_ADD//,/ }; do
      CI_TRON_EXECUTORCTL_EXTRA_ARGS="$CI_TRON_EXECUTORCTL_EXTRA_ARGS --minio-group $group"
    done
  fi
fi

mkdir -p "$(dirname "$CI_TRON_JOB_SCRIPT_PATH")"

# Generate job script header
cat > "$CI_TRON_JOB_SCRIPT_PATH" << 'JOBSCRIPT_EOF'
#!/bin/sh
set -eu
JOBSCRIPT_EOF

# Export environment (filter sensitive vars)
python3 "$SCRIPT_DIR/export-env.py" >> "$CI_TRON_JOB_SCRIPT_PATH"

# Add executorctl command
cat >> "$CI_TRON_JOB_SCRIPT_PATH" << 'JOBSCRIPT_EOF2'

EXECUTOR_EXITCODE=0
PYTHONUNBUFFERED=1 \
executorctl run \
  --job-id "$CI_JOB_NAME_SLUG" \
  --machine-id "$CI_RUNNER_DESCRIPTION" \
  --forward-env-regex ".*" \
  --job-cookie "$CI_TRON_JOB_COOKIE" \
  $CI_TRON_EXECUTORCTL_EXTRA_ARGS \
  --wait \
  "$CI_TRON_JOB_TEMPLATE" \
  || EXECUTOR_EXITCODE=$?

case $EXECUTOR_EXITCODE in
  0) echo "PASS: session_end and job_success patterns matched.";;
  1) echo "FAIL: session_end matched but job_success did not.";;
  2) echo "WARN: Job succeeded with warning.";;
  3) echo "COMPLETE: Job finished but no job_success pattern defined.";;
  4) echo "INCOMPLETE: session_end pattern not matched.";;
  5) echo "SETUP_FAIL: Job setup failed.";;
  6) echo "UNKNOWN: Job exited in unknown state.";;
  143) echo "Job was killed (timeout or cancelled).";;
  *) echo "Job exited with code $EXECUTOR_EXITCODE.";;
esac

exit $EXECUTOR_EXITCODE
JOBSCRIPT_EOF2

chmod +x "$CI_TRON_JOB_SCRIPT_PATH"

echo "=== Generated Job Script ==="
cat "$CI_TRON_JOB_SCRIPT_PATH"
echo "============================"

echo "=== Executing CI-Tron Job ==="
sh "$CI_TRON_JOB_SCRIPT_PATH"
EXIT_CODE=$?

case $EXIT_CODE in
  0) STATUS="PASS";;
  1) STATUS="FAIL";;
  2) STATUS="WARN";;
  3) STATUS="COMPLETE";;
  4) STATUS="INCOMPLETE";;
  5) STATUS="SETUP_FAIL";;
  6) STATUS="UNKNOWN";;
  143) STATUS="KILLED";;
  *) STATUS="UNEXPECTED";;
esac

echo "exit_code=$EXIT_CODE" >> $GITHUB_OUTPUT
echo "status=$STATUS" >> $GITHUB_OUTPUT

exit $EXIT_CODE