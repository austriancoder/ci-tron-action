#!/usr/bin/env python3
"""
Parse dut.yml to extract default variable values.
"""
import os
import sys
import urllib.request
import yaml

def download_dut_yml(url, commit):
    """Download dut.yml from GitLab"""
    full_url = f"{url}/-/raw/{commit}/.gitlab-ci/dut.yml"
    print(f"Downloading: {full_url}", file=sys.stderr)
    with urllib.request.urlopen(full_url) as response:
        return response.read().decode('utf-8')

def load_local_dut_yml(path):
    """Load dut.yml from local filesystem"""
    print(f"Loading from local file: {path}", file=sys.stderr)
    with open(path, 'r', encoding="utf-8") as f:
        return f.read()

def extract_variables(job_definition):
    """Extract variables from a GitLab job definition"""
    if not isinstance(job_definition, dict):
        return {}

    variables = job_definition.get('variables', {})

    # Handle extends - recursively merge parent variables
    extends = job_definition.get('extends', [])
    if isinstance(extends, str):
        extends = [extends]

    return variables, extends

def resolve_extends(jobs, job_name, resolved_cache=None):
    """Recursively resolve extended variables"""
    if resolved_cache is None:
        resolved_cache = {}

    if job_name in resolved_cache:
        return resolved_cache[job_name]

    if job_name not in jobs:
        return {}

    job = jobs[job_name]
    variables, extends = extract_variables(job)

    # Start with this job's variables
    result = dict(variables)

    # Merge in extended jobs (in reverse order so first extend takes precedence)
    for parent_name in reversed(extends):
        parent_vars = resolve_extends(jobs, parent_name, resolved_cache)
        # Parent variables are overridden by child
        for key, value in parent_vars.items():
            if key not in result:
                result[key] = value

    resolved_cache[job_name] = result
    return result

def main():
    # Check if we should use local file or download from remote
    use_local = os.environ.get('CI_TRON_USE_LOCAL_DUT_YML', '').lower() in ('true', '1', 'yes')

    if use_local:
        # Load from local filesystem
        dut_yml_content = load_local_dut_yml('dut.yml')
    else:
        # Download from remote
        url = os.environ.get('CI_TRON_JOB_TEMPLATE_URL', 'https://gitlab.freedesktop.org/gfx-ci/ci-tron')
        commit = os.environ.get('CI_TRON_JOB_TEMPLATE_COMMIT', 'main')
        dut_yml_content = download_dut_yml(url, commit)

    # Require job_type to be explicitly set
    job_type = os.environ.get('JOB_TYPE')
    if not job_type:
        print("ERROR: JOB_TYPE environment variable is required", file=sys.stderr)
        sys.exit(1)

    # Parse dut.yml
    jobs = yaml.safe_load(dut_yml_content)

    # Map job types to GitLab job names
    job_map = {
        'ci-tron-job': '.ci-tron-job-v1',
        'ci-tron-b2c-job': '.ci-tron-b2c-job-v1',
        'ci-tron-b2c-diskless': '.ci-tron-b2c-diskless-v1'
    }

    target_job = job_map.get(job_type, '.ci-tron-b2c-job-v1')
    print(f"DEBUG: Target job: {target_job}", file=sys.stderr)
    print(f"DEBUG: Job extends: {jobs.get(target_job, {}).get('extends', [])}", file=sys.stderr)

    # Resolve all variables including extended ones
    variables = resolve_extends(jobs, target_job)

    # Export as environment variables
    for key, value in sorted(variables.items()):
        # Convert value to string (handles multi-line strings)
        if isinstance(value, str):
            value_str = value
        elif value is None:
            continue
        else:
            value_str = str(value)

        # Only export CI_TRON_ variables that aren't already set
        if key.startswith('CI_TRON_'):
            if key not in os.environ:
                # Use a safe escaping approach with $'...' syntax
                safe_value = value_str.replace("'", "'\\''")
                print(f"export {key}='{safe_value}'")
                # Also log to stderr for visibility
                print(f"Setting default: {key} {safe_value}", file=sys.stderr)

    print("Defaults loaded successfully", file=sys.stderr)

if __name__ == '__main__':
    main()