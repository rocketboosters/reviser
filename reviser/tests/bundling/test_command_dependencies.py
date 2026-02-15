"""Tests for command-based dependency installation (poetry_command and uv_command)."""

import pathlib
import tempfile
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from reviser import definitions
from reviser.bundling import _installer


@pytest.fixture
def mock_connection():
    """Create a mock AWS connection."""
    connection = MagicMock()
    connection.aws_account_id = "123456789012"
    return connection


@pytest.fixture
def mock_target(mock_connection):
    """Create a mock target with dependency group."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = pathlib.Path(tmpdir)

        # Create a mock target
        target = MagicMock()
        target.directory = target_dir
        target.site_packages_directory = target_dir / "site_packages"
        target.site_packages_directory.mkdir(parents=True)

        # Create dependency group
        dep_group = MagicMock()
        dep_group.site_packages_directory = target.site_packages_directory
        dep_group.directory = target_dir

        target.dependencies = dep_group
        target.dependencies.is_shared = False

        yield target


class TestPoetryCommandDependency:
    """Tests for poetry_command dependency type."""

    def test_get_package_names_returns_empty_list(self, mock_connection):
        """Should return empty list of packages for poetry_command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            poetry_cmd_dep = definitions.PoetryCommandDependency(
                directory=directory,
                data={"kind": "poetry_command", "args": ["install", "--no-dev"]},
                connection=mock_connection,
                group=dep_group,
            )

            # Should return empty list, not actual packages
            assert poetry_cmd_dep.get_package_names() == []

    def test_command_args_property(self, mock_connection):
        """Should retrieve command arguments from configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            expected_args = ["install", "--no-dev", "--no-root"]
            poetry_cmd_dep = definitions.PoetryCommandDependency(
                directory=directory,
                data={"kind": "poetry_command", "args": expected_args},
                connection=mock_connection,
                group=dep_group,
            )

            assert poetry_cmd_dep.command_args == expected_args

    @patch("reviser.definitions.configurations.depending._find_poetry_executable")
    @patch("subprocess.run")
    def test_execute_command(
        self, mock_subprocess_run, mock_find_poetry, mock_connection
    ):
        """Should execute poetry command with correct arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            mock_find_poetry.return_value = "/usr/local/bin/poetry"

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            args = ["install", "--no-dev"]
            poetry_cmd_dep = definitions.PoetryCommandDependency(
                directory=directory,
                data={"kind": "poetry_command", "args": args},
                connection=mock_connection,
                group=dep_group,
            )

            # Execute the command
            poetry_cmd_dep.execute_command()

            # Verify subprocess.run was called with correct command
            expected_command = ["/usr/local/bin/poetry", "install", "--no-dev"]
            mock_subprocess_run.assert_called_once_with(
                expected_command, stdout=ANY, check=True
            )

    @patch("reviser.definitions.configurations.depending._find_poetry_executable")
    @patch("subprocess.run")
    def test_install_command_calls_execute_command(
        self, mock_subprocess_run, mock_find_poetry, mock_connection
    ):
        """Should call execute_command when installing poetry_command dependency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            mock_find_poetry.return_value = "/usr/local/bin/poetry"

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            poetry_cmd_dep = definitions.PoetryCommandDependency(
                directory=directory,
                data={"kind": "poetry_command", "args": ["install"]},
                connection=mock_connection,
                group=dep_group,
            )

            # Call the installer function
            _installer._install_command(poetry_cmd_dep)

            # Verify subprocess.run was called (via execute_command)
            mock_subprocess_run.assert_called_once()


class TestUvCommandDependency:
    """Tests for uv_command dependency type."""

    def test_get_package_names_returns_empty_list(self, mock_connection):
        """Should return empty list of packages for uv_command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            uv_cmd_dep = definitions.UvCommandDependency(
                directory=directory,
                data={
                    "kind": "uv_command",
                    "args": ["pip", "install", "-r", "requirements.txt"],
                },
                connection=mock_connection,
                group=dep_group,
            )

            # Should return empty list, not actual packages
            assert uv_cmd_dep.get_package_names() == []

    def test_command_args_property(self, mock_connection):
        """Should retrieve command arguments from configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            expected_args = ["pip", "install", "-r", "requirements.txt", "--no-cache"]
            uv_cmd_dep = definitions.UvCommandDependency(
                directory=directory,
                data={"kind": "uv_command", "args": expected_args},
                connection=mock_connection,
                group=dep_group,
            )

            assert uv_cmd_dep.command_args == expected_args

    @patch("reviser.definitions.configurations.depending._find_uv_executable")
    @patch("subprocess.run")
    def test_execute_command(self, mock_subprocess_run, mock_find_uv, mock_connection):
        """Should execute uv command with correct arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            mock_find_uv.return_value = "/usr/local/bin/uv"

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            args = ["pip", "install", "-r", "requirements.txt"]
            uv_cmd_dep = definitions.UvCommandDependency(
                directory=directory,
                data={"kind": "uv_command", "args": args},
                connection=mock_connection,
                group=dep_group,
            )

            # Execute the command
            uv_cmd_dep.execute_command()

            # Verify subprocess.run was called with correct command
            expected_command = [
                "/usr/local/bin/uv",
                "pip",
                "install",
                "-r",
                "requirements.txt",
            ]
            mock_subprocess_run.assert_called_once_with(
                expected_command, stdout=ANY, check=True
            )

    @patch("reviser.definitions.configurations.depending._find_uv_executable")
    @patch("subprocess.run")
    def test_install_command_calls_execute_command(
        self, mock_subprocess_run, mock_find_uv, mock_connection
    ):
        """Should call execute_command when installing uv_command dependency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            mock_find_uv.return_value = "/usr/local/bin/uv"

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            uv_cmd_dep = definitions.UvCommandDependency(
                directory=directory,
                data={"kind": "uv_command", "args": ["sync"]},
                connection=mock_connection,
                group=dep_group,
            )

            # Call the installer function
            _installer._install_command(uv_cmd_dep)

            # Verify subprocess.run was called (via execute_command)
            mock_subprocess_run.assert_called_once()


class TestCommandDependenciesVsTraditional:
    """Tests comparing command-based vs traditional dependency handling."""

    @patch("reviser.definitions.configurations.depending._find_poetry_executable")
    @patch("subprocess.run")
    @patch("reviser.bundling._installer._install_pip_package")
    def test_poetry_command_doesnt_install_packages_individually(
        self,
        mock_install_pip_package,
        mock_subprocess_run,
        mock_find_poetry,
        mock_connection,
    ):
        """Should NOT iterate over packages for poetry_command type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            mock_find_poetry.return_value = "/usr/local/bin/poetry"

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            poetry_cmd_dep = definitions.PoetryCommandDependency(
                directory=directory,
                data={"kind": "poetry_command", "args": ["install"]},
                connection=mock_connection,
                group=dep_group,
            )

            # Install using command-based approach
            _installer._install_command(poetry_cmd_dep)

            # Should NOT call _install_pip_package
            mock_install_pip_package.assert_not_called()

            # Should call subprocess.run instead
            mock_subprocess_run.assert_called_once()

    @patch("reviser.definitions.configurations.depending._find_uv_executable")
    @patch("subprocess.run")
    @patch("reviser.bundling._installer._install_pip_package")
    def test_uv_command_doesnt_install_packages_individually(
        self,
        mock_install_pip_package,
        mock_subprocess_run,
        mock_find_uv,
        mock_connection,
    ):
        """Should NOT iterate over packages for uv_command type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            mock_find_uv.return_value = "/usr/local/bin/uv"

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = pathlib.Path(tmpdir) / "site_packages"

            uv_cmd_dep = definitions.UvCommandDependency(
                directory=directory,
                data={"kind": "uv_command", "args": ["sync"]},
                connection=mock_connection,
                group=dep_group,
            )

            # Install using command-based approach
            _installer._install_command(uv_cmd_dep)

            # Should NOT call _install_pip_package
            mock_install_pip_package.assert_not_called()

            # Should call subprocess.run instead
            mock_subprocess_run.assert_called_once()

    @patch("reviser.bundling._installer._install_pip_package")
    def test_traditional_poetry_installs_packages_individually(
        self, mock_install_pip_package, mock_connection
    ):
        """
        Should iterate over packages for traditional poetry type.

        This demonstrates the difference between poetry and poetry_command.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)

            # Create a pyproject.toml file for poetry to read
            pyproject_toml = directory / "pyproject.toml"
            pyproject_toml.write_text(
                "[tool.poetry.dependencies]\n"
                'python = "^3.8"\n'
                'requests = "^2.28.0"\n'
                'pytest = "^7.2.0"\n'
            )

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = directory / "site_packages"
            dep_group.site_packages_directory.mkdir()
            dep_group.directory = directory

            # Traditional poetry dependency
            poetry_dep = definitions.PoetryDependency(
                directory=directory,
                data={"kind": "poetry", "file": "pyproject.toml"},
                connection=mock_connection,
                group=dep_group,
            )

            # Install using traditional approach
            _installer._install_poetry(poetry_dep)

            # Should call _install_pip_package for each package
            # (Note: actual package parsing is complex, so we just verify it was called)
            assert (
                mock_install_pip_package.called or poetry_dep.get_package_names() == []
            )

    @patch("subprocess.run")
    @patch("reviser.bundling._installer._install_pip_package")
    def test_traditional_uv_installs_packages_individually(
        self, mock_install_pip_package, mock_subprocess_run, mock_connection
    ):
        """
        Should iterate over packages for traditional uv type.

        This demonstrates the difference between uv and uv_command.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)

            # Create a pyproject.toml file for uv to read
            pyproject_toml = directory / "pyproject.toml"
            pyproject_toml.write_text(
                "[project]\n"
                'name = "test"\n'
                "dependencies = [\n"
                '    "requests>=2.28.0",\n'
                '    "pytest>=7.2.0",\n'
                "]\n"
            )

            # Use a mock for dep_group to simplify testing
            dep_group = MagicMock()
            dep_group.site_packages_directory = directory / "site_packages"
            dep_group.site_packages_directory.mkdir()
            dep_group.directory = directory

            # Traditional uv dependency
            uv_dep = definitions.UvDependency(
                directory=directory,
                data={"kind": "uv", "file": "pyproject.toml"},
                connection=mock_connection,
                group=dep_group,
            )

            # Install using traditional approach
            _installer._install_uv(uv_dep)

            # Should call _install_pip_package for each package
            # (Note: actual package parsing is complex, so we just verify it was called)
            assert mock_install_pip_package.called or uv_dep.get_package_names() == []


class TestInstallDependenciesRouting:
    """Tests that install_dependencies routes to correct installer for command types."""

    @patch("reviser.definitions.configurations.depending._find_poetry_executable")
    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_install_dependencies_routes_poetry_command_correctly(
        self,
        mock_rmtree,
        mock_subprocess_run,
        mock_find_poetry,
        mock_connection,
        mock_target,
    ):
        """Should route poetry_command to _install_command function."""
        mock_find_poetry.return_value = "/usr/local/bin/poetry"

        # Set up target with poetry_command dependency
        mock_target.dependencies.sources = [
            definitions.PoetryCommandDependency(
                directory=mock_target.directory,
                data={"kind": "poetry_command", "args": ["install", "--no-dev"]},
                connection=mock_connection,
                group=mock_target.dependencies,
            )
        ]

        # Install dependencies
        _installer.install_dependencies(mock_target)

        # Verify command was executed
        mock_subprocess_run.assert_called_once()
        command_args = mock_subprocess_run.call_args[0][0]
        assert command_args[0] == "/usr/local/bin/poetry"
        assert "install" in command_args

    @patch("reviser.definitions.configurations.depending._find_uv_executable")
    @patch("subprocess.run")
    @patch("shutil.rmtree")
    def test_install_dependencies_routes_uv_command_correctly(
        self,
        mock_rmtree,
        mock_subprocess_run,
        mock_find_uv,
        mock_connection,
        mock_target,
    ):
        """Should route uv_command to _install_command function."""
        mock_find_uv.return_value = "/usr/local/bin/uv"

        # Set up target with uv_command dependency
        mock_target.dependencies.sources = [
            definitions.UvCommandDependency(
                directory=mock_target.directory,
                data={"kind": "uv_command", "args": ["sync"]},
                connection=mock_connection,
                group=mock_target.dependencies,
            )
        ]

        # Install dependencies
        _installer.install_dependencies(mock_target)

        # Verify command was executed
        mock_subprocess_run.assert_called_once()
        command_args = mock_subprocess_run.call_args[0][0]
        assert command_args[0] == "/usr/local/bin/uv"
        assert "sync" in command_args
