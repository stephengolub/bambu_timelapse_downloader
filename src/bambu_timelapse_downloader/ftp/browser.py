import asyncio
from collections import defaultdict
import ftplib
import json
import pathlib
import typing as t

import aioftp
import click
import inquirer
from readchar import key
from textual import log
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Header, Footer, LoadingIndicator, Static, Tree
from textual.widgets.tree import TreeNode

from bambu_timelapse_downloader.ftp.client import get_ftp_client_context, FTPPath, ImplicitFTP_TLS


class UpDir(Exception):
    pass


class MultiSelectSwap(Exception):
    def __init__(self, question, option):
        self.question = question
        self.option = question.choices[option]


class ListRender(inquirer.render.console._list.List):
    def process_input(self, pressed):
        if pressed == key.BACKSPACE:
            raise UpDir()
        elif pressed == key.SPACE:
            raise MultiSelectSwap(self.question, self.current)
        else:
            super().process_input(pressed)


class BrowseRender(inquirer.render.console.ConsoleRender):
    def render_factory(self, question_type):
        if question_type == 'list':
            return ListRender
        return super().render_factory(question_type)


class FTPBrowser:
    def __init__(self, ftp_client: ImplicitFTP_TLS, downloader: t.Callable[[FTPPath], None]):
        self.ftp_client = ftp_client
        self.downloader = downloader

    def _perform_download(self, path: str | FTPPath):
        if self.downloader is not None:
            self.downloader(FTPPath(path))
        else:
            self.ftp_client.download(FTPPath(path), ".")


    def _prompt(self, *args, **kwargs):
        return inquirer.prompt(
            *args,
            render=BrowseRender(theme=inquirer.themes.Default()),
            **kwargs,
        )

    def handle_file(self, path: str | FTPPath | list[str | FTPPath]):
        path = [FTPPath(p) for p in path] if isinstance(path, list) else FTPPath(path)
        try:
            if isinstance(path, list) and len(path) >= 1:
                click.echo("Selected Files:\n * {}".format('\n * '.join(path)))
                message = f"Action ({len(path)} files):"
            else:
                filesize = self.ftp_client.sizemb(path)
                message = f"Action: {path} [{filesize} MB]"

            answer = self._prompt([
                inquirer.List(
                    'action',
                    message=message,
                    choices=[
                        ('Download', 'download',),
                        ('Delete', 'delete',),
                    ],
                )
            ])
        except UpDir:
            return

        if answer is None:
            return
        path = path if isinstance(path, list) else [path]
        match answer['action']:
            case 'download':
                for p in path:
                    self._perform_download(p)
            case 'delete':
                if click.confirm(f"Are you sure you want to delete {len(path)} files?"):
                    for p in path:
                        click.echo(f"Deleting {p}")
                        self.ftp_client.delete(p)
            case _:
                pass

    def browse(self, path: str | FTPPath = ''):
        path = FTPPath(path)
        click.echo(f"Loading {path}")
        try:
            files = self.ftp_client.iterdir(path)
        except ftplib.error_perm:
            raise
        else:
            try:
                answer = self._prompt([
                    inquirer.List(
                        'file',
                        message=f"Files in {path}",
                        choices=[(f.name(), f) for f in files],
                    )
                ])
            except UpDir:
                if path == '/' or path == '':
                    click.echo("At root. Exiting.")
                    return
                self.browse(path.dirname())
            except MultiSelectSwap as mss:
                file_choices = [val.tag for val in mss.question.choices if not val.value[0]]
                multi_answer = inquirer.prompt([
                    inquirer.Checkbox(
                        "files",
                        message=f"Select files to action on",
                        choices=file_choices,
                        default=[mss.option.tag],
                    )
                ])
                if multi_answer is None:
                    return
                self.handle_file(multi_answer['files'])
            else:
                if answer is None:
                    return
                file = answer['file']
                if file.is_dir:
                    self.browse(file)
                else:
                    self.handle_file(file)
                    self.browse(path)


class DebugData(VerticalScroll):
    data = reactive("")

    def compose(self):
        yield Static(self.data)


class Debug(Screen):
    def compose(self):
        yield DebugData(id="debug-data")


