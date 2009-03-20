Eschalon Book 1 Savefile Editor
Copyright (C) 2008, 2009 CJ Kucera

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

ABOUT
-----

This little app lets you edit your character in the savegame of Eschalon
Book I, by Basilisk Games.

   http://basiliskgames.com/book1.html
   http://www.playgreenhouse.com/game/BASLX-000001-01/

Right now it supports just about everything you'd want to edit, though
there's still plenty of values in the file of whose purpose I'm unaware.
See the TODO file for information on what needs to be done with the app
still, which is quite a bit.

The app seems stable enough for me, but use your head and keep a backup of
any character file that you use this on.  Do let me know if it ends up
eating your savefile, because I'd like to fix the bug.  Just don't get upset
if it does.  :)

This was developed on Linux, and it uses Python, GTK+, and PyGTK/Glade to do
its stuff.  I know that those packages are available on Windows / OSX, but
since I don't have easy access to either of those platforms, I'm not sure
what needs to be done to package it up.  If you're familiar with those
kinds of things, let me know and I'll get going on it.

One other note: Certainly let me know if you use this on other architectures
(I'm just on x86) and see funky values through the GUI.  I'm not sure if the
game has a set endianness to its values or not, which could possibly weird
some stuff out.

INSTALLATION, LINUX
-------------------

This is a very early version still, and the code's rather raw.  There's no
official installation scripts or anything like that.  What I'd recommend on a
Linux system is just leaving it untarred wherever you untarred it, and make
a symlink to eschalon_b1_char.py into somewhere in your $PATH (~/bin is
probably the best location).  For example:

   $ cd ~/bin
   $ ln -s /path/to/eschalon_b1_char.py .

Everything should work fine at that point, or at least it does on my system.

INSTALLATION, WINDOWS
---------------------

As with the Linux version, there's no actual installation script or anything
like that.  If you have gtk+, Python, and PyGTK installed, though, you should
be able to just run it from wherever you unzipped it.  The various pieces of
software you'll need to run the program are:

gtk+ Runtime:
  http://sourceforge.net/project/showfiles.php?group_id=98754&package_id=121281
  Note that this version, from the gladewin32 Sourceforge project, is the
  main officially-blessed gtk+ runtime endorsed by PyGTK, so it's the best to
  use.  You can probably get it working with other gtk+ runtime packages, but
  you may have to do more work.  If you DO have other gtk+ runtimes installed,
  certainly be careful about installing this one side-by-side.  You probably
  only want one installed at any given time.

Python:
  http://python.org/download/releases/2.5.2/
  Note that as of this writing (October 2008), PyGTK only ships installation
  packages which use Python 2.5, not Python 2.6, so you'll have to install a
  2.5 release of Python for now.

PyGTK:
  http://www.pygtk.org/downloads.html
  Be sure to install all three of PyCairo, PyGObject, and PyGTK.  You *need*
  all three, otherwise it won't work.

Once you've got those components installed, you should be able to just
double-click on eschalon_b1_char.py, and it'll open up an "Open" dialog.

I'll look into distributing the required packages as one bundle.

USAGE
-----

Here's the full output from the --help option:

To launch the GUI:
	eschalon_b1_char.py [<charfile>]

To list character attributes on the console:
	eschalon_b1_char.py -l [-s <all|stats|avatar|magic|equip|inv>] [-u] <charfile>
	eschalon_b1_char.py --list [--show=<all|stats|...>] [--unknowns] <charfile>

To manipulate character data from the console:
	eschalon_b1_char.py [--set-gold=<num>] [--rm-disease]
		[--set-mana-max=<num>] [--set-mana-cur=<num>]
		[--set-hp-max=<num>] [--set-hp-cur=<num>] <charfile>

Wherever <charfile> appears in the above, you should specify the
location of the file named 'char' inside your savegame folder.

By default, the application will launch the GUI.  Note that
specifying a character file is optional when you're launching
the GUI, but required when using any of the other commandline
options.

For a textual representation of the charfile instead, use -l or
--list.

To only show a listing of specific character information, use
the -s or --show option, which can be specified more than once.
For instance, to show both the basic character stats and the
character's magic information, you would use:

	eschalon_b1_char.py -l -s stats -s magic <charfile>
	or
	eschalon_b1_char.py --list --show=stats --show=magic <charfile>

Currently, the following arguments are valid for --show:

	all - Show all information (this is the default)
	stats - Base Character Statistics
	avatar - Avatar information
	magic - Magic information
	equip - Equipment information (armor, weapons, etc)
	inv - Inventory listings (including "ready" slots)

When being shown the listing, specify -u or --unknowns to
also show unknown data from the charfile.

There are a few options to set your character's gold level, hitpoints,
mana, and remove any diseases.  These should be fairly self-explanatory.
Note that equipped items on your character may increase your effective
HP or MP, so even if this util reports that you're at your maximum HP,
you may find that you're slightly off when you enter the game.  Using the
--set-hp-max or --set-mana-max options will also bring your current HP or
MP up to the new Max level.

Additionally, you may use -h or --help to view this message

CONTACT
-------

Feel free to email me at pez@apocalyptech.com if you've got questions /
concerns.  I'm also logged in to irc.freenode.net as the user "sekhmet" if
you'd prefer that.  Note that Freenode requires that you register a nick
before it'll send privmsgs to other users.
