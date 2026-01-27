from zeep import Client
import json
import re
import sys
from datetime import datetime

def validate_vat_tool(input_data: str) -> str:
    try:
        # Parse input
        data = json.loads(input_data)
        country_code = data["country_code"].upper()
        vat_number = re.sub(r'[\s\.\-]', '', data["vat_number"])
        
        # Call EU VIES service
        client = Client("https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl")
        response = client.service.checkVat(countryCode=country_code, vatNumber=vat_number)
        
        # Return result
        result = {
            "valid": bool(response.valid),
            "country_code": response.countryCode,
            "vat_number": response.vatNumber,
            "name": response.name or "Not available",
            "address": response.address or "Not available",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()})

def validate_vat_simple(vat_number: str) -> str:
    """Simple VAT validation function that takes just a VAT number"""
    try:
        # Clean the VAT number
        cleaned_vat = re.sub(r'[\s\.\-]', '', vat_number)
        
        # Extract country code (first 2 characters) and number
        if len(cleaned_vat) < 3:
            raise ValueError("VAT number too short")
            
        country_code = cleaned_vat[:2].upper()
        vat_num = cleaned_vat[2:]
        
        # Call EU VIES service
        client = Client("https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl")
        response = client.service.checkVat(countryCode=country_code, vatNumber=vat_num)
        
        # Return result
        result = {
            "valid": bool(response.valid),
            "country_code": response.countryCode,
            "vat_number": response.vatNumber,
            "name": response.name or "Not available",
            "address": response.address or "Not available",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validation.py <vat_number>")
        print("Example: python validation.py BE0403200393")
        sys.exit(1)
    
    vat_number = sys.argv[1]
    result = validate_vat_simple(vat_number)
    print(result)