class Loader(Screen):
    def compose(self):
        with Vertical():
            yield LoadingIndicator("fileLoading")


class FolderList(VerticalScroll):
    folder_tree = reactive(Tree("/").root)

    def compose(self):
        yield self.folder_tree


class FileList(VerticalScroll):
    files = reactive([])

    def render(self) -> ComposeResult:
        return '\n'.join(self.files)


FileTreeDict = dict[str, t.Union["FileTreeDict", list]]


class Browser(Screen):
    _file_tree: FileTreeDict = {}
    node_lookup_map = reactive({})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def update_tree(cls, file_tree):
        log("Updating file tree", tree=file_tree)
        try:
            cls._file_tree.update(file_tree)
        except Exception as e:
            log("Failed to update file tree", exception=e)

    def _build_tree(
        self,
        file_map: FileTreeDict,
        node: TreeNode | None = None,
        path_parts: list[str] | None = None,
    ) -> Tree:
        if path_parts is None:
            path_parts = []

        if node is None:
            node = self.folder_tree
            node.expand()

        for dirname, dircontents in file_map.items():
            self.log("Building tree", dirname=dirname, dircontents=dircontents)
            if dirname == '_':
                self.node_lookup_map[node] = dircontents
            else:
                self._build_tree(file_map[dirname], node.add(str(dirname)), path_parts + [dirname])

        return node.tree

    def compose(self):
        yield Header()

        with Container(id="app-grid"):
            yield FolderList(id="folderlist")
            yield FileList(id="filelist")
            yield Footer(id="footer")

    async def on_tree_node_selected(self, message):
        node = message.node
        if node in self.node_lookup_map:
            self.log("Selected node", node=node)
            FileList.files = self.node_lookup_map[node]

    async def on_mount(self):
        self.log("Mounting Browser", tree=self._file_tree)
        FolderList.folder_tree = self._build_tree(self._file_tree)
        FileList.files = self._file_tree.get('_', []) or []


class TUIFTPBrowser(App):
    CSS = """
    #sidebar {
        dock: left;
        width: 50;
        height: 100%;
        color: #0f2b41;
        background: dodgerblue;
    }
    """
    SCREENS = {
        "loader": Loader,
        "browser": Browser,
        "debug": Debug,
    }

    def __init__(
        self,
        ftp_args: tuple[t.Any],
        downloader: t.Callable[[FTPPath], None],
        default_path: str = '/',
    ):
        self._ftp_args = ftp_args
        self.downloader = downloader
        self.default_path = default_path
        self._tree_load_task = None
        super().__init__()


    def _parse_filelist(self, filelist: list[tuple[pathlib.PurePosixPath, dict]]):
        result: FileTreeDict = {}
        filelist = sorted(filelist, key=lambda x: x[0])

        for filepath, info in filelist:
            fileparts = filepath.parts[1:]
            cur = result
            for p in fileparts[:-1]:
                if p not in cur:
                    cur[p] = {}
                cur = cur[p]
            if info['type'] == 'file':
                cur['_'] = cur.get('_', []) + [fileparts[-1]]
            else:
                cur[fileparts[-1]] = {}

        return result

    async def fetch_filetree(self, path: str, recursive: bool = False):
        self.log("Connecting to FTP server", ip=self._ftp_args[0])
        try:
            async with get_ftp_client_context(*self._ftp_args) as ftp:
                self.log("Connected, fetching directory structure")
                return self._parse_filelist(await ftp.list(path, recursive=recursive))
        except Exception:
            self.log("Failed to connect to FTP server", exc_info=True)
            self.exit()

    async def load_page(self):
        try:
            file_data = await self.fetch_filetree(self.default_path)
        except Exception as e:
            self.log("Failed to fetch file tree", exception=e)
            self.exit()
        else:
            #  self.switch_screen("debug")
            #  DebugData.data = json.dumps(file_data, sort_keys=True, indent=4)

            self.log("File tree loaded, updating browser", files=file_data)
            try:
                Browser.update_tree(file_data)
            except Exception as e:
                self.log("Issue updating file tree", exception=e)
                self.exit()
            else:
                self.switch_screen("browser")

    def on_mount(self):
        self.log("Loading page")
        asyncio.create_task(self.load_page())
        self.push_screen("loader")
