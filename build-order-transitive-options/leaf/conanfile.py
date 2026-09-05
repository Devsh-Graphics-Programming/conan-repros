from conan import ConanFile

class LeafConan(ConanFile):
    name = "leaf"
    version = "1.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = {"shared": False}
