"""
    Copyright 2023 Habibur Rahaman Fahim

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""


import requests
from bs4 import BeautifulSoup
import os
import firebase_admin
from firebase_admin import credentials, storage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the Firebase admin SDK JSON file ('.json' file named as 'firebase_config.json' here, which is inside 'firebase' folder)
FIREBASE_ADMIN_SDK_FILE = os.path.join(BASE_DIR, "firebase", "firebase_config.json")

# Initialize the Firebase app with the admin SDK credentials
cred = credentials.Certificate(FIREBASE_ADMIN_SDK_FILE)
firebase_admin.initialize_app(
    # Add storageBucket link here
    cred, {"storageBucket": "authentication-2244f.appspot.com"}
)

# Get a reference to the Firebase Storage bucket
bucket = storage.bucket()

urls = {
    # First tested site: https://rents.com.bd/all-properties/
    "https://rents.com.bd/all-properties/": (
        "h2", 
        {"class": "item-title"}),
    # Second tested site: https://www.bproperty.com/en/dhaka/apartments-for-rent/
    "https://www.bproperty.com/en/dhaka/apartments-for-rent/": (
        "h2",
        {"class": "_7f17f34f"},
    ),
}

for url, search_pattern in urls.items():
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
   
    for item_listing_wrap in soup.find_all(
        "div", 
        {"class": "item-listing-wrap hz-item-gallery-js card"}
    ) + soup.find_all(
        "li", 
        {"class": "ef447dde"}
        ):
        ad_name_element = item_listing_wrap.find(search_pattern[0], search_pattern[1])
        if ad_name_element is not None:
            ad_name = ad_name_element.get_text().strip()
            ad_name = (
                ad_name.replace(".", " ")
                .replace("$", " ")
                .replace("#", " ")
                .replace("[", " ")
                .replace("]", " ")
                .replace("/", " ")
                .replace("-", " ")
            )
        else:
            ad_name = ""

        for img in item_listing_wrap.find_all("img"):
            src = img.get("src")
            if src:
                filename, extension = os.path.splitext(os.path.basename(src))
                if extension.lower() in (".jpg", ".jpeg"):
                    # The image with the same name as the ad name
                    filename = f"{ad_name}"
                    response = requests.get(src)
                    if response.status_code == 200:
                        # Image to Firebase Storage
                        blob = bucket.blob(filename)
                        blob.upload_from_string(
                            response.content, content_type="image/jpeg"
                        )
                        print(f"Image {filename} uploaded to Firebase Storage.")
                    else:
                        print(
                            f"Failed to load image {filename}. Status code: {response.status_code}"
                        )
