# refol.general

`refol.general` is an Ansible Collection containing general-purpose modules, including the following modules:

 [consolidate_variable](docs/consolidate_variable.md), which consolidates list-type variables from multiple inventories and renders Jinja2 expressions recursively.
 [redmine_wiki_mirror](docs/redmine_wiki_mirror.md), which performs a one-way mirror of a Redmine wiki pages to a GitHub repository by converting the wiki pages to markdown files.

---

## Building

Build the collection from source:

```bash
ansible-galaxy collection build ../refol.general
```

This creates a `refol-general-0.0.1.tar.gz` file.

---

## Installation

Install the collection from a local build or Galaxy:

```bash
# From source
ansible-galaxy collection install . --force
```

```bash
# From local build
ansible-galaxy collection install ./refol-general-0.0.1.tar.gz

# From Galaxy (if published)
ansible-galaxy collection install refol.general
```

When running playbooks that reference the collection's modules without setting `ANSIBLE_LIBRARY` or
`ANSIBLE_MODULE_UTILS` environment variables, ensure your `ansible.cfg` includes the collection's
plugin paths. Add the following to the `[defaults]` section of `ansible.cfg` if you install the
collection into the default user collection path (`~/.ansible/collections`):

```ini
# (pathspec) Colon-separated paths in which Ansible will search for Modules.
library=~/.ansible/collections/ansible_collections/refol/general/plugins/modules:

# (pathspec) Colon-separated paths in which Ansible will search for Module utils files, which are shared by modules.
module_utils=~/.ansible/collections/ansible_collections/refol/general/plugins/module_utils
```

If you're developing in-tree (running modules from the repository), you can alternatively set the
environment variables for the run instead of modifying `ansible.cfg`:

```bash
export ANSIBLE_LIBRARY=./plugins/modules
export ANSIBLE_MODULE_UTILS=./plugins/module_utils
```

## Verify the installation

Run the following to show that the collection has been installed.

```bash
ansible-galaxy collection list refol.general
```
