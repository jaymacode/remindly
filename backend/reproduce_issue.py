"""Reproduce the profile-update request against a running backend.

Credentials are read from the environment, never hard-coded:
    REMINDLY_TEST_EMAIL     email of an existing test account
    REMINDLY_TEST_PASSWORD  password of that account
Optional:
    REMINDLY_BASE_URL       defaults to http://127.0.0.1:8000
"""
import os
import sys

import httpx

BASE_URL = os.getenv("REMINDLY_BASE_URL", "http://127.0.0.1:8000")


def get_credentials():
    email = os.getenv("REMINDLY_TEST_EMAIL")
    password = os.getenv("REMINDLY_TEST_PASSWORD")
    if not email or not password:
        sys.exit(
            "Missing test credentials. Set REMINDLY_TEST_EMAIL and "
            "REMINDLY_TEST_PASSWORD in the environment, then run again."
        )
    return email, password


def test_update():
    email, password = get_credentials()

    # 1. Login
    print("Logging in...")
    try:
        res = httpx.post(f"{BASE_URL}/login", json={"email": email, "password": password})
        if res.status_code != 200:
            print(f"Login failed: {res.status_code} {res.text}")
            return

        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        # 2. Update profile with an extra field (email) that is NOT in ProfileUpdate
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "date_of_birth": "2023-01-01",
            "email": email,
            "phone_number": "000000000",
            "country": "Indonesia",
            "city": "Jakarta",
            "profile_picture": "",
        }

        print("\nSending Update (with email field)...")
        res = httpx.put(f"{BASE_URL}/profile", json=payload, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

        # 3. Update profile WITHOUT the extra field
        payload_clean = payload.copy()
        del payload_clean["email"]

        print("\nSending Update (without email field)...")
        res = httpx.put(f"{BASE_URL}/profile", json=payload_clean, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_update()
