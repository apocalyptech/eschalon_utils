Eschalon Book 1 Character Editor
Copyright (C) 2008 CJ Kucera

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

INSTALLATION
------------

This is a very early version still, and the code's rather raw.  There's no
official installation scripts or anything like that.  What I'd recommend on a
Linux system is just leaving it untarred wherever you untarred it, and make
a symlink to eschalon_b1_char.py into somewhere in your $PATH (~/bin is
probably the best location).  For example:

   $ cd ~/bin
   $ ln -s /path/to/eschalon_b1_char.py .

Everything should work fine at that point, or at least it does on my system.
I should have this straightened out by the time 0.3.0 rolls around.

USAGE
-----

Right now the GUI doesn't actually support opening files itself, so you've got
to specify the filename on the commandline, like so:

  eschalon_b1_char.py ~/eschalon_b1_saved_games/slot2/char

Note that at this point, you do have to point it at the "char" file, not just
the slot directory.  If somebody gets this working on Windows or OSX, the
procedure should be the same (so for Windows you'd have to run it from cmd).

If you'd prefer to just get a text listing of the character on the console,
without launching any GUI, you can do so with:

  eschalon_b1_char.py -l ~/eschalon_b1_saved_games/slot2/char
    or
  eschalon_b1_char.py --list ~/eschalon_b1_saved_games/slot2/char

If you add in the -u flag (or --unknowns), it will also print out the list of
unknown variables from the savefile.

CONTACT
-------

Feel free to email me at pez@apocalyptech.com if you've got questions /
concerns.  I'm also logged in to irc.freenode.net as the user "sekhmet" if
you'd prefer that.  Note that Freenode requires that you register a nick
before it'll send privmsgs to other users.
