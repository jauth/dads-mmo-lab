"""The lifecycle of one stack install: status, start, stop and its log (`catalog.SingleStack`).

The `single_controller.SingleServer` of the third runtime. A stack is several
containers of one compose project (FFXI: a database, a one-shot update and five
servers), so status is read from every listener, Start and Stop are the project's
own `compose up` / `compose stop`, and the console follows every listener at once.
What it does not know it asks `docker.py` through seams, so no UI file builds a
docker argv (style-guide §3).

Ownership is checked the way the install engine claims it: a container of ours
answers to this install's compose project (`composegen.project_name()`), or it is
not ours to stop.

Start first brings the install up to date (forever-unbound-own-image, design D4). An
install's compose files and stack files are written at install, and nothing else wrote
them again, so an install kept the image ref and the world SQL of the Yu'lon that made
it. Start renders them again, with the one function the install stage and Play's
certificate remake already use, which writes only what differs and refuses a compose
file Yu'lon did not write. When that changed the compose file, a changed image is pulled
before `up`, with its output said line by line. Volumes, databases and passwords are
untouched: `.env` is written once at install and never by the render.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from yulon import docker, platform
from yulon.catalog import composegen
from yulon.catalog.catalog import SingleEntry, load_catalog
from yulon.catalog.installer import InstallerError
from yulon.catalog.stack_install import StackInstaller, missing_ready_lines, stack_of
from yulon.log import get_logger
from yulon.single_controller import RUNNING, STARTING, STOPPED, UNKNOWN, SingleServerError

logger = get_logger(__name__)

STOP_TIMEOUT_SECONDS = 120.0
"""How long one `compose stop` may take. Each service gets its own 30 s grace period."""

_STOPPED_STATES = ("exited", "dead", "created")
"""What Docker calls a container that is not running and not about to be."""


def server_named_by(container: str) -> str | None:
    """The name of the single server in the bundled catalog that runs `container`, if any.

    It lets a refused Start name the server to stop ("WoW Forever") rather than one of its
    containers ("wowforever-bnet"). Two Forever-login servers both need port 1119, so one
    of them is always the holder when the other is started.
    """
    for entry in load_catalog().single:
        if container in entry.containers():
            return entry.name
    return None


def refresh_install(entry: SingleEntry, server_dir: Path) -> list[str]:
    """Render `entry`'s compose files and stack files into `server_dir`; what changed, said.

    `StackInstaller.write_compose()`: it writes only a file whose content differs and raises
    `InstallerError` for a compose file Yu'lon did not write, before writing anything.
    """
    return StackInstaller(entry).write_compose(server_dir)


@dataclass(frozen=True)
class StackControlSeams:
    """Everything the controller reaches outside itself through. Real by default."""

    platform_id: Callable[[], str] = platform.detect
    state_of: Callable[[str], docker.ContainerState] = docker.container_state
    run_log: Callable[[str], docker.RunLog] = docker.current_run_log
    container_project: Callable[[str], str | None] = docker.container_project
    port_conflicts: Callable[[tuple[int, ...]], list[str]] = docker.port_conflicts
    up: Callable[..., None] = docker.compose_up_all
    stop: Callable[..., None] = docker.compose_stop_all
    follow: Callable[[Path, Sequence[str]], Iterator[str]] = docker.compose_follow_logs
    server_of: Callable[[str], str | None] = server_named_by
    refresh: Callable[[SingleEntry, Path], Sequence[str]] = refresh_install
    pull: Callable[..., docker.AttachedRun] = docker.compose_pull


class StackController:
    """Start, stop, read the status of, and follow the log of one stack install."""

    follows_with_cancel = False
    """`docker compose logs -f` is a child process, which the panel's own Stop ends."""

    def __init__(
        self,
        entry: SingleEntry,
        server_dir: Path,
        *,
        seams: StackControlSeams | None = None,
    ) -> None:
        self.entry = entry
        self.server_dir = server_dir
        self.stack = stack_of(entry)
        self._seams = seams if seams is not None else StackControlSeams()
        self.say: docker.OutputSink = logger.info
        """Where Start says what it brought up to date and the pull's output, one line each.

        Called on Start's own thread. The server tab points it at its console through a
        queued signal; left alone, the lines go to Yu'lon's log."""

    def project(self) -> str:
        """This install's compose project, which its containers are labelled with."""
        return composegen.project_name(
            self.entry.id, self.server_dir, platform_id=self._seams.platform_id
        )

    def status(self) -> str:
        """`running` once every listener is up and printed its ready lines, else what Docker says.

        `stopped` is every listener absent or not running; `unknown` is a daemon that
        would not answer about one of them, which is never read as stopped; anything
        between (some up, some not yet listening, one in restart backoff) is `starting`.
        """
        listeners = self.stack.listeners
        states = [self._seams.state_of(s.container) for s in listeners]
        if any(state.status == "" and not state.missing for state in states):
            return UNKNOWN
        if all(state.missing or state.status in _STOPPED_STATES for state in states):
            return STOPPED
        if any(state.status != "running" for state in states):
            return STARTING
        for service in listeners:
            if not service.ready:
                continue
            log = self._seams.run_log(service.container)
            if not log.this_run_only or missing_ready_lines(service, log.text):
                return STARTING
        return RUNNING

    def is_ours(self) -> bool:
        """Whether every listener that exists belongs to this install's compose project."""
        project = self.project()
        found = False
        for service in self.stack.listeners:
            owner = self._seams.container_project(service.container)
            if owner is None:
                continue
            found = True
            if owner != project:
                return False
        return found

    def start(self, *, account: str = "", client_dir: Path | None = None) -> None:
        """Bring the install up to date, then the stack up.

        Refuses while somebody else's container holds one of its ports, before anything is
        written. The refusal names the server a holding container belongs to, so the player
        is told which one to stop. A container no catalog server runs is named as itself.
        Then the compose files and stack files are rendered again; when the compose file
        changed, the images it names are pulled (live, through `say`) before `up`.
        `account` and `client_dir` are the process runtime's (`SingleServer`): a stack's
        client logs in through its loader, at its own prompt.
        """
        ours = set(self.entry.containers())
        held = [
            name for name in self._seams.port_conflicts(self.entry.host_ports()) if name not in ours
        ]
        if held:
            holders = sorted({self._seams.server_of(name) or name for name in held})
            raise SingleServerError(
                f"{self.entry.name} needs ports "
                f"{', '.join(str(p) for p in self.entry.host_ports())}, and "
                f"{', '.join(holders)} is running on one of them. Stop it first."
            )
        self._bring_up_to_date()
        try:
            self._seams.up(self.server_dir)
        except docker.DockerCommandError as exc:
            raise SingleServerError(f"{self.entry.name} could not be started: {exc}") from exc
        logger.info(f"{self.entry.id} started from {self.server_dir}")

    def _compose_bytes(self) -> bytes | None:
        try:
            return (self.server_dir / composegen.BASE_FILE).read_bytes()
        except OSError:
            return None

    def _bring_up_to_date(self) -> None:
        """Render this install's files again, and pull when its compose file changed."""
        before = self._compose_bytes()
        try:
            changed = self._seams.refresh(self.entry, self.server_dir)
        except InstallerError as exc:
            raise SingleServerError(f"{self.entry.name} could not be started: {exc}") from exc
        for line in changed:
            self.say(line)
        if self._compose_bytes() == before:
            return
        self.say(f"{self.entry.name}'s server changed. Downloading it before the start.")
        run = self._seams.pull(self.server_dir, sink=self.say)
        if run.returncode != 0:
            said = " ".join(run.tail[-3:]).strip() or f"exit {run.returncode}"
            raise SingleServerError(
                f"{self.entry.name} could not download its server, so it was not started: "
                f"{said}. Check the internet connection and press Start again."
            )
        logger.info(f"{self.entry.id} pulled its images in {self.server_dir}")

    def stop(self) -> bool:
        """Stop the stack if it is ours and running; False when there was nothing to stop.

        Never stops containers of our names that another install's project owns: two
        folders of one game share the names, and the running one may be the other's.
        """
        if self.status() == STOPPED:
            return False
        if not self.is_ours():
            raise SingleServerError(
                f"The running {self.entry.name} server was not started from {self.server_dir}, "
                "so it was left running. Stop it from the tab of the folder it belongs to."
            )
        try:
            self._seams.stop(self.server_dir, timeout=STOP_TIMEOUT_SECONDS)
        except docker.DockerCommandError as exc:
            raise SingleServerError(f"{self.entry.name} could not be stopped: {exc}") from exc
        logger.info(f"{self.entry.id} stopped in {self.server_dir}")
        return True

    def follow_logs(self, cancel: threading.Event | None = None) -> Iterator[str]:
        """Every listener's log, live, for the tab's console (`docker compose logs -f`).

        `cancel` is not read (`follows_with_cancel` is False): the panel ends the child.
        """
        return self._seams.follow(self.server_dir, [s.service for s in self.stack.listeners])

    def session_account(self) -> str | None:
        """None: a stack server is not started for one account."""
        return None

    def advertised(self) -> str | None:
        """None: a stack publishes on this computer only, and keeps no address file."""
        return None

    def advertise(self, address: str) -> bool:
        """Refused: there is no address file to write (`entry.advertise` is None)."""
        raise SingleServerError(
            f"{self.entry.name} takes players on this computer only, so there is no address "
            "to change."
        )
