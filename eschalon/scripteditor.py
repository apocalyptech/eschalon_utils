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

from eschalon import constants as c

def format_completion_text(layout, cell, model, iter, column):
    """
    Formats our completion text for our script commands
    """
    cell.set_property('markup', model.get_value(iter, column))

def match_completion(completion, key, iter, column):
    """
    Matches based on what's been typed in, for our script commands
    """
    model = completion.get_model()
    text = model.get_value(iter, column)
    if text.lower().startswith(key.lower()):
        return True
    return False

class ScriptEditorRow(object):

    def __init__(self, rownum, table, completion_model, parser,
            entry_callback, delbutton_callback, upbutton_callback, downbutton_callback,
            text=''):

        self.parser = parser
        self.table = table
        self.rownum = rownum

        # Our widgets
        self.numlabel = gtk.Label()
        self.update_rownum()
        self.commandentry = gtk.Entry()
        self.commandentry.set_text(text)
        self.commandentry.set_size_request(240, -1)
        self.tokenlabel = gtk.Label()
        self.delbutton = gtk.Button()
        self.delbutton.add(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
        self.delbutton.set_tooltip_text('Delete this command')
        self.upbutton = gtk.Button()
        self.upbutton.add(gtk.image_new_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON))
        self.upbutton.set_tooltip_text('Move this command up a line')
        self.downbutton = gtk.Button()
        self.downbutton.add(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON))
        self.downbutton.set_tooltip_text('Move this command down a line')

        self.widgets = (self.numlabel, self.commandentry, self.tokenlabel,
                self.delbutton, self.upbutton, self.downbutton)

        # Attach a completion to our text Entry
        completion = gtk.EntryCompletion()
        completion.set_model(completion_model)
        completion.set_popup_set_width(False)
        renderer = gtk.CellRendererText()
        completion.pack_start(renderer)
        completion.set_property('text-column', 0)
        completion.set_match_func(match_completion, 0)
        completion.set_cell_data_func(renderer, format_completion_text, 1)
        self.commandentry.set_completion(completion)

        # Attach our widgets to the table
        table.attach(self.numlabel, 0, 1, rownum, rownum+1, gtk.FILL, gtk.FILL)
        table.attach(self.commandentry, 1, 2, rownum, rownum+1, gtk.FILL, gtk.FILL, 5)
        table.attach(self.delbutton, 2, 3, rownum, rownum+1, gtk.FILL, gtk.FILL)
        table.attach(self.upbutton, 3, 4, rownum, rownum+1, gtk.FILL, gtk.FILL)
        table.attach(self.downbutton, 4, 5, rownum, rownum+1, gtk.FILL, gtk.FILL)
        table.attach(self.tokenlabel, 5, 6, rownum, rownum+1, gtk.FILL, gtk.FILL, 5)

        # Now connect some signal handlers
        self.commandentry.connect('changed', entry_callback, self)
        self.delbutton.connect('clicked', delbutton_callback, self)
        self.upbutton.connect('clicked', upbutton_callback, self)
        self.downbutton.connect('clicked', downbutton_callback, self)

        # And now we're basically done
        for widget in self.widgets:
            widget.show_all()

        self.update_tokens()

    def get_commands_text(self):
        """
        Returns the current text of our command, parsed for validity and
        normalized.  could possibly contain compound commands.
        """
        return ' ; '.join([' '.join(c) for c in self.get_commands()])

    def get_commands(self):
        """
        Returns the current text of our command.  Runs through our parser to
        check for validity and 
        """
        return self.parser(self.commandentry.get_text())

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
        Update our token count, and return how many tokens we've got.
        """
        commands = self.get_commands()
        tokencount = sum([len(command) for command in commands])
        if tokencount == 1:
            plural = ''
        else:
            plural = 's'
        self.tokenlabel.set_markup('<i>(%d token%s)</i>' % (tokencount, plural))
        return tokencount

class ScriptEditor(object):

    def __init__(self, parent):
        """
        Script Editor
        """

        self.allow_autoscroll = True
        self.window = gtk.Dialog('Script Editor',
                parent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_OK, gtk.RESPONSE_OK))
        self.window.set_size_request(500, 400)

        # Header
        label = gtk.Label()
        label.set_markup('<b>Script Editor</b>')
        label.set_padding(0, 7)
        self.window.vbox.pack_start(label, False)

        # ScrolledWindow; this holds the main table
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

        # Bottom HBox, shows some buttons and our token count
        hbox = gtk.HBox()
        self.window.vbox.pack_start(hbox, False)

        align = gtk.Alignment(0, .5, 0, 1)
        align.set_padding(7, 7, 9, 9)
        hbox.pack_start(align, False)
        normbutton = gtk.Button()
        align.add(normbutton)
        normhbox = gtk.HBox()
        normhbox.add(gtk.image_new_from_stock(gtk.STOCK_REDO, gtk.ICON_SIZE_BUTTON))
        normhbox.add(gtk.Label('Normalize'))
        normbutton.add(normhbox)
        normbutton.connect('clicked', self.normalize_page)

        self.token_total_label = gtk.Label()
        self.token_total_label.set_alignment(1, .5)
        self.token_total_label.set_padding(9, 0)
        self.token_total_label.set_markup('<b>Total Tokens:</b> 0')
        label.set_padding(5, 7)
        hbox.add(self.token_total_label)

        # Set up the completion model, for our Entry completions to use
        self.completion_model = gtk.ListStore(str, str)
        for command in sorted(c.commands):
            iter = self.completion_model.append()
            markup = ['<b>%s</b>' % (command)]
            for arg in c.commands[command]:
                if arg[0] == '(':
                    markup.append('(<i>&lt;%s&gt;</i>)' % (arg[1:-1]))
                else:
                    markup.append('<i>&lt;%s&gt;</i>' % (arg))
            self.completion_model.set(iter, 0, command)
            self.completion_model.set(iter, 1, ' '.join(markup))

        # Now show everything
        self.window.vbox.show_all()
        self.rows = []

    def add_row(self, text=''):
        """
        Adds a new line in our script editor window
        """
        rownum = len(self.rows)
        self.rows.append(ScriptEditorRow(rownum, self.table,
            completion_model=self.completion_model,
            parser=self.command_parser,
            entry_callback=self.text_changed,
            delbutton_callback=self.remove_button_clicked,
            upbutton_callback=self.move_row_up,
            downbutton_callback=self.move_row_down,
            text=text))
        if self.allow_autoscroll:
            vadj = self.sw.get_vadjustment()
            vadj.set_value(vadj.get_upper())
        self.update_gui()

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
        self.update_gui()

    def swap_rows(self, row1, row2):
        """
        Swaps the order of two rows.  Note that row1 should be the
        top row, to avoid problems with swaps at the very end of the
        list.
        """
        command1 = row1.commandentry.get_text()
        command2 = row2.commandentry.get_text()
        row2.commandentry.set_text(command1)
        row1.commandentry.set_text(command2)

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

    def launch(self, initial_script=''):
        """
        Launches our script editor
        """
        self.normalize_script(initial_script)

        res = self.window.run()
        self.window.hide()

        return res

    def update_gui(self):
        """
        Performs various tasks that need to be done when we have
        structural changes.  Right now this includes:
          1) Making sure that the last row's "remove" and "down"
             buttons aren't clickable, and the rest are shown.
          2) Making sure the first row's "up" button isn't clickable
          3) Setting the tab order
        """
        taborder_entries = []
        taborder_buttons = []
        for (idx, row) in enumerate(self.rows[:-1]):
            row.delbutton.set_sensitive(True)
            row.upbutton.set_sensitive((idx != 0))
            row.downbutton.set_sensitive(True)
            taborder_entries.append(row.commandentry)
            taborder_buttons.append(row.delbutton)
        self.rows[-1].delbutton.set_sensitive(False)
        self.rows[-1].upbutton.set_sensitive(len(self.rows) > 1)
        self.rows[-1].downbutton.set_sensitive(False)
        taborder_entries.append(self.rows[-1].commandentry)
        self.table.set_focus_chain(taborder_entries + taborder_buttons)

    def update_token_counts(self):
        """
        Updates all the token counts on the page
        """
        tokens = 0
        for row in self.rows:
            tokens += row.update_tokens()
        if tokens > 50:
            self.token_total_label.set_markup('<span color="red"><b>Total Tokens:</b> %d</span>' % (tokens))
        else:
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
                    tokens.append('%s)' % (text[lparen:]))
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
                        if len(command) > 0:
                            command = []
                            commands.append(command)
                    subtokens = subcommand.split()
                    for subtoken in subtokens:
                        subtoken = subtoken.strip()
                        if subtoken != '':
                            command.append(subtoken)
        # Prune a trailing empty command
        if len(commands) > 1 and len(commands[-1]) == 0:
            del commands[-1]

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

    def get_command_aggregate(self):
        """
        Returns all of our commands as a single string
        """
        ret_list = []
        for command in [row.get_commands_text() for row in self.rows]:
            if command != '':
                ret_list.append(command)
        return ' ; '.join(ret_list)

    ###
    ### Our own handlers
    ###
    
    def normalize_page(self, widget):
        """
        Normalizes the display so that each command is in its own line
        """
        self.normalize_script(self.get_command_aggregate())

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
            if widget.get_text() == '' and self.rows[-1].commandentry.get_text().strip() == '':
                self.del_row(len(self.rows)-1)
        self.update_token_counts()

    def remove_button_clicked(self, widget, row):
        """
        GUI callback for remove button
        """
        self.del_row(row.rownum)

    def move_row_up(self, widget, row):
        """
        Move a row up one
        """
        if row.rownum != 0:
            self.swap_rows(self.rows[row.rownum-1], row)

    def move_row_down(self, widget, row):
        """
        Move a row down one
        """
        if row.rownum != (len(self.rows)-1):
            self.swap_rows(row, self.rows[row.rownum+1])
