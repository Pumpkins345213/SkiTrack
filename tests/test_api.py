
import json
from urllib.request import urlopen
import ssl


BASE_URL = "https://localhost:8443"

# Самоподписан сертификат за локално тестване
SSL_CONTEXT = ssl._create_unverified_context()


def test_get_resorts():
    with urlopen(
        f"{BASE_URL}/api/resorts",
        context=SSL_CONTEXT
    ) as response:
        assert response.status == 200

        resorts = json.load(response)

        assert isinstance(resorts, list)
        assert len(resorts) == 5

        names = [resort["name"] for resort in resorts]

        assert "Банско" in names
        assert "Боровец" in names
        assert "Пампорово" in names
        assert "Витоша" in names
        assert "Добринище" in names

def test_get_single_resort():
    with urlopen(
        f"{BASE_URL}/api/resorts/1",
        context=SSL_CONTEXT
    ) as response:
        assert response.status == 200

        resort = json.load(response)

        assert isinstance(resort, dict)
        assert resort["id"] == 1
        assert resort["name"] == "Банско"
        assert "mountain" in resort
        assert "description" in resort


from urllib.error import HTTPError


def test_get_nonexistent_resort():
    try:
        urlopen(
            f"{BASE_URL}/api/resorts/99999",
            context=SSL_CONTEXT
        )
        assert False, "Очаква се грешка 404"
    except HTTPError as error:
        assert error.code == 404

        data = json.load(error)
        assert data["error"] == "Курортът не е намерен."


from urllib.request import Request
from urllib.error import HTTPError


def test_create_resort_validation():
    data = json.dumps({
        "name": "",
        "mountain": ""
    }).encode("utf-8")

    request = Request(
        f"{BASE_URL}/api/resorts",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        urlopen(request, context=SSL_CONTEXT)
        assert False, "Очаква се грешка 400"
    except HTTPError as error:
        assert error.code == 400

        result = json.load(error)
        assert "error" in result


def test_update_resort_validation():
    data = json.dumps({
        "name": "",
        "mountain": ""
    }).encode("utf-8")

    request = Request(
        f"{BASE_URL}/api/resorts/1",
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )

    try:
        urlopen(request, context=SSL_CONTEXT)
        assert False, "Очаква се грешка 400"
    except HTTPError as error:
        assert error.code == 400

        result = json.load(error)
        assert "error" in result


def test_delete_nonexistent_resort():
    request = Request(
        f"{BASE_URL}/api/resorts/99999",
        method="DELETE"
    )

    try:
        urlopen(request, context=SSL_CONTEXT)
        assert False, "Очаква се грешка 404"
    except HTTPError as error:
        assert error.code == 404

        result = json.load(error)
        assert result["error"] == "Курортът не е намерен."
