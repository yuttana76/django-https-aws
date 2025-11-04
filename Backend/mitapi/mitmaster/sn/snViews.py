import os
import csv
from io import StringIO
from .countryUtil import getCountryCode
from .snUtil import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.http import HttpResponse,FileResponse

class structureNoteViewSet(viewsets.ModelViewSet):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    @action(detail=False, methods=['post'], url_path='investorfile')
    def investorAPI(self, request):
        # Parse JSON input
        # print(request.data)
        data = request.data

        # Ensure the input is a list
        if not isinstance(data, list):
            return Response({"error": "Input must be a list of objects"}, status=400)

        # Process each item in the list
        csv_data = []
        for item in data:
            
            customerDetail = item.get("customerDetail")
            address = customerDetail["address"]
            # print(address["contactAddress"]["Country"])

            # For Juristic
            registerCountry =customerDetail.get("registeredCountry")

            current_contact_country = getCountryCode(address["contactAddress"]["Country"]) if item.get("customerType", "") == "Individual" else ""

            if item.get("customerType", "") == "Individual" and item.get("idType", "") == "IDCard":
                idType = "1"
            elif item.get("customerType", "") == "Individual" and item.get("idType", "") == "Passport":
                idType = "2"
            elif item.get("customerType", "") == "Corporate" :
                idType = "4"
            else:
                idType = "5"

            _postCode = address["contactAddress"]["PostalCode"] if item.get("customerType", "") == "Individual" else ""
            _address= address["contactAddress"]["AdressNo"] if item.get("customerType", "") == "Individual" else ""        
            if idType in ["2","3","4","5","9"]:
                _address=""
                _postCode= ""

            account_data = {
                    "investor_type": get_investor_type(item.get("customerType", "")),
                    "juristic_type": "1" if item.get("customerType", "") != "Individual" else "",
                    "juristic_type_other_desc": "",
                    "investor_class": "1",
                    "vulnerable_investor_flag": customerDetail.get("isSensitive",""),
                    # "id_type": "1" if item.get("customerType", "") == "Individual"  else "4", 
                    "id_type": idType,
                    "id_type_description": "",
                    "id_no": item.get("cardId", ""),
                    "tax_id": item.get("cardId", "") if item.get("customerType") != "Individual" else "",
                    "nationality_register_country":getCountryCode(item.get("nationality")) if item.get("customerType", "") == "Individual" else getCountryCode(registerCountry),
                    "current_contact_country": current_contact_country,
                    "current_contact_postal_code": _postCode,
                    "birth_date": format_date(item.get("birthDate", "")), # YYYY-MM-DD
                    "occupation_id": "170",
                    "occupation_desc": customerDetail.get("occupation","พนักงานบริษัท"),
                    "income_id": "LEVEL5" if item.get("customerType") == "Individual" else "",

                    "investment_objective": "เพื่อการลงทุน" if item.get("customerType", "") == "Individual" else "บริหารเงินรอลงทุน",
                    "investment_objective_other": "",
                    "income_type_code": "1,5" if item.get("customerType", "") == "Individual" else "101", 
                    "income_source_desc": "",
                    "risk_profile_level": get_riskLevel(item.get("riskLevel", "")),
                    "suitability_test_date": item.get("suitDate", ""),
                    "derivatives_and_structured_notes_risk_flag": "",
                    "fx_risk_flag": "",
                    "contactable_investor": "Y",
                    "workplace_name": item.get("workPlace", ""),
                    "work_address": "",
                    "work_moo": "",
                    "work_place": "",
                    "work_room_no": "",
                    "work_floor": "",
                    "work_soi": "",
                    "work_road": "",
                    "work_tambon": "",
                    "work_amphur": "",
                    "work_postal_code": "",
                    "work_country": "",
                    "current_contact_address": _address,
                    "current_contact_moo": address.get("contactAddress",{}).get("MooNo",""),
                    "current_contact_place": address.get("contactAddress",{}).get("Building",""),
                    "current_contact_room_no": address.get("contactAddress",{}).get("RoomNo",""),
                    "current_contact_floor": address.get("contactAddress",{}).get("Floor",""),
                    "current_contact_soi": address.get("contactAddress",{}).get("Soi",""),
                    "current_contact_road": address.get("contactAddress",{}).get("Road",""),
                    "current_contact_tambon": address.get("contactAddress",{}).get("SubDistrict",""),
                    "current_contact_amphur": address.get("contactAddress",{}).get("District",""),
                    "email": item.get("email", ""),
                    "mobile_phone_no": item.get("mobilePhone", ""),
                    "contact_telephone":customerDetail.get("homeTelephone",""),

            }
            csv_data.append(account_data)

        # Generate CSV
        csv_file = self.generate_csv(csv_data)

        # V.1 Return CSV as response
        # response = HttpResponse(csv_file, content_type='text/csv')
        # response['Content-Disposition'] = 'attachment; filename="BL10-SN_Investor-Profile.csv"'
        # return response

        # V2. Write the CSV content to a file
        file_name = "BL10-SN_Investor-Profile.csv"  # Name of the file to be created
        file_path = f'./files/{file_name}'  # Path to save the file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_file)
                    
        # Check if file exists
        if os.path.exists(file_path):
            # Serve the file as a response
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            
            # Delete the file after it has been served
            # os.remove(file_path)
            
            return response
        else:
            return Response({"error": "File not found"}, status=404)
    

    @action(detail=False, methods=['post'], url_path='accountfile')
    def accountAPI(self, request):
        # Parse JSON input
        data = request.data

        # Ensure the input is a list
        if not isinstance(data, list):
            return Response({"error": "Input must be a list of objects"}, status=400)

        # Process each item in the list
        csv_data = []
        for item in data:
            
            account_data = {
                    "id_no": item.get("cardId", ""),  # Default to an empty string if key is missing
                    "nationality_register_country": getCountryCode(item.get("nationality","")),
                    "account_no": item.get("account_code", ""),
                    "account_type": "07",
                    "account_opening_date": format_date(item.get("created_at", "")),
                    "flag_attorney": "N",
                    "attorney_id_no": "",
                    "register_sale_no": item.get("marketingCode", ""),
                    "sbl_flag": "",
                    "last_traded_date": "",
                
            }
            csv_data.append(account_data)

        # Generate CSV
        csv_file = self.generate_csv(csv_data)

        # Return CSV as response
        # response = HttpResponse(csv_file, content_type='text/csv')
        # response['Content-Disposition'] = 'attachment; filename="BL10-SN_Account.csv"'
        # return response

        # V2. Write the CSV content to a file
        file_name = "BL10-SN_Account.csv"  # Name of the file to be created
        file_path = f'./files/{file_name}'  # Path to save the file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_file)
                    
        # Check if file exists
        if os.path.exists(file_path):
            # Serve the file as a response
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            
            # Delete the file after it has been served
            # os.remove(file_path)
            
            return response
        else:
            return Response({"error": "File not found"}, status=404)

    @action(detail=False, methods=['post'], url_path='outstandingfile')
    def outstandingAPI(self, request):
        # Parse JSON input
        data = request.data
        
        # Ensure the input is a list
        if not isinstance(data, list):
            return Response({"error": "Input must be a list of objects"}, status=400)



        # Process each item in the list
        csv_data = []
        for item in data:

            security_type = item.get("security_type", "")
            market_code = "06"
            

            # volume
            volume = float(item.get("volume", 0))
            formatted_volume = f"{volume:.2f}"  # Format as 0.00

            # Volume Condition
            asset_code="44"
            if security_type == "01":
                formatted_volume = ''
                market_code = "07"
                asset_code="01"

            # value
            value = float(item.get("value", 0))
            formatted_value = f"{value:.2f}"  # Format as 0.00

            issue_code=""
            isin_code=""
            if market_code != "06":
                issue_code = item.get("issue_code", "")
            else:
                isin_code = item.get("isin", "")

            account_data = {
                "account_no": item.get("account_no", ""),  # Default to an empty string if key is missing
                "account_type": "07",
                "security_type": security_type,
                "pledged_shares_flag": "",
                "asset_code": asset_code,
                # "asset_code": item.get("asset_code", "44"),
                "market_code": market_code,
                "issue_code": issue_code,
                "isin_code": isin_code,
                "volume": formatted_volume,  # Default to 0 for numeric fields
                # "notional_amount": item.get("notional_amount", 0),
                "notional_amount": "",
                "value": formatted_value
            }
            csv_data.append(account_data)

        # Generate CSV
        csv_file = self.generate_csv(csv_data)

        # Return CSV as response
        # response = HttpResponse(csv_file, content_type='text/csv')
        # response['Content-Disposition'] = 'attachment; filename="BL10-SN_Investor-Outstanding.csv"'
        # return response

        # V2. Write the CSV content to a file
        file_name = "BL10-SN_Investor-Outstanding.csv"  # Name of the file to be created
        file_path = f'./files/{file_name}'  # Path to save the file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_file)
                    
        # Check if file exists
        if os.path.exists(file_path):
            # Serve the file as a response
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            
            # Delete the file after it has been served
            # os.remove(file_path)
            
            return response
        else:
            return Response({"error": "File not found"}, status=404)    

    @action(detail=False, methods=['post'], url_path='downlaodFile')
    def downlaodFileAPI(self, request):
        # Parse JSON input
        
        # print(request.data)
        # data = request.data

        # Process each item in the list
        csv_data = [{"Name": "Test1","Age":1},
                    {"Name": "Test2","Age":2},
                    {"Name": "Test3","Age":3}
                    ]

        # Generate CSV
        csv_file = self.generate_csv(csv_data)

        print(csv_file)

        # Write the CSV content to a file
        file_name = "output.csv"  # Name of the file to be created
        file_path = f'./files/{file_name}'  # Path to save the file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_file)
                    
        # Check if file exists
        if os.path.exists(file_path):
            # Serve the file as a response
            response = FileResponse(open(file_path, 'rb'), as_attachment=True)
            
            # Delete the file after it has been served
            # os.remove(file_path)
            
            return response
        else:
            return Response({"error": "File not found"}, status=404)
    

    
# ***********************************
    def generate_csv(self, data):
        """
        Helper method to generate a CSV file from a list of dictionaries.
        """
        from io import StringIO
        import csv

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys(), delimiter='|')

        # Write header
        writer.writeheader()

        # Write rows
        writer.writerows(data)

        return output.getvalue()