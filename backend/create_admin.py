"""One-off CLI to create or promote an admin user.

Usage:
    python create_admin.py <username> <email> <password>
    python create_admin.py --promote <existing_username>
"""

import sys
from auth.models import init_db, create_user, get_user_by_username, set_user_role


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
        set_user_role(username, "admin")
        print(f"'{username}' promoted to admin.")
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
