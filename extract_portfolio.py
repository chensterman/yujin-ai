import json
import csv
import os

# Load the JSON data


def load_json_data(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

# Clean company name by removing quotes and extra whitespace


def clean_company_name(name):
    # Remove quotes (both single and double)
    name = name.replace('"', '').replace("'", '')
    # Remove extra whitespace
    name = name.strip()
    return name

# Extract unique portfolio companies


def extract_portfolio_companies(data):
    # Set to track unique companies
    unique_companies = set()

    for row in data:
        if "Portfolio companies" in row and row["Portfolio companies"]:
            # Split the portfolio companies string by comma and possibly other separators
            port_cos = row["Portfolio companies"].split(", ")
            # Further split by comma without space
            expanded_companies = []
            for company in port_cos:
                expanded_companies.extend(company.split(","))

            # Add each company to the set
            for company in expanded_companies:
                company = clean_company_name(company)
                if company:  # Only add non-empty strings
                    unique_companies.add(company)

    return sorted(list(unique_companies))  # Sort for readability

# Write data to CSV


def write_to_csv(data, output_file):
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write the data to a CSV file
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)

        # Write header
        writer.writerow(['company_name'])

        # Write each company on a separate row
        for company in data:
            writer.writerow([company])


def main():
    # Path to the input and output files
    input_file = '/Users/emmythamakaison/Documents/yujin-ai/Folk_All VCs_2025_04_12.csv'
    output_file = 'data/csv/portfolio_companies.csv'

    # Load the data from CSV
    with open(input_file, 'r') as file:
        csv_reader = csv.DictReader(file)
        data = list(csv_reader)

    # Extract the portfolio companies
    companies = extract_portfolio_companies(data)

    # Write to CSV
    write_to_csv(companies, output_file)

    print(
        f"Successfully extracted {len(companies)} unique portfolio companies to {output_file}")


if __name__ == "__main__":
    main()
