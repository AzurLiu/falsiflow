#!/usr/bin/env sh
set -eu

usage() {
  cat <<'EOF'
Falsiflow local installer

Usage:
  scripts/install_local.sh [options]

Options:
  --prefix DIR       Install directory. Defaults to $FALSIFLOW_HOME or ~/.falsiflow
  --repo-url URL     Git repository URL. Defaults to $FALSIFLOW_REPO_URL or a placeholder public URL
  --branch NAME      Git branch to clone. Defaults to $FALSIFLOW_BRANCH or main
  --from-local DIR   Install from an existing local checkout instead of cloning
  --force            Replace an existing source checkout inside the install directory
  --check            After install, run `falsiflow start --check --json`
  --no-start         Install only; do not start the local browser app
  -h, --help         Show this help

Examples:
  scripts/install_local.sh --from-local . --check
  FALSIFLOW_REPO_URL=https://github.com/YOUR_ORG/falsiflow.git scripts/install_local.sh --check
EOF
}

PREFIX="${FALSIFLOW_HOME:-$HOME/.falsiflow}"
REPO_URL="${FALSIFLOW_REPO_URL:-https://github.com/falsiflow/falsiflow.git}"
BRANCH="${FALSIFLOW_BRANCH:-main}"
FROM_LOCAL=""
FORCE=0
CHECK=0
NO_START=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --prefix)
      PREFIX="${2:?--prefix requires a directory}"
      shift 2
      ;;
    --repo-url)
      REPO_URL="${2:?--repo-url requires a URL}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:?--branch requires a name}"
      shift 2
      ;;
    --from-local)
      FROM_LOCAL="${2:?--from-local requires a directory}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --check)
      CHECK=1
      shift
      ;;
    --no-start)
      NO_START=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 127
  fi
}

need_cmd python3
if [ -z "$FROM_LOCAL" ]; then
  need_cmd git
fi

PREFIX_ABS="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "$PREFIX")"
SOURCE_DIR="$PREFIX_ABS/source"
VENV_DIR="$PREFIX_ABS/venv"
APP_DIR="$PREFIX_ABS/app"

mkdir -p "$PREFIX_ABS"

if [ -n "$FROM_LOCAL" ]; then
  FROM_LOCAL_ABS="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "$FROM_LOCAL")"
  if [ ! -f "$FROM_LOCAL_ABS/pyproject.toml" ] || [ ! -d "$FROM_LOCAL_ABS/falsiflow" ]; then
    echo "--from-local must point to a Falsiflow checkout." >&2
    exit 2
  fi
  if [ "$FORCE" -eq 1 ] && [ -e "$SOURCE_DIR" ]; then
    rm -rf "$SOURCE_DIR"
  fi
  if [ -e "$SOURCE_DIR" ]; then
    echo "Using existing source checkout: $SOURCE_DIR"
  else
    mkdir -p "$SOURCE_DIR"
    (cd "$FROM_LOCAL_ABS" && tar -cf - \
      --exclude './.git' \
      --exclude './build' \
      --exclude './dist' \
      --exclude './*.egg-info' \
      --exclude './__pycache__' \
      .) | (cd "$SOURCE_DIR" && tar -xf -)
  fi
else
  if [ "$FORCE" -eq 1 ] && [ -e "$SOURCE_DIR" ]; then
    rm -rf "$SOURCE_DIR"
  fi
  if [ -d "$SOURCE_DIR/.git" ]; then
    echo "Updating existing source checkout: $SOURCE_DIR"
    git -C "$SOURCE_DIR" fetch --quiet origin "$BRANCH"
    git -C "$SOURCE_DIR" checkout --quiet "$BRANCH"
    git -C "$SOURCE_DIR" pull --ff-only --quiet origin "$BRANCH"
  elif [ -e "$SOURCE_DIR" ]; then
    echo "Source directory already exists and is not a git checkout: $SOURCE_DIR" >&2
    echo "Use --force to replace it." >&2
    exit 2
  else
    echo "Cloning Falsiflow from $REPO_URL"
    git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$SOURCE_DIR"
  fi
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install -e "$SOURCE_DIR" >/dev/null

cat <<EOF
Falsiflow installed.

Install directory: $PREFIX_ABS
Launcher: $VENV_DIR/bin/falsiflow

Next commands:
  $VENV_DIR/bin/falsiflow start
  $VENV_DIR/bin/falsiflow start --check --json
EOF

if [ "$NO_START" -eq 1 ]; then
  exit 0
fi

if [ "$CHECK" -eq 1 ]; then
  exec "$VENV_DIR/bin/falsiflow" start --out-dir "$APP_DIR" --check --json
fi

exec "$VENV_DIR/bin/falsiflow" start --out-dir "$APP_DIR"
