from conan import ConanFile

class MiddleConan(ConanFile):
    name = "middle"
    version = "1.0"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    def requirements(self):
        self.requires("leaf/1.0")
