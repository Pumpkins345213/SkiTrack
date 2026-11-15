
import bcrypt
import getpass
import subprocess
import yaml

password = getpass.getpass("Новый пароль Dozzle: ")
confirm = getpass.getpass("Повтори пароль: ")

if not password or password != confirm:
    print("Ошибка: пароли не совпадают.")
else:
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", "skitrack_dozzle_data:/data:ro",
            "alpine:3.20", "cat", "/data/users.yml"
        ],
        capture_output=True,
        text=True,
        check=True
    )

    users_data = yaml.safe_load(result.stdout)

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    users_data["users"]["admin"]["password"] = password_hash

    updated_yaml = yaml.safe_dump(
        users_data,
        allow_unicode=True,
        sort_keys=False
    )

    subprocess.run(
        [
            "docker", "run", "--rm", "-i",
            "-v", "skitrack_dozzle_data:/data",
            "alpine:3.20",
            "sh", "-c", "cat > /data/users.yml"
        ],
        input=updated_yaml,
        text=True,
        check=True
    )

    print("Пароль обновлён!")
