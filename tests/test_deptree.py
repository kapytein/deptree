from deptree.parser import NPMParser

npm = NPMParser(package_filename='example/package.json',
                lock_filename='example/package-lock.json')

packages = npm.parse_file()
print(packages)
