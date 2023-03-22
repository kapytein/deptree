import json
from logging import root
from struct import pack

from deptree.exceptions import VersionNotSupported


class NPMParser():

    def __init__(self, package_filename, lock_filename) -> None:
        self.package_filename = package_filename
        self.lock_filename = lock_filename

    def __parse_dependency_from_dependency(self, tree, dependency):
        dep_tree = {"dependencies": {}}
        node_entry = {}

        if tree[dependency].__contains__("requires"):

            for inner_dep in tree[dependency]["requires"]:
                version = tree[inner_dep]["version"]
                is_dev = 'dev' in tree[inner_dep].keys()

                if "dependencies" in tree[dependency].keys():
                    if inner_dep in tree[dependency]["dependencies"]:
                        version = tree[dependency]["dependencies"][inner_dep]["version"]
                        is_dev = 'dev' in tree[dependency]["dependencies"][inner_dep].keys(
                        )

                node_entry = {inner_dep: {
                    "version": version, "is_dev": is_dev}}

                if tree[inner_dep].__contains__("requires"):
                    if tree[inner_dep].__contains__("dependencies"):
                        # Updating tree, as dependencies property inside a dependency has preference over the dependencies in the root
                        tree.update(tree[inner_dep]["dependencies"])

                    node_entry[inner_dep] = self.__parse_dependency_from_dependency(
                        tree, inner_dep)
                    node_entry[inner_dep]["version"] = version
                    node_entry[inner_dep]["is_dev"] = is_dev

                dep_tree["dependencies"].update(node_entry)
        else:
            dep_tree.pop("dependencies", None)

        return dep_tree

    def __parse_tree(self, tree, dependency):
        dependency_map = []
        node_entry = {}

        for dep in dependency["requires"]:
            # @TODO: Add is_dev value here..
            node_entry = {
                dep: {"version": tree[dep]["version"], "is_dev": 'dev' in tree[dep].keys()}}
            node_entry.update(
                self.__parse_dependency_from_dependency(tree, dep))

            dependency_map.append(node_entry)

        return dependency_map

    def parse_file(self):
        f_package = open(self.package_filename)
        package_data = json.load(f_package)

        f_lock = open(self.lock_filename)
        lock_data = json.load(f_lock)

        if lock_data["lockfileVersion"] != 1:
            raise VersionNotSupported(
                "Only lock file version 1 is supported currently.")

        dependencies = {}

        for i in package_data['dependencies']:
            dependency_map = {}

            if lock_data['dependencies'][i].__contains__('requires'):
                dependency_map = self.__parse_tree(
                    lock_data["dependencies"], lock_data['dependencies'][i])

            dependencies.update({i: {"version": lock_data['dependencies'][i]['version'],
                                "is_dev": 'dev' in lock_data['dependencies'][i].keys(), "dependencies": dependency_map}})

        return dependencies
