import json
import sublime
import sublime_plugin
import os
import re
from .jinja2 import Environment


class PluginMixin():
    def get_selection(self):
        selections = []
        for region in self.view.sel():
            if not region.empty():
                selections.append(region)
        if len(selections) == 0:
            # select whole document
            selections.append(sublime.Region(0, self.view.size()))
        return selections

    def get_contents(self):
        contents = self.view.substr(sublime.Region(0, self.view.size()))
        return contents

    def write_new_buffer(self, contents, output_suffix=" - output"):
        # Create a new output window
        buffername = self.view.name()
        filename = self.view.file_name()
        new_view = self.view.window().new_file()
        if buffername:
            new_view.set_name(buffername + output_suffix)
        elif filename:
            basename = os.path.basename(filename)
            new_view.set_name(basename + output_suffix)
        else:
            new_view.set_name('Untitled' + output_suffix)
        new_view.set_scratch(True)
        new_view.run_command('my_view_command', {'command': 'set_text', 'text': contents})

    def raise_err(self, message, exception_cls=None):
        exception_cls = exception_cls or Exception
        sublime.active_window().run_command("show_panel", {"panel": "console", "toggle": True})
        sublime.status_message(message)
        raise exception_cls(message)


class Mattmc3CodegenFromJinja2(sublime_plugin.TextCommand, PluginMixin):
    def run(self, edit):
        sublime.active_window().show_input_panel(
            "Jinja2 JSON data",
            '''[{"value":"hello"}]''',
            on_done=self.make_it_so,
            on_change=None,
            on_cancel=None)

    def make_it_so(self, input):
        doc = self.get_contents()
        generated = []

        # get json data
        try:
            data = json.loads(input)
        except Exception as ex:
            self.raise_err(str(ex))

        # make sure we can iterate
        try:
            iter(data)
        except TypeError as te:
            data = list(data)

        try:
            for templ_vars in data:
                result = Environment().from_string(doc).render(templ_vars)
                generated.append(result)
        except Exception as ex:
            self.raise_err(str(ex))

        self.write_new_buffer("\n".join(generated))


class MyViewCommandCommand(sublime_plugin.TextCommand, PluginMixin):
    def run(self, edit, **args):
        if 'command' not in args:
            self.raise_err("No command provided")

        if args['command'] == "set_text":
            self.view.replace(edit, sublime.Region(0, self.view.size()), args['text'])
        else:
            self.raise_err("Command not recognized: {}".format(args['command']))
