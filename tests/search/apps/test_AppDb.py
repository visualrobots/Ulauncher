import pytest
import mock
from ulauncher.search.apps.AppDb import AppDb, search_name
from collections import Iterable


class TestAppDb(object):

    @pytest.fixture
    def app_db(self):
        return AppDb(':memory:').open()

    @pytest.fixture
    def db_with_data(self, app_db):
        values = [
            {'name': 'john', 'description': 'test', 'search_name': 'john',
                'desktop_file': 'john.desktop', 'icon': 'icon'},
            {'name': 'james', 'description': 'test', 'search_name': 'james',
                'desktop_file': 'james.desktop', 'icon': 'icon'},
            {'name': 'o.jody', 'description': 'test', 'search_name': 'o.jody',
                'desktop_file': 'o.jdy.desktop', 'icon': 'icon'},
            {'name': 'sandy', 'description': 'test', 'search_name': 'sandy',
                'desktop_file': 'sandy.desktop', 'icon': 'icon'},
            {'name': 'jane', 'description': 'test', 'search_name': 'jane',
                'desktop_file': 'jane.desktop', 'icon': 'icon'},
            {'name': 'LibreOffice Calc', 'description': 'test', 'search_name': 'LibreOffice Calc',
                'desktop_file': 'libre.calc', 'icon': 'icon'},
            {'name': 'Calc', 'description': 'test', 'search_name': 'Calc',
                'desktop_file': 'calc', 'icon': 'icon'},
            {'name': 'Guake Terminal', 'description': 'test', 'search_name': 'Guake Terminal',
                'desktop_file': 'Guake Terminal', 'icon': 'icon'},
            {'name': 'Keyboard', 'description': 'test', 'search_name': 'Keyboard',
                'desktop_file': 'Keyboard', 'icon': 'icon'}
        ]
        app_db.get_cursor().executemany("""INSERT INTO app_db (name, desktop_file, description, search_name)
            VAlUES (:name, :desktop_file, :description, :search_name)""", values)
        for rec in values:
            app_db.get_icons()[rec['desktop_file']] = rec['icon']
        return app_db

    @pytest.fixture(autouse=True)
    def get_app_icon_pixbuf(self, mocker):
        return mocker.patch('ulauncher.search.apps.AppDb.get_app_icon_pixbuf')

    @pytest.fixture(autouse=True)
    def force_unicode(self, mocker):
        force_unicode = mocker.patch('ulauncher.search.apps.AppDb.force_unicode')
        force_unicode.side_effect = lambda x: x

    def test_remove_by_path(self, db_with_data):
        assert db_with_data.get_by_path('jane.desktop')
        db_with_data.remove_by_path('jane.desktop')
        assert not db_with_data.get_by_path('jane.desktop')

    def test_put_app(self, app_db, get_app_icon_pixbuf, mocker):
        app = mock.MagicMock()
        app.get_filename.return_value = 'file_name_test1'
        app.get_string.return_value = None
        app.get_name.return_value = 'name_test1'
        app.get_description.return_value = 'description_test1'

        app_db.put_app(app)

        assert app_db.get_by_path('file_name_test1') == {
            'desktop_file': 'file_name_test1',
            'name': 'name_test1',
            'description': 'description_test1',
            'search_name': 'name_test1',
            'icon': get_app_icon_pixbuf.return_value
        }

    def test_find_returns_sorted_results(self, db_with_data, mocker):
        SortedList = mocker.patch('ulauncher.search.apps.AppDb.SortedList')
        result_list = SortedList.return_value
        AppResultItem = mocker.patch('ulauncher.search.apps.AppDb.AppResultItem')

        assert db_with_data.find('bro') is result_list
        result_list.append.assert_called_with(AppResultItem.return_value)
        SortedList.assert_called_with('bro', min_score=mock.ANY, limit=9)

        for rec in db_with_data.get_records():
            AppResultItem.assert_any_call(rec)

    def test_find_empty_query(self, db_with_data, mocker):
        assert isinstance(db_with_data.find(''), Iterable)

    def test_get_by_name(self, db_with_data):
        # also test case insensitive search
        assert db_with_data.get_by_name('JohN') == {
            'name': 'john',
            'description': 'test',
            'desktop_file': 'john.desktop',
            'icon': 'icon',
            'search_name': 'john'
        }

    def test_get_by_path(self, db_with_data):
        # also test case insensitive search
        assert db_with_data.get_by_path('libre.calc') == {
            'name': 'LibreOffice Calc',
            'description': 'test',
            'desktop_file': 'libre.calc',
            'icon': 'icon',
            'search_name': 'LibreOffice Calc'
        }


def test_search_name():
    assert search_name('GNU Image Manipulation Program', r'gimp-2.8 %U') == 'GNU Image Manipulation Program gimp-2.8'
    assert search_name('Content Hub Clipboard', r'content-hub-clipboard %U') == 'Content Hub Clipboard'
    assert search_name('Scopes', r'/usr/bin/unity8-dash') == 'Scopes unity8-dash'
    assert search_name('Mouse & Touchpad', r'unity-control-center mouse') == 'Mouse & Touchpad unity-control-center'
    assert search_name('Back Up', r'deja-dup --backup') == 'Back Up deja-dup'
    assert search_name('Calendar', r'gnome-calendar') == 'Calendar'
    assert search_name('Amazon', r'unity-webapps-runner --amazon --app-id=ubuntu-amazon-default') == \
        'Amazon unity-webapps-runner'
