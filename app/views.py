from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import pandas as pd
import psycopg2
from psycopg2 import sql
import requests
from simple_salesforce import Salesforce

def sync_salesforce_data(request):
    if request.method == 'GET':
        # Salesforce credentials
        username = "sireesha.rtestapp@totalitglobal.com"
        password = "Happy@23"
        security_token = "DiZfecvGR48xd6Ywo0N0nxMqr" 
        domain = "test"

        try:
            # Authenticate with Salesforce
            sf = Salesforce(username=username, password=password, security_token=security_token, domain=domain)

            # Salesforce SOQL query
            soql_query = """
                SELECT Project_Site__r.Country1__c,
                       Project_Site__r.City__c,
                       Project__r.Name AS projectname,
                       Skill_Level__c,
                       CurrencyIsoCode,
                       Project__c,
                       Purchase_Order__r.Customer__r.Name AS Customername,
                       Vendor_Project__r.Name AS vendorproject,
                       Vendor__r.Name AS vendorName,
                       MIN(Monthly_Rate__c) AS minMonthRate,
                       MAX(Monthly_Rate__c) AS maxMonthRate,
                       MIN(Vendor_Monthly_Rate__c) AS minVendorRate,
                       MAX(Vendor_Monthly_Rate__c) AS maxVendorRate,
                       AVG(Monthly_Rate__c) AS avgMonthlyRate,
                       AVG(Vendor_Monthly_Rate__c) AS avgVendorRate
                FROM Project_Services__c
                WHERE RecordType.Name = 'FTE'
                    AND Service_End_Date__c >= TODAY
                GROUP BY Project_Site__r.Country1__c, Project_Site__r.City__c, Vendor__r.Name, Project__r.Name, Purchase_Order__r.Customer__r.Name, Vendor_Project__r.Name, Skill_Level__c, CurrencyIsoCode, Project__c
            """

            # Perform query
            result = sf.query_all(soql_query)

            # Convert Salesforce query result to DataFrame
            records = result.get('records', [])
            df = pd.DataFrame(records)

            # Now you can proceed with storing this data in PostgreSQL or any other operations

            return JsonResponse({'status': 'success', 'message': 'Salesforce data synchronized successfully'}, status=200)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


from django.http import JsonResponse
from .utils import sync_salesforce_data

@require_http_methods(["POST"])
def trigger_sync(request):
    if request.method == 'POST':
        # Trigger Salesforce data synchronization
        response = sync_salesforce_data(request)
        return response
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
