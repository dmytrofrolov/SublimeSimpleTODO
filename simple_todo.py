import sublime, sublime_plugin
import os

SETTING_FILE_NAME = "SimpleTODO.sublime-settings"

class SimpleTodoListener(sublime_plugin.EventListener):
    def __init__(self):
        self.refresh(sublime.active_window().active_view())

    def on_load(self, view):
        self.refresh(view)

    def on_activated(self, view):
        self.refresh(view)

    def refresh(self, view):
        if view.window() and view.window().folders():
            directory = view.window().folders()[0]
            settings = sublime.load_settings(SETTING_FILE_NAME)
            todo = settings.get(directory)
            if todo:
                regions = []
                for item in todo:
                    if view.file_name() == os.path.join(directory, item["file_name"]):
                        point = view.text_point(int(item["line_number"]) - 1 ,0)
                        regions.append(sublime.Region(point, point))

                view.add_regions("SimpleTodo", regions, "mark", "dot", sublime.HIDDEN)

class SimpleTodoCommand(sublime_plugin.TextCommand):
    def run(self, edit, mode):
        self.window = self.view.window()
        self.directory = self.window.folders()[0]

        if mode == "add":
            self.add()
        elif mode == "list":
            self.list()
        elif mode == "list_and_select":
            self.list_and_select()

    def add(self):
        def on_done(text):
            todo = self.load_todo()
            file_name = self.view.file_name().replace(self.directory + '/', '', 1)
            todo.insert(0, {
                "text": text,
                "file_name": file_name,
                "line_number": self.view.rowcol(self.view.sel()[0].begin())[0] + 1
            })
            self.save_todo(todo)
            self.list()

        sel = self.view.sel()[0]
        if not sel.begin() == sel.end():
            default_text = self.view.substr(sel).strip()
        else:
            default_text = ''

        self.window.show_input_panel('New TODO', default_text, on_done, None, None)

    def list(self):
        settings = self.load_settings()
        todo = settings.get(self.directory)
        if todo == None:
            todo = []

        def on_done(index):
            if index == 0:
                self.add()
            elif index >= 1:
                self.actions(todo[index - 1])

        items = [["+ New", ""]] + [[i["text"], "%s:%s" % (i["file_name"], int(i["line_number"]))] for i in todo]
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, on_done), 0)

    def list_and_select(self):
        settings = self.load_settings()
        todo = settings.get(self.directory)
        if todo == None:
            todo = []

        def on_done(index):
            item = todo[index]
            row = int(item["line_number"]) - 1
            file_path = "{}:{}:{}".format(os.path.join(self.directory, item["file_name"]), row+1, 0)
            view = self.window.open_file(file_path, sublime.ENCODED_POSITION)
            point = view.text_point(row ,0)
            regison = view.line(point)
            view.sel().clear()
            view.sel().add(regison)
            view.show_at_center(regison)

        items = [[i["text"], "%s:%s" % (i["file_name"], int(i["line_number"]))] for i in todo]
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, on_done), 0)

    def actions(self, item):
        def on_done(index):
            if index == 0:
                self.list()
            elif index == 1:
                row = int(item["line_number"])
                file_path = "{}:{}:{}".format(os.path.join(self.directory, item["file_name"]), row, 0)
                view = self.window.open_file(file_path, sublime.ENCODED_POSITION)
                point = view.text_point(row ,0)
                regison = view.line(point)
                view.sel().clear()
                view.sel().add(regison)
                view.show_at_center(regison)
            elif index == 2:
                todo = self.load_todo()
                todo.remove(item)
                self.save_todo(todo)
                self.list()

        info = "%s - %s:%s" % (item["text"], item["file_name"], int(item["line_number"]))
        items = [['< Back', ''], ['> Jump', info], ['- Delete', '']]
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, on_done), 0)

    def load_todo(self):
        settings = self.load_settings()
        todo = settings.get(self.directory)
        if todo == None:
            todo = []
        return todo

    def save_todo(self, todo):
        self.load_settings().set(self.directory, todo)
        self.save_settings()

    def load_settings(self):
        return sublime.load_settings(SETTING_FILE_NAME)

    def save_settings(self):
        sublime.save_settings(SETTING_FILE_NAME)
