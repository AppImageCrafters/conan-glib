#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os


class GLibConan(ConanFile):
    name = "glib"
    version = "2.40.0"
    description = "GLib provides the core application building blocks for libraries and applications written in C"
    url = "https://github.com/bincrafters/conan-glib"
    homepage = "https://github.com/GNOME/glib"
    author = "BinCrafters <bincrafters@gmail.com>"
    license = "LGPL-2.1"
    exports = ["LICENSE.md"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "with_pcre": [True, False]}
    default_options = "shared=False", "fPIC=True", "with_pcre=False"
    requires = "zlib/1.2.11@conan/stable"
    source_subfolder = "source_subfolder"
    exports_sources = "patches/*"
    autotools = None

    def configure(self):
        if self.settings.os != 'Linux':
            raise Exception("GNOME glib is only supported on Linux for now.")
        del self.settings.compiler.libcxx

    def system_requirements(self):
        pkgs_name = None
        if tools.os_info.linux_distro == "ubuntu":
            pkgs_name = ["libffi-dev"]

        if pkgs_name:
            installer = tools.SystemPackageTool()
            for pkg_name in pkgs_name:
                installer.install(pkg_name)

    def requirements(self):
        if self.options.with_pcre:
            self.requires.add("pcre/8.41@bincraftres/stable")

    def source(self):
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version))
        extracted_dir = self.name + "-" + self.version

        # work around error: m4_copy: won't overwrite defined macro: glib_DEFUN
        tools.replace_in_file(extracted_dir + "/m4macros/glib-gettext.m4", "m4_copy", "m4_copy_force")
        tools.patch(base_path=extracted_dir, patch_file="patches/gdate_suppress_string_format_literal_warning.patch")

        os.rename(extracted_dir, self.source_subfolder)
        self._create_extra_files()

    def _create_extra_files(self):
        with open(os.path.join(self.source_subfolder, 'gtk-doc.make'), 'w+') as fd:
            fd.write('EXTRA_DIST =\n')
            fd.write('CLEANFILES =\n')
        for file_name in ['README', 'INSTALL']:
            open(os.path.join(self.source_subfolder, file_name), 'w+')

    def _configure_autotools(self):
        if not self.autotools:
            configure_args = ['--disable-man']
            if not self.options.with_pcre:
                configure_args.append('--without-pcre')
            if not self.options.shared:
                configure_args.append('--enable-static')
                configure_args.append('--disable-shared')
            with tools.chdir(self.source_subfolder):
                self.autotools = AutoToolsBuildEnvironment(self)
                self.autotools.fpic = self.options.fPIC
                self.run("autoreconf --force --install --verbose")
                self.autotools.configure(args=configure_args)
        return self.autotools

    def build(self):
        autotools = self._configure_autotools()
        with tools.chdir(self.source_subfolder):
            autotools.make()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self.source_subfolder)
        autotools = self._configure_autotools()
        with tools.chdir(self.source_subfolder):
            autotools.make(["install"])

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
        self.cpp_info.includedirs.append(os.path.join('include', 'glib-2.0'))
        self.cpp_info.includedirs.append(os.path.join('lib', 'glib-2.0', 'include'))
