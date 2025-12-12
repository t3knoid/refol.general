#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2025, Francis Refol <francis@example.com>
# GNU General Public License v3.0+
# This module is part of the community.general collection

from ansible.module_utils.basic import AnsibleModule
import os
import yaml
from jinja2 import Template

DOCUMENTATION = r'''
---
module: consolidate_variable
short_description: Consolidate and render a variable from multiple inventories and roles
version_added: "1.0.0"
description:
  - Scans inventories under a base directory, including group_vars and host_vars.
  - Loads role defaults and vars from a roles directory.
  - Consolidates list-type variables (e.g., rproxy_setup_sites).
  - Recursively renders variables using Jinja2 with the merged variable space.
options:
  inventory_dir:
    description:
      - Base directory containing multiple inventory folders.
    required: true
    type: str
  target_var:
    description:
      - Name of the variable to consolidate.
    required: true
    type: str
  roles_dir:
    description:
      - Directory containing roles.
    required: true
    type: str
    default: "roles"
  debug:
    description:
      - Enable debug logging.
    required: false
    type: bool
    default: false
author:
  - "Francis Refol"
'''

EXAMPLES = r'''
- name: Consolidate rproxy setup sites
  community.general.consolidate_variable:
    inventory_dir: "{{ lookup('env','PWD') }}/inventory"
    target_var: rproxy_setup_sites
    roles_dir: roles/
    debug: true
  register: rproxy_config

- debug:
    var: rproxy_config.result
'''

RETURN = r'''
result:
  description: Fully consolidated and rendered variable list
  type: list
  returned: success
debug_log:
  description: Optional debug trace output
  type: list
  returned: when debug=true
'''

# -----------------------------
# Helpers
# -----------------------------
def log(debug, loglist, msg):
    if debug:
        loglist.append(msg)

def load_yaml(path, debug=False, loglist=None):
    if loglist is None:
        loglist = []
    if not os.path.isfile(path):
        log(debug, loglist, f"Skipping missing YAML: {path}")
        return {}
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                log(debug, loglist, f"Loaded {path} keys={list(data.keys())}")
                return data
            log(debug, loglist, f"Ignoring non-dict YAML: {path}")
            return {}
    except Exception as e:
        log(debug, loglist, f"Error reading {path}: {e}")
        return {}

def load_role_vars(roles_dir, debug=False, loglist=None):
    out = {}
    if not os.path.isdir(roles_dir):
        log(debug, loglist, f"No roles directory found: {roles_dir}")
        return out

    for role in sorted(os.listdir(roles_dir)):
        role_path = os.path.join(roles_dir, role)
        if not os.path.isdir(role_path):
            continue
        for subdir in ("defaults", "vars"):
            dir_path = os.path.join(role_path, subdir)
            if not os.path.isdir(dir_path):
                continue
            for root, _, files in os.walk(dir_path):
                for f in files:
                    if f.endswith((".yml", ".yaml")):
                        data = load_yaml(os.path.join(root, f), debug, loglist)
                        for k, v in data.items():
                            if k in out and isinstance(out[k], dict) and isinstance(v, dict):
                                out[k].update(v)
                            else:
                                out[k] = v
                        log(debug, loglist, f"Loaded role var file: {os.path.join(root,f)}")
    return out

def load_inventory_vars(base_dir, debug=False, loglist=None):
    merged = {}
    if not os.path.isdir(base_dir):
        log(debug, loglist, f"Inventory base missing: {base_dir}")
        return merged
    for inv in sorted(os.listdir(base_dir)):
        inv_path = os.path.join(base_dir, inv)
        if not os.path.isdir(inv_path):
            continue
        log(debug, loglist, f"Scanning inventory: {inv}")

        # group_vars
        group_root = os.path.join(inv_path, "group_vars")
        if os.path.isdir(group_root):
            for entry in sorted(os.listdir(group_root)):
                entry_path = os.path.join(group_root, entry)
                files = []
                if os.path.isdir(entry_path):
                    files = [os.path.join(entry_path, f) for f in sorted(os.listdir(entry_path)) if f.endswith((".yml",".yaml"))]
                elif entry.endswith((".yml",".yaml")):
                    files = [entry_path]
                for fpath in files:
                    data = load_yaml(fpath, debug, loglist)
                    merged.update(data)

        # host_vars
        host_root = os.path.join(inv_path, "host_vars")
        if os.path.isdir(host_root):
            for f in sorted(os.listdir(host_root)):
                if f.endswith((".yml", ".yaml")):
                    data = load_yaml(os.path.join(host_root, f), debug, loglist)
                    merged.update(data)
    log(debug, loglist, f"Loaded {len(merged)} inventory vars")
    return merged

