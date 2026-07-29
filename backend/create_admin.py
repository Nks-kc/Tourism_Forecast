"""One-off CLI to create, promote, or permanently protect an admin user.

Usage:
    python create_admin.py <username> <email> <password>
        Create a new admin account (regular admin, can be demoted by any admin).

    python create_admin.py --promote <existing_username>
        Promote an existing user to admin (regular admin, can be demoted).

    python create_admin.py --make-permanent <existing_username>
        Mark an existing user as the permanent admin. This promotes them to
        admin if needed, and afterwards NO admin -- including this account
        itself -- can demote them through the /admin/users/<username>/role
        API endpoint. Intended to be run once, deliberately, for the one
        account that should always retain admin access.
"""

import sys

from auth.models import (
    create_user,
    get_user_by_username,
    init_db,
    set_permanent_admin,
    set_user_role,
)


def main():
    init_db()
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    if args[0] == "--promote":
        if len(args) != 2:
            print("Usage: python create_admin.py --promote <username>")
            return
        username = args[1]
        if not get_user_by_username(username):
            print(f"No user named '{username}' found.")
            return
        result = set_user_role(username, "admin")
        print(
            f"'{username}' promoted to admin."
            if result["ok"]
            else f"Error: {result['error']}"
        )
        return

    if args[0] == "--make-permanent":
        if len(args) != 2:
            print("Usage: python create_admin.py --make-permanent <username>")
            return
        username = args[1]
        result = set_permanent_admin(username)
        if not result["ok"]:
            print(f"Error: {result['error']}")
            return
        print(f"'{username}' is now the permanent admin and cannot be demoted.")
        if "warning" in result:
            print(f"Warning: {result['warning']}")
        return

    if len(args) != 3:
        print(__doc__)
        return

    username, email, password = args
    result = create_user(username, email, password, role="admin")
    print(
        f"Admin user '{username}' created."
        if result["ok"]
        else f"Error: {result['error']}"
    )


if __name__ == "__main__":
    main()
