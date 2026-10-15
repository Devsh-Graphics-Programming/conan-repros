from conan import ConanFile


class CompilerConan(ConanFile):
    name = "compiler"
    version = "1.0"
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
