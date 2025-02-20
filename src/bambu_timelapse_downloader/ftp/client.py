import ftplib
import pathlib
import ssl
import typing as t

import aioftp


class FTPPath:
    def __init__(self, path: t.Any, is_dir: bool | None = None):
        self.path = str(path).replace('//', '/')
        if self.path.endswith('/'):
            self.path = self.path[:-1]
            self.is_dir = True
        else:
            self.is_dir = is_dir or False

    def __truediv__(self, other: t.Union[str, "FTPPath"]):
        is_dir = self.is_dir
        if isinstance(other, FTPPath):
            is_dir = other.is_dir
            other = other.path
        return FTPPath(f"{self.path}/{other}", is_dir=is_dir)

    def __str__(self):
        return f"{self.path}{'/' if self.is_dir else ''}"

    def __repr__(self):
        return f"FTPPath({self.path})"

    def __eq__(self, other: t.Union["FTPPath", str]):
        return isinstance(other, (FTPPath, str)) and str(other) == self.path

    def __hash__(self):
        return hash(self.path)

    def dirname(self) -> "FTPPath":
        return FTPPath('/'.join(self.path.split('/')[:-1]), is_dir=True)

    def name(self, trailing_slash: bool = True) -> str:
        return self.path.split('/')[-1] + ('/' if self.is_dir and trailing_slash else '')


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    def ntransfercmd(self, cmd, rest=None):
        # Overridden to ensure that the socket is reused
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

    def cwd(self, path: str | FTPPath):
        """Change the current working directory."""
        return super().cwd(str(path))

    def isdir(self, path: str) -> bool:
        """Return True if the path is a directory."""
        cur_dir = self.pwd()
        try:
            self.cwd(path)
        except ftplib.error_perm as e:
            if "550" in str(e):
                return False
            raise
        else:
            return True
        finally:
            self.cwd(cur_dir)

    def nlst(self, path: str | FTPPath) -> t.Generator[FTPPath, None, None]:
        """List a directory."""
        path = FTPPath(path)
        for file in super().nlst(str(path)):
            yield path / FTPPath(file, is_dir=self.isdir(path / file))

    def iterdir(self, path: str | FTPPath) -> t.Generator[FTPPath, None, None]:
        """Iterate over the contents of the directory."""
        path = FTPPath(path)
        try:
            return self.nlst(path)
        except ftplib.error_perm:
            raise

    def download(self, remote_path: str | FTPPath, destination: str | pathlib.Path):
        destination = pathlib.Path(destination)
        try:
            with destination.open('wb') as fhandle:
                self.retrbinary(f'RETR {remote_path}', fhandle.write)
        except ftplib.error_perm:
            destination.unlink()
            raise

    def size(self, path: str | FTPPath) -> int | None:
        return super().size(str(path))

    def sizemb(self, path: str | FTPPath) -> float:
        size = self.size(path)
        if not size:
            return 0
        return round(size / 1024 / 1024, 2)


def get_ftp_client_context(host, port, user, passwd):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return aioftp.Client.context(host, port, user, passwd, ssl=ssl_context)
