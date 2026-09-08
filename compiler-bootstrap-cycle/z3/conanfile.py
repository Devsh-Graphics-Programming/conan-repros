from conan import ConanFile


class Z3(ConanFile):
    name = "z3"
    version = "1.0"
    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
