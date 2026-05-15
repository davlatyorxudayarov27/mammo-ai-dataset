from __future__ import annotations

import argparse
import getpass
import secrets
import sys
from pathlib import Path

from . import auth as auth_mod
from . import db as db_mod


def cmd_create(args):
    db_mod.init_db()
    if auth_mod.get_user_by_username(args.username):
        print(f"error: user '{args.username}' already exists", file=sys.stderr)
        sys.exit(1)
    password = args.password or getpass.getpass(f"Password for {args.username}: ")
    if not password:
        print("error: empty password", file=sys.stderr)
        sys.exit(1)
    user = auth_mod.create_user(
        username=args.username,
        password=password,
        role=args.role,
        display_name=args.display_name,
        email=args.email,
    )
    print(f"created user id={user['id']} username={user['username']} role={user['role']}")


def cmd_passwd(args):
    db_mod.init_db()
    if not auth_mod.get_user_by_username(args.username):
        print(f"error: user '{args.username}' not found", file=sys.stderr)
        sys.exit(1)
    password = args.password or getpass.getpass(f"New password for {args.username}: ")
    if not password:
        print("error: empty password", file=sys.stderr)
        sys.exit(1)
    auth_mod.update_password(args.username, password)
    print(f"password updated for {args.username}")


def cmd_rotate_secret(_args):
    secret_file = Path(__file__).resolve().parent / ".jwt_secret"
    new_secret = secrets.token_urlsafe(48)
    secret_file.write_text(new_secret, encoding="utf-8")
    print(f"yangi JWT secret yozildi: {secret_file}")
    print("Diqqat: barcha mavjud sessiyalar bekor qilindi. Server restart qiling.")


def cmd_list(_args):
    db_mod.init_db()
    users = auth_mod.list_users()
    if not users:
        print("(no users)")
        return
    fmt = "{:>3} {:<20} {:<10} {:<25} {:<30} {}"
    print(fmt.format("id", "username", "role", "display_name", "email", "last_login"))
    for u in users:
        print(fmt.format(
            u["id"], u["username"], u["role"],
            u.get("display_name") or "", u.get("email") or "",
            u.get("last_login_at") or "—",
        ))


def main():
    ap = argparse.ArgumentParser(description="Manage users for MAMOGRAF DICOM Viewer")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("create", help="create new user")
    p.add_argument("username")
    p.add_argument("--role", required=True, choices=auth_mod.ROLES)
    p.add_argument("--display-name", dest="display_name")
    p.add_argument("--email")
    p.add_argument("--password", help="(optional) provide on cmdline; otherwise prompted")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("passwd", help="change user password")
    p.add_argument("username")
    p.add_argument("--password", help="(optional)")
    p.set_defaults(func=cmd_passwd)

    p = sub.add_parser("list", help="list all users")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("rotate-secret", help="JWT secret'ni yangilash (barcha sessiyalar bekor)")
    p.set_defaults(func=cmd_rotate_secret)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
