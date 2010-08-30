#!/usr/bin/python
# vim: set expandtab tabstop=4 shiftwidth=4:
# $Id$
#
# Eschalon Savefile Editor
# Copyright (C) 2008-2010 CJ Kucera
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import sys
import gtk

class ScriptEditorRow(object):

    def __init__(self, rownum, table, parser, entry_callback, delbutton_callback, text=''):

        self.rownum = rownum
        self.parser = parser

        self.numlabel = gtk.Label('%d.' % (rownum + 1))
        self.commandentry = gtk.Entry()
        self.commandentry.set_text(text)
        self.commandentry.set_size_request(240, -1)
        self.tokenlabel = gtk.Label()
        self.delbutton = gtk.Button()
        self.delbutton.add(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))

        self.widgets = (self.numlabel, self.commandentry, self.tokenlabel, self.delbutton)

        table.attach(self.numlabel, 0, 1, rownum, rownum+1, gtk.FILL, gtk.FILL)
        table.attach(self.commandentry, 1, 2, rownum, rownum+1, gtk.FILL, gtk.FILL, 5)
        table.attach(self.delbutton, 2, 3, rownum, rownum+1, gtk.FILL, gtk.FILL)
        table.attach(self.tokenlabel, 3, 4, rownum, rownum+1, gtk.FILL, gtk.FILL, 5)

        self.commandentry.connect('changed', entry_callback, self)
        self.delbutton.connect('clicked', delbutton_callback, self)

        for widget in self.widgets:
            widget.show_all()

        self.table = table
        self.update_tokens()

    def get_command(self):
        """
        Returns the current text of our command
        """
        return self.commandentry.get_text().strip()

    def move_up(self):
        """
        Move us "up" - a command before us has been deleted
        """

        table = self.table
        for widget in self.widgets:
            for prop in ['top-attach', 'bottom-attach']:
                table.child_set_property(widget, prop, table.child_get_property(widget, prop)-1)
        self.rownum -= 1
        self.update_rownum()

    def move_down(self):
        """
        Move us "down" - a command has been added before us
        """
        table = self.table
        for widget in self.widgets:
            for prop in ['bottom-attach', 'top-attach']:
                table.child_set_property(widget, prop, table.child_get_property(widget, prop)+1)
        self.rownum += 1
        self.update_rownum()

    def update_rownum(self):
        """
        Do whatever we need to do when our rownum changes, from a visual perspective.
        """
        self.numlabel.set_text('%d.' % (self.rownum + 1))

    def update_tokens(self):
        """
        Update our token count, and return how many tokens we've got
        """
        commands = self.parser(self.get_command())
        tokencount = sum([len(command) for command in commands])
        if tokencount == 1:
            plural = ''
        else:
            plural = 's'
        self.tokenlabel.set_markup('<i>(%d token%s)</i>' % (tokencount, plural))
        return tokencount

