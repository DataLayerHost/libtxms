# SPDX-License-Identifier: MIT
import os
from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, rmdir

required_conan_version = ">=2.12"


class LibtxmsConan(ConanFile):
	url = "https://github.com/DataLayerHost/libtxms"
	exports_sources = "CMakeLists.txt", "cmake/*", "include/*", "src/*", "LICENSE", "NOTICE"

	name = "libtxms"
	package_type = "library"
	license = "LicenseRef-libtxms-CORE"
	homepage = "https://github.com/DataLayerHost/libtxms"
	description = "C11 TxMS transaction messaging codec"
	topics = ("sms", "encoding", "blockchain")
	settings = "os", "arch", "compiler", "build_type"
	options = {"shared": [True, False], "fPIC": [True, False]}
	default_options = {"shared": False, "fPIC": True}

	def config_options(self):
		if self.settings.os == "Windows":
			del self.options.fPIC

	def configure(self):
		if self.options.shared:
			self.options.rm_safe("fPIC")
		self.settings.rm_safe("compiler.cppstd")
		self.settings.rm_safe("compiler.libcxx")

	def layout(self):
		cmake_layout(self)

	def generate(self):
		tc = CMakeToolchain(self)
		tc.variables["BUILD_TESTING"] = False
		tc.variables["TXMS_SANITIZE"] = False
		tc.variables["TXMS_FUZZ"] = False
		tc.generate()

	def build(self):
		cmake = CMake(self)
		cmake.configure()
		cmake.build()

	def package(self):
		copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
		copy(self, "NOTICE", self.source_folder, os.path.join(self.package_folder, "licenses"))
		CMake(self).install()
		rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
		rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

	def package_info(self):
		self.cpp_info.libs = ["txms"]
		self.cpp_info.set_property("cmake_file_name", "txms")
		self.cpp_info.set_property("cmake_target_name", "txms::txms")
		self.cpp_info.set_property("pkg_config_name", "txms")

	def set_version(self):
		if not self.version:
			import re
			from conan.tools.files import load
			self.version = re.search(r"project\(txms VERSION ([0-9.]+)", load(self, os.path.join(self.recipe_folder, "CMakeLists.txt"))).group(1)
