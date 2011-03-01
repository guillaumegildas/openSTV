#!/usr/bin/env python
## Copyright (C) 2003-2009  Jeffrey O'Neill
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

import sys
import os

if sys.platform == "win32":
    from distutils.core import setup
    import py2exe
elif sys.platform == "cygwin":
    from distutils.core import setup
else:
    from setuptools import setup

from openstv.version import v as OpenSTV_version

__revision__ = "$Id: setup.py 722 2010-03-08 14:14:34Z jeff.oneill $"

################################################################

# The manifest will be inserted as resource into OpenSTV.exe.  This
# gives the controls the Windows XP appearance (if run on XP ;-)

manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="OpenSTV"
    type="win32"
/>
<description>OpenSTV Program</description>
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
</dependency>
</assembly>
'''

################################################################

class InnoScript:
    def __init__(self, lib_dir, dist_dir, windows_exe_files,
                 lib_files):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.lib_files = [self.chop(p) for p in lib_files]
        self.issFile = r"dist\OpenSTV.iss"

    def chop(self, pathname):
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]
    
    def create(self):
        ofi = open(self.issFile, "w")
        print >> ofi, r'''
; WARNING: This script has been created by py2exe. Changes to this script
; will be overwritten the next time py2exe is run!
[Setup]
AppName=OpenSTV
AppVerName=OpenSTV %s
DefaultDirName={pf}\OpenSTV
DefaultGroupName=OpenSTV
ChangesAssociations=yes
OutputBaseFilename=OpenSTV-%s-win32
OutputDir=.

[Files]
''' % (OpenSTV_version, OpenSTV_version)

        for path in self.windows_exe_files + self.lib_files:
            print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path))
        print >> ofi, r'Source: "gdiplus.dll"; DestDir: "{app}"; Flags: ignoreversion'

        print >> ofi, r'''

[Tasks]
Name: "associatebltfiles"; Description: "&Associate BLT files with OpenSTV"; Flags: checkedonce 
Name: "desktopicon"; Description: "Create a &Desktop icon"; Flags: checkedonce 
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; Flags: checkedonce 

[Icons]
'''

        for path in self.windows_exe_files:
            print >> ofi, r'Name: "{group}\OpenSTV"; Filename: "{app}\%s"' % (path)
        
        print >> ofi, r'''
Name: "{group}\Help"; Filename: "{app}\Help.html"
Name: "{group}\Uninstall OpenSTV"; Filename: "{uninstallexe}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\OpenSTV"; Filename: "{app}\OpenSTV.exe"; Tasks: quicklaunchicon
Name: "{userdesktop}\OpenSTV"; Filename: "{app}\OpenSTV.exe"; Tasks: desktopicon

[Registry]
Root: HKCR; Subkey: ".blt"; ValueType: string; ValueName: ""; ValueData: "ERSBLTFile"; Tasks: associatebltfiles
Root: HKCR; Subkey: "ERSBLTFile"; ValueType: string; ValueName: ""; ValueData: "ERS Ballot File"; Flags: uninsdeletekey; Tasks: associatebltfiles
Root: HKCR; Subkey: "ERSBLTFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\Icons\blt.ico,0"; Tasks: associatebltfiles
Root: HKCR; Subkey: "ERSBLTFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\OpenSTV.exe"" ""%1"""; Tasks: associatebltfiles
'''

    def compile(self):
        os.startfile(self.issFile)

################################################################

if sys.platform == "win32":
    class build_installer(py2exe.build_exe.py2exe):
    # This class first builds the exe file(s), then creates a Windows installer.
    # You need InnoSetup for it.
        def run(self):
            # First, let py2exe do its work.
            py2exe.build_exe.py2exe.run(self)
            
            # create the Installer, using the files py2exe has created.
            script = InnoScript(self.lib_dir, self.dist_dir,
                                self.windows_exe_files, self.lib_files)
            print "*** creating the inno setup script***"
            script.create()
            print "*** compiling the inno setup script***"
            script.compile()
            
################################################################

# generic arguments for setup()
name = "OpenSTV"
description = "Implements the single transferable vote, instant runoff "\
              "voting, and several other voting systems."
author = "Jeff O'Neill"
author_email = "jeff.oneill@openstv.org"
url = "http://www.openstv.org"
license = "Gnu General Public License version 2"
packages = ["openstv",
            "openstv.MethodPlugins", 
            "openstv.LoaderPlugins",
            "openstv.ReportPlugins"]
data_files = [ ("", ["openstv/Help.html",
                     "openstv/License.html"]),
               ("Icons",
                 ["openstv/Icons/pie.ico",
                  "openstv/Icons/blt.ico",
                  "openstv/Icons/splash.png"]) ]

# Get list of plugins because they won't be automatically included
includes = []
pluginPackageNames = ["openstv.MethodPlugins", "openstv.LoaderPlugins", "openstv.ReportPlugins"]
import pkgutil
for x in pluginPackageNames:
    package = __import__(x, fromlist="dummy")
    ppath = package.__path__
    pname = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(ppath, pname):
        includes.append(modname)

if sys.platform == "win32":
    # py2exe ignores package_data
    # Note that Python 2.6 is more difficult for some reason so better to
    # stick with Python 2.5.
    py2exeArgs = dict(
        script = "openstv/OpenSTV.py",
        icon_resources = [(1, "openstv/Icons/pie.ico")],
        other_resources = [(24, 1, manifest_template)],
        dest_base = "OpenSTV")
    py2exeOptions = dict(includes = includes,
                         compressed = 1,
                         optimize = 1,
                         bundle_files = 2)
    setup(name = name,
          version = OpenSTV_version,
          description = description,
          author = author,
          author_email = author_email,
          url = url,
          license = license,
          packages = packages,
          data_files = data_files,          
          windows = [py2exeArgs],
          options = dict(py2exe = py2exeOptions),
          cmdclass = {"py2exe": build_installer},
          zipfile = None
          )

elif sys.platform == "darwin":
    #
    # usage: ./setup.py
    #
    # py2app options
    plist = {
        "CFBundleDocumentTypes":
            [{"CFBundleTypeName": "OpenSTV ballot file",
             "CFBundleTypeIconFile": "blt.icns",
             "CFBundleTypeExtensions": ["blt", "txt"],
             "CFBundleTypeRole": "Viewer"}]
    }
    py2app_options = dict(
        includes = includes,
        plist = plist,
        iconfile = 'openstv/Icons/pie.icns',
        no_strip = 0,
    )
    setup(name = name,
          script_name = 'setup.py',
          script_args = ['py2app'],
          version = OpenSTV_version,
          description = description,
          author = author,
          author_email = author_email,
          url = url,
          license = license,
          packages = packages, 
          data_files = data_files,
          options = dict(py2app=py2app_options),
          scripts = ['openstv/OpenSTV.py'],
          app = ['openstv/OpenSTV.py'],
          setup_requires = ["py2app"],
          )
    os.system("hdiutil create -ov -imagekey zlib-level=9 -srcfolder dist/OpenSTV.app dist/OpenSTV.dmg")

else:
    # For *nix, data_files goes into the /usr directory, which we don't want.
    # pacakge_data doesn't appear to work for sdist so use MANIFEST.in

    setup(name = name,
          version = OpenSTV_version,
          description = description,
          author = author,
          author_email = author_email,
          url = url,
          license = license,
          packages = packages,
          )
