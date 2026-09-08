from conan import ConanFile


class ClangHybrid(ConanFile):
    name = "clang-hybrid"
    version = "1.0"
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    requires = "z3/1.0"
