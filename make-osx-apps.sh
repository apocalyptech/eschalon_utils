#!/bin/sh

# Requirements:
# 
# - pygtk installed from homebrew
# - py2app, czipfile, and pycrypto installed with easy_install
# - OS X developer tools
#
# Developed on Mac OS 10.8.3 64 bit and tested on latest 10.9

# Build these apps
APPS="eschalon_utils"
# Include these python modules
INCLUDE="gtk,gio,atk,pangocairo"
# Add these files to each app bundle.  We can't include gtk here because the
# MachO header rebuild fails with the python library - see below for more
# info
RESOURCES="data,/usr/local/lib/pango,/usr/local/lib/gdk-pixbuf-2.0"
# The version numbers for these libraries as they appear in the file names
PANGO=1.0.0
GDKPIXBUF=2.0.0
# Make sure python knows how to find libraries installed by Homebrew
export PYTHONPATH=/usr/local/lib/python2.7/site-packages:/usr/local/lib/python2.7/site-packages/gtk-2.0
# Dynamically figure out the version number and include that in the name
VERSION=$(grep 'version =' eschalon/__init__.py|perl -i -ne '/([0-9.]+)/ && print "$1\n"')
DMG="Eschalon Utils $VERSION"

# Exit if any step exits uncleanly. Helpful for a hack job like this
set -e

mkdir -p "$DMG"
rm -rf "$DMG/*"
for APP in $APPS; do
  # Clean up from previous runs
  rm -f setup.py
  rm -rf build

  PRETTY=$(echo $APP|perl -i -pe 's/_/ /g; s/([\w]+)/\u\L$1/g')
  cp $APP.py "$PRETTY".py

  # Run py2app
  py2applet --make-setup "$PRETTY.py"
  # Set icon file, which evidently can't be specified on the command line
  perl -i -pe 's/(OPTIONS = {.*?)}/$1, "iconfile":"data\/eschalon1.icns"}/' setup.py
  python setup.py py2app -i "$INCLUDE" -r "$RESOURCES" -d "$DMG"

  # The libraries are referenced by these names, and py2app doesn't make
  # the appropriate links, so make them ourselves
  cd "$DMG"/"$PRETTY".app/Contents/Frameworks

  # The data directory gets referenced relative to the contents of the
  # site-packages directory.  If it's a zip file as py2app makes, this
  # doesn't work right
  cd ../Resources/lib/python2.7
  mkdir site-packages
  cd site-packages
  unzip ../site-packages.zip
  rm ../site-packages.zip
  mv ../../../data .

  # Put the included libraries in the right place
  cd ../../..
  mv pango gdk-pixbuf-2.0 lib/
  # Manually copy in the GTK modules. If we ask py2app to do this for us, it
  # will try to rewrite the library paths with macholib.  That would be fine
  # except that macholib will error out with "new Mach header too large"
  # even for 64-bit executables that don't have that limitation. Fortunately
  # install_name_tool deals with 64-bit executables correctly
  cp -HR /usr/local/lib/gtk-2.0 lib/
  cd lib/gtk-2.0
  # The files are more 444 by default, and install_name_tool can't override
  chmod -R u+w .
  # Modify library paths in the modules manually with install_name_tool
  # Stolen from tegaki create_app_bundle.sh
  for dylib in */*.so */*/*.so; do
    echo "Modifying library references in $dylib"
    changes=""
    for lib in `otool -L $dylib | egrep "(/opt/local|/local/|libs/)" | awk '{print $1}'` ; do
      base=`basename $lib`
      changes="$changes -change $lib @executable_path/../Frameworks/$base"
    done
    if test "x$changes" != x ; then
      if ! install_name_tool $changes $dylib ; then
        echo "Error for $dylib"
      fi
    fi
    install_name_tool -id @executable_path/../Resources/lib/gtk-2.0/$dylib $dylib
  done

  cd ../..
  # Create pango config files
  mkdir -p etc/pango
  pango-querymodules |perl -i -pe 's/^[^#].*\///' > etc/pango/pango.modules
  gdk-pixbuf-query-loaders |perl -i -pe 's/^[^#].*\/(lib\/.*")$/"..\/Resources\/$1/' > lib/gdk-pixbuf-2.0/2.10.0/loaders.cache
  echo "[Pango]\nModuleFiles=./etc/pango/pango.modules\n" > etc/pango/pangorc

  # Modify the pango libraries to look for config files and modules in the
  # right place

  # First, double-check that the library version numbers are 6 characters. 
  # If they're not, this won't work.
  for i in libpango-$PANGO libgdk_pixbuf-$GDKPIXBUF; do
    if ! readlink /usr/local/lib/$i.dylib |egrep -q "/Cellar/.*?/.{6}/lib/lib"; then
      echo "Fatal: $i version is not 6 characters long"
      exit
    fi
  done

  # Do the modifications. Our new paths are shorter than the old ones,
  # so null-terminate the string and pad up with dots.
  cd ../Frameworks
  perl -i -pe 's?/usr/local/Cellar/pango/.{6}/etc/pango?../Resources/etc/pango\x00.................?' libpango-$PANGO.dylib
  perl -i -pe 's?/usr/local/Cellar/pango/.{6}/lib/pango?../Resources/lib/pango\x00.................?' libpango-$PANGO.dylib
  perl -i -pe 's?/usr/local/Cellar/gdk-pixbuf/.{6}/lib?../Resources/lib/\x00.....................?' libgdk_pixbuf-$GDKPIXBUF.dylib

  # Go back to the root to start the next loop iteration
  cd ../../../..

  # We don't need this any more
  rm "$PRETTY".py
done

hdiutil create "$DMG".dmg -srcfolder "$DMG" -ov
