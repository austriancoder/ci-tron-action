#!/usr/bin/env python3
import os
import shlex

shell_vars = {"_", "HOME", "HOSTNAME", "OLDPWD", "PATH", "PWD", "TERM", "XDG_RUNTIME_DIR"}
sensitive_keywords = ("TOKEN", "PASSWORD", "SECRET", "KEY")

for key, value in sorted(os.environ.items()):
    if key in shell_vars:
        print(f"# {key} not stored (shell variable)")
    elif any(keyword in key for keyword in sensitive_keywords):
        print(f"# {key} not stored (credentials)")
    else:
        print(f"export {key}={shlex.quote(value)}")
