#!/usr/bin/env python3
import argparse
import json
import re
import sys
from typing import Sequence

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    import tomllib
else:  # pragma: <3.11 cover
    import tomli as tomllib

import ruamel.yaml

yaml = ruamel.yaml.YAML(typ="safe")


def _parse_num_to_int(s: str) -> int | str:
    """Convert string numbers to int, leaving strings as is."""
    try:
        return int(s)
    except ValueError:
        return s


def _is_file_to_exclude(filename, exclude_files) -> bool:

    if exclude_files is None:
        return False

    for pattern in exclude_files:
        if re.match(pattern, filename):
            return True

    return False


def _extract_frontmatter_as_toml(content):

    extract = ""
    for i in range(1, len(content)):
        if content[i].rstrip() == "+++":
            break
        extract += content[i]

    return tomllib.loads(extract)


def _extract_frontmatter_as_yaml(content):

    extract = ""
    for i in range(1, len(content)):
        if content[i].rstrip() == "---":
            break
        extract += content[i]

    return yaml.load(extract)


def _extract_frontmatter_as_json(content):
    extract = ""
    for i in range(0, len(content)):
        extract += content[i]
        if content[i].rstrip() == "}":
            break

    return json.loads(extract)


def check_front_matter_content(filename, frontmatter, args) -> int:
    ret = 0

    if (
        not args.ignore_title
        and "title" not in frontmatter
        and "Title" not in frontmatter
    ):
        ret = 1
        print(f"In file {filename}, missing `title` in front-matter")

    if (
        not args.ignore_summary_and_description
        and "summary" not in frontmatter
        and "Summary" not in frontmatter
        and "description" not in frontmatter
        and "Description" not in frontmatter
    ):
        ret = 1
        print(f"In file {filename}, missing `summary` or `description` in front-matter")

    if not args.ignore_date and "date" not in frontmatter and "Date" not in frontmatter:
        ret = 1
        print(f"In file {filename}, missing `date` in front-matter")

    if not args.ignore_tags:
        if "tags" not in frontmatter and "Tags" not in frontmatter:
            ret = 1
            print(f"In file {filename}, missing `tags` in front-matter")

        elif (
            "tags" in frontmatter and len(frontmatter["tags"]) < args.minimum_tags
        ) or ("Tags" in frontmatter and len(frontmatter["Tags"]) < args.minimum_tags):
            ret = 1
            print(
                f"In file {filename}, minimum {args.minimum_tags} `tags` required in front-matter"
            )

    return ret


def check_front_matter(filename, args) -> int:
    ret = 0
    with open(filename, "r", encoding="utf-8") as file:
        content = file.readlines()

        if (
            content[0].rstrip() != "+++"
            and content[0].rstrip() != "---"
            and content[0].rstrip() != "{"
        ):
            ret = 1
            print(f"In file {filename}, missing front-matter")
        elif content[0].rstrip() == "+++":
            frontmatter = _extract_frontmatter_as_toml(content)
            ret = check_front_matter_content(filename, frontmatter, args)
        elif content[0].rstrip() == "---":
            frontmatter = _extract_frontmatter_as_yaml(content)
            ret = check_front_matter_content(filename, frontmatter, args)
        elif content[0].rstrip() == "{":
            frontmatter = _extract_frontmatter_as_json(content)
            ret = check_front_matter_content(filename, frontmatter, args)

    return ret


def main(argv: Sequence[str] | None = None) -> int:
    ret = 0
    parser = argparse.ArgumentParser("Check FrontMatter")

    parser.add_argument(
        "--base_path",
        dest="base_path",
        default="",
        help="Set base path for files to check",
    )

    parser.add_argument(
        "--exclude_file",
        action="append",
        help="Files to exclude",
    )

    parser.add_argument(
        "--ignore_title",
        action="store_true",
        dest="ignore_title",
        help="Do not check title",
    )

    parser.add_argument(
        "--ignore_summary_and_description",
        action="store_true",
        dest="ignore_summary_and_description",
        help="Do not check summary and description",
    )

    parser.add_argument(
        "--ignore_date",
        action="store_true",
        dest="ignore_date",
        help="Do not check date",
    )

    parser.add_argument(
        "--ignore_tags",
        action="store_true",
        dest="ignore_tags",
        help="Do not check tags",
    )

    parser.add_argument(
        "--minimum_tags",
        type=_parse_num_to_int,
        default="2",
        help="Minimum number of tags (default: 2)",
    )

    parser.add_argument(
        "filenames",
        nargs="*",
        help="Filenames pre-commit believes are changed.",
    )
    args = parser.parse_args(argv)

    for filename in args.filenames:
        if filename.startswith(args.base_path) and not _is_file_to_exclude(
            filename, args.exclude_file
        ):

            ret = check_front_matter(filename, args)

    return ret


if __name__ == "__main__":
    raise SystemExit(main())
