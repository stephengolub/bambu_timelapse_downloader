import ftplib
import ssl
from unittest import mock

import pytest

from bambu_timelapse_downloader import ftp as subject_module


class TestImplicitFTP_TLS:
    @pytest.fixture
    def cls(self):
        return subject_module.ImplicitFTP_TLS

    @pytest.fixture
    def instance(self, cls):
        return cls()

    @pytest.fixture
    def wrap_socket(self):
        return mock.MagicMock()

    @pytest.fixture
    def mocked_context(self, instance, wrap_socket):
        old_context = instance.context
        instance.context = mock.PropertyMock(wrap_socket=wrap_socket)
        yield instance.context
        instance.context = old_context

    @pytest.fixture(
        params=('sock_value_none', 'sock_value_test', 'sock_value_socket'),
    )
    def socket_value(self, request):
        match request.param:
            case 'sock_value_none':
                return None
            case 'sock_value_test':
                return 'test-value'
            case 'sock_value_socket':
                with mock.patch('socket.socket') as mocked_sock:
                    return mocked_sock

    def test_bases(self, cls):
        assert cls.__bases__ == (ftplib.FTP_TLS,)

    def test_initial_sock(self, instance):
        assert instance._sock is None

    def test_sock_property(self, instance):
        assert instance._sock is instance.sock

    def test_sock_setter(self, instance, mocked_context, socket_value):
        instance.sock = socket_value

        if isinstance(socket_value, ssl.SSLSocket) or socket_value is None:
            instance.context.wrap_socket.assert_not_called()
        else:
            instance.context.wrap_socket.assert_called_once_with(socket_value)


