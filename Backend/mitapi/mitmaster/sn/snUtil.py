from datetime import datetime


def get_investor_type(customer_type):
    
    mapping = {
        "Individual": "1",
        "Juristic": "2",
        "Corporate": "2",
    }
    return mapping.get(customer_type, "")  # Default to "Unknown" if not found

def get_riskLevel(riskLevel):
    
    mapping = {
        1: "1",
        2: "3",
        3: "4",
    }
    return mapping.get(riskLevel, "")  # Default to "Unknown" if not found



def format_date(date_str):
    # """
    # Function to format a date string into 'YYYY-MM-DD'.
    # :param date_str: The input date string.
    # :return: The formatted date string or an empty string if invalid.
    # """
    # print(f"format_date: {date_str}")
    # try:
    #     # Parse the input date and format it as 'YYYY-MM-DD'

    #     # format_date: 2025-03-20T08:21:14.000000Z

    #     formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")

    #     return formatted_date
    # except (ValueError, TypeError):
    #     # Return an empty string if the input is invalid
    #     return ""
    formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%fZ"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return ""