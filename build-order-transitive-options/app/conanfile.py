from conan import ConanFile

class AppConan(ConanFile):
    name = "app"
    version = "1.0"
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"
    default_options = {"middle/*:shared": True, "leaf/*:shared": True}
    def requirements(self):
        self.requires("middle/1.0")
