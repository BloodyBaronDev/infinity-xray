#!/usr/bin/env python3
"""Сборка Infinity Xray из закреплённой базы и единого патча."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
PUBLIC_FILES = (
    "VERSION", "release.json", "infinity-xray.patch", "build.py", "test_build.py",
    "build.sh", "build.ps1", "Dockerfile", "README.md", "CHANGELOG.md",
    "LICENSE", "NOTICE.md", ".gitignore", ".gitattributes",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_release(root=ROOT):
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-rc\.[1-9]\d*)?", version):
        raise ValueError("VERSION: ожидается MAJOR.MINOR.PATCH или MAJOR.MINOR.PATCH-rc.N")
    release = json.loads((root / "release.json").read_text(encoding="utf-8"))
    patch = root / release["patch"]["file"]
    if patch.resolve().parent != root.resolve():
        raise ValueError("Патч должен лежать в корне проекта")
    if sha256(patch) != release["patch"]["sha256"]:
        raise ValueError("SHA256 единого патча не совпадает с release.json")
    release["version"] = version
    return release


def run(arguments, cwd=None, env=None, capture=False):
    result = subprocess.run(
        [str(arg) for arg in arguments], cwd=cwd, env=env, check=True,
        stdout=subprocess.PIPE if capture else None, encoding="utf-8",
    )
    return result.stdout.strip() if capture else None


def prepare(release, source_cache=None):
    work = ROOT / ".work"
    work.mkdir(exist_ok=True)
    source = Path(tempfile.mkdtemp(prefix="infinity-xray-", dir=work)) / "source"
    upstream = release["upstream"]
    if source_cache:
        run(["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", source_cache, source])
        run(["git", "-c", "core.autocrlf=false", "checkout", "--quiet", "--detach", upstream["commit"]], cwd=source)
    else:
        run(["git", "-c", "core.autocrlf=false", "clone", "--quiet", "--depth", "1", "--branch", upstream["tag"], upstream["repository"], source])
    actual = run(["git", "rev-parse", "HEAD"], cwd=source, capture=True)
    if actual != upstream["commit"]:
        raise ValueError(f"Неверная база Xray: {actual}")
    patch = ROOT / release["patch"]["file"]
    run(["git", "apply", "--check", patch], cwd=source)
    run(["git", "apply", patch], cwd=source)
    print(f"Исходники: {source}", flush=True)
    return source


def go_environment(release, target=None):
    env = os.environ.copy()
    env["GOTOOLCHAIN"] = release["go_toolchain"]
    # Проверки выполняются для текущей ОС, сборка — для явно выбранной цели.
    for key in ("GOOS", "GOARCH", "GOFLAGS"):
        env.pop(key, None)
    if target:
        env["GOOS"], env["GOARCH"] = target.split("/")
        env["CGO_ENABLED"] = "0"
    return env


def checks(source, release, full=False):
    env = go_environment(release)
    tags = ",".join(release["build_tags"])
    packages = ["./common/icstats", "./common/icusers", "./app/dispatcher", "./common/mux", "./app/proxyman/inbound",
                "./transport/internet/reality", "./transport/internet/tls", "./proxy/hysteria"]
    run(["go", "vet", "-tags", tags, *packages], cwd=source, env=env)
    run(["go", "test", "-tags", tags, "-count=1", "-timeout=3m", *packages], cwd=source, env=env)
    # В infra/conf уже есть предупреждения vet по protobuf; здесь проверяется парсер.
    run(["go", "test", "-vet=off", "-tags", tags, "./infra/conf", "-run", "^TestXHTTPH2Flow$", "-count=1", "-timeout=60s"], cwd=source, env=env)
    run(["go", "test", "-tags", tags, "./main", "-run", "^TestShutdown", "-count=1", "-timeout=90s"], cwd=source, env=env)
    if full:
        run(["go", "test", "-tags", tags, "./transport/internet/splithttp", "-run",
             "Test(H2|Flow)|TestFrameParserChunking|TestRewriteInitialWindow|FuzzFlow",
             "-count=1", "-timeout=8m"], cwd=source, env=env)


def build(source, release, target, image=False):
    out = ROOT / "out" / release["version"] / target.replace("/", "-")
    out.mkdir(parents=True, exist_ok=True)
    binary = out / ("xray.exe" if target.startswith("windows/") else "xray")
    flags = f"-s -w -X github.com/xtls/xray-core/core.build=Infinity-Xray/v{release['version']}"
    env = go_environment(release, target)
    tags = ",".join(release["build_tags"])
    run(["go", "build", "-tags", tags, "-trimpath", "-buildvcs=false", "-ldflags", flags, "-o", binary, "./main"], cwd=source, env=env)
    info = {"name": release["name"], "version": release["version"], "target": target,
            "upstream": release["upstream"], "patch": release["patch"],
            "go_toolchain": release["go_toolchain"], "build_tags": release["build_tags"],
            "binary_sha256": sha256(binary)}
    (out / "build-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "SHA256SUMS").write_text(f"{info['binary_sha256']}  {binary.name}\n", encoding="utf-8")
    if image:
        tag = f"infinity-xray:{release['version']}-node{release['node_tag']}"
        run(["docker", "build", "--platform", "linux/amd64", "--build-arg", f"NODE_TAG={release['node_tag']}",
             "--build-arg", f"INFINITY_VERSION={release['version']}", "-t", tag, "-f", ROOT / "Dockerfile", out])
        print(f"Образ: {tag}")
    print(f"Бинарник: {binary}\nSHA256: {info['binary_sha256']}")
    return binary


def export(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("Каталог экспорта уже существует; укажите новый путь")
    # Только явный список: история монорепозитория, lab и локальные данные не копируются.
    for name in PUBLIC_FILES:
        if not (ROOT / name).is_file():
            raise ValueError(f"Нет файла для экспорта: {name}")
    destination.mkdir(parents=True)
    for name in PUBLIC_FILES:
        shutil.copyfile(ROOT / name, destination / name)
    print(f"Комплект для GitHub: {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "build", "image", "export"), nargs="?", default="build")
    parser.add_argument("--target", choices=("linux/amd64", "windows/amd64"), default="linux/amd64")
    parser.add_argument("--source-cache", type=Path, help="Локальный git-репозиторий официальной базы Xray")
    parser.add_argument("--full-checks", action="store_true", help="Также выполнить профильные тесты governor")
    parser.add_argument("--destination", type=Path, help="Новый каталог для отдельного репозитория")
    args = parser.parse_args()
    if args.command == "image" and args.target != "linux/amd64":
        parser.error("Образ Remnawave поддержан только для linux/amd64")
    if args.command == "export" and not args.destination:
        parser.error("Для export требуется --destination")
    release = load_release()
    if args.command == "export":
        export(args.destination)
        return
    source = prepare(release, args.source_cache)
    if args.command == "prepare":
        return
    checks(source, release, full=args.full_checks)
    build(source, release, args.target, image=args.command == "image")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Ошибка сборки: {error}") from error