def consolidate_target_var(base_dir, target_var, debug=False, loglist=None):
    result = []
    if not os.path.isdir(base_dir):
        log(debug, loglist, f"Inventory base missing: {base_dir}")
        return result
    for inv in sorted(os.listdir(base_dir)):
        inv_path = os.path.join(base_dir, inv)
        if not os.path.isdir(inv_path):
            continue
        log(debug, loglist, f"Searching for {target_var} in inventory: {inv}")

        # group_vars
        group_root = os.path.join(inv_path, "group_vars")
        if os.path.isdir(group_root):
            for entry in sorted(os.listdir(group_root)):
                entry_path = os.path.join(group_root, entry)
                files = []
                if os.path.isdir(entry_path):
                    files = [os.path.join(entry_path, f) for f in sorted(os.listdir(entry_path)) if f.endswith((".yml",".yaml"))]
                elif entry.endswith((".yml",".yaml")):
                    files = [entry_path]
                for fpath in files:
                    data = load_yaml(fpath, debug, loglist)
                    if isinstance(data.get(target_var), list):
                        result.extend(data[target_var])

        # host_vars
        host_root = os.path.join(inv_path, "host_vars")
        if os.path.isdir(host_root):
            for f in sorted(os.listdir(host_root)):
                if f.endswith((".yml",".yaml")):
                    data = load_yaml(os.path.join(host_root, f), debug, loglist)
                    if isinstance(data.get(target_var), list):
                        result.extend(data[target_var])
    log(debug, loglist, f"Consolidated {target_var}: {len(result)} items")
    return result

def merge_variables(role_vars, inv_vars, debug=False, loglist=None):
    merged = {}
    merged.update(role_vars)
    log(debug, loglist, f"Merged role_vars keys: {list(role_vars.keys())}")
    for k, v in inv_vars.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k].update(v)
        else:
            merged[k] = v
    log(debug, loglist, f"Merged inventory vars keys: {list(inv_vars.keys())}")
    return merged

def render_variables(obj, variables, debug=False, loglist=None, max_iterations=10):
    for _ in range(max_iterations):
        obj_new = _render_recursive(obj, variables, debug, loglist)
        if obj_new == obj:
            return obj_new
        obj = obj_new
    return obj

def _render_recursive(value, variables, debug=False, loglist=None):
    if isinstance(value, str):
        try:
            rendered = Template(value).render(variables)
            if debug and loglist is not None:
                loglist.append(f"Rendered '{value}' -> '{rendered}'")
            return rendered
        except Exception as e:
            if debug and loglist is not None:
                loglist.append(f"Render error for '{value}': {e}")
            return value
    elif isinstance(value, list):
        return [_render_recursive(v, variables, debug, loglist) for v in value]
    elif isinstance(value, dict):
        return {k: _render_recursive(v, variables, debug, loglist) for k, v in value.items()}
    else:
        return value

def main():
    module = AnsibleModule(
        argument_spec=dict(
            inventory_dir=dict(type="str", required=True),
            roles_dir=dict(type="str", required=True),
            target_var=dict(type="str", required=True),
            debug=dict(type="bool", required=False, default=False),
        ),
        supports_check_mode=True
    )

    params = module.params
    debug = params["debug"]
    loglist = []

    # Resolve absolute paths
    inventory_dir = os.path.abspath(params["inventory_dir"])
    roles_dir = os.path.abspath(params["roles_dir"])
    log(debug, loglist, f"Resolved inventory_dir: {inventory_dir}")
    log(debug, loglist, f"Resolved roles_dir: {roles_dir}")

    # Load role vars and inventory vars
    role_vars = load_role_vars(roles_dir, debug, loglist)
    inv_vars = load_inventory_vars(inventory_dir, debug, loglist)

    # Merge variables
    merged_vars = merge_variables(role_vars, inv_vars, debug, loglist)

    # Consolidate target variable
    raw_list = consolidate_target_var(inventory_dir, params["target_var"], debug, loglist)

    # Render recursively
    rendered = render_variables(raw_list, merged_vars, debug, loglist)

    result = dict(
        changed=False,
        result=rendered
    )
    if debug:
        result["debug_log"] = loglist

    module.exit_json(**result)

if __name__ == "__main__":
    main()
