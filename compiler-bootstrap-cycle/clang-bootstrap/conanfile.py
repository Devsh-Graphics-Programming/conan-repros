from conan import ConanFile


class ClangBootstrap(ConanFile):
    name = "clang-bootstrap"
    version = "1.0"
    package_type = "application"
    settings = "os", "arch"
