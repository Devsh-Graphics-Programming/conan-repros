from conan import ConanFile


class CompilerWrapperConan(ConanFile):
    name = "compiler-wrapper"
    version = "1.0"
    package_type = "application"
    tool_requires = "compiler/1.0"