class ScriptEditor(object):

    def __init__(self, parent, initial_script=''):
        """
        Script Editor
        """

        self.allow_autoscroll = True
        self.window = gtk.Dialog('Script Editor',
                parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.window.set_size_request(400, 300)

        label = gtk.Label()
        label.set_markup('<b>Script Editor</b>')
        label.set_padding(0, 7)
        self.window.vbox.pack_start(label, False)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.sw.set_shadow_type(gtk.SHADOW_NONE)
        self.window.vbox.add(self.sw)
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        self.sw.add(vp)

        align = gtk.Alignment(.5, .5, 1, 1)
        align.set_padding(5, 5, 5, 5)
        vp.add(align)
        self.table = gtk.Table()
        align.add(self.table)

        align = gtk.Alignment(0, .5, 0, 1)
        align.set_padding(7, 0, 0, 0)
        self.window.vbox.pack_start(align, False)
        normbutton = gtk.Button()
        align.add(normbutton)
        normhbox = gtk.HBox()
        normhbox.add(gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_BUTTON))
        normhbox.add(gtk.Label('Normalize'))
        normbutton.add(normhbox)
        normbutton.connect('clicked', self.normalize_page)

        self.token_total_label = gtk.Label()
        self.token_total_label.set_alignment(0, .5)
        self.token_total_label.set_markup('<b>Total Tokens:</b> 0')
        label.set_padding(5, 7)
        self.window.vbox.pack_start(self.token_total_label, False)

        self.window.show_all()
        self.rows = []

    def add_row(self, text=''):
        """
        Adds a new line in our script editor window
        """
        rownum = len(self.rows)
        self.rows.append(ScriptEditorRow(rownum, self.table,
            parser=self.command_parser,
            entry_callback=self.text_changed,
            delbutton_callback=self.remove_button_clicked,
            text=text))
        if self.allow_autoscroll:
            vadj = self.sw.get_vadjustment()
            vadj.set_value(vadj.get_upper())

    def del_row(self, rownum):
        """
        Deletes a line in our script editor window
        """
        to_del = self.rows[rownum]
        to_shift = self.rows[rownum+1:]
        for widget in to_del.widgets:
            self.table.remove(widget)
        for row in to_shift:
            row.move_up()
        del self.rows[rownum]
        self.force_blank()

    def force_blank(self):
        """
        Forces a blank line at the end, so the user can always add One More Command
        """
        self.allow_autoscroll = False
        if len(self.rows) > 0:
            self.rows[-1].commandentry.emit('changed')
        else:
            self.add_row()
        self.allow_autoscroll = True

    def del_all_rows(self):
        """
        Completely wipes out our table
        """
        for row in self.rows:
            for widget in row.widgets:
                self.table.remove(widget)
        self.rows = []

    def launch(self):
        """
        Launches our script editor
        """
        self.del_all_rows()
        self.add_row()

        res = self.window.run()
        self.window.hide()

    def update_token_counts(self):
        """
        Updates all the token counts on the page
        """
        tokens = 0
        for row in self.rows:
            tokens += row.update_tokens()
        self.token_total_label.set_markup('<b>Total Tokens:</b> %d' % (tokens))

    def command_parser(self, text):
        """
        Returns a list of commands in the given text, which themselves will be
        lists of tokens.
        """

        # First loop through and find any parenthetical tokens,
        # separate them out.
        cur = 0
        tokens = []
        while True:
            try:
                lparen = text.index('(', cur)
                if lparen != 0:
                    tokens.append(text[cur:lparen])
                try:
                    rparen = text.index(')', cur)
                    tokens.append(text[lparen:rparen+1])
                    cur = rparen+1
                    if cur == len(text):
                        break
                except ValueError:
                    tokens.append(text[lparen:])
                    break
            except ValueError:
                tokens.append(text[cur:])
                break

        # Now loop through and process any nonparenthetical tokens,
        # which may involve splitting on ;
        commands = []
        command = []
        commands.append(command)
        for token in tokens:
            token = token.strip()
            if token == '':
                continue
            elif token[0] == '(':
                command.append(token)
            else:
                for (idx, subcommand) in enumerate(token.split(';')):
                    if idx != 0:
                        command = []
                        commands.append(command)
                    subtokens = subcommand.split()
                    for subtoken in subtokens:
                        subtoken = subtoken.strip()
                        if subtoken != '':
                            command.append(subtoken)
        #print commands
        return commands

    def normalize_script(self, text):
        """
        Given a script, populate the initial display.
        """
        self.allow_autoscroll = False
        self.del_all_rows()
        commands = self.command_parser(text)
        for command in commands:
            if len(command) > 0:
                self.add_row(' '.join(command))
        self.force_blank()
        self.allow_autoscroll = True

    ###
    ### Our own handlers
    ###
    
    def normalize_page(self, widget):
        """
        Normalizes the display so that each command is in its own line
        """
        full_script = ' ; '.join([row.get_command() for row in self.rows])
        self.normalize_script(full_script)

    ###
    ### Handlers called by row elements
    ###

    def text_changed(self, widget, row):
        """
        When our text changes
        """
        if row.rownum == len(self.rows)-1:
            if widget.get_text() != '':
                self.add_row()
        elif row.rownum == len(self.rows)-2:
            if widget.get_text() == '' and self.rows[-1].get_command() == '':
                self.del_row(len(self.rows)-1)
        self.update_token_counts()

    def remove_button_clicked(self, widget, row):
        """
        GUI callback for remove button
        """
        self.del_row(row.rownum)
