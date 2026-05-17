#!/usr/bin/env bash

set -euo pipefail

MANIFEST_NAME="manifest.json"
DRY_RUN=0
ALL_MODULES=0
MODULES=()
CURRENT_TMP_PATH=""

cleanup_tmp() {
    if [[ -n ${CURRENT_TMP_PATH:-} ]]; then
        rm -f -- "$CURRENT_TMP_PATH"
    fi
}

trap cleanup_tmp EXIT INT TERM

usage() {
    cat <<'USAGE'
Usage:
  tools/create-module-manifest.sh all
  tools/create-module-manifest.sh --all
  tools/create-module-manifest.sh allsky_adsb [allsky_other ...]

Options:
  --manifest-name NAME   Manifest filename to create in each module directory.
                         Default: manifest.json
  --dry-run              Print the manifest instead of writing it.
  -h, --help             Show this help.

Run this from anywhere inside the allsky-modules git repository.
USAGE
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

json_escape() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//$'\b'/\\b}
    value=${value//$'\f'/\\f}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    value=${value//$'\t'/\\t}
    printf '%s' "$value"
}

repo_root() {
    git rev-parse --show-toplevel 2>/dev/null || pwd
}

validate_manifest_name() {
    local name=$1
    [[ $name != */* ]] || die "--manifest-name must be a filename, not a path"
    [[ $name != "." && $name != ".." && -n $name ]] || die "Invalid manifest filename"
}

parse_args() {
    while (($#)); do
        case "$1" in
            --all|all)
                ALL_MODULES=1
                shift
                ;;
            --manifest-name)
                (($# >= 2)) || die "--manifest-name requires a value"
                MANIFEST_NAME=$2
                shift 2
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            --)
                shift
                while (($#)); do
                    MODULES+=("$1")
                    shift
                done
                ;;
            -*)
                die "Unknown option: $1"
                ;;
            *)
                MODULES+=("$1")
                shift
                ;;
        esac
    done

    validate_manifest_name "$MANIFEST_NAME"

    if ((ALL_MODULES == 1 && ${#MODULES[@]} > 0)); then
        die "Specify either all modules or explicit module names, not both"
    fi

    if ((ALL_MODULES == 0 && ${#MODULES[@]} == 0)); then
        usage >&2
        exit 1
    fi
}

discover_modules() {
    local module

    while IFS= read -r -d '' module; do
        module=${module#./}
        MODULES+=("$module")
    done < <(find . -maxdepth 1 -mindepth 1 -type d -name 'allsky_*' -print0 | LC_ALL=C sort -z)

    ((${#MODULES[@]} > 0)) || die "No allsky_* module directories found"
}

validate_module() {
    local module=$1

    [[ $module =~ ^allsky_[A-Za-z0-9_]+$ ]] || die "Invalid module name: $module"
    [[ -d $module ]] || die "Module directory not found: $module"
}

file_mode() {
    stat -c '%a' -- "$1"
}

file_size() {
    stat -c '%s' -- "$1"
}

file_sha256() {
    sha256sum -- "$1" | awk '{print $1}'
}

write_manifest() {
    local module=$1
    local generated_utc
    local manifest_path
    local tmp_path
    local file
    local rel_path
    local escaped_path
    local sha
    local size
    local mode
    local first=1
    local file_count=0
    local files=()

    validate_module "$module"

    while IFS= read -r -d '' file; do
        files+=("$file")
    done < <(
        find "$module" -type f \
            ! -path "$module/$MANIFEST_NAME" \
            ! -path "$module/.${MANIFEST_NAME}.tmp.*" \
            -print0 | LC_ALL=C sort -z
    )

    ((${#files[@]} > 0)) || die "No files found in module: $module"

    generated_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    manifest_path="$module/$MANIFEST_NAME"
    tmp_path="$module/.${MANIFEST_NAME}.tmp.$$"
    CURRENT_TMP_PATH=$tmp_path

    {
        printf '{\n'
        printf '  "schema_version": 1,\n'
        printf '  "module": "%s",\n' "$(json_escape "$module")"
        printf '  "generated_utc": "%s",\n' "$(json_escape "$generated_utc")"
        printf '  "hash_algorithm": "sha256",\n'
        printf '  "files": {\n'

        for file in "${files[@]}"; do
            rel_path=${file#"$module/"}
            escaped_path=$(json_escape "$rel_path")
            sha=$(file_sha256 "$file")
            size=$(file_size "$file")
            mode=$(file_mode "$file")

            if ((first == 0)); then
                printf ',\n'
            fi
            first=0
            file_count=$((file_count + 1))

            printf '    "%s": {\n' "$escaped_path"
            printf '      "sha256": "%s",\n' "$sha"
            printf '      "size": %s,\n' "$size"
            printf '      "mode": "%s"\n' "$(json_escape "$mode")"
            printf '    }'
        done

        printf '\n'
        printf '  },\n'
        printf '  "file_count": %s\n' "$file_count"
        printf '}\n'
    } > "$tmp_path"

    if ((DRY_RUN == 1)); then
        if ((${#MODULES[@]} > 1)); then
            printf '%s\n' "--- $manifest_path ---"
        fi
        cat "$tmp_path"
        rm -f -- "$tmp_path"
        CURRENT_TMP_PATH=""
        return
    fi

    mv -f -- "$tmp_path" "$manifest_path"
    CURRENT_TMP_PATH=""
    printf 'Wrote %s (%s files)\n' "$manifest_path" "$file_count"
}

main() {
    parse_args "$@"

    cd "$(repo_root)"
    [[ -d .git ]] || die "This does not look like the root of a git checkout"

    if ((ALL_MODULES == 1)); then
        discover_modules
    fi

    for module in "${MODULES[@]}"; do
        write_manifest "$module"
    done
}

main "$@"
