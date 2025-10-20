#!/usr/bin/env python3
"""
Expand CI_TRON_* variables that reference other CI_TRON_* variables.
Handles both ${VAR} and $VAR syntax, with proper ordering to resolve dependencies.
"""
import os
import re
import sys

def get_ci_tron_vars():
    """Get all CI_TRON_* environment variables"""
    return {k: v for k, v in os.environ.items() if k.startswith('CI_TRON_')}

def contains_ci_tron_ref(value):
    """Check if value contains references to CI_TRON_* variables"""
    return bool(re.search(r'\$\{?CI_TRON_', value))

def count_ci_tron_refs(value):
    """Count how many CI_TRON_* variable references are in the value"""
    return len(re.findall(r'\$\{?CI_TRON_', value))

def expand_variables(variables, max_passes=10):
    """
    Expand variables in multiple passes until no more expansions can be made.
    This handles dependency chains where var A references var B which references var C.
    """
    for pass_num in range(max_passes):
        changes_made = False

        # Sort variables by number of references (expand leaf nodes first)
        sorted_vars = sorted(variables.items(), key=lambda x: count_ci_tron_refs(x[1]))

        for var_name, var_value in sorted_vars:
            if not contains_ci_tron_ref(var_value):
                continue

            print(f"Pass {pass_num + 1}: Expanding {var_name}...", file=sys.stderr)
            print(f"  Before: {var_value}", file=sys.stderr)

            expanded_value = var_value

            # Find all CI_TRON_* variable references in the value
            # Match both ${CI_TRON_*} and $CI_TRON_* forms
            all_refs = set(re.findall(r'\$\{?(CI_TRON_[A-Za-z0-9_]+)\}?', var_value))

            for ref_var in all_refs:
                # Get the value, defaulting to empty string if not defined
                ref_value = variables.get(ref_var, '')

                # Handle CI_TRON__B2C_EXEC_CMD specially: convert newlines to semicolons
                if ref_var == "CI_TRON__B2C_EXEC_CMD" and ref_value:
                    ref_value = ref_value.replace('\n', ' ; ')

                # Replace ${VAR} form (with braces)
                expanded_value = expanded_value.replace(f'${{{ref_var}}}', ref_value)

                # Replace $VAR form (without braces) - only if followed by non-alphanumeric
                pattern = re.compile(r'\$' + re.escape(ref_var) + r'(?=[^A-Za-z0-9_]|$)')
                expanded_value = pattern.sub(ref_value, expanded_value)

            # Check if we made changes
            if expanded_value != var_value:
                variables[var_name] = expanded_value
                changes_made = True
                print(f"  After: {expanded_value}", file=sys.stderr)

        if not changes_made:
            print(f"No more expansions needed after {pass_num + 1} pass(es)", file=sys.stderr)
            break
    else:
        print(f"WARNING: Reached maximum of {max_passes} passes, may have unresolved references", file=sys.stderr)

    return variables

def main():
    variables = get_ci_tron_vars()

    # Expand variables in multiple passes
    expanded_vars = expand_variables(variables)

    # Export the expanded variables
    for var_name, var_value in sorted(expanded_vars.items()):
        # Escape single quotes for shell
        safe_value = var_value.replace("'", "'\\''")
        print(f"export {var_name}='{safe_value}'")

if __name__ == '__main__':
    main()