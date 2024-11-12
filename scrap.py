import json
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# File paths
input_file = "service_providers.json"
output_file = "service_providers_details.csv"

# Base URL for fetching provider details
base_url = "https://www.workforceaustralia.gov.au/api/v1/serviceproviders/providers/{site_code}/{provider_type}/undefined"

def fetch_provider_details(site_code, provider_type, driver):
    """Fetch the provider details from the website using Selenium."""
    url = base_url.format(site_code=site_code, provider_type=provider_type)
    try:
        driver.get(url)
        time.sleep(2)  # Allow some time for the page to load

        # Extract the page content (assuming the data is available in the page's source)
        content = driver.find_element(By.TAG_NAME, "pre").text
        return json.loads(content)
    except Exception as e:
        print(f"Error fetching details for {site_code} - {provider_type}: {e}")
        return None

def safe_get(data, key, default="N/A"):
    """Safely get a value from a dictionary, or return default if the key is missing or the data is None."""
    if isinstance(data, dict):
        return data.get(key, default)
    return default

def extract_info(provider, details):
    """Extract required information from the fetched data."""
    # Extracting required fields with fallbacks using safe_get to avoid 'NoneType' errors
    name = safe_get(details.get("siteData", {}), "name")
    
    # Check if socialLinksData exists and extract website
    social_links = safe_get(details, "socialLinksData", {})
    website = safe_get(social_links, "website")
    
    # Constructing site information
    service = safe_get(details.get("siteData", {}), "service")
    specialisation = safe_get(details.get("siteData", {}), "specialisation", "")
    site_information = f"We service {service} and we specialise in {specialisation if specialisation else 'all job seekers'}."
    
    phone_number = safe_get(details.get("contactData", {}), "phone")
    email = safe_get(details.get("contactData", {}), "email")
    
    # Extract address details
    address_line1 = safe_get(details.get("siteData", {}), "addressLine1")
    address_line2 = safe_get(details.get("siteData", {}), "addressLine2")
    address = f"{address_line1} {address_line2}".strip()

    # Extracting additional fields from the provider data
    city = safe_get(provider, "suburb")
    state = safe_get(provider, "state")
    postal_code = safe_get(provider, "postcode")
    country = "Australia"  # Assuming all entries are in Australia
    latitude = safe_get(provider, "latitude")
    longitude = safe_get(provider, "longitude")
    
    # Adding the Institution Location as an object
    institution_location = {
        "address": address,
        "city": city,
        "state": state,
        "country": country,
        "lat": latitude,
        "long": longitude,
        "postal_code": postal_code
    }

    return {
        "name": name,
        "website": website,
        "site_information": site_information,
        "phone_number": phone_number,
        "email": email,
        "address": address,
        "city": city,
        "state": state,
        "country": country,
        "postal_code": postal_code,
        "latitude": latitude,
        "longitude": longitude,
        "institution_location": json.dumps(institution_location)  # Store as JSON string for CSV
    }

def main():
    # Set up Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # Run browser in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Load the list of providers from the input JSON file
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Prepare to write to the CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "name", "website", "site_information", "phone_number", 
                "email", "address", "city", "state", "country", 
                "postal_code", "latitude", "longitude", "institution_location"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Counter for progress updates
            provider_count = 0

            # Iterate over the providers and fetch details
            for item in data.get("results", []):  # Fetch only the first 10 items
                result = item.get("result", {})
                site_code = result.get("siteCode")
                provider_type = result.get("providerType")
                
                if not site_code or not provider_type:
                    continue
                
                # Fetch detailed info using Selenium
                details = fetch_provider_details(site_code, provider_type, driver)
                
                if details:
                    # Extract and format the information
                    info = extract_info(result, details)
                    # Write the row to CSV
                    writer.writerow(info)
                    
                    # Increment provider count and print updates
                    provider_count += 1
                    print(f"Provider {provider_count}: {info['name']} fetched.")
                    
                    if provider_count % 50 == 0:
                        print(f"Fetched {provider_count} providers so far.")

        print(f"Details saved to {output_file}")

    finally:
        # Quit the WebDriver
        driver.quit()

# Run the script
if __name__ == "__main__":
    main()